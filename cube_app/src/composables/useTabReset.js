import { ref } from 'vue'

const resetTrigger = ref(0)

export function useTabReset() {
  function triggerReset() {
    resetTrigger.value++
  }
  return { resetTrigger, triggerReset }
}
