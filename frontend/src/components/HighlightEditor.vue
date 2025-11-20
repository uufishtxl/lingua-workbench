<template>
  <div class="dark-editor">
    <!-- Top row: Tags and Close button -->
    <div class="flex justify-between items-center">
      <div class="flex items-center gap-2">
        <i-tabler-tag class="text-gray-400" />
        <el-select v-model="editableHighlight.tags" multiple placeholder="Select tags" size="small" class="tags-select"
          popper-class="dark-select-popper">
          <el-option v-for="tagOption in allTagOptions" :key="tagOption.value" :label="tagOption.value"
            :value="tagOption.value">
            {{ tagOption.label }}
          </el-option>
        </el-select>
      </div>
      <el-button text circle @click="handleCancel">
        <i-tabler-x class="text-gray-400" />
      </el-button>
    </div>

    <!-- Note -->
    <div class="note-input-wrapper">
      <el-input v-model="editableHighlight.note" type="textarea" :rows="2" placeholder="Add a note..." />
    </div>

    <!-- IPA Keyboard -->
    <div class="flex flex-col gap-1">
      <div class="flex items-center justify-center">
        <el-button class="symbol-button" @click="addSymbol(_symbol)" v-for="(_symbol, sid) in ipaSymbols" :key="sid" size="small">{{ _symbol }}</el-button>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-end mt-auto">
      <el-button text circle type="danger" @click="handleDelete">
        <i-tabler-eraser />
      </el-button>
      <el-button text circle type="primary" @click="handleSave">
        <i-tabler-device-floppy />
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import ipaSymbols from '@/data/ipa';
// Removed: import { Erase } from '@element-plus/icons-vue';

type TagType = 'Flap T' | 'Reduction' | 'Linking' | 'Resyllabification' | 'Flap-T'; // These are the full display names
type AbbreviatedTag = 'FT' | 'RED' | 'LINK' | 'RESYL' | 'FT_HYPHEN'; // These are the actual values stored

interface Hili {
  id: string;
  start: number;
  end: number;
  content: string;
  tags: AbbreviatedTag[]; // tags now store abbreviated values
  note: string;
}

const props = defineProps<{
  highlight: Hili;
}>();

const emit = defineEmits<{
  (e: 'update:highlight', highlight: Hili): void;
  (e: 'delete-highlight', highlightId: string): void;
  (e: 'cancel'): void;
}>();

const editableHighlight = ref<Hili>({ ...props.highlight });

const allTagOptions: { value: AbbreviatedTag; label: TagType }[] = [
  { value: 'FT', label: 'Flap T' },
  { value: 'RED', label: 'Reduction' },
  { value: 'LINK', label: 'Linking' },
  { value: 'RESYL', label: 'Resyllabification' },
  { value: 'FT_HYPHEN', label: 'Flap-T' },
];

watch(() => props.highlight, (newHighlight) => {
  editableHighlight.value = { ...newHighlight };
}, { deep: true, immediate: true });

const addSymbol = (symbol: string) => {
  editableHighlight.value.note += symbol
}

const handleSave = () => {
  emit('update:highlight', editableHighlight.value);
};

const handleCancel = () => {
  emit('cancel');
};

const handleDelete = () => {
  emit('delete-highlight', props.highlight.id);
}
</script>

<style scoped>
.dark-editor {
  background-color: #1C1338;
  height: 156px;
  /* Adjusted height for better spacing */
  padding: 8px;
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tags-select {
  width: 200px;
}

:deep(.el-select) {
  --el-select-input-focus-border-color: #4E466E;
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner) {
  background-color: #302849;
  box-shadow: none;
  color: white;
  border: 1px solid #4E466E;
}

:deep(.el-input__inner::placeholder),
:deep(.el-textarea__inner::placeholder) {
  color: #7d7a8c;
}

:deep(.el-select .el-select__tags-text) {
  color: white;
}

:deep(.el-tag) {
  --el-tag-bg-color: #4E466E;
  --el-tag-border-color: #675F93;
  --el-tag-hover-color: #7d7a8c;
}

:deep(.el-tag__close) {
  color: white;
}

:deep(.el-tag__close:hover) {
  background-color: #7d7a8c;
}

/* Ensure the el-select's input wrapper also gets the dark background */
:deep(.tags-select .el-input__wrapper) {
  background-color: #302849 !important;
  border: 1px solid #4E466E;
  box-shadow: none;
  color: white;
}

/* For the dropdown options list itself */
:deep(.el-select__wrapper),
:deep(.el-select__selection) {
  background: #1C1338;
}


:deep(.el-select__popper) {
  background-color: #302849 !important;
  border: 1px solid #4E466E;
}

:deep(.el-select-dropdown__item) {
  color: white;
}

:deep(.el-select-dropdown__item.hover),
:deep(.el-select-dropdown__item.selected) {
  background-color: #4E466E !important;
}

:deep(.el-button--small) {
  font-size: 10px;
  padding: 4px 6px;
}

:deep(.symbol-button.el-button) {
  background: black;
  color: white;
}

:deep(.el-tag--small) {
  font-size: 8px;
}

:deep(.el-textarea__inner) {
  border: 1px solid black;
  background: #302849;
  font-size:10px;
  resize: none;
}
</style>

<style>
/* Global styles for the dark popper, targeting the custom class */
.dark-select-popper {
  background-color: #302849 !important;
  border: 1px solid #4E466E !important;
}

.dark-select-popper .el-select-dropdown__item {
  background-color: #302849 !important; /* Default background for all items */
  color: white; /* Default text color for all items */
  font-size: 12px;
}

.dark-select-popper .el-select-dropdown__item.hover,
.dark-select-popper .el-select-dropdown__item:hover,
.dark-select-popper .el-select-dropdown__item:focus,
.dark-select-popper .el-select-dropdown__item.is-focus,
.dark-select-popper .el-select-dropdown__item.selected {
  background-color: #4E466E !important;
  color: #fff;
}

/* Optional: Style the arrow */
.dark-select-popper .el-popper__arrow::before {
  background: #302849 !important;
  border-color: #4E466E !important;
}
</style>
