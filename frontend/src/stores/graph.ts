import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getGraphData, type GraphNode, type GraphEdge } from '../api/graph'

export interface EChartsGraphNode {
  id: string
  name: string
  type: string
  x: number
  y: number
  size: number
  color: string
  description?: string
}

export interface EChartsGraphEdge {
  source: string
  target: string
  name: string
  value: number
  relationType: string
}

export const useGraphStore = defineStore('graph', () => {
  // 状态
  const nodes = ref<EChartsGraphNode[]>([])
  const edges = ref<EChartsGraphEdge[]>([])
  const selectedNode = ref<EChartsGraphNode | null>(null)
  const loading = ref(false)
  const searchQuery = ref('')

  // 实体类型颜色映射
  const typeColors: Record<string, string> = {
    'person': '#409EFF',
    'location': '#67C23A',
    'organization': '#E6A23C',
    'event': '#F56C6C',
    'concept': '#909399',
    'unknown': '#C0C4CC'
  }

  // 方法
  async function fetchGraphData(personaId: string, entityName?: string, maxDepth: number = 2) {
    loading.value = true
    try {
      const graphData = await getGraphData(personaId, entityName, maxDepth)
      setGraphData(graphData)
    } catch (error) {
      console.error('Failed to fetch graph data:', error)
      nodes.value = []
      edges.value = []
    } finally {
      loading.value = false
    }
  }

  function setGraphData(graphData: { nodes: GraphNode[], edges: GraphEdge[] }) {
    const nodeMap = new Map<string, EChartsGraphNode>()
    const edgeList: EChartsGraphEdge[] = []

    // 处理节点
    graphData.nodes.forEach((node) => {
      const nodeId = node.name
      if (!nodeMap.has(nodeId)) {
        nodeMap.set(nodeId, {
          id: nodeId,
          name: node.name,
          type: node.type,
          description: node.description,
          x: Math.random() * 800,
          y: Math.random() * 600,
          size: 30,
          color: typeColors[node.type] || typeColors['unknown']!
        })
      }
    })

    // 处理边
    graphData.edges.forEach((edge) => {
      edgeList.push({
        source: edge.from_entity,
        target: edge.to_entity,
        name: edge.relation_type,
        value: edge.weight || 1,
        relationType: edge.relation_type
      })
    })

    nodes.value = Array.from(nodeMap.values())
    edges.value = edgeList
  }

  function setSelectedNode(node: EChartsGraphNode | null) {
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
    fetchGraphData,
    setGraphData,
    setSelectedNode,
    setSearchQuery,
    clearGraph
  }
})
