<template>
  <div class="ble-test-page">
    <div class="header">
      <van-nav-bar title="蓝牙测试" left-text="返回" @click-left="onBack" />
    </div>

    <div class="content">
      <!-- 3D 魔方区域 -->
      <div class="cube-section">
        <Cube3D ref="cube3dRef" :animation-speed="150" />
      </div>

      <!-- 设备状态 -->
      <div class="status-card">
        <div class="status-item">
          <span class="label">连接状态：</span>
          <span :class="['status-value', connected ? 'online' : 'offline']">
            {{ connected ? '已连接' : '未连接' }}
          </span>
        </div>
        <div class="status-item" v-if="connectedDevice">
          <span class="label">设备名称：</span>
          <span class="status-value">{{ connectedDevice.name }}</span>
        </div>
        <div class="status-item" v-if="connectedDevice">
          <span class="label">型号：</span>
          <span class="status-value">{{ connectedDevice.gen }}</span>
        </div>
        <div class="status-item" v-if="batteryLevel !== null">
          <span class="label">电量：</span>
          <span class="status-value">{{ batteryLevel }}%</span>
        </div>
      </div>

      <!-- 连接方式 -->
      <div class="action-section">
        <van-button
          type="primary"
          block
          :loading="connecting"
          :disabled="connected"
          @click="connectByPicker"
        >
          {{ connecting ? '连接中...' : '连接 GAN 魔方（推荐）' }}
        </van-button>

        <div class="scan-hint" style="margin-top: 8px;">
          点击后弹出系统蓝牙设备选择器，选择你的 GAN 魔方即可
        </div>

        <van-divider style="margin: 16px 0;">或输入 MAC 地址直连</van-divider>

        <van-field
          v-model="macInput"
          label="MAC 地址"
          placeholder="如 DC:8D:82:0D:F2:9C"
          clearable
        />

        <van-button
          type="warning"
          block
          :loading="connectingMac"
          :disabled="connected || !macInput"
          @click="connectByMacAddr"
          style="margin-top: 10px;"
        >
          通过 MAC 连接
        </van-button>

        <div class="scan-hint" style="margin-top: 8px;">
          已保存设备会自动填充 MAC，从 Web 端或之前扫描可获取
        </div>

        <van-divider style="margin: 16px 0;">或手动扫描</van-divider>

        <div class="scan-options">
          <van-switch v-model="showAllDevices" size="20px" />
          <span class="scan-option-label">显示全部设备（调试用）</span>
        </div>

        <van-button
          type="default"
          block
          :loading="scanning"
          :disabled="connected"
          @click="startScan"
          style="margin-top: 10px;"
        >
          {{ scanning ? '扫描中...' + devices.length + ' 台' : '手动扫描' }}
        </van-button>

        <div v-if="scanning" class="scan-hint">
          正在扫描周围的蓝牙设备，请确保魔方已开启...
        </div>

        <van-button
          type="danger"
          block
          v-if="connected"
          :loading="disconnecting"
          @click="doDisconnect"
          style="margin-top: 12px;"
        >
          断开连接
        </van-button>
      </div>

      <!-- 设备列表 -->
      <div class="device-list">
        <div class="list-title">发现的设备（{{ devices.length }} 台）</div>
        <van-empty v-if="!scanning && devices.length === 0" description="未发现设备" />
        <van-cell-group inset v-else>
          <van-cell
            v-for="device in devices"
            :key="device.deviceId"
            :title="device.name"
            :label="'ID: ' + device.deviceId + '  |  RSSI: ' + device.rssi + ' dBm'"
            is-link
            :loading="connectingId === device.deviceId"
            @click="connectDevice(device)"
          />
        </van-cell-group>
      </div>

      <!-- 调试日志 -->
      <div class="debug-log">
        <div class="debug-log-header">
          <span class="list-title">调试日志</span>
          <van-button size="mini" type="default" @click="clearDebugLog">清空</van-button>
        </div>
        <div class="log-content">
          <div v-for="(log, i) in debugLog" :key="i" class="log-line">
            <span class="log-time">{{ log.time }}</span>
            <span :class="['log-tag', 'log-' + log.level]">{{ log.level }}</span>
            <span class="log-msg">{{ log.msg }}</span>
          </div>
          <div v-if="debugLog.length === 0" class="log-empty">暂无日志</div>
        </div>
      </div>

      <!-- 转动日志 -->
      <div class="move-log" v-if="moveLog.length > 0">
        <div class="list-title">转动记录（最近 20 条）</div>
        <div class="moves">
          <span v-for="(m, i) in moveLog" :key="i" class="move-chip">
            {{ m }}
          </span>
        </div>
      </div>

      <!-- 测试按钮 -->
      <div class="test-buttons" v-if="connected">
        <div class="list-title">3D 测试</div>
        <div class="btn-row">
          <van-button size="small" @click="testRotate('R')">R</van-button>
          <van-button size="small" @click="testRotate(invR)">R'</van-button>
          <van-button size="small" @click="testRotate('U')">U</van-button>
          <van-button size="small" @click="testRotate(invU)">U'</van-button>
          <van-button size="small" @click="testRotate('F')">F</van-button>
          <van-button size="small" @click="testRotate(invF)">F'</van-button>
        </div>
        <div class="btn-row" style="margin-top: 8px;">
          <van-button size="small" type="primary" @click="testScramble">随机打乱</van-button>
          <van-button size="small" @click="resetCube">复位</van-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * 蓝牙 + 3D 魔方测试页
 *
 * 用于验证阶段一成果：
 *   1. 蓝牙扫描 GAN 魔方
 *   2. 连接设备
 *   3. 接收转动事件
 *   4. 3D 魔方实时跟随转动
 */

import { ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { showToast, showDialog } from 'vant'
import Cube3D from '@/components/cube/Cube3D.vue'
import {
    initializeBle,
    requestGanDevice,
    connectByMac,
    scanGanDevices,
    stopScan,
    connectGanCube,
    disconnect,
    startNotifications,
    writeCharacteristic,
} from '@/utils/ble'
import { Gen4ProtocolDriver } from '@/utils/gan-ble'

const router = useRouter()
const cube3dRef = ref(null)

const scanning = ref(false)
const connected = ref(false)
const disconnecting = ref(false)
const connectingId = ref(null)
const connecting = ref(false) // 设备选择器方式的连接状态
const connectingMac = ref(false) // MAC 直连的连接状态
const macInput = ref('')

// 从本地存储读取保存的 MAC
const savedMac = localStorage.getItem('gan_cube_mac')
if (savedMac) {
    macInput.value = savedMac
}
const connectedDevice = ref(null)
const devices = ref([])
const moveLog = ref([])
const batteryLevel = ref(null)
const showAllDevices = ref(false) // 是否显示全部设备（调试用）
const debugLog = ref([]) // 调试日志

// 添加调试日志
function addLog(msg, level = 'info') {
    const now = new Date()
    const time = now.toTimeString().slice(0, 8) + '.' + String(now.getMilliseconds()).padStart(3, '0')
    debugLog.value.unshift({ time, level, msg })
    if (debugLog.value.length > 50) {
        debugLog.value.pop()
    }
}

function clearDebugLog() {
    debugLog.value = []
}

// 逆步骤常量（避免模板中单引号转义问题）
const invR = "R'"
const invU = "U'"
const invF = "F'"

let protocolDriver = null
let connectionInfo = null

function onBack() {
    router.back()
}

// ===== 通过系统设备选择器连接（推荐方式） =====
async function connectByPicker() {
    if (connecting.value || connected.value) return

    connecting.value = true
    addLog('打开系统设备选择器...', 'info')

    try {
        // 1. 弹出系统设备选择器
        const device = await requestGanDevice()
        addLog('已选择设备: ' + device.name + ' (' + device.deviceId + ')', 'info')

        // 2. 建立连接并设置通知
        await doConnect(device)
    } catch (err) {
        const msg = err?.message || String(err)
        // 用户取消选择不算错误
        if (msg.includes('cancelled') || msg.includes('cancel')) {
            addLog('用户取消选择', 'warn')
        } else {
            addLog('连接失败: ' + msg, 'error')
            showDialog({
                title: '连接失败',
                message: msg,
                confirmButtonText: '好的',
            })
        }
    } finally {
        connecting.value = false
    }
}

// ===== 通过 MAC 地址直连 =====
async function connectByMacAddr() {
    if (connectingMac.value || connected.value) return

    const mac = macInput.value.trim()
    if (!mac) {
        showToast('请输入 MAC 地址')
        return
    }

    // 简单格式校验
    const macRegex = /^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$/
    if (!macRegex.test(mac)) {
        showToast('MAC 地址格式不正确')
        return
    }

    connectingMac.value = true
    addLog('通过 MAC 直连: ' + mac, 'info')

    try {
        const device = await connectByMac(mac)
        await doConnect(device)

        // 连接成功后保存 MAC
        localStorage.setItem('gan_cube_mac', mac.toUpperCase())
        addLog('MAC 地址已保存到本地', 'info')
    } catch (err) {
        const msg = err?.message || String(err)
        addLog('MAC 直连失败: ' + msg, 'error')
        showDialog({
            title: '连接失败',
            message: msg,
            confirmButtonText: '好的',
        })
    } finally {
        connectingMac.value = false
    }
}

// ===== 实际连接逻辑（共用） =====
async function doConnect(device) {
    addLog('正在建立 GATT 连接...', 'info')
    connectionInfo = await connectGanCube(device.deviceId, {
        onDisconnect: handleDisconnect,
    })
    addLog('连接成功，型号: ' + connectionInfo.gen, 'info')

    // 创建协议解析器（用设备 MAC 作为 AES 解密的 salt）
    addLog('初始化协议解析器，MAC: ' + device.deviceId, 'info')
    protocolDriver = new Gen4ProtocolDriver(device.deviceId)

    // 设置回调
    protocolDriver.onMove = handleMove
    protocolDriver.onBattery = handleBattery
    protocolDriver.onHardware = handleHardware
    protocolDriver.onFacelets = handleFacelets

    // 启动通知监听
    addLog('启动状态通知监听...', 'info')
    await startNotifications(
        connectionInfo.deviceId,
        connectionInfo.serviceUuid,
        connectionInfo.stateUuid,
        (data) => {
            protocolDriver.handleStateNotification(data)
        },
    )

    connected.value = true
    connectedDevice.value = {
        name: device.name,
        gen: connectionInfo.gen,
    }
    addLog('🎉 全部就绪，转动魔方试试吧！', 'info')
}

async function startScan() {
    if (scanning.value) return

    try {
        await initializeBle()
    } catch (err) {
        const detail = err?.message || String(err)
        console.error('[BLE] 初始化错误详情:', err)
        showDialog({
            title: '蓝牙初始化失败',
            message: detail + '\n\n（请确认已授予蓝牙权限且蓝牙已开启）',
            confirmButtonText: '好的',
        })
        return
    }

    devices.value = []
    scanning.value = true
    addLog('开始扫描，显示全部设备=' + showAllDevices.value, 'info')

    try {
        await scanGanDevices((device) => {
            addLog('发现设备: ' + device.name + ' (' + device.deviceId + ') rssi=' + device.rssi, 'info')
            devices.value.push(device)
        }, {
            timeoutMs: 10000,
            filterGan: !showAllDevices.value,
        })
        addLog('扫描结束，共发现 ' + devices.value.length + ' 台设备', 'info')
    } catch (err) {
        addLog('扫描失败: ' + (err.message || err), 'error')
        showToast('扫描失败：' + (err.message || err))
    } finally {
        scanning.value = false
    }
}

async function connectDevice(device) {
    if (connectingId.value) return

    connectingId.value = device.deviceId
    addLog('开始连接: ' + device.name + ' (' + device.deviceId + ')', 'info')

    try {
        // 先停止扫描
        if (scanning.value) {
            await stopScan()
            scanning.value = false
        }

        // 共用连接逻辑
        await doConnect(device)
    } catch (err) {
        console.error('连接失败:', err)
        const msg = err?.message || String(err)
        addLog('连接失败: ' + msg, 'error')
        showDialog({
            title: '连接失败',
            message: msg,
            confirmButtonText: '好的',
        })
    } finally {
        connectingId.value = null
    }
}

function handleMove(e) {
    console.log('[MOVE]', e.move)
    // 添加到日志
    moveLog.value.unshift(e.move)
    if (moveLog.value.length > 20) {
        moveLog.value.pop()
    }
    // 驱动 3D 魔方转动
    if (cube3dRef.value) {
        cube3dRef.value.rotate(e.move)
    }
}

function handleBattery(e) {
    console.log('[BATTERY]', e)
    batteryLevel.value = e.batteryLevel
}

function handleHardware(e) {
    console.log('[HARDWARE]', e)
}

function handleFacelets(e) {
    console.log('[FACELETS] solved:', e.isSolved)
}

function handleDisconnect() {
    connected.value = false
    connectedDevice.value = null
    batteryLevel.value = null
    protocolDriver = null
    connectionInfo = null
    showToast('已断开连接')
}

async function doDisconnect() {
    if (!connected.value || !connectionInfo) return
    disconnecting.value = true
    try {
        await disconnect(connectionInfo.deviceId)
    } catch (err) {
        console.warn('断开失败:', err)
    } finally {
        disconnecting.value = false
    }
}

// ===== 3D 测试按钮 =====

function testRotate(move) {
    if (cube3dRef.value) {
        cube3dRef.value.rotate(move)
    }
}

function testScramble() {
    // 简单随机打乱 10 步，测试 3D 动画
    const moves = ['R', "R'", 'L', "L'", 'U', "U'", 'D', "D'", 'F', "F'"]
    const seq = []
    for (let i = 0; i < 10; i++) {
        seq.push(moves[Math.floor(Math.random() * moves.length)])
    }
    if (cube3dRef.value) {
        cube3dRef.value.rotateSequence(seq.join(' '))
    }
}

function resetCube() {
    if (cube3dRef.value) {
        cube3dRef.value.reset()
    }
    moveLog.value = []
}

onBeforeUnmount(() => {
    if (connectionInfo) {
        disconnect(connectionInfo.deviceId).catch(() => {})
    }
    if (scanning.value) {
        stopScan().catch(() => {})
    }
})
</script>

<style scoped>
.ble-test-page {
    min-height: 100vh;
    background: #f7f8fa;
}

.header {
    position: sticky;
    top: 0;
    z-index: 100;
    background: #fff;
}

.content {
    padding: 12px;
}

.cube-section {
    height: 280px;
    background: #fff;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 12px;
}

.status-card {
    background: #fff;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}

.status-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    font-size: 14px;
}

.label {
    color: #969799;
}

.status-value {
    color: #323233;
    font-weight: 500;
}

.status-value.online {
    color: #07c160;
}

.status-value.offline {
    color: #969799;
}

.action-section {
    margin-bottom: 12px;
}

.scan-options {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 4px;
}

.scan-option-label {
    font-size: 13px;
    color: #646566;
}

.scan-hint {
    text-align: center;
    font-size: 12px;
    color: #969799;
    margin-top: 8px;
}

.device-list {
    margin-bottom: 12px;
}

.list-title {
    font-size: 14px;
    color: #969799;
    margin-bottom: 8px;
    padding: 0 4px;
}

.debug-log {
    background: #fff;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 12px;
}

.debug-log-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.log-content {
    max-height: 200px;
    overflow-y: auto;
    background: #f7f8fa;
    border-radius: 4px;
    padding: 8px;
    font-size: 12px;
}

.log-line {
    display: flex;
    gap: 6px;
    padding: 2px 0;
    font-family: 'Courier New', monospace;
    word-break: break-all;
}

.log-time {
    color: #969799;
    flex-shrink: 0;
}

.log-tag {
    padding: 0 4px;
    border-radius: 2px;
    font-size: 10px;
    font-weight: bold;
    flex-shrink: 0;
    height: 16px;
    line-height: 16px;
}

.log-info {
    background: #e8f4ff;
    color: #1989fa;
}

.log-error {
    background: #ffedeb;
    color: #ee0a24;
}

.log-warn {
    background: #fff7e8;
    color: #ff976a;
}

.log-msg {
    color: #323233;
    flex: 1;
}

.log-empty {
    text-align: center;
    color: #c8c9cc;
    padding: 20px 0;
}

.move-log {
    background: #fff;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 12px;
}

.moves {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.move-chip {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 32px;
    height: 28px;
    padding: 0 8px;
    background: #ebedf0;
    color: #323233;
    border-radius: 4px;
    font-size: 13px;
    font-family: 'Courier New', monospace;
    font-weight: bold;
}

.test-buttons {
    background: #fff;
    border-radius: 8px;
    padding: 12px;
}

.btn-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}
</style>
