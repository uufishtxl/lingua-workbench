<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { GraphChart } from 'echarts/charts';
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components';
import type { GraphData, WordNode } from '@/api/englishCornerApi';

use([
  CanvasRenderer,
  GraphChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
]);

const props = defineProps<{
  data: GraphData;
}>();

const emit = defineEmits(['node-click']);

const searchQuery = ref('');
const selectedBoxLevel = ref<number | null>(null);

// Filtered Data
const filteredData = computed(() => {
  let nodes = props.data.nodes;
  
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    nodes = nodes.filter(n => n.label.toLowerCase().includes(q) || n.explanation.toLowerCase().includes(q));
  }
  
  if (selectedBoxLevel.value !== null) {
    nodes = nodes.filter(n => n.box_level === selectedBoxLevel.value);
  }
  
  const nodeIds = new Set(nodes.map(n => String(n.id)));
  const links = props.data.links.filter(l => nodeIds.has(String(l.source)) && nodeIds.has(String(l.target)));
  
  return { nodes, links };
});

const chartOptions = computed(() => {
  const nodes = (filteredData.value.nodes || []).map(node => {
    if (!node || !node.id) return null;
    return {
      ...node,
      id: node.id,
      name: node.id,
      displayName: node.label,
      symbolSize: 30 + ((node.mastery || 0) / 100) * 40,
      itemStyle: {
        color: node.node_type === 'phrase' ? '#3b82f6' : '#10b981',
        shadowBlur: 10,
        shadowColor: 'rgba(0,0,0,0.3)'
      },
      label: {
        show: true,
        position: 'right',
        color: '#94a3b8',
        fontSize: 12,
        formatter: (params: any) => params.data.displayName || params.data.label
      }
    };
  }).filter(Boolean);

  const nodeIds = new Set(nodes.map(n => String(n!.id)));

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      enterable: true,
      confine: true,
      backgroundColor: 'rgba(15, 23, 42, 0.9)',
      backdropFilter: 'blur(8px)',
      borderColor: '#334155',
      textStyle: { color: '#f8fafc' },
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const node = params.data;
          const name = node.displayName || node.label || node.id;
          return `
            <div style="padding: 12px; max-width: 280px; font-family: sans-serif; word-wrap: break-word; white-space: normal; overflow: hidden;">
              <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
                <span style="font-weight: 800; color: #fbbf24; font-size: 16px;">${name}</span>
                <span style="background: #334155; color: #94a3b8; font-size: 10px; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">${node.node_type || 'WORD'}</span>
              </div>
              <div style="color: #cbd5e1; font-size: 13px; line-height: 1.5; margin-bottom: 8px;">
                ${node.explanation || ''}
              </div>
              <div style="font-style: italic; color: #64748b; font-size: 12px; border-left: 2px solid #334155; padding-left: 8px;">
                "${node.example || ''}"
              </div>
              <div style="margin-top: 10px; display: flex; gap: 12px; font-size: 11px; color: #94a3b8;">
                <span>Mastery: ${node.mastery || 0}%</span>
                <span>Box: ${node.box_level || 1}</span>
              </div>
            </div>
          `;
        }
        return params.data.relation;
      },
    },
    series: [
      {
        id: 'main-graph',
        type: 'graph',
        layout: 'force',
        data: nodes,
        links: (filteredData.value.links || []).filter(link => {
          return nodeIds.has(String(link.source)) && nodeIds.has(String(link.target));
        }),
        roam: true,
        force: {
          repulsion: 1500,
          edgeLength: 120,
        },
        lineStyle: {
          color: 'rgba(255, 255, 255, 0.1)',
          width: 2,
          curveness: 0.1,
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 4,
            color: '#3b82f6',
          },
        },
      },
    ],
  };
});

const onChartClick = (params: any) => {
  if (params.dataType === 'node' && params.data) {
    emit('node-click', params.data);
  }
};
</script>

<template>
  <div class="graph-container">
    <v-chart class="chart" :option="chartOptions" @click="onChartClick" autoresize />
    
    <!-- Filter & Search Controls (Commented out) -->
    <!--
    <div class="controls-overlay">
      ...
    </div>
    -->
  </div>
</template>

<style scoped>
.graph-container {
  width: 100%;
  height: 100%;
  position: relative;
  background: radial-gradient(circle at center, #1e293b 0%, #0f172a 100%);
}

.chart {
  width: 100%;
  height: 100%;
}

.controls-overlay {
  position: absolute;
  top: 40px;
  left: 60px;
  display: flex;
  flex-direction: row; /* Horizontal Layout */
  align-items: center;
  gap: 32px;
  z-index: 50;
  pointer-events: auto;
}

.header-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.header-section .title {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 900;
  color: #f8fafc;
  letter-spacing: 0.1em;
  text-shadow: 0 0 20px rgba(255, 255, 255, 0.1);
}

.header-section .divider {
  width: 40px;
  height: 3px;
  background: #3b82f6;
  border-radius: 2px;
}

.search-box {
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  width: 300px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
}

.search-icon {
  font-size: 14px;
  opacity: 0.5;
}

.search-box input {
  background: transparent;
  border: none;
  color: white;
  font-size: 0.9rem;
  width: 100%;
  outline: none;
}

.clear-btn {
  background: none;
  border: none;
  color: #64748b;
  cursor: pointer;
  font-size: 12px;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-group .label {
  font-size: 0.6rem;
  font-weight: 800;
  color: #475569;
  letter-spacing: 0.15em;
}

.chips {
  display: flex;
  gap: 8px;
}

.filter-chip {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
  padding: 8px 16px;
  border-radius: 10px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-chip:hover {
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.filter-chip.active {
  background: #3b82f6;
  border-color: #3b82f6;
  color: white;
  box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
}
</style>
