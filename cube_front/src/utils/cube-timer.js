/**
 * CubeTimer — 智能魔方计时器状态机
 *
 * 状态流转：
 *   IDLE → SCRAMBLING → OBSERVATION → SOLVING → SOLVED → SCRAMBLING → ...
 *
 * 触发打乱：检测到来回拨动（如 R R'）
 * 打乱模式：系统生成序列，用户按序列转动，逐步校验
 * 错误处理：做错步骤 → 插入逆步骤到当前位置后 → toast 提醒
 * 分支回退：做上一步的逆 → 出栈回退
 */

// ===== 常量 =====

const FACES = ['U', 'R', 'F', 'D', 'L', 'B']
const OPPOSITE = { U: 'D', D: 'U', R: 'L', L: 'R', F: 'B', B: 'F' }
const OBSERVATION_TIME = 15 // 秒
const SCRAMBLE_LENGTH = 20

// ===== 工具函数 =====

function inverseMove(move) {
  if (move.endsWith("'")) return move.slice(0, -1)
  return move + "'"
}

function isInverse(a, b) {
  return a === inverseMove(b)
}

function formatTime(ms) {
  const totalSec = ms / 1000
  const min = Math.floor(totalSec / 60)
  const sec = totalSec % 60
  if (min > 0) {
    return `${min}:${sec.toFixed(2).padStart(5, '0')}`
  }
  return sec.toFixed(2)
}

/**
 * 生成 WCA 风格打乱序列
 * 规则：不连续同面，不连续对面（避免冗余）
 */
function generateScramble(length = SCRAMBLE_LENGTH) {
  const sequence = []
  let lastFace = null
  let lastLastFace = null

  while (sequence.length < length) {
    const face = FACES[Math.floor(Math.random() * 6)]
    if (face === lastFace) continue
    if (face === lastLastFace && OPPOSITE[face] === lastFace) continue

    const dir = Math.random() < 0.5 ? '' : "'"
    sequence.push(face + dir)

    lastLastFace = lastFace
    lastFace = face
  }

  return sequence
}

// ===== 状态机 =====

const STATES = {
  IDLE: 'idle',
  SCRAMBLING: 'scrambling',
  OBSERVATION: 'observation',
  SOLVING: 'solving',
  SOLVED: 'solved',
}

export { STATES as TimerStates }

export class CubeTimer {
  constructor({
    mode = 'practice',
    onStateChange = () => {},
    onTimeUpdate = () => {},
    onScrambleProgress = () => {},
    onCorrection = () => {},
    onWarning = () => {},
    onSolveComplete = () => {},
    onScrambleGenerated = () => {},
  } = {}) {
    this._mode = mode
    this._state = STATES.IDLE
    this._callbacks = {
      onStateChange, onTimeUpdate, onScrambleProgress,
      onCorrection, onWarning, onSolveComplete, onScrambleGenerated,
    }

    this._scrambleSequence = []
    this._scrambleStep = 0
    this._scrambleStack = []
    this._recentMoves = []
    this._observationStart = null
    this._observationElapsed = 0
    this._solveStart = null
    this._solveElapsed = 0
    this._solveMoves = []
    this._timerInterval = null
    this._lastResult = null
  }

  get state() { return this._state }
  get mode() { return this._mode }
  get scrambleSequence() { return this._scrambleSequence }
  get scrambleStep() { return this._scrambleStep }
  get lastResult() { return this._lastResult }

  setMode(mode) {
    this._mode = mode
  }

  reset() {
    this._stopTimer()
    this._state = STATES.IDLE
    this._scrambleSequence = []
    this._scrambleStep = 0
    this._scrambleStack = []
    this._recentMoves = []
    this._observationStart = null
    this._observationElapsed = 0
    this._solveStart = null
    this._solveElapsed = 0
    this._solveMoves = []
    this._lastResult = null
    this._callbacks.onStateChange(STATES.IDLE)
  }

  stop() {
    this.reset()
  }

  /**
   * 处理 MOVE 事件
   */
  onMove(move, isSolved) {
    switch (this._state) {
      case STATES.IDLE:
        this._handleIdleMove(move, isSolved)
        break
      case STATES.SCRAMBLING:
        this._handleScramblingMove(move, isSolved)
        break
      case STATES.OBSERVATION:
        this._handleObservationMove(move)
        break
      case STATES.SOLVING:
        this._handleSolvingMove(move, isSolved)
        break
      case STATES.SOLVED:
        this._handleSolvedMove(move, isSolved)
        break
    }
  }

  /**
   * 处理 FACELETS 事件 — 检查复原状态
   */
  onFacelets(isSolved) {
    if (this._state === STATES.SOLVING && isSolved) {
      this._onSolved()
    }
  }

  // ===== IDLE：等待来回拨动触发打乱 =====

  _handleIdleMove(move, isSolved) {
    this._recentMoves.push(move)
    if (this._recentMoves.length > 2) {
      this._recentMoves.shift()
    }

    if (this._recentMoves.length === 2) {
      const [a, b] = this._recentMoves
      if (isInverse(a, b)) {
        this._startScramble()
        this._recentMoves = []
      }
    }
  }

  _startScramble() {
    this._scrambleSequence = generateScramble()
    this._scrambleStep = 0
    this._scrambleStack = []
    this._state = STATES.SCRAMBLING
    this._callbacks.onStateChange(STATES.SCRAMBLING)
    this._callbacks.onScrambleGenerated(this._scrambleSequence)
    this._callbacks.onScrambleProgress(0, this._scrambleSequence.length, this._scrambleSequence[0])
  }

  // ===== SCRAMBLING：按序列转动 =====

  _handleScramblingMove(move, isSolved) {
    if (this._scrambleStep < this._scrambleSequence.length) {
      const expected = this._scrambleSequence[this._scrambleStep]

      if (move === expected) {
        // 正确步骤
        this._scrambleStack.push(move)
        this._scrambleStep++
        const next = this._scrambleSequence[this._scrambleStep] || null
        this._callbacks.onScrambleProgress(this._scrambleStep, this._scrambleSequence.length, next)

        // 打乱完成
        if (this._scrambleStep >= this._scrambleSequence.length) {
          this._enterObservation()
        }
      } else if (this._scrambleStack.length > 0 && move === inverseMove(this._scrambleStack[this._scrambleStack.length - 1])) {
        // 分支回退：做上一步的逆 → 出栈
        const undone = this._scrambleStack.pop()
        this._scrambleStep--
        // 同时从序列中移除当前 expected（因为它是被插入的或原始的）
        this._scrambleSequence.splice(this._scrambleStep, 1)
        const next = this._scrambleSequence[this._scrambleStep] || null
        this._callbacks.onCorrection(undone)
        this._callbacks.onScrambleProgress(this._scrambleStep, this._scrambleSequence.length, next)
      } else {
        // 错误步骤：插入逆步骤到当前位置前，用户先回退再做原步骤
        const invMove = inverseMove(move)
        this._scrambleSequence.splice(this._scrambleStep, 0, invMove)
        this._callbacks.onWarning(`步骤错误：${move}，请做 ${invMove} 回退`)
        this._callbacks.onScrambleProgress(this._scrambleStep, this._scrambleSequence.length, invMove)
      }
    }
  }

  // ===== OBSERVATION：观察倒计时 =====

  _enterObservation() {
    this._state = STATES.OBSERVATION
    this._observationStart = Date.now()
    this._observationElapsed = 0
    this._callbacks.onStateChange(STATES.OBSERVATION)
    this._startTimer()
  }

  _handleObservationMove(move) {
    this._stopTimer()
    this._solveMoves = [move]
    this._solveStart = Date.now()
    this._solveElapsed = 0
    this._state = STATES.SOLVING
    this._callbacks.onStateChange(STATES.SOLVING)
    this._startTimer()
  }

  // ===== SOLVING：复原计时 =====

  _handleSolvingMove(move, isSolved) {
    this._solveMoves.push(move)
    if (isSolved) {
      this._onSolved()
    }
  }

  _onSolved() {
    this._stopTimer()
    this._solveElapsed = Date.now() - this._solveStart
    this._state = STATES.SOLVED

    const result = {
      solveTime: this._solveElapsed,
      solveTimeFormatted: formatTime(this._solveElapsed),
      observationTime: this._observationElapsed,
      observationTimeFormatted: formatTime(this._observationElapsed),
      moveCount: this._solveMoves.length,
      scramble: [...this._scrambleSequence],
      solve: [...this._solveMoves],
    }

    this._lastResult = result
    this._callbacks.onSolveComplete(result)
    this._callbacks.onStateChange(STATES.SOLVED)
  }

  // ===== SOLVED：等待新一轮 =====

  _handleSolvedMove(move, isSolved) {
    this._recentMoves.push(move)
    if (this._recentMoves.length > 2) {
      this._recentMoves.shift()
    }

    if (this._recentMoves.length === 2) {
      const [a, b] = this._recentMoves
      if (isInverse(a, b)) {
        this._startScramble()
        this._recentMoves = []
      }
    }
  }

  // ===== 计时器 =====

  _startTimer() {
    this._stopTimer()
    this._timerInterval = setInterval(() => {
      if (this._state === STATES.OBSERVATION) {
        this._observationElapsed = Date.now() - this._observationStart
        const remaining = OBSERVATION_TIME * 1000 - this._observationElapsed

        if (this._mode === 'practice' && remaining <= 0) {
          this._stopTimer()
          this._state = STATES.SOLVED
          this._lastResult = {
            solveTime: null,
            solveTimeFormatted: 'DNF',
            observationTime: this._observationElapsed,
            observationTimeFormatted: formatTime(this._observationElapsed),
            moveCount: 0,
            scramble: [...this._scrambleSequence],
            solve: [],
            dnf: true,
          }
          this._callbacks.onSolveComplete(this._lastResult)
          this._callbacks.onStateChange(STATES.SOLVED)
        } else {
          this._callbacks.onTimeUpdate({
            state: STATES.OBSERVATION,
            display: this._mode === 'practice'
              ? Math.max(0, remaining / 1000).toFixed(2)
              : (this._observationElapsed / 1000).toFixed(2),
            elapsed: this._observationElapsed,
            remaining: Math.max(0, remaining),
          })
        }
      } else if (this._state === STATES.SOLVING) {
        this._solveElapsed = Date.now() - this._solveStart
        this._callbacks.onTimeUpdate({
          state: STATES.SOLVING,
          display: (this._solveElapsed / 1000).toFixed(2),
          elapsed: this._solveElapsed,
        })
      }
    }, 50)
  }

  _stopTimer() {
    if (this._timerInterval) {
      clearInterval(this._timerInterval)
      this._timerInterval = null
    }
  }
}
