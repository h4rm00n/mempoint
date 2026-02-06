import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { MemoryListItem } from '../types/memory'

export interface GraphNode {
  id: string
  name: string
  type: string
  x: number
  y: number
  size: number
  color: string
}

export interface GraphEdge {
  source: string
  target: string
  name: string
  value: number
}

export const useGraphStore = defineStore('graph', () => {
  // 状态
  const nodes = ref<GraphNode[]>([])
  const edges = ref<GraphEdge[]>([])
  const selectedNode = ref<GraphNode | null>(null)
  const loading = ref(false)
  const searchQuery = ref('')

  // 方法
  function setGraphData(memories: MemoryListItem[]) {
    // 简单的图谱数据构建逻辑
    const nodeMap = new Map<string, GraphNode>()
    const edgeList: GraphEdge[] = []

    memories.forEach((memory, index) => {
      const nodeId = memory.id
      if (!nodeMap.has(nodeId)) {
        nodeMap.set(nodeId, {
          id: nodeId,
          name: memory.content.substring(0, 20) + '...',
          type: memory.type,
          x: Math.random() * 800,
          y: Math.random() * 600,
          size: 20,
          color: memory.type === 'long_term' ? '#409EFF' : '#67C23A'
        })
      }
    })

    nodes.value = Array.from(nodeMap.values())
    edges.value = edgeList
  }

  function setSelectedNode(node: GraphNode | null) {
    selectedNode.value = node
  }

  function setSearchQuery(query: string) {
    searchQuery.value = query
  }

  function clearGraph() {
    nodes.value = []
    edges.value = []
    selectedNode.value = null
    searchQuery.value = ''
  }

  return {
    // 状态
    nodes,
    edges,
    selectedNode,
    loading,
    searchQuery,
    // 方法
    setGraphData,
    setSelectedNode,
    setSearchQuery,
    clearGraph
  }
})
