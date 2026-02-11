<template>
  <div class="graph-view">
    <div class="view-header">
      <h2>知识图谱</h2>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="loadGraphData">刷新</el-button>
        <el-button :icon="Download" @click="exportGraph">导出</el-button>
      </div>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm">
        <el-form-item label="搜索实体">
          <el-input
            v-model="graphStore.searchQuery"
            placeholder="搜索实体..."
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #append>
              <el-button :icon="Search" @click="handleSearch" />
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="记忆体">
          <el-select
            v-model="filterForm.persona_id"
            placeholder="选择记忆体"
            clearable
            @change="loadGraphData"
          >
            <el-option
              v-for="persona in personaStore.personas"
              :key="persona.id"
              :label="persona.name || persona.id"
              :value="persona.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="查询深度">
          <el-select
            v-model="filterForm.maxDepth"
            placeholder="选择深度"
            @change="loadGraphData"
          >
            <el-option label="1层" :value="1" />
            <el-option label="2层" :value="2" />
            <el-option label="3层" :value="3" />
          </el-select>
        </el-form-item>
      </el-form>
    </el-card>

    <div class="graph-container">
      <div v-loading="graphStore.loading" ref="graphRef" class="graph-chart"></div>
      <el-card v-if="graphStore.selectedNode" class="node-detail-card">
        <template #header>
          <div class="card-header">
            <h3>实体详情</h3>
            <el-button circle :icon="Close" @click="graphStore.setSelectedNode(null)" />
          </div>
        </template>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="名称">
            {{ graphStore.selectedNode.name }}
          </el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag>{{ graphStore.selectedNode.type }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="描述" v-if="graphStore.selectedNode.description">
            {{ graphStore.selectedNode.description }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
      
      <!-- 图例 -->
      <div class="graph-legend">
        <div class="legend-title">图例</div>
        <div class="legend-items">
          <div class="legend-item" v-for="(color, type) in typeColors" :key="type">
            <span class="legend-color" :style="{ backgroundColor: color }"></span>
            <span class="legend-label">{{ typeLabels[type] || type }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { useGraphStore } from '../stores/graph'
import { usePersonaStore } from '../stores/persona'
import { Refresh, Download, Search, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const graphStore = useGraphStore()
const personaStore = usePersonaStore()

const graphRef = ref<HTMLElement>()
const chartInstance = ref<echarts.ECharts>()
const filterForm = ref({
  persona_id: '',
  maxDepth: 2
})

// 实体类型颜色映射
const typeColors: Record<string, string> = {
  'person': '#409EFF',
  'location': '#67C23A',
  'organization': '#E6A23C',
  'event': '#F56C6C',
  'concept': '#909399',
  'unknown': '#C0C4CC'
}

// 实体类型中文标签
const typeLabels: Record<string, string> = {
  'person': '人物',
  'location': '地点',
  'organization': '组织',
  'event': '事件',
  'concept': '概念',
  'unknown': '未知'
}

onMounted(async () => {
  await personaStore.fetchPersonas()
  await loadGraphData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (chartInstance.value) {
    chartInstance.value.dispose()
  }
  window.removeEventListener('resize', handleResize)
})

async function loadGraphData() {
  if (!filterForm.value.persona_id) {
    ElMessage.warning('请先选择记忆体')
    return
  }
  await graphStore.fetchGraphData(filterForm.value.persona_id, undefined, filterForm.value.maxDepth)
  renderGraph()
}

function renderGraph() {
  if (!graphRef.value) return

  if (chartInstance.value) {
    chartInstance.value.dispose()
  }

  chartInstance.value = echarts.init(graphRef.value)

  const graphData = graphStore.nodes.map((node) => {
    return {
      id: node.id,
      name: node.name,
      symbolSize: node.size,
      itemStyle: {
        color: node.color
      },
      // 添加自定义数据
      type: node.type,
      description: node.description
    }
  })

  const option = {
    tooltip: {
      formatter: (params: any) => {
        if (params.dataType === 'node') {
          const typeLabel = typeLabels[params.data.type] || params.data.type
          let tooltip = `<strong>${params.name}</strong><br/>`
          tooltip += `<span style="display:inline-block;width:10px;height:10px;background-color:${params.color};margin-right:5px;"></span>${typeLabel}`
          if (params.data.description) {
            tooltip += `<br/><small>${params.data.description}</small>`
          }
          return tooltip
        } else if (params.dataType === 'edge') {
          return `${params.data.source} --[${params.data.name}]--> ${params.data.target}`
        }
        return params.name
      }
    },
    series: [
      {
        type: 'graph',
        layout: 'force',
        data: graphData,
        links: graphStore.edges,
        roam: true,
        label: {
          show: true,
          position: 'right',
          formatter: '{b}',
          fontSize: 12
        },
        edgeLabel: {
          show: true,
          formatter: '{c}',
          fontSize: 10
        },
        lineStyle: {
          color: 'source',
          curveness: 0.3,
          width: 2
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 4
          }
        },
        force: {
          repulsion: 1000,
          edgeLength: 100,
          gravity: 0.1
        }
      }
    ]
  }

  chartInstance.value.setOption(option)

  chartInstance.value.on('click', (params: any) => {
    if (params.dataType === 'node') {
      const node = graphStore.nodes.find((n) => n.id === params.data.id)
      if (node) {
        graphStore.setSelectedNode(node)
      }
    }
  })
}

function handleSearch() {
  if (!chartInstance.value) return

  if (graphStore.searchQuery) {
    const matchedNodes = graphStore.nodes.filter((node) =>
      node.name.toLowerCase().includes(graphStore.searchQuery.toLowerCase())
    )

    const searchData = graphStore.nodes.map((node) => {
      return {
        ...node,
        itemStyle: {
          color: matchedNodes.some((n) => n.id === node.id)
            ? '#f56c6c'
            : node.color
        }
      }
    })

    chartInstance.value.setOption({
      series: [
        {
          data: searchData
        }
      ]
    })
  } else {
    renderGraph()
  }
}

function handleResize() {
  chartInstance.value?.resize()
}

function exportGraph() {
  if (!chartInstance.value) return

  const url = chartInstance.value.getDataURL({
    type: 'png',
    pixelRatio: 2
  })

  const link = document.createElement('a')
  link.download = 'graph.png'
  link.href = url
  link.click()

  ElMessage.success('图谱已导出')
}
</script>

<style scoped>
.graph-view {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.view-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.view-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.filter-card {
  margin-bottom: 0;
}

.graph-container {
  position: relative;
  height: 600px;
  background-color: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.graph-chart {
  width: 100%;
  height: 100%;
}

.node-detail-card {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 300px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}

.graph-legend {
  position: absolute;
  bottom: 20px;
  left: 20px;
  background-color: rgba(255, 255, 255, 0.95);
  padding: 12px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 10;
}

.legend-title {
  font-weight: bold;
  margin-bottom: 8px;
  font-size: 14px;
}

.legend-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  flex-shrink: 0;
}

.legend-label {
  color: #606266;
}
</style>
