import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

import vueDevTools from 'vite-plugin-vue-devtools'
import tailwindcss from '@tailwindcss/vite'
import AutoImport from 'unplugin-auto-import/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import Icons from 'unplugin-icons/vite'
import IconsResolver from 'unplugin-icons/resolver'
import Components from 'unplugin-vue-components/vite'
import { FileSystemIconLoader } from 'unplugin-icons/loaders'


// https://vite.dev/config/
export default defineConfig((config) => {

  // 从传入的 config 对象中获取 mode
  const mode = config.mode;

  // 1. 加载 .env 文件
  const env = loadEnv(mode, process.cwd(), '');

  // 2. 从 .env 中获取你的后端 API 地址
  const backendUrl = env.VITE_API_BASE_URL;

  // 3. 返回你的 Vite 配置
  return {
    plugins: [
      vue(),
      vueDevTools(),
      tailwindcss(),
      AutoImport({
        resolvers: [ElementPlusResolver()],
      }),
      // 2. 配置 unplugin-vue-components
      Components({
        // dts: true 自动生成 'components.d.ts'
        // 这将为所有自动导入的组件（包括图标）提供 TypeScript 类型提示
        dts: true,
        resolvers: [
          ElementPlusResolver(),
          // 3. 配置 unplugin-icons 的解析器
          IconsResolver({
            // 约定：所有 'i-' 开头的组件都会被 unplugin-icons 解析
            // 默认就是 'i'，你也可以改为 'icon'
            prefix: 'i',

            // 4. (可选) 配置本地 SVG 图标
            // 'local' 是你给本地图标集起的名字
            // 它会查找 './src/icons' 目录下的 SVG 文件
            customCollections: ['local'],
          }),
        ],
      }),

      // 5. 配置 unplugin-icons
      Icons({
        compiler: 'vue3', // 使用 Vue 3 编译器
        autoInstall: true, // 自动安装需要的图标集

        // 6. (可选) 定义本地 SVG 图标集的加载器
        // vite.config.js
        customCollections: {
          local: FileSystemIconLoader(
            './src/icons',
            svg => svg
              .replace(/^<svg /, '<svg fill="currentColor" ')
              // 使用正则表达式查找并移除 width="..." 属性
              .replace(/ width="[^"]*"/, '')
              // 使用正则表达式查找并移除 height="..." 属性
              .replace(/ height="[^"]*"/, '')
          ),
        },
      }),
    ],
    server: {
      host: '0.0.0.0',
      proxy: {
        // 使用带斜杠的 '/api' 就说暗号，说明要转发至目标
        '/api': {
          target: backendUrl, // 代理的目标地址
          changeOrigin: true, // 必须开启
          // rewrite: (path) => path.replace(/^\/api/, ''), // 去掉 /api 前缀
        },
        // Whisper 服务代理
        '/whisper': {
          target: 'http://localhost:8001',
          changeOrigin: true,
          // 替换掉 whisper 前缀，比如前端请求 /whisper/transcribe 发到目标网络服务地址（这里是8001端口）时，会替换为 http://localhost:8001/transcribe
          rewrite: (path) => path.replace(/^\/whisper/, ''),
        }
      }
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url))
      },
    },
    optimizeDeps: {
      exclude: ['wavesurfer.js']
    },
  };
});