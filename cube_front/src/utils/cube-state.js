/**
 * cube-state.js — 3x3 魔方状态模拟器
 *
 * 功能：
 *   - 初始化为已复原状态（白顶绿前）
 *   - 逐步应用标准记号序列 → 得到打乱后状态
 *   - 输出 54 字符面字符串，用于 2D 平面图渲染
 *
 * 面顺序：U(上) R(右) F(前) D(下) L(左) B(后)
 * 每个面 9 个贴纸，按行优先排列（左上→右上→左中→...→右下）
 *
 * 颜色约定：
 *   U=white, D=yellow, F=green, B=blue, R=red, L=orange
 */

// 面索引
const U = 0
const R = 1
const F = 2
const D = 3
const L = 4
const B = 5

const FACES = ['U', 'R', 'F', 'D', 'L', 'B']

// 颜色映射（面 → 颜色名）
const FACE_COLORS = {
  U: 'white',
  R: 'red',
  F: 'green',
  D: 'yellow',
  L: 'orange',
  B: 'blue'
}

/**
 * 创建已复原的魔方状态
 * 每个面用长度为 9 的数组表示，初始全部为该面的颜色
 * @returns {string[][]} 6 个面 × 9 个贴纸
 */
function createSolvedState() {
  const state = []
  for (let i = 0; i < 6; i++) {
    state.push(new Array(9).fill(FACE_COLORS[FACES[i]]))
  }
  return state
}

/**
 * 顺时针旋转一个面 90 度
 * 面的贴纸索引：
 *   0 1 2
 *   3 4 5
 *   6 7 8
 * 顺时针旋转后：
 *   6 3 0
 *   7 4 1
 *   8 5 2
 */
function rotateFaceCW(face) {
  const newFace = new Array(9)
  newFace[0] = face[6]
  newFace[1] = face[3]
  newFace[2] = face[0]
  newFace[3] = face[7]
  newFace[4] = face[4]
  newFace[5] = face[1]
  newFace[6] = face[8]
  newFace[7] = face[5]
  newFace[8] = face[2]
  return newFace
}

/**
 * 逆时针旋转一个面 90 度
 */
function rotateFaceCCW(face) {
  const newFace = new Array(9)
  newFace[0] = face[2]
  newFace[1] = face[5]
  newFace[2] = face[8]
  newFace[3] = face[1]
  newFace[4] = face[4]
  newFace[5] = face[7]
  newFace[6] = face[0]
  newFace[7] = face[3]
  newFace[8] = face[6]
  return newFace
}

/**
 * 旋转 180 度
 */
function rotateFace180(face) {
  const newFace = new Array(9)
  newFace[0] = face[8]
  newFace[1] = face[7]
  newFace[2] = face[6]
  newFace[3] = face[5]
  newFace[4] = face[4]
  newFace[5] = face[3]
  newFace[6] = face[2]
  newFace[7] = face[1]
  newFace[8] = face[0]
  return newFace
}

/**
 * 执行 R 转动（右面顺时针）
 * 影响的边贴纸：U 的右列(2,5,8) → F 的右列(2,5,8) → D 的右列(2,5,8) → B 的左列(0,3,6) → U 的右列
 * 注意：B 面的左列是反向的
 */
function moveR(state) {
  state[R] = rotateFaceCW(state[R])

  const uCol = [state[U][2], state[U][5], state[U][8]]
  const fCol = [state[F][2], state[F][5], state[F][8]]
  const dCol = [state[D][2], state[D][5], state[D][8]]
  // B 面左列，反向
  const bCol = [state[B][6], state[B][3], state[B][0]]

  // U → F → D → B(反向) → U
  state[F][2] = uCol[0]
  state[F][5] = uCol[1]
  state[F][8] = uCol[2]

  state[D][2] = fCol[0]
  state[D][5] = fCol[1]
  state[D][8] = fCol[2]

  state[B][6] = dCol[0]
  state[B][3] = dCol[1]
  state[B][0] = dCol[2]

  state[U][2] = bCol[0]
  state[U][5] = bCol[1]
  state[U][8] = bCol[2]
}

/**
 * 执行 L 转动（左面顺时针）
 * 影响的边贴纸：U 的左列(0,3,6) → B 的右列(2,5,8) → D 的左列(0,3,6) → F 的左列(0,3,6) → U 的左列
 */
function moveL(state) {
  state[L] = rotateFaceCW(state[L])

  const uCol = [state[U][0], state[U][3], state[U][6]]
  const fCol = [state[F][0], state[F][3], state[F][6]]
  const dCol = [state[D][0], state[D][3], state[D][6]]
  // B 面右列，反向
  const bCol = [state[B][8], state[B][5], state[B][2]]

  // U → B(反向) → D → F → U
  state[B][8] = uCol[0]
  state[B][5] = uCol[1]
  state[B][2] = uCol[2]

  state[D][0] = bCol[0]
  state[D][3] = bCol[1]
  state[D][6] = bCol[2]

  state[F][0] = dCol[0]
  state[F][3] = dCol[1]
  state[F][6] = dCol[2]

  state[U][0] = fCol[0]
  state[U][3] = fCol[1]
  state[U][6] = fCol[2]
}

/**
 * 执行 U 转动（上面顺时针）
 * 影响的边贴纸：F 的顶行(0,1,2) → R 的顶行(0,1,2) → B 的顶行(0,1,2) → L 的顶行(0,1,2) → F 的顶行
 */
function moveU(state) {
  state[U] = rotateFaceCW(state[U])

  const fRow = [state[F][0], state[F][1], state[F][2]]
  const rRow = [state[R][0], state[R][1], state[R][2]]
  const bRow = [state[B][0], state[B][1], state[B][2]]
  const lRow = [state[L][0], state[L][1], state[L][2]]

  // F → L → B → R → F
  state[L][0] = fRow[0]
  state[L][1] = fRow[1]
  state[L][2] = fRow[2]

  state[B][0] = lRow[0]
  state[B][1] = lRow[1]
  state[B][2] = lRow[2]

  state[R][0] = bRow[0]
  state[R][1] = bRow[1]
  state[R][2] = bRow[2]

  state[F][0] = rRow[0]
  state[F][1] = rRow[1]
  state[F][2] = rRow[2]
}

/**
 * 执行 D 转动（下面顺时针）
 * 影响的边贴纸：F 的底行(6,7,8) → L 的底行(6,7,8) → B 的底行(6,7,8) → R 的底行(6,7,8) → F 的底行
 */
function moveD(state) {
  state[D] = rotateFaceCW(state[D])

  const fRow = [state[F][6], state[F][7], state[F][8]]
  const rRow = [state[R][6], state[R][7], state[R][8]]
  const bRow = [state[B][6], state[B][7], state[B][8]]
  const lRow = [state[L][6], state[L][7], state[L][8]]

  // F → R → B → L → F
  state[R][6] = fRow[0]
  state[R][7] = fRow[1]
  state[R][8] = fRow[2]

  state[B][6] = rRow[0]
  state[B][7] = rRow[1]
  state[B][8] = rRow[2]

  state[L][6] = bRow[0]
  state[L][7] = bRow[1]
  state[L][8] = bRow[2]

  state[F][6] = lRow[0]
  state[F][7] = lRow[1]
  state[F][8] = lRow[2]
}

/**
 * 执行 F 转动（前面顺时针）
 * 影响的边贴纸：U 的底行(6,7,8) → R 的左列(0,3,6) → D 的顶行(2,1,0) → L 的右列(2,5,8) → U 的底行
 */
function moveF(state) {
  state[F] = rotateFaceCW(state[F])

  const uRow = [state[U][6], state[U][7], state[U][8]]
  const rCol = [state[R][0], state[R][3], state[R][6]]
  const dRow = [state[D][2], state[D][1], state[D][0]] // 反向
  const lCol = [state[L][8], state[L][5], state[L][2]] // 反向

  // U → R → D → L → U
  state[R][0] = uRow[0]
  state[R][3] = uRow[1]
  state[R][6] = uRow[2]

  state[D][2] = rCol[0]
  state[D][1] = rCol[1]
  state[D][0] = rCol[2]

  state[L][8] = dRow[0]
  state[L][5] = dRow[1]
  state[L][2] = dRow[2]

  state[U][6] = lCol[0]
  state[U][7] = lCol[1]
  state[U][8] = lCol[2]
}

/**
 * 执行 B 转动（后面顺时针）
 * 影响的边贴纸：U 的顶行(2,1,0) → L 的左列(0,3,6) → D 的底行(6,7,8) → R 的右列(8,5,2) → U 的顶行
 */
function moveB(state) {
  state[B] = rotateFaceCW(state[B])

  const uRow = [state[U][2], state[U][1], state[U][0]] // 反向
  const lCol = [state[L][0], state[L][3], state[L][6]]
  const dRow = [state[D][6], state[D][7], state[D][8]]
  const rCol = [state[R][8], state[R][5], state[R][2]] // 反向

  // U → L → D → R → U
  state[L][0] = uRow[0]
  state[L][3] = uRow[1]
  state[L][6] = uRow[2]

  state[D][6] = lCol[0]
  state[D][7] = lCol[1]
  state[D][8] = lCol[2]

  state[R][8] = dRow[0]
  state[R][5] = dRow[1]
  state[R][2] = dRow[2]

  state[U][2] = rCol[0]
  state[U][1] = rCol[1]
  state[U][0] = rCol[2]
}

// 转动映射表
const MOVE_MAP = {
  'R': moveR,
  "R'": (s) => { moveR(s); moveR(s); moveR(s) },
  'R2': (s) => { moveR(s); moveR(s) },
  'L': moveL,
  "L'": (s) => { moveL(s); moveL(s); moveL(s) },
  'L2': (s) => { moveL(s); moveL(s) },
  'U': moveU,
  "U'": (s) => { moveU(s); moveU(s); moveU(s) },
  'U2': (s) => { moveU(s); moveU(s) },
  'D': moveD,
  "D'": (s) => { moveD(s); moveD(s); moveD(s) },
  'D2': (s) => { moveD(s); moveD(s) },
  'F': moveF,
  "F'": (s) => { moveF(s); moveF(s); moveF(s) },
  'F2': (s) => { moveF(s); moveF(s) },
  'B': moveB,
  "B'": (s) => { moveB(s); moveB(s); moveB(s) },
  'B2': (s) => { moveB(s); moveB(s) },
}

/**
 * 应用一个打乱序列到魔方状态
 * @param {string[]} moves 打乱序列，如 ['R', "U'", 'F2']
 * @param {string[][]} [initialState] 初始状态，默认复原状态
 * @returns {string[][]} 应用后的状态
 */
function applyScramble(moves, initialState) {
  const state = initialState ? state.map(face => [...face]) : createSolvedState()
  for (const move of moves) {
    const fn = MOVE_MAP[move]
    if (fn) fn(state)
  }
  return state
}

/**
 * 将状态转换为 54 字符字符串（U R F D L B 顺序，每面 9 个）
 * @param {string[][]} state
 * @returns {string}
 */
function stateToString(state) {
  return state.map(face => face.join('')).join('')
}

/**
 * 获取指定面的颜色数组
 * @param {string[][]} state
 * @param {string} faceName 'U' | 'R' | 'F' | 'D' | 'L' | 'B'
 * @returns {string[]}
 */
function getFace(state, faceName) {
  const idx = FACES.indexOf(faceName)
  return idx >= 0 ? state[idx] : null
}

export {
  FACES,
  FACE_COLORS,
  createSolvedState,
  applyScramble,
  stateToString,
  getFace,
}
