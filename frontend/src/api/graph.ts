/**
 * Graph API - 知识图谱数据接口
 */
import request from '@/utils/request'

export interface GraphNode {
  name: string
  type: string
  description?: string
  created_at?: number
  last_accessed_at?: number
}

export interface GraphEdge {
  from_entity: string
  to_entity: string
  relation_type: string
  weight?: number
  created_at?: number
}

export interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

/**
 * 获取知识图谱数据
 * @param personaId 记忆体ID
 * @param entityName 实体名称（可选）
 * @param maxDepth 最大查询深度
 */
export async function getGraphData(
  personaId: string,
  entityName?: string,
  maxDepth: number = 2
): Promise<GraphData> {
  const params: any = {
    persona_id: personaId,
    max_depth: maxDepth
  }
  if (entityName) {
    params.entity_name = entityName
  }

  const response = await request.get<GraphData>('/v1/graph', { params })
  return response.data
}

/**
 * 获取所有实体节点
 * @param limit 返回数量限制
 */
export async function getAllEntities(limit: number = 100): Promise<GraphNode[]> {
  const response = await request.get<GraphNode[]>('/v1/graph/entities', {
    params: { limit }
  })
  return response.data
}

/**
 * 获取指定实体及其关联关系
 * @param entityName 实体名称
 * @param maxDepth 最大查询深度
 */
export async function getEntityRelations(
  entityName: string,
  maxDepth: number = 2
): Promise<GraphData> {
  const response = await request.get<GraphData>(`/v1/graph/entities/${entityName}`, {
    params: { max_depth: maxDepth }
  })
  return response.data
}
