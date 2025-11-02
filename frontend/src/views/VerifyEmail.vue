<template>
  <div class="w-full max-w-lg p-8 bg-white rounded-lg shadow-md text-center">
    <h2 class="text-2xl font-bold mb-6 text-gray-800">
      Almost there!
    </h2>
    <p class="text-lg text-slate-700">
      We've sent a verification link to your email address.
    </p>
    <p class="mt-4 text-base text-slate-500">
      (Psst... since we're in development, please check your
      <strong>Django `runserver` console</strong>. The link is printed there!)
    </p>
  </div>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router'
import { onMounted } from 'vue'

const route = useRoute()
const router = useRouter()

onMounted(() => {
  // 检查一下“门票”
  if (route.query.from !== 'register') {
    // 这个人没有票！他可能是F5刷新的，也可能是直接输URL闯进来的
    // 统统踢回到登录页
    router.push({ name: 'login' })
  }
})
</script>