// frontend/src/utils/layouts.ts
// (这是可选的，但非常规范)
import AppLayout from '@/layouts/AppLayout.vue'
import AuthLayout from '@/layouts/AuthLayout.vue'
import BlankLayout from '@/layouts/BlankLayout.vue'

export const layouts = {
    'AppLayout': AppLayout,
    'AuthLayout': AuthLayout,
    'BlankLayout': BlankLayout,
}

// 解决 
export type LayoutKey = keyof typeof layouts;