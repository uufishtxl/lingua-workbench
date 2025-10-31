// frontend/src/utils/layouts.ts
// (这是可选的，但非常规范)
import AppLayout from '@/layouts/AppLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'

export const layouts = {
    'AppLayout': AppLayout,
    'AuthLayout': AuthLayout,
    // (如果你有第三个布局, 在这里添加)
}

// 解决 
export type LayoutKey = keyof typeof layouts;