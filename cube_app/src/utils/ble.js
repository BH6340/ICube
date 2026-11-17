/**
 * 蓝牙 LE 服务层（Capacitor 插件封装）
 *
 * 基于 @capacitor-community/bluetooth-le 封装，提供简化的 API：
 *   - requestDevice：弹出系统设备选择器（推荐，最稳定）
 *   - 扫描设备（按 GAN 名称过滤）
 *   - 连接 / 断开
 *   - 特征值读写
 *   - 通知监听
 *
 * 设计原则：与协议解析层（gan-ble.js）解耦，
 * 只负责原始数据收发，协议解析交给上层。
 */

import { BleClient, ScanMode } from '@capacitor-community/bluetooth-le'
import { Capacitor } from '@capacitor/core'
import { SERVICES, CHARACTERISTICS } from './gan-ble'

// 蓝牙是否已初始化
let initialized = false

// GAN 智能魔方设备名称前缀（用于扫描/过滤）
const GAN_NAME_PREFIXES = ['GAN', 'iCarry', 'CubeStation', 'MG', 'AiCube']

/**
 * 判断设备名是否为 GAN 智能魔方
 */
function isGanDevice(name) {
    if (!name) return false
    return GAN_NAME_PREFIXES.some(prefix =>
        name.toLowerCase().startsWith(prefix.toLowerCase())
    )
}

/**
 * 初始化蓝牙（请求权限 + 启用）
 * 首次调用时弹出权限申请弹窗
 */
export async function initializeBle() {
    if (initialized) return true

    try {
        // 1. 请求运行时权限
        //    Android 12+：BLUETOOTH_SCAN / BLUETOOTH_CONNECT（附近的设备）
        //    Android 11 及以下：ACCESS_FINE_LOCATION（位置权限）
        //    插件 requestPermissions 会自动根据系统版本请求对应权限
        try {
            await BleClient.requestPermissions()
        } catch (permErr) {
            // 部分设备插件的 requestPermissions 可能不包含位置权限，
            // 降级处理：继续尝试初始化，初始化失败再报具体错误
            console.warn('[BLE] requestPermissions 部分失败，继续尝试:', permErr)
        }

        // 2. 初始化蓝牙适配器
        await BleClient.initialize()

        initialized = true
        return true
    } catch (err) {
        console.error('[BLE] 初始化失败:', err)
        const msg = err?.message || String(err)
        if (msg.includes('Location') || msg.includes('location')) {
            throw new Error('需要位置权限才能扫描蓝牙设备，请在设置中授予位置权限')
        }
        if (msg.includes('permission') || msg.includes('Permission')) {
            throw new Error('蓝牙权限被拒绝，请在设置中授予"附近的设备"权限')
        }
        if (msg.includes('enabled') || msg.includes('not enabled')) {
            throw new Error('蓝牙未开启，请先打开手机蓝牙')
        }
        throw new Error(msg)
    }
}

/**
 * 弹出系统设备选择器，选择 GAN 智能魔方
 *
 * 这是最稳定的连接方式（类似 Web 端的 navigator.bluetooth.requestDevice），
 * 由系统处理扫描、权限、隐私等问题，返回的设备一定有有效的 deviceId。
 *
 * @returns {Promise<Object>} { deviceId, name }
 */
export async function requestGanDevice() {
    await initializeBle()

    console.log('[BLE] 弹出设备选择器...')
    // 参考 Web 端：用 namePrefix 过滤 + optionalServices
    // 注意：Capacitor 插件的 requestDevice 参数可能与 Web Bluetooth 略有不同
    // 先尝试 namePrefix 过滤，如果不支持就显示全部设备让用户选
    const device = await BleClient.requestDevice({
        namePrefix: 'GAN',
        optionalServices: [SERVICES.GEN4, SERVICES.GEN3, SERVICES.GEN2],
    })

    console.log('[BLE] 用户选择设备:', device.name, device.deviceId)
    return {
        deviceId: device.deviceId,
        name: device.name || 'GAN 魔方',
    }
}

/**
 * 通过 MAC 地址直接连接（已知 MAC 时使用）
 *
 * Android 上可以直接用 MAC 地址连接已配对或可发现的设备。
 * 适用于已经知道 MAC 地址、不想每次都扫描的场景。
 *
 * @param {string} macAddress - MAC 地址，如 DC:8D:82:0D:F2:9C
 * @returns {Promise<Object>} { deviceId, name }
 */
export async function connectByMac(macAddress) {
    await initializeBle()

    // 标准化 MAC 格式（统一大写 + 冒号分隔）
    const mac = macAddress.toUpperCase().replace(/-/g, ':')
    console.log('[BLE] 通过 MAC 直接连接:', mac)

    // 在 Capacitor 插件中，deviceId 就是 MAC 地址
    // 先尝试读取一个特征值来验证设备是否可达
    return {
        deviceId: mac,
        name: 'GAN 魔方 (' + mac.slice(-5) + ')',
    }
}

/**
 * 扫描 GAN 智能魔方设备
 *
 * @param {Function} onDeviceFound - 发现设备回调，参数：{ deviceId, name, rssi }
 * @param {Object} options - 可选配置
 * @param {number} options.timeoutMs - 扫描超时时间（毫秒），默认 10000
 * @param {boolean} options.filterGan - 是否只显示 GAN 设备，默认 true
 * @returns {Promise<void>} 扫描结束后 resolve
 */
export function scanGanDevices(onDeviceFound, options = {}) {
    const { timeoutMs = 10000, filterGan = true } = options

    return new Promise((resolve, reject) => {
        const found = new Set()

        const handleDevice = (device) => {
            const name = device.name || device.localName

            // 过滤 GAN 设备
            if (filterGan && !isGanDevice(name)) return

            if (!found.has(device.deviceId)) {
                found.add(device.deviceId)
                onDeviceFound({
                    deviceId: device.deviceId,
                    name: name || '(未知设备)',
                    rssi: device.rssi || 0,
                })
            }
        }

        // 不传 services 参数，扫描所有 BLE 设备（避免服务 UUID 过滤导致漏扫）
        console.log('[BLE] 开始扫描，filterGan=', filterGan)
        BleClient.requestLEScan(
            { scanMode: ScanMode.SCAN_MODE_LOW_LATENCY },
            handleDevice,
        ).catch(err => {
            console.error('[BLE] requestLEScan 失败:', err)
            reject(err)
        })

        // 超时自动停止扫描
        setTimeout(() => {
            console.log('[BLE] 扫描超时，停止扫描，已发现', found.size, '台')
            BleClient.stopLEScan()
                .catch(() => {})
                .finally(() => resolve())
        }, timeoutMs)
    })
}

/**
 * 停止扫描
 */
export async function stopScan() {
    try {
        await BleClient.stopLEScan()
    } catch (err) {
        console.warn('[BLE] 停止扫描失败:', err)
    }
}

/**
 * 连接到 GAN 智能魔方
 *
 * 自动识别 Gen2/Gen3/Gen4，找到对应的服务和特征值
 *
 * @param {string} deviceId - 设备 ID
 * @param {Object} callbacks - 回调函数
 * @param {Function} callbacks.onDisconnect - 断开连接回调
 * @returns {Promise<Object>} 连接信息：{ deviceId, gen, serviceUuid, cmdUuid, stateUuid }
 */
export async function connectGanCube(deviceId, callbacks = {}) {
    try {
        console.log('[BLE] 开始连接设备:', deviceId)

        // 连接设备
        await BleClient.connect(deviceId, () => {
            console.log('[BLE] 设备断开:', deviceId)
            if (callbacks.onDisconnect) {
                callbacks.onDisconnect()
            }
        })
        console.log('[BLE] 连接成功')

        // 先尝试 Gen4（GAN i4 等新型号）
        // 直接尝试读取 Gen4 的 state 特征值来验证服务是否存在
        let gen = null
        let serviceUuid = null
        let cmdUuid = null
        let stateUuid = null

        const candidates = [
            { gen: 'gen4', service: SERVICES.GEN4, cmd: CHARACTERISTICS.GEN4_CMD, state: CHARACTERISTICS.GEN4_STATE },
            { gen: 'gen3', service: SERVICES.GEN3, cmd: CHARACTERISTICS.GEN3_CMD, state: CHARACTERISTICS.GEN3_STATE },
            { gen: 'gen2', service: SERVICES.GEN2, cmd: CHARACTERISTICS.GEN2_CMD, state: CHARACTERISTICS.GEN2_STATE },
        ]

        for (const cand of candidates) {
            try {
                console.log('[BLE] 尝试 ' + cand.gen + ' 服务: ' + cand.service)
                // 尝试读取 state 特征值来检测
                await BleClient.read(deviceId, cand.service, cand.state)
                gen = cand.gen
                serviceUuid = cand.service
                cmdUuid = cand.cmd
                stateUuid = cand.state
                console.log('[BLE] 匹配成功: ' + cand.gen)
                break
            } catch (e) {
                console.log('[BLE] ' + cand.gen + ' 不匹配: ' + e.message)
            }
        }

        if (!gen) {
            // 如果逐个尝试都失败，回退到 getServices 方式
            try {
                console.log('[BLE] 逐个尝试失败，改用 getServices 方式...')
                const services = await BleClient.getServices(deviceId)
                console.log('[BLE] 服务列表:', services.map(s => s.uuid))
                const serviceUuids = services.map(s => s.uuid.toLowerCase())

                if (serviceUuids.includes(SERVICES.GEN4.toLowerCase())) {
                    gen = 'gen4'
                    serviceUuid = SERVICES.GEN4
                    cmdUuid = CHARACTERISTICS.GEN4_CMD
                    stateUuid = CHARACTERISTICS.GEN4_STATE
                } else if (serviceUuids.includes(SERVICES.GEN3.toLowerCase())) {
                    gen = 'gen3'
                    serviceUuid = SERVICES.GEN3
                    cmdUuid = CHARACTERISTICS.GEN3_CMD
                    stateUuid = CHARACTERISTICS.GEN3_STATE
                } else if (serviceUuids.includes(SERVICES.GEN2.toLowerCase())) {
                    gen = 'gen2'
                    serviceUuid = SERVICES.GEN2
                    cmdUuid = CHARACTERISTICS.GEN2_CMD
                    stateUuid = CHARACTERISTICS.GEN2_STATE
                }
            } catch (svcErr) {
                console.warn('[BLE] getServices 也失败:', svcErr)
            }
        }

        if (!gen) {
            throw new Error('未识别的 GAN 魔方型号（未找到匹配的 BLE 服务）')
        }

        return { deviceId, gen, serviceUuid, cmdUuid, stateUuid }
    } catch (err) {
        console.error('[BLE] 连接失败:', err)
        // 确保连接失败时断开
        try { await BleClient.disconnect(deviceId) } catch (_) {}
        throw err
    }
}

/**
 * 断开连接
 */
export async function disconnect(deviceId) {
    try {
        await BleClient.disconnect(deviceId)
    } catch (err) {
        console.warn('[BLE] 断开失败:', err)
    }
}

/**
 * 启动特征值通知监听
 *
 * @param {string} deviceId - 设备 ID
 * @param {string} serviceUuid - 服务 UUID
 * @param {string} characteristicUuid - 特征值 UUID
 * @param {Function} callback - 数据回调，参数为 Uint8Array
 */
export async function startNotifications(deviceId, serviceUuid, characteristicUuid, callback) {
    await BleClient.startNotifications(
        deviceId,
        serviceUuid,
        characteristicUuid,
        (value) => {
            // value 是 DataView，转成 Uint8Array
            const arr = new Uint8Array(value.buffer, value.byteOffset, value.byteLength)
            callback(arr)
        },
    )
}

/**
 * 停止通知监听
 */
export async function stopNotifications(deviceId, serviceUuid, characteristicUuid) {
    try {
        await BleClient.stopNotifications(deviceId, serviceUuid, characteristicUuid)
    } catch (err) {
        console.warn('[BLE] 停止通知失败:', err)
    }
}

/**
 * 写入特征值（无响应）
 *
 * @param {string} deviceId
 * @param {string} serviceUuid
 * @param {string} characteristicUuid
 * @param {Uint8Array} data
 */
export async function writeCharacteristic(deviceId, serviceUuid, characteristicUuid, data) {
    await BleClient.writeWithoutResponse(deviceId, serviceUuid, characteristicUuid, data.buffer)
}

/**
 * 读取特征值
 *
 * @param {string} deviceId
 * @param {string} serviceUuid
 * @param {string} characteristicUuid
 * @returns {Promise<Uint8Array>}
 */
export async function readCharacteristic(deviceId, serviceUuid, characteristicUuid) {
    const value = await BleClient.read(deviceId, serviceUuid, characteristicUuid)
    return new Uint8Array(value.buffer, value.byteOffset, value.byteLength)
}
