/**
 * GAN 智能魔方 BLE 协议解析层（App 端移植版）
 *
 * 实现 GAN Gen4 蓝牙协议解析，与蓝牙实现完全解耦：
 *   - AES-128-CBC 加解密（MAC 地址 salt）
 *   - 协议消息解析（MOVE / GYRO / FACELETS / BATTERY / HARDWARE / DISCONNECT）
 *   - 纯数据进、事件回调出，不依赖任何平台蓝牙 API
 *
 * 协议参考：afedotov/gan-web-bluetooth
 *
 * 使用方式：
 *   import { Gen4ProtocolDriver, SERVICES, CHARACTERISTICS } from '@/utils/gan-ble'
 *
 *   const driver = new Gen4ProtocolDriver('AA:BB:CC:DD:EE:FF')
 *   driver.onMove = (event) => { ... }
 *   driver.onFacelets = (event) => { ... }
 *   // 收到蓝牙通知时：
 *   driver.handleStateNotification(data) // data 为 Uint8Array 原始加密数据
 *   // 发送命令时：
 *   const cmd = driver.createCommandMessage('REQUEST_FACELETS')
 */

import { ModeOfOperation } from 'aes-js'

// ===== BLE 服务与特征值 UUID =====

const SERVICES = {
  GEN2: '6e400001-b5a3-f393-e0a9-e50e24dc4179',
  GEN3: '8653000a-43e6-47b7-9cb0-5fc21d4ae340',
  GEN4: '00000010-0000-fff7-fff6-fff5fff4fff0',
}

const CHARACTERISTICS = {
  GEN2_CMD: '28be4a4a-cd67-11e9-a32f-2a2ae2dbcce4',
  GEN2_STATE: '28be4cb6-cd67-11e9-a32f-2a2ae2dbcce4',
  GEN3_CMD: '8653000c-43e6-47b7-9cb0-5fc21d4ae340',
  GEN3_STATE: '8653000b-43e6-47b7-9cb0-5fc21d4ae340',
  GEN4_CMD: '0000fff5-0000-1000-8000-00805f9b34fb',
  GEN4_STATE: '0000fff6-0000-1000-8000-00805f9b34fb',
}

// AES-128-CBC 固定密钥（Gen2/Gen3/Gen4 通用）
const ENCRYPTION_KEY = {
  key: [
    0x01, 0x02, 0x42, 0x28, 0x31, 0x91, 0x16, 0x07, 0x20, 0x05, 0x18, 0x54, 0x42, 0x11, 0x12, 0x53,
  ],
  iv: [
    0x11, 0x03, 0x32, 0x28, 0x21, 0x01, 0x76, 0x27, 0x20, 0x95, 0x78, 0x14, 0x32, 0x12, 0x02, 0x43,
  ],
}

// GAN 厂商 CIC 列表（用于 manufacturer data 过滤）
const CIC_LIST = Array.from({ length: 256 }, (_, i) => (i << 8) | 0x01)

// 面 bitmask → 面序号映射（0=U, 1=R, 2=F, 3=D, 4=L, 5=B）
const FACE_BITMASKS = [2, 32, 8, 1, 16, 4]
const FACE_NAMES = 'URFDLB'

// ===== Gen4 事件类型 =====

const EventType = {
  MOVE: 0x01,
  GYRO: 0xec,
  FACELETS: 0xed,
  DISCONNECT: 0xea,
  BATTERY: 0xef,
  MOVE_HISTORY: 0xd1,
  PRODUCT_DATE: 0xfa,
  HARDWARE_NAME: 0xfc,
  SOFTWARE_VERSION: 0xfd,
  HARDWARE_VERSION: 0xfe,
}

// ===== 协议消息视图：按位读取二进制数据 =====

class ProtocolMessageView {
  constructor(message) {
    this.bits = Array.from(message)
      .map((byte) => (byte + 0x100).toString(2).slice(1))
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
      return bitLength === 16 ? dv.getUint16(0, littleEndian) : dv.getUint32(0, littleEndian)
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
      this._key[i] = (key[i] + salt[i]) % 0xff
      this._iv[i] = (iv[i] + salt[i]) % 0xff
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

// ===== 工具函数 =====

/**
 * 将 MAC 地址字符串转换为倒序 Uint8Array（作为 AES salt）
 * @param {string} mac MAC 地址，如 "AA:BB:CC:DD:EE:FF"
 * @returns {Uint8Array} 6 字节倒序 salt
 */
function macToSalt(mac) {
  return new Uint8Array(
    mac
      .split(/[:-\s]+/)
      .map((c) => parseInt(c, 16))
      .reverse()
  )
}

/**
 * 反转一步转动方向（R → R'，R' → R，R2 不变）
 * @param {string} move 单步转动，如 "R"、"U'"、"D2"
 * @returns {string} 反向转动
 */
function inverseMove(move) {
  if (move.endsWith("'")) return move.charAt(0)
  if (move.endsWith('2')) return move
  return move + "'"
}

// ===== Gen4 协议驱动 =====

class Gen4ProtocolDriver {
  /**
   * @param {string} macAddress 魔方 MAC 地址，如 "AA:BB:CC:DD:EE:FF"
   */
  constructor(macAddress) {
    this._mac = macAddress
    const salt = macToSalt(macAddress)
    this._encrypter = new CubeEncrypter(ENCRYPTION_KEY.key, ENCRYPTION_KEY.iv, salt)
    this._moveBuffer = []
    this._lastSerial = -1

    // ===== 事件回调（由使用方赋值） =====
    /** 转动事件回调 @type {(event: object) => void} */
    this.onMove = null
    /** 陀螺仪事件回调 @type {(event: object) => void} */
    this.onGyro = null
    /** 面块状态事件回调 @type {(event: object) => void} */
    this.onFacelets = null
    /** 电量事件回调 @type {(event: object) => void} */
    this.onBattery = null
    /** 硬件信息事件回调 @type {(event: object) => void} */
    this.onHardware = null
    /** 断开连接事件回调 @type {(event: object) => void} */
    this.onDisconnect = null
  }

  /** 获取魔方 MAC 地址 */
  get macAddress() {
    return this._mac
  }

  /**
   * 构造加密后的命令消息（20 字节，零填充）
   * @param {string} command 命令类型：REQUEST_FACELETS / REQUEST_HARDWARE / REQUEST_BATTERY / REQUEST_RESET
   * @returns {Uint8Array|undefined} 加密后的命令数据，可直接写入 CMD characteristic
   */
  createCommandMessage(command) {
    const msg = new Uint8Array(20).fill(0)
    switch (command) {
      case 'REQUEST_FACELETS':
        msg.set([0xdd, 0x04, 0x00, 0xed, 0x00, 0x00])
        break
      case 'REQUEST_HARDWARE':
        msg.set([0xdf, 0x03, 0x00, 0x00, 0x00])
        break
      case 'REQUEST_BATTERY':
        msg.set([0xdd, 0x04, 0x00, 0xef, 0x00, 0x00])
        break
      case 'REQUEST_RESET':
        msg.set([
          0xd2, 0x0d, 0x05, 0x39, 0x77, 0x00, 0x00, 0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0x00, 0x00,
          0x00,
        ])
        break
      default:
        return undefined
    }
    return this._encrypter.encrypt(msg)
  }

  /**
   * 处理 State Characteristic 通知数据（加密原始数据）
   * 内部完成 AES 解密 → 协议解析 → 回调分发
   * 一个通知包可能包含多个事件拼接，循环解析并依次触发回调
   * MOVE 事件先缓冲，FACELETS 事件到达后按序发出
   *
   * @param {Uint8Array} data 从蓝牙特征值收到的原始加密数据
   */
  handleStateNotification(data) {
    if (!data || data.byteLength < 16) return
    try {
      const decrypted = this._encrypter.decrypt(data)
      const events = this._handleStateEvent(decrypted)
      for (const event of events) {
        this._dispatchEvent(event)
      }
    } catch (err) {
      console.error('GAN 数据解析失败:', err)
    }
  }

  /**
   * 分发解析后的事件到对应回调
   * @param {object} event 解析后的事件对象
   */
  _dispatchEvent(event) {
    switch (event.type) {
      case 'MOVE':
        if (this.onMove) this.onMove(event)
        break
      case 'GYRO':
        if (this.onGyro) this.onGyro(event)
        break
      case 'FACELETS':
        if (this.onFacelets) this.onFacelets(event)
        break
      case 'BATTERY':
        if (this.onBattery) this.onBattery(event)
        break
      case 'HARDWARE':
        if (this.onHardware) this.onHardware(event)
        break
      case 'DISCONNECT':
        if (this.onDisconnect) this.onDisconnect(event)
        break
      default:
        break
    }
  }

  /**
   * 解析已解密的状态消息，返回事件数组
   * 一个通知包可能包含多个事件拼接，循环解析
   * MOVE 事件先缓冲，FACELETS 事件到达后按序发出
   *
   * @param {Uint8Array} eventMessage 已解密的消息数据
   * @returns {Array<object>} 解析出的事件列表
   */
  _handleStateEvent(eventMessage) {
    const events = []
    const timestamp = Date.now()
    let offset = 0
    const totalBytes = eventMessage.length

    while (offset + 2 <= totalBytes) {
      const eventType = eventMessage[offset]
      const dataLength = eventMessage[offset + 1]
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
      case EventType.MOVE:
        return 9
      case EventType.GYRO:
        return 12
      case EventType.FACELETS:
        return 16
      case EventType.BATTERY:
        return 4
      case EventType.DISCONNECT:
        return 2
      case EventType.HARDWARE_NAME:
        return 10
      case EventType.SOFTWARE_VERSION:
        return 10
      case EventType.HARDWARE_VERSION:
        return 10
      default:
        return 0
    }
  }

  _parseMove(msg, timestamp) {
    const cubeTimestamp = msg.getBitWord(16, 32, true)
    const serial = msg.getBitWord(48, 16, true)
    const direction = msg.getBitWord(64, 2)
    const faceBitmask = msg.getBitWord(66, 6)
    const face = FACE_BITMASKS.indexOf(faceBitmask)
    if (face === -1) return null
    const move = (FACE_NAMES.charAt(face) + " '".charAt(direction)).trim()
    return {
      type: 'MOVE',
      timestamp,
      serial,
      face,
      direction,
      move,
      cubeTimestamp,
      localTimestamp: timestamp,
    }
  }

  _parseFacelets(msg, timestamp) {
    const serial = msg.getBitWord(16, 16, true)
    const cp = [],
      co = [],
      ep = [],
      eo = []

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

    const isSolved =
      cp.every((v, i) => v === i) &&
      co.every((v) => v === 0) &&
      ep.every((v, i) => v === i) &&
      eo.every((v) => v === 0)

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
    const toFloat = (raw) => ((1 - (raw >> 15) * 2) * (raw & 0x7fff)) / 0x7fff
    const qw = msg.getBitWord(16, 16)
    const qx = msg.getBitWord(32, 16)
    const qy = msg.getBitWord(48, 16)
    const qz = msg.getBitWord(64, 16)
    const vx = msg.getBitWord(80, 4)
    const vy = msg.getBitWord(84, 4)
    const vz = msg.getBitWord(88, 4)
    return {
      type: 'GYRO',
      timestamp,
      quaternion: { w: toFloat(qw), x: toFloat(qx), y: toFloat(qy), z: toFloat(qz) },
      velocity: {
        x: (1 - (vx >> 3) * 2) * (vx & 0x7),
        y: (1 - (vy >> 3) * 2) * (vy & 0x7),
        z: (1 - (vz >> 3) * 2) * (vz & 0x7),
      },
    }
  }
}

// ===== 导出 =====

export {
  // 常量
  SERVICES,
  CHARACTERISTICS,
  ENCRYPTION_KEY,
  CIC_LIST,
  FACE_BITMASKS,
  FACE_NAMES,
  EventType,
  // 核心类
  ProtocolMessageView,
  CubeEncrypter,
  Gen4ProtocolDriver,
  // 工具函数
  macToSalt,
  inverseMove,
}
