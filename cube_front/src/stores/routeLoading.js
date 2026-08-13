import { ref } from 'vue'

const OVERLAY_DELAY = 180
const MIN_FEEDBACK_DURATION = 400

const status = ref('idle')
const progressVisible = ref(false)
const overlayVisible = ref(false)
const targetPath = ref('')
const layoutMounted = ref(false)

let overlayTimer = null
let settleTimer = null
let startedAt = 0
let sequence = 0
let errorPending = false

const clearTimers = () => {
    clearTimeout(overlayTimer)
    clearTimeout(settleTimer)
    overlayTimer = null
    settleTimer = null
}

const setIdle = () => {
    status.value = 'idle'
    progressVisible.value = false
    overlayVisible.value = false
    targetPath.value = ''
}

const reset = () => {
    sequence++
    clearTimers()
    errorPending = false
    setIdle()
}

const start = (path) => {
    sequence++
    clearTimers()
    errorPending = false
    startedAt = Date.now()
    status.value = 'loading'
    progressVisible.value = true
    overlayVisible.value = false
    targetPath.value = path

    const currentSequence = sequence
    overlayTimer = setTimeout(() => {
        if (currentSequence === sequence && status.value === 'loading') {
            overlayVisible.value = true
        }
    }, OVERLAY_DELAY)
}

const finish = () => {
    if (status.value !== 'loading' || errorPending) return

    clearTimeout(overlayTimer)
    overlayTimer = null

    if (!overlayVisible.value) {
        setIdle()
        return
    }

    const currentSequence = sequence
    const remaining = Math.max(0, MIN_FEEDBACK_DURATION - (Date.now() - startedAt))
    settleTimer = setTimeout(() => {
        if (currentSequence === sequence && !errorPending) {
            setIdle()
        }
    }, remaining)
}

const fail = (path) => {
    if (status.value !== 'loading') {
        start(path)
    }

    clearTimers()
    errorPending = true
    targetPath.value = path
    progressVisible.value = true
    overlayVisible.value = true

    const currentSequence = sequence
    const remaining = Math.max(0, MIN_FEEDBACK_DURATION - (Date.now() - startedAt))
    settleTimer = setTimeout(() => {
        if (currentSequence === sequence && errorPending) {
            status.value = 'error'
            progressVisible.value = false
            overlayVisible.value = false
        }
    }, remaining)
}

const setLayoutMounted = (mounted) => {
    layoutMounted.value = mounted
}

export const useRouteLoading = () => ({
    status,
    progressVisible,
    overlayVisible,
    targetPath,
    layoutMounted,
    start,
    finish,
    fail,
    reset,
    setLayoutMounted
})
