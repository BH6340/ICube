/**
 * GAN 智能魔方 BLE 协议模块
 *
 * 实现 GAN Gen4 蓝牙协议，包括：
 *   - BLE 连接管理（Web Bluetooth API）
 *   - AES-128-CBC 加解密（MAC 地址 salt）
 *   - 协议消息解析（MOVE / FACELETS / BATTERY / HARDWARE）
 *   - MAC 地址自动获取（watchAdvertisements）
 *
 * 协议参考：afedotov/gan-web-bluetooth
 */

import { ModeOfOperation } from 'aes-js'

// ===== BLE 服务与特征值 UUID =====

const SERVICES = {
  GEN2: '6e400001-b5a3-f393-e0a9-e50e24dc4179',
  GEN3: '8653000a-43e6-47b7-9cb0-5fc21d4ae340',
  GEN4: '00000010-0000-fff7-fff6-fff5fff4fff0'
}

const CHARACTERISTICS = {
  GEN2_CMD: '28be4a4a-cd67-11e9-a32f-2a2ae2dbcce4',
  GEN2_STATE: '28be4cb6-cd67-11e9-a32f-2a2ae2dbcce4',
  GEN3_CMD: '8653000c-43e6-47b7-9cb0-5fc21d4ae340',
  GEN3_STATE: '8653000b-43e6-47b7-9cb0-5fc21d4ae340',
  GEN4_CMD: '0000fff5-0000-1000-8000-00805f9b34fb',
  GEN4_STATE: '0000fff6-0000-1000-8000-00805f9b34fb'
}

// AES-128-CBC 固定密钥（Gen2/Gen3/Gen4 通用）
const ENCRYPTION_KEY = {
  key: [0x01, 0x02, 0x42, 0x28, 0x31, 0x91, 0x16, 0x07,
        0x20, 0x05, 0x18, 0x54, 0x42, 0x11, 0x12, 0x53],
  iv: [0x11, 0x03, 0x32, 0x28, 0x21, 0x01, 0x76, 0x27,
       0x20, 0x95, 0x78, 0x14, 0x32, 0x12, 0x02, 0x43]
}

// GAN 厂商 CIC 列表（用于 manufacturer data 过滤）
const CIC_LIST = Array.from({ length: 256 }, (_, i) => (i << 8) | 0x01)

// 面 bitmask → 面序号映射（0=U, 1=R, 2=F, 3=D, 4=L, 5=B）
const FACE_BITMASKS = [2, 32, 8, 1, 16, 4]
const FACE_NAMES = 'URFDLB'

// ===== Gen4 事件类型 =====

const EventType = {
  MOVE: 0x01,
  GYRO: 0xEC,
  FACELETS: 0xED,
  DISCONNECT: 0xEA,
  BATTERY: 0xEF,
  MOVE_HISTORY: 0xD1,
  PRODUCT_DATE: 0xFA,
  HARDWARE_NAME: 0xFC,
  SOFTWARE_VERSION: 0xFD,
  HARDWARE_VERSION: 0xFE
}

// ===== 协议消息视图：按位读取二进制数据 =====

class ProtocolMessageView {
  constructor(message) {
    this.bits = Array.from(message)
      .map(byte => (byte + 0x100).toString(2).slice(1))
      .join('')
  }

  /**
   * 从指定比特位读取数值
   * @param {number} startBit 起始位
   * @param {number} bitLength 位长度（≤8 / 16 / 32）
   * @param {boolean} littleEndian 是否小端序
   */
  getBitWord(startBit, bitLength, littleEndian = false) {
    if (bitLength <= 8) {
      return parseInt(this.bits.slice(startBit, startBit + bitLength), 2)
    }
    if (bitLength === 16 || bitLength === 32) {
      const buf = new Uint8Array(bitLength / 8)
      for (let i = 0; i < buf.length; i++) {
        buf[i] = parseInt(this.bits.slice(8 * i + startBit, 8 * i + startBit + 8), 2)
      }
      const dv = new DataView(buf.buffer)
      return bitLength === 16
        ? dv.getUint16(0, littleEndian)
        : dv.getUint32(0, littleEndian)
    }
    throw new Error(`不支持的位长度: ${bitLength}`)
  }
}

// ===== AES-128-CBC 加密器（GAN salt 方案） =====

class CubeEncrypter {
  /**
   * @param {Array<number>} key 16 字节密钥
   * @param {Array<number>} iv 16 字节 IV
   * @param {Uint8Array} salt 6 字节 salt（MAC 地址倒序）
   */
  constructor(key, iv, salt) {
    this._key = new Uint8Array(key)
    this._iv = new Uint8Array(iv)
    // 用 salt 修正前 6 字节
    for (let i = 0; i < 6; i++) {
      this._key[i] = (key[i] + salt[i]) % 0xFF
      this._iv[i] = (iv[i] + salt[i]) % 0xFF
    }
  }

  encrypt(data) {
    const res = new Uint8Array(data)
    this._processChunk(res, 0, true)
    if (res.length > 16) this._processChunk(res, res.length - 16, true)
    return res
  }

  decrypt(data) {
    const res = new Uint8Array(data)
    if (res.length > 16) this._processChunk(res, res.length - 16, false)
    this._processChunk(res, 0, false)
    return res
  }

  _processChunk(buffer, offset, isEncrypt) {
    const cipher = new ModeOfOperation.cbc(this._key, this._iv)
    const chunk = buffer.subarray(offset, offset + 16)
    const result = isEncrypt ? cipher.encrypt(chunk) : cipher.decrypt(chunk)
    buffer.set(result, offset)
  }
}

// ===== Gen4 协议驱动 =====

class Gen4ProtocolDriver {
  constructor() {
    this._moveBuffer = []
    this._lastSerial = -1
  }

  /**
   * 构造命令消息（20 字节，零填充）
   */
  createCommandMessage(command) {
    const msg = new Uint8Array(20).fill(0)
    switch (command) {
      case 'REQUEST_FACELETS':
        msg.set([0xDD, 0x04, 0x00, 0xED, 0x00, 0x00])
        break
      case 'REQUEST_HARDWARE':
        msg.set([0xDF, 0x03, 0x00, 0x00, 0x00])
        break
      case 'REQUEST_BATTERY':
        msg.set([0xDD, 0x04, 0x00, 0xEF, 0x00, 0x00])
        break
      case 'REQUEST_RESET':
        msg.set([0xD2, 0x0D, 0x05, 0x39, 0x77, 0x00, 0x00,
          0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0x00, 0x00, 0x00])
        break
      default:
        return undefined
    }
    return msg
  }

  /**
   * 处理 State Characteristic 通知，解析事件
   * 一个通知包可能包含多个事件拼接，循环解析
   * MOVE 事件先缓冲，FACELETS 事件到达后按序发出
   */
  handleStateEvent(eventMessage) {
    const events = []
    const timestamp = Date.now()
    let offset = 0
    const totalBytes = eventMessage.length

    while (offset + 2 <= totalBytes) {
      const eventType = eventMessage[offset]
      const dataLength = eventMessage[offset + 1]
      const eventBytes = totalBytes - offset
      // 估算事件总字节：2 字节头 + dataLength 字节数据
      const eventTotalBytes = 2 + dataLength

      // 如果剩余字节不足以解析一个完整事件，跳出
      if (offset + 2 > totalBytes) break

      // 用当前偏移量切片创建消息视图
      const slice = eventMessage.slice(offset)
      const msg = new ProtocolMessageView(slice)

      if (eventType === EventType.MOVE) {
        const move = this._parseMove(msg, timestamp)
        if (move) this._moveBuffer.push(move)
      } else if (eventType === EventType.FACELETS) {
        const facelets = this._parseFacelets(msg, timestamp)
        if (facelets) {
          while (this._moveBuffer.length > 0) {
            events.push(this._moveBuffer.shift())
          }
          events.push(facelets)
          this._lastSerial = facelets.serial
        }
      } else if (eventType === EventType.BATTERY) {
        // dataLength=2 时：第 1 字节 = 充电状态，第 2 字节 = 电量百分比
        const charging = msg.getBitWord(16, 8)
        const batteryLevel = dataLength >= 2 ? msg.getBitWord(24, 8) : msg.getBitWord(16, 8)
        events.push({ type: 'BATTERY', timestamp, batteryLevel, charging, dataLength })
      } else if (eventType === EventType.GYRO) {
        const gyro = this._parseGyro(msg, timestamp)
        if (gyro) events.push(gyro)
      } else if (eventType === EventType.DISCONNECT) {
        events.push({ type: 'DISCONNECT', timestamp })
      } else if (eventType === EventType.HARDWARE_NAME) {
        const name = this._parseString(msg, 16)
        if (name) events.push({ type: 'HARDWARE', timestamp, hardwareName: name })
      } else if (eventType === EventType.SOFTWARE_VERSION) {
        const ver = this._parseString(msg, 16)
        if (ver) events.push({ type: 'HARDWARE', timestamp, softwareVersion: ver })
      } else if (eventType === EventType.HARDWARE_VERSION) {
        const ver = this._parseString(msg, 16)
        if (ver) events.push({ type: 'HARDWARE', timestamp, hardwareVersion: ver })
      }

      // 推进偏移量：如果 dataLength 可用就按它走，否则按事件类型固定长度
      if (dataLength > 0 && offset + eventTotalBytes <= totalBytes) {
        offset += eventTotalBytes
      } else {
        // dataLength=0 或越界，用固定长度推
        const fixedLen = this._eventFixedLength(eventType)
        if (fixedLen > 0) {
          offset += fixedLen
        } else {
          // 无法确定长度，跳出避免死循环
          break
        }
      }
    }

    // 安全阀：缓冲区过大时强制输出
    if (this._moveBuffer.length > 50) {
      while (this._moveBuffer.length > 0) {
        events.push(this._moveBuffer.shift())
      }
    }

    return events
  }

  /** 各事件类型的固定字节长度（用于多事件解析时推算偏移） */
  _eventFixedLength(eventType) {
    switch (eventType) {
      case EventType.MOVE: return 9
      case EventType.GYRO: return 12
      case EventType.FACELETS: return 16
      case EventType.BATTERY: return 4
      case EventType.DISCONNECT: return 2
      case EventType.HARDWARE_NAME: return 10
      case EventType.SOFTWARE_VERSION: return 10
      case EventType.HARDWARE_VERSION: return 10
      default: return 0
    }
  }

  _parseMove(msg, timestamp) {
    const cubeTimestamp = msg.getBitWord(16, 32, true)
    const serial = msg.getBitWord(48, 16, true)
    const direction = msg.getBitWord(64, 2)
    const faceBitmask = msg.getBitWord(66, 6)
    const face = FACE_BITMASKS.indexOf(faceBitmask)
    if (face === -1) return null
    const move = (FACE_NAMES.charAt(face) + ' \''.charAt(direction)).trim()
    return {
      type: 'MOVE', timestamp, serial, face, direction, move,
      cubeTimestamp, localTimestamp: timestamp
    }
  }

  _parseFacelets(msg, timestamp) {
    const serial = msg.getBitWord(16, 16, true)
    const cp = [], co = [], ep = [], eo = []

    for (let i = 0; i < 7; i++) {
      cp.push(msg.getBitWord(32 + i * 3, 3))
      co.push(msg.getBitWord(53 + i * 2, 2))
    }
    cp.push(28 - cp.reduce((a, v) => a + v, 0))
    co.push((3 - (co.reduce((a, v) => a + v, 0) % 3)) % 3)

    for (let i = 0; i < 11; i++) {
      ep.push(msg.getBitWord(69 + i * 4, 4))
      eo.push(msg.getBitWord(113 + i, 1))
    }
    ep.push(66 - ep.reduce((a, v) => a + v, 0))
    eo.push((2 - (eo.reduce((a, v) => a + v, 0) % 2)) % 2)

    const isSolved = cp.every((v, i) => v === i) &&
      co.every(v => v === 0) &&
      ep.every((v, i) => v === i) &&
      eo.every(v => v === 0)

    return { type: 'FACELETS', timestamp, serial, state: { cp, co, ep, eo }, isSolved }
  }

  _parseString(msg, startBit) {
    let str = ''
    for (let i = 0; i < 8; i++) {
      const code = msg.getBitWord(startBit + i * 8, 8)
      if (code === 0) break
      str += String.fromCharCode(code)
    }
    return str || null
  }

  _parseGyro(msg, timestamp) {
    const toFloat = (raw) => (1 - (raw >> 15) * 2) * (raw & 0x7FFF) / 0x7FFF
    const qw = msg.getBitWord(16, 16)
    const qx = msg.getBitWord(32, 16)
    const qy = msg.getBitWord(48, 16)
    const qz = msg.getBitWord(64, 16)
    const vx = msg.getBitWord(80, 4)
    const vy = msg.getBitWord(84, 4)
    const vz = msg.getBitWord(88, 4)
    return {
      type: 'GYRO', timestamp,
      quaternion: { w: toFloat(qw), x: toFloat(qx), y: toFloat(qy), z: toFloat(qz) },
      velocity: {
        x: (1 - (vx >> 3) * 2) * (vx & 0x7),
        y: (1 - (vy >> 3) * 2) * (vy & 0x7),
        z: (1 - (vz >> 3) * 2) * (vz & 0x7)
      }
    }
  }
}

// ===== BLE 客户端 =====

export class GanCubeClient {
  constructor() {
    this._device = null
    this._commandChar = null
    this._stateChar = null
    this._encrypter = null
    this._driver = new Gen4ProtocolDriver()
    this._eventCallback = null
    this._mac = null
    this._name = null
    this._connected = false
    this._connecting = false
    // 绑定回调，保证 removeEventListener 引用一致
    this._onDisconnect = this._onDisconnect.bind(this)
    this._onStateUpdate = this._onStateUpdate.bind(this)
    this._watchAdvCleanup = null
  }

  /** 给 Promise 加超时，防止 GATT 操作 hang 住 */
  _withTimeout(promise, ms = 8000) {
    return Promise.race([
      promise,
      new Promise((_, reject) => setTimeout(() => reject(new Error('操作超时')), ms))
    ])
  }

  get deviceName() { return this._name || 'GAN-XXXX' }
  get deviceMAC() { return this._mac || '00:00:00:00:00:00' }
  get connected() { return this._connected }

  static get isSupported() {
    return typeof navigator !== 'undefined' && !!navigator.bluetooth
  }

  /** 注册事件回调 */
  onEvent(callback) { this._eventCallback = callback }

  /**
   * 连接 GAN 智能魔方
   * @param {{ onMacAddressRequired?: () => Promise<string|null> }} options
   */
  async connect({ onMacAddressRequired } = {}) {
    if (!GanCubeClient.isSupported) {
      throw new Error('当前浏览器不支持 Web Bluetooth API，请使用 Chrome 或 Edge 浏览器')
    }

    // 防止重复连接
    if (this._connecting) return
    this._connecting = true

    try {
      // 已连接则直接返回
      if (this._device?.gatt?.connected) return

      // 场景 A：已有 device 对象，直接重连（无需重新选择设备）
      if (this._device && this._mac) {
        await this._reconnect()
        return
      }

      // 场景 B：有 MAC 但无 device（刷新后自动重连失败的情况）
      //         仍需弹出设备选择器，但复用已有 MAC
      await this._firstConnect({ onMacAddressRequired })
    } finally {
      this._connecting = false
    }
  }

  /** 首次连接：设备选择 + MAC 获取 + GATT 连接 */
  async _firstConnect({ onMacAddressRequired }) {
    // 1. 弹出设备选择器
    this._device = await navigator.bluetooth.requestDevice({
      filters: [
        { namePrefix: 'GAN' },
        { namePrefix: 'MG' },
        { namePrefix: 'AiCube' }
      ],
      optionalServices: [SERVICES.GEN4, SERVICES.GEN3, SERVICES.GEN2],
      optionalManufacturerData: CIC_LIST
    })
    this._name = this._device.name || 'GAN-XXXX'

    // 2. 获取 MAC 地址（加密 salt 来源）— 复用已预设的 MAC
    if (!this._mac) {
      this._mac = await this._autoRetrieveMac()
    }
    if (!this._mac && onMacAddressRequired) {
      this._mac = await onMacAddressRequired(this._device)
    }
    if (!this._mac) {
      throw new Error('无法获取魔方 MAC 地址，连接终止')
    }

    // 3. 连接 GATT + 设置服务（带超时+重试）
    await this._connectAndSetupWithRetry()
    this._connected = true
  }

  /** 重连：已有 device 和 MAC，直接 gatt.connect + 设置服务 */
  async _reconnect() {
    // 如果 GATT 还显示已连接但实际已失效，先断开再重连
    if (this._device?.gatt?.connected) {
      try { this._device.gatt.disconnect() } catch {}
      await new Promise(r => setTimeout(r, 500))
    }
    await this._connectAndSetupWithRetry()
    this._connected = true
  }

  /**
   * 完整连接流程（带超时 + 递增重试）
   * 重试整个 connect → getServices → setup 流程，不只是 gatt.connect()
   */
  async _connectAndSetupWithRetry() {
    const salt = new Uint8Array(
      this._mac.split(/[:-\s]+/).map(c => parseInt(c, 16)).reverse()
    )
    const delays = [500, 1000, 1500]
    let lastErr = null

    for (let i = 0; i <= delays.length; i++) {
      try {
        // 每次重试前确保彻底断开
        if (this._device?.gatt?.connected) {
          try { this._device.gatt.disconnect() } catch {}
          await new Promise(r => setTimeout(r, 300))
        }

        // gatt.connect() 加超时防止 hang
        await this._withTimeout(this._device.gatt.connect(), 8000)

        // 连接成功后立即 setup（也可能失败）
        await this._setupService(this._device.gatt, salt)
        return
      } catch (err) {
        lastErr = err
        if (i < delays.length) {
          await new Promise(r => setTimeout(r, delays[i]))
        }
      }
    }
    throw lastErr || new Error('连接失败')
  }

  /** 发现并设置 Gen4 服务 + 特征值 + 监听通知 */
  async _setupService(gatt, salt) {
    const services = await this._withTimeout(gatt.getPrimaryServices(), 8000)

    // 查找 Gen4 服务和特征值
    for (const service of services) {
      const uuid = service.uuid.toLowerCase()
      if (uuid === SERVICES.GEN4) {
        this._commandChar = await this._withTimeout(service.getCharacteristic(CHARACTERISTICS.GEN4_CMD), 5000)
        this._stateChar = await this._withTimeout(service.getCharacteristic(CHARACTERISTICS.GEN4_STATE), 5000)
        this._encrypter = new CubeEncrypter(ENCRYPTION_KEY.key, ENCRYPTION_KEY.iv, salt)
        break
      }
    }

    if (!this._commandChar) {
      throw new Error('未找到 GAN Gen4 BLE 服务，可能是不支持的魔方型号')
    }

    // 监听 State 通知（先移除再添加，防止重连时重复注册）
    this._device.removeEventListener('gattserverdisconnected', this._onDisconnect)
    this._stateChar.removeEventListener('characteristicvaluechanged', this._onStateUpdate)
    this._device.addEventListener('gattserverdisconnected', this._onDisconnect)
    this._stateChar.addEventListener('characteristicvaluechanged', this._onStateUpdate)
    await this._withTimeout(this._stateChar.startNotifications(), 5000)

    // 请求初始状态
    await this.sendCommand('REQUEST_FACELETS')
    await this.sendCommand('REQUEST_BATTERY')
  }

  /** 发送命令到魔方 */
  async sendCommand(command) {
    if (!this._commandChar || !this._encrypter) return
    const msg = this._driver.createCommandMessage(command)
    if (!msg) return
    const encrypted = this._encrypter.encrypt(msg)
    try {
      if (this._commandChar.writeValueWithResponse) {
        await this._commandChar.writeValueWithResponse(encrypted)
      } else {
        await this._commandChar.writeValue(encrypted)
      }
    } catch (err) {
      // GATT 操作可能因连接断开而失败，不向上抛
    }
  }

  /** 复位魔方硬件状态 */
  async resetCube() {
    await this.sendCommand('REQUEST_RESET')
  }

  /** 请求电量信息 */
  async requestBattery() {
    await this.sendCommand('REQUEST_BATTERY')
  }

  /** 断开连接（用户主动断开，完全清理） */
  async disconnect() {
    this._fullCleanup()
  }

  /** 同步断开（供 beforeunload 使用，完全清理） */
  disconnectSync() {
    this._fullCleanup()
  }

  /** GATT 断开事件回调 */
  _onDisconnect() {
    this._cleanupState()
  }

  /** 清理所有内部状态 */
  _cleanup() {
    if (this._watchAdvCleanup) {
      this._watchAdvCleanup()
      this._watchAdvCleanup = null
    }
    if (this._device) {
      this._device.removeEventListener('gattserverdisconnected', this._onDisconnect)
    }
    if (this._stateChar) {
      this._stateChar.removeEventListener('characteristicvaluechanged', this._onStateUpdate)
      this._stateChar.stopNotifications().catch(() => {})
    }
    if (this._device?.gatt?.connected) {
      this._device.gatt.disconnect()
    }
    this._cleanupState()
  }

  /** 仅清理内部引用（不触发 GATT 断开，保留 device/mac/name 用于重连） */
  _cleanupState() {
    if (this._eventCallback) {
      this._eventCallback({ type: 'DISCONNECT', timestamp: Date.now() })
    }
    this._commandChar = null
    this._stateChar = null
    this._encrypter = null
    this._driver = new Gen4ProtocolDriver()
    this._connected = false
  }

  /** 完全清理：断开 GATT + 移除监听，但保留 device/mac/name 用于重连 */
  _fullCleanup() {
    if (this._watchAdvCleanup) {
      this._watchAdvCleanup()
      this._watchAdvCleanup = null
    }
    if (this._device) {
      this._device.removeEventListener('gattserverdisconnected', this._onDisconnect)
    }
    if (this._stateChar) {
      this._stateChar.removeEventListener('characteristicvaluechanged', this._onStateUpdate)
      this._stateChar.stopNotifications().catch(() => {})
    }
    if (this._device?.gatt?.connected) {
      this._device.gatt.disconnect()
    }
    this._cleanupState()
    // 保留 _device / _mac / _name，断开后可快速重连
  }

  /** State Characteristic 通知回调 */
  async _onStateUpdate(evt) {
    const value = evt.target.value
    if (!value || value.byteLength < 16) return
    if (!this._encrypter || !this._driver || !this._eventCallback) return
    const data = new Uint8Array(value.buffer, value.byteOffset, value.byteLength)
    try {
      const decrypted = this._encrypter.decrypt(data)
      const events = this._driver.handleStateEvent(decrypted)
      for (const e of events) {
        this._eventCallback(e)
      }
    } catch (err) {
      console.error('GAN 数据解析失败:', err)
    }
  }

  /** 通过 watchAdvertisements 自动获取 MAC 地址 */
  async _autoRetrieveMac() {
    if (typeof this._device?.watchAdvertisements !== 'function') return null
    return new Promise(resolve => {
      const controller = new AbortController()
      let settled = false
      let timer = null

      const finish = (mac) => {
        if (settled) return
        settled = true
        if (timer) clearTimeout(timer)
        this._device.removeEventListener('advertisementreceived', onAdv)
        try { controller.abort() } catch {}
        this._watchAdvCleanup = null
        resolve(mac)
      }

      const onAdv = (evt) => {
        const mac = this._extractMac(evt.manufacturerData)
        finish(mac || null)
      }

      this._watchAdvCleanup = () => finish(null)
      this._device.addEventListener('advertisementreceived', onAdv)
      this._device.watchAdvertisements({ signal: controller.signal })
        .catch(() => finish(null))
      timer = setTimeout(() => finish(null), 10000)
    })
  }

  /** 从 manufacturer data 提取 MAC 地址（最后 6 字节，倒序） */
  _extractMac(manufacturerData) {
    let dataView
    if (manufacturerData instanceof DataView) {
      dataView = new DataView(manufacturerData.buffer.slice(2, 11))
    } else {
      for (const id of CIC_LIST) {
        if (manufacturerData.has(id)) {
          dataView = new DataView(manufacturerData.get(id).buffer.slice(0, 9))
          break
        }
      }
    }
    if (!dataView || dataView.byteLength < 6) return null
    const mac = []
    for (let i = 1; i <= 6; i++) {
      mac.push(dataView.getUint8(dataView.byteLength - i).toString(16).toUpperCase().padStart(2, '0'))
    }
    return mac.join(':')
  }
}

// ===== 单例导出 =====

let _instance = null

const STORAGE_KEY = 'icube_smartcube_last_device'

export function getCubeClient() {
  if (!_instance) _instance = new GanCubeClient()
  return _instance
}

/**
 * 尝试自动重连（页面加载时调用）
 * - 从 localStorage 读取上次设备名和 MAC
 * - 用 navigator.bluetooth.getDevices() 查找已授权设备
 * - 找到匹配设备则静默重连
 * @returns {Promise<boolean>} 是否成功启动重连
 */
export async function tryAutoReconnect() {
  const saved = _loadSavedDevice()
  if (!saved) return false

  const client = getCubeClient()
  // 预设 MAC 和 Name，即使 getDevices 失败也能走 _firstConnect 复用
  if (!client._mac) client._mac = saved.mac
  if (!client._name) client._name = saved.name

  if (!navigator.bluetooth?.getDevices) return false

  try {
    const devices = await navigator.bluetooth.getDevices()
    const match = devices.find(d => d.name === saved.name)
    if (!match) return false

    client._device = match
    client._name = match.name || saved.name
    await client._reconnect()
    return true
  } catch (err) {
    console.warn('自动重连失败:', err)
    return false
  }
}

/** 保存设备信息到 localStorage */
export function saveDeviceInfo(name, mac) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ name, mac }))
  } catch {}
}

/** 清除保存的设备信息 */
export function clearSavedDevice() {
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch {}
}

function _loadSavedDevice() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

