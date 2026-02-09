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
          <el-descriptions-item label="大小">
            {{ graphStore.selectedNode.size }}
          </el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'
import { useGraphStore } from '../stores/graph'
import { useMemoryStore } from '../stores/memory'
import { usePersonaStore } from '../stores/persona'
import { Refresh, Download, Search, Close } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const graphStore = useGraphStore()
const memoryStore = useMemoryStore()
const personaStore = usePersonaStore()

const graphRef = ref<HTMLElement>()
const chartInstance = ref<echarts.ECharts>()
const filterForm = ref({
  persona_id: ''
})

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
  graphStore.loading = true
  await memoryStore.fetchMemories(filterForm.value)
  graphStore.setGraphData(memoryStore.memories)
  renderGraph()
  graphStore.loading = false
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
      }
    }
  })

  const option = {
    tooltip: {
      formatter: (params: any) => params.name
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
          formatter: '{b}'
        },
        lineStyle: {
          color: 'source',
          curveness: 0.3
        },
        emphasis: {
          focus: 'adjacency',
          lineStyle: {
            width: 10
          }
        },
        force: {
          repulsion: 1000,
          edgeLength: 100
        }
      }
    ]
  }

  chartInstance.value.setOption(option)

  chartInstance.value.on('click', (params: any) => {
    const node = graphStore.nodes.find((n) => n.id === params.data.id)
    if (node) {
      graphStore.setSelectedNode(node)
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
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
}
</style>
