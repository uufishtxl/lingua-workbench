/**
 * UrlInput 组件测试
 * 这些测试可以在 Windows 上运行，需要安装 vitest
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import UrlInput from '../UrlInput.vue'

// 模拟 whisperApi
vi.mock('@/api/whisperApi', () => ({
  getVideoInfo: vi.fn()
}))

import { getVideoInfo } from '@/api/whisperApi'

describe('UrlInput', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders input field correctly', () => {
    const wrapper = mount(UrlInput)
    
    // 验证输入框存在
    expect(wrapper.find('input').exists()).toBe(true)
    
    // 验证占位符文本
    expect(wrapper.find('input').attributes('placeholder')).toContain('YouTube URL')
  })

  it('shows invalid URL hint for invalid input', async () => {
    const wrapper = mount(UrlInput)
    
    // 输入无效 URL
    await wrapper.find('input').setValue('not-a-url')
    await nextTick()
    
    // 验证显示提示
    expect(wrapper.find('.url-hint').exists()).toBe(true)
    expect(wrapper.find('.url-hint').text()).toContain('有效的 URL')
  })

  it('does not show invalid URL hint for valid input', async () => {
    const wrapper = mount(UrlInput)
    
    // 输入有效 URL
    await wrapper.find('input').setValue('https://www.youtube.com/watch?v=test123')
    await nextTick()
    
    // 验证不显示提示
    expect(wrapper.find('.url-hint').exists()).toBe(false)
  })

  it('calls getVideoInfo when clicking fetch button', async () => {
    // 模拟返回数据
    const mockInfo = {
      title: 'Test Video',
      thumbnail_url: 'https://example.com/thumb.jpg',
      duration: 120,
      author: 'Test Author',
      platform: 'youtube'
    }
    vi.mocked(getVideoInfo).mockResolvedValue(mockInfo)

    const wrapper = mount(UrlInput)
    
    // 输入有效 URL
    await wrapper.find('input').setValue('https://www.youtube.com/watch?v=test123')
    await nextTick()
    
    // 点击获取预览按钮
    await wrapper.find('.el-input-group__append button').trigger('click')
    
    // 等待异步操作
    await vi.waitFor(() => {
      expect(getVideoInfo).toHaveBeenCalledWith('https://www.youtube.com/watch?v=test123')
    })
    
    // 验证触发了 preview 事件
    expect(wrapper.emitted('preview')).toBeTruthy()
    expect(wrapper.emitted('preview')![0]).toEqual([mockInfo])
  })

  it('emits error event on API failure', async () => {
    // 模拟 API 错误
    const mockError = new Error('Network error')
    vi.mocked(getVideoInfo).mockRejectedValue(mockError)

    const wrapper = mount(UrlInput)
    
    // 输入有效 URL
    await wrapper.find('input').setValue('https://www.youtube.com/watch?v=test123')
    await nextTick()
    
    // 点击获取预览按钮
    await wrapper.find('.el-input-group__append button').trigger('click')
    
    // 等待异步操作
    await vi.waitFor(() => {
      expect(wrapper.emitted('error')).toBeTruthy()
    })
    
    // 验证错误消息
    expect(wrapper.emitted('error')![0]).toEqual(['Network error'])
  })

  it('debounces input for auto-fetch', async () => {
    // 模拟返回数据
    const mockInfo = {
      title: 'Test Video',
      thumbnail_url: 'https://example.com/thumb.jpg',
      duration: 120,
      author: 'Test Author',
      platform: 'youtube'
    }
    vi.mocked(getVideoInfo).mockResolvedValue(mockInfo)

    const wrapper = mount(UrlInput)
    
    // 快速输入多个字符
    await wrapper.find('input').setValue('h')
    await wrapper.find('input').setValue('ht')
    await wrapper.find('input').setValue('htt')
    await wrapper.find('input').setValue('https://www.youtube.com/watch?v=test123')
    
    // 等待防抖时间（500ms）
    await new Promise(resolve => setTimeout(resolve, 600))
    
    // 验证只调用了一次 API
    expect(getVideoInfo).toHaveBeenCalledTimes(1)
    expect(getVideoInfo).toHaveBeenCalledWith('https://www.youtube.com/watch?v=test123')
  })

  it('disables input while loading', async () => {
    // 模拟慢速 API 响应
    vi.mocked(getVideoInfo).mockImplementation(() => 
      new Promise(resolve => setTimeout(resolve, 1000))
    )

    const wrapper = mount(UrlInput)
    
    // 输入有效 URL
    await wrapper.find('input').setValue('https://www.youtube.com/watch?v=test123')
    await nextTick()
    
    // 点击获取预览按钮
    await wrapper.find('.el-input-group__append button').trigger('click')
    
    // 验证输入框被禁用
    expect(wrapper.find('input').attributes('disabled')).toBeDefined()
  })
})

// 运行测试的说明
console.log("请使用 vitest 运行测试:")
console.log("cd /workspace/frontend")
console.log("npx vitest run src/components/whisper/__tests__/UrlInput.test.ts")
