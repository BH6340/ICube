import test from 'node:test'
import assert from 'node:assert/strict'

const wait = (duration) => new Promise(resolve => setTimeout(resolve, duration))

test('快速路由切换不会显示内容区遮罩', async () => {
    const { useRouteLoading } = await import('../src/stores/routeLoading.js')
    const routeLoading = useRouteLoading()

    routeLoading.reset()
    routeLoading.start('/formulas')

    assert.equal(routeLoading.status.value, 'loading')
    assert.equal(routeLoading.progressVisible.value, true)
    assert.equal(routeLoading.overlayVisible.value, false)

    routeLoading.finish()

    assert.equal(routeLoading.status.value, 'idle')
    assert.equal(routeLoading.progressVisible.value, false)
})

test('较慢的路由切换显示遮罩并满足最短展示时间', async () => {
    const { useRouteLoading } = await import('../src/stores/routeLoading.js')
    const routeLoading = useRouteLoading()

    routeLoading.reset()
    routeLoading.start('/forum')
    await wait(200)

    assert.equal(routeLoading.overlayVisible.value, true)

    routeLoading.finish()
    assert.equal(routeLoading.status.value, 'loading')

    await wait(230)
    assert.equal(routeLoading.status.value, 'idle')
    assert.equal(routeLoading.overlayVisible.value, false)
})

test('路由加载失败显示错误状态且不会被完成钩子覆盖', async () => {
    const { useRouteLoading } = await import('../src/stores/routeLoading.js')
    const routeLoading = useRouteLoading()

    routeLoading.reset()
    routeLoading.start('/shop')
    routeLoading.fail('/shop')
    routeLoading.finish()

    assert.equal(routeLoading.status.value, 'loading')
    assert.equal(routeLoading.overlayVisible.value, true)

    await wait(430)
    assert.equal(routeLoading.status.value, 'error')
    assert.equal(routeLoading.targetPath.value, '/shop')
    assert.equal(routeLoading.progressVisible.value, false)
})

test('主布局挂载状态可用于选择全局或内容区兜底', async () => {
    const { useRouteLoading } = await import('../src/stores/routeLoading.js')
    const routeLoading = useRouteLoading()

    routeLoading.setLayoutMounted(true)
    assert.equal(routeLoading.layoutMounted.value, true)

    routeLoading.setLayoutMounted(false)
    assert.equal(routeLoading.layoutMounted.value, false)
})
