<template>
    <!-- Toggle Button (when only 2 options) -->
    <el-button 
        v-if="speedOptions.length === 2"
        size="small" 
        circle 
        :type="theme === 'light' ? 'primary' : ''"
        class="speed-control-btn"
        :class="{ 'control-button is-dark': theme === 'dark' }"
        @click="handleToggleSpeed"
    >
        <span :class="theme === 'light' ? 'text-white' : 'text-sky-500'" class="text-[0.7em]">{{ currentRate }}x</span>
    </el-button>

    <!-- Dropdown (when > 2 options) -->
    <el-dropdown v-else @command="handleSpeedChange" trigger="click" popper-class="dark-popper">
        <el-button 
            size="small" 
            circle 
            :type="theme === 'light' ? 'primary' : ''"
            class="speed-control-btn"
            :class="{ 'control-button is-dark': theme === 'dark' }"
        >
            <span :class="theme === 'light' ? 'text-white' : 'text-sky-500'" class="text-[0.7em]">{{ currentRate }}x</span>
        </el-button>
        <template #dropdown>
            <el-dropdown-menu>
                <el-dropdown-item v-for="speed in speedOptions" :key="speed" :command="speed">
                    {{ speed }}x
                </el-dropdown-item>
            </el-dropdown-menu>
        </template>
    </el-dropdown>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';

const props = withDefaults(defineProps<{
    modelValue: number;
    theme?: 'light' | 'dark';
    options?: number[];
}>(), {
    theme: 'dark',
    options: () => [0.5, 1]
});

const emit = defineEmits<{
    (e: 'update:modelValue', value: number): void;
    (e: 'change', value: number): void;
}>();

const currentRate = ref(props.modelValue);
const speedOptions = computed(() => props.options);

watch(() => props.modelValue, (newVal) => {
    currentRate.value = newVal;
});

const handleSpeedChange = (rate: number) => {
    currentRate.value = rate;
    emit('update:modelValue', rate);
    emit('change', rate);
};

const handleToggleSpeed = () => {
    const currentIndex = speedOptions.value.indexOf(currentRate.value);
    // If current rate is not in options, default to first option
    const baseIndex = currentIndex === -1 ? 0 : currentIndex;
    const nextIndex = (baseIndex + 1) % speedOptions.value.length;
    handleSpeedChange(speedOptions.value[nextIndex]);
};
</script>

<style scoped>
.control-button.is-dark {
    --el-button-bg-color: #222b37;
    --el-button-border-color: #222b37;
    --el-button-hover-bg-color: #334155;
    --el-button-hover-border-color: #334155;
    --el-button-text-color: #fff;
    --el-button-hover-text-color: #fff;
    
    /* Force base styles */
    background-color: var(--el-button-bg-color) !important;
    border-color: var(--el-button-border-color) !important;
    color: var(--el-button-text-color) !important;
}

/* Force hover styles explicitly */
.control-button.is-dark:hover,
.control-button.is-dark:focus {
    background-color: var(--el-button-hover-bg-color) !important;
    border-color: var(--el-button-hover-border-color) !important;
    color: var(--el-button-hover-text-color) !important;
}
</style>
