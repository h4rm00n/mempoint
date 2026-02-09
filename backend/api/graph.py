"""
Graph API - 知识图谱数据接口
"""
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status, Header, Query
from pydantic import BaseModel, Field

from config import settings
from memory.graph_store import get_graph_store
from utils.logger import logger


router = APIRouter()


def verify_api_key(authorization: Optional[str] = Header(None)) -> None:
    """
    验证API Key权限

    Args:
        authorization: 从Authorization header中获取的Bearer token

    Raises:
        HTTPException: 如果API Key验证失败
    """
    if settings.API_KEY:
        # 从 Authorization header 中提取 Bearer token
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header. Expected: 'Bearer <token>'"
            )
        token = authorization[7:]  # 移除 "Bearer " 前缀
        if token != settings.API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key"
            )


class GraphNodeResponse(BaseModel):
    """图谱节点响应"""
    name: str = Field(..., description="实体名称")
    type: str = Field(..., description="实体类型")
    description: Optional[str] = Field(None, description="实体描述")
    created_at: Optional[int] = Field(None, description="创建时间戳")
    last_accessed_at: Optional[int] = Field(None, description="最后访问时间戳")


class GraphEdgeResponse(BaseModel):
    """图谱边响应"""
    from_entity: str = Field(..., description="起始实体")
    to_entity: str = Field(..., description="目标实体")
    relation_type: str = Field(..., description="关系类型")
    weight: Optional[float] = Field(None, description="关系权重")
    created_at: Optional[int] = Field(None, description="创建时间戳")


class GraphDataResponse(BaseModel):
    """图谱数据响应"""
    nodes: List[GraphNodeResponse] = Field(..., description="节点列表")
    edges: List[GraphEdgeResponse] = Field(..., description="边列表")


class GraphQueryRequest(BaseModel):
    """图谱查询请求"""
    entity_name: Optional[str] = Field(None, description="实体名称（可选，如果提供则查询该实体及其关联）")
    max_depth: int = Field(2, ge=1, le=5, description="最大查询深度")


@router.get("/graph", response_model=GraphDataResponse)
async def get_graph_data(
    persona_id: str = Query(..., description="记忆体ID"),
    entity_name: Optional[str] = Query(None, description="实体名称（可选）"),
    max_depth: int = Query(2, ge=1, le=5, description="最大查询深度"),
    authorization: Optional[str] = Header(None)
):
    """
    获取知识图谱数据

    Args:
        persona_id: 记忆体ID
        entity_name: 实体名称（可选），如果提供则查询该实体及其关联
        max_depth: 最大查询深度（1-5）
        authorization: Authorization header，格式为 'Bearer <token>'

    Returns:
        图谱数据（节点和边）
    """
    verify_api_key(authorization)

    try:
        graph_store = get_graph_store()

        # 如果提供了实体名称，查询该实体及其关联
        if entity_name:
            result = await graph_store.query_entity(
                entity_name=entity_name,
                persona_id=persona_id,
                max_depth=max_depth
            )
            logger.info(f"Queried graph for entity: {entity_name}, found {len(result['nodes'])} nodes, {len(result['edges'])} edges")
        else:
            # 查询所有实体和关系
            result = await _get_all_graph_data(graph_store, persona_id)
            logger.info(f"Queried all graph data for persona: {persona_id}, found {len(result['nodes'])} nodes, {len(result['edges'])} edges")

        return GraphDataResponse(
            nodes=[GraphNodeResponse(**node) for node in result["nodes"]],
            edges=[GraphEdgeResponse(**edge) for edge in result["edges"]]
        )

    except Exception as e:
        logger.error(f"Error getting graph data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


async def _get_all_graph_data(graph_store, persona_id: str) -> Dict[str, Any]:
    """
    获取所有图谱数据

    Args:
        graph_store: 图谱存储实例
        persona_id: 记忆体ID

    Returns:
        图谱数据（节点和边）
    """
    try:
        escaped_persona_id = persona_id.replace("'", "''")
        
        # 查询所有实体节点
        entities_result = graph_store.conn.execute(f"""
            MATCH (e:{settings.KUZU_NODE_TABLE_ENTITY} {{persona_id: '{escaped_persona_id}'}})
            RETURN e
        """)

        nodes = []
        for row in entities_result:
            entity = row[0]
            nodes.append({
                "name": entity.get("name"),
                "type": entity.get("type"),
                "description": entity.get("description"),
                "created_at": entity.get("created_at"),
                "last_accessed_at": entity.get("last_accessed_at")
            })

        # 查询所有关系边
        relations_result = graph_store.conn.execute(f"""
            MATCH (e1:{settings.KUZU_NODE_TABLE_ENTITY} {{persona_id: '{escaped_persona_id}'}})-[r:{settings.KUZU_REL_TABLE_RELATED_TO}]->(e2:{settings.KUZU_NODE_TABLE_ENTITY} {{persona_id: '{escaped_persona_id}'}})
            RETURN e1.name AS from_entity, e2.name AS to_entity, r.weight AS weight, r.created_at AS created_at
        """)

        edges = []
        for row in relations_result:
            edges.append({
                "from_entity": row[0],
                "to_entity": row[1],
                "relation_type": "RELATED_TO",
                "weight": row[2],
                "created_at": row[3]
            })

        return {
            "nodes": nodes,
            "edges": edges
        }

    except Exception as e:
        logger.error(f"Error getting all graph data: {e}")
        return {"nodes": [], "edges": []}


@router.get("/graph/entities", response_model=List[GraphNodeResponse])
async def get_all_entities(
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
    authorization: Optional[str] = Header(None)
):
    """
    获取所有实体节点

    Args:
        limit: 返回数量限制
        authorization: Authorization header，格式为 'Bearer <token>'

    Returns:
        实体节点列表
    """
    verify_api_key(authorization)

    try:
        graph_store = get_graph_store()

        # 查询所有实体节点
        entities_result = graph_store.conn.execute(f"""
            MATCH (e:{settings.KUZU_NODE_TABLE_ENTITY})
            RETURN e
            LIMIT {limit}
        """)

        nodes = []
        for row in entities_result:
            entity = row[0]
            nodes.append({
                "name": entity.get("name"),
                "type": entity.get("type"),
                "description": entity.get("description"),
                "created_at": entity.get("created_at"),
                "last_accessed_at": entity.get("last_accessed_at")
            })

        logger.info(f"Retrieved {len(nodes)} entities")
        return [GraphNodeResponse(**node) for node in nodes]

    except Exception as e:
        logger.error(f"Error getting entities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/graph/entities/{entity_name}", response_model=GraphDataResponse)
async def get_entity_relations(
    entity_name: str,
    persona_id: str = Query(..., description="记忆体ID"),
    max_depth: int = Query(2, ge=1, le=5, description="最大查询深度"),
    authorization: Optional[str] = Header(None)
):
    """
    获取指定实体及其关联关系

    Args:
        entity_name: 实体名称
        persona_id: 记忆体ID
        max_depth: 最大查询深度（1-5）
        authorization: Authorization header，格式为 'Bearer <token>'

    Returns:
        图谱数据（节点和边）
    """
    verify_api_key(authorization)

    try:
        graph_store = get_graph_store()

        result = await graph_store.query_entity(
            entity_name=entity_name,
            persona_id=persona_id,
            max_depth=max_depth
        )

        logger.info(f"Retrieved relations for entity: {entity_name}, found {len(result['nodes'])} nodes, {len(result['edges'])} edges")

        return GraphDataResponse(
            nodes=[GraphNodeResponse(**node) for node in result["nodes"]],
            edges=[GraphEdgeResponse(**edge) for edge in result["edges"]]
        )

    except Exception as e:
        logger.error(f"Error getting entity relations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
