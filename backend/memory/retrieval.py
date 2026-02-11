"""
检索策略
"""
from typing import List, Dict, Any, Optional
import asyncio

from config import settings
from utils.logger import logger
from utils.helpers import calculate_similarity_score, get_current_timestamp_ms
from memory.vector_store import vector_store
from memory.graph_store import graph_store
from memory.memory_manager import memory_manager


class RetrievalStrategy:
    """
    检索策略类
    实现不同的记忆检索策略
    """

    def __init__(self):
        """初始化检索策略"""
        self.top_k = settings.MILVUS_TOP_K
        # 评分权重（从settings中获取）
        self.similarity_weight = settings.MEMORY_SCORE_SIMILARITY_WEIGHT
        self.access_weight = settings.MEMORY_SCORE_ACCESS_WEIGHT
        self.recency_weight = settings.MEMORY_SCORE_RECENCY_WEIGHT
        self.graph_weight = settings.MEMORY_SCORE_GRAPH_WEIGHT
        self.lambda_decay = settings.MEMORY_RECENCY_DECAY_LAMBDA
        logger.info("RetrievalStrategy initialized")

    async def retrieve(
        self,
        query_embedding: List[float],
        query_text: str,
        persona_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索记忆

        Args:
            query_embedding: 查询向量
            query_text: 查询文本
            persona_id: 记忆体ID

        Returns:
            长期记忆列表
        """
        logger.info(f"[DEBUG] RetrievalStrategy.retrieve: query_text='{query_text}', persona_id='{persona_id}'")
        # 检索长期记忆
        long_term_memories = await self._retrieve_long_term(
            query_embedding,
            query_text,
            persona_id
        )

        logger.info(f"[DEBUG] RetrievalStrategy retrieved {len(long_term_memories)} long-term memories")

        return long_term_memories

    async def _retrieve_long_term(
        self,
        query_embedding: List[float],
        query_text: str,
        persona_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        检索长期记忆

        Args:
            query_embedding: 查询向量
            query_text: 查询文本
            persona_id: 记忆体ID

        Returns:
            长期记忆列表
        """
        try:
            logger.info(f"[DEBUG] _retrieve_long_term: persona_id='{persona_id}', top_k={self.top_k}")
            # 从向量存储中搜索
            results = await vector_store.search_knowledge(
                embedding=query_embedding,
                top_k=self.top_k,
                persona_id=persona_id
            )
            logger.info(f"[DEBUG] vector_store.search_knowledge returned {len(results)} results")

            # 从数据库中获取event_time信息
            results = await self._enrich_with_event_time(results)
            logger.info(f"[DEBUG] After enrich_with_event_time: {len(results)} results")

            # 增强结果：添加图谱信息
            enhanced_results = await self._enhance_with_graph(
                results,
                query_text,
                persona_id
            )
            logger.info(f"[DEBUG] After enhance_with_graph: {len(enhanced_results)} results")

            # 使用综合评分重新排序
            scored_results = self._rescore_with_memory_score(enhanced_results)
            logger.info(f"[DEBUG] After rescore_with_memory_score: {len(scored_results)} results")

            # 更新访问信息（使用memory_id）
            for result in scored_results:
                memory_id = result.get("memory_id")
                if memory_id:
                    await memory_manager.update_memory_access(memory_id)

            return scored_results

        except Exception as e:
            logger.error(f"Failed to retrieve long-term memories: {e}")
            return []

    def _rescore_with_memory_score(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        使用综合评分重新排序记忆

        Args:
            results: 检索结果

        Returns:
            重新排序后的结果
        """
        scored_results = []
        for result in results:
            similarity = result.get("similarity", 0.0)
            graph_score = result.get("graph_score", 0.0)
            
            # 直接在这里计算综合评分，避免循环导入
            access_count = result.get("access_count", 0) or 0
            last_accessed_at = result.get("last_accessed_at") or get_current_timestamp_ms()
            created_at = result.get("created_at") or get_current_timestamp_ms()
            
            # 计算评分
            final_score = calculate_similarity_score(
                similarity=similarity,
                access_count=access_count,
                max_access_count=100,
                last_accessed_at=last_accessed_at,
                created_at=created_at,
                lambda_decay=self.lambda_decay,
                graph_score=graph_score
            )

            result["final_score"] = final_score
            
            # 确保memory_id存在
            if "memory_id" not in result and "vector_id" in result:
                # 如果只有vector_id，使用它作为临时ID（向后兼容）
                result["memory_id"] = result["vector_id"]
            
            scored_results.append(result)

        # 按综合评分降序排序
        scored_results.sort(key=lambda x: x.get("final_score", 0.0), reverse=True)

        return scored_results

    async def _enhance_with_graph(
        self,
        results: List[Dict[str, Any]],
        query_text: str,
        persona_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        使用图谱信息增强检索结果（批量查询优化）

        Args:
            results: 向量检索结果
            query_text: 查询文本
            persona_id: 记忆体ID

        Returns:
            增强后的结果列表
        """
        enhanced_results = []

        # 1. 收集所有需要查询的entity_id
        entity_ids = set()
        for result in results:
            entity_id = result.get("entity_id")
            if entity_id:
                entity_ids.add(entity_id)

        # 2. 批量查询图谱数据
        graph_data_map = {}
        if entity_ids:
            try:
                # 使用并发查询
                query_tasks = [
                    graph_store.query_entity(entity_name=entity_id, persona_id=persona_id or "", max_depth=2)
                    for entity_id in entity_ids
                ]
                query_results = await asyncio.gather(*query_tasks, return_exceptions=True)

                for entity_id, result in zip(entity_ids, query_results):
                    if isinstance(result, Exception):
                        logger.warning(f"Failed to query entity {entity_id}: {result}")
                    else:
                        graph_data_map[entity_id] = result

            except Exception as e:
                logger.warning(f"Failed to batch query graph data: {e}")

        # 3. 将图谱数据添加到结果中
        for result in results:
            entity_id = result.get("entity_id")
            if not entity_id:
                enhanced_results.append(result)
                continue

            try:
                graph_data = graph_data_map.get(entity_id, {"nodes": [], "edges": []})
                graph_score = self._calculate_graph_score(graph_data)

                result["graph_data"] = graph_data
                result["graph_score"] = graph_score

                enhanced_results.append(result)

            except Exception as e:
                logger.warning(f"Failed to enhance result with graph: {e}")
                enhanced_results.append(result)

        return enhanced_results

    def _calculate_graph_score(self, graph_data: Dict[str, Any]) -> float:
        """
        计算图谱评分

        Args:
            graph_data: 图谱数据

        Returns:
            图谱评分 (0-1)
        """
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        if not nodes:
            return 0.0

        # 基于节点数量和边数量计算评分
        node_score = min(len(nodes) / 10.0, 1.0)  # 最多10个节点
        edge_score = min(len(edges) / 20.0, 1.0)  # 最多20条边

        # 计算平均权重
        avg_weight = 0.0
        if edges:
            total_weight = sum(edge.get("weight", 0) for edge in edges)
            avg_weight = total_weight / len(edges)

        weight_score = min(avg_weight, 1.0)

        # 综合评分
        graph_score = (node_score * 0.4 + edge_score * 0.3 + weight_score * 0.3)

        return graph_score

    async def _enrich_with_event_time(
        self,
        results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        从数据库中获取event_time信息并添加到结果中
        同时将id统一为memory_id（数据库中的Memory.id）

        Args:
            results: 向量检索结果

        Returns:
            增强后的结果列表
        """
        try:
            # 获取所有vector_id
            vector_ids = [result.get("id") for result in results]
            
            if not vector_ids:
                return results
            
            # 从数据库中查询event_time和memory_id
            from models.database import SessionLocal, Memory
            db = SessionLocal()
            
            try:
                # 查询所有相关的记忆
                memories = db.query(Memory).filter(Memory.vector_id.in_(vector_ids)).all()
                
                # 创建vector_id到event_time和memory_id的映射
                event_time_map = {}
                memory_id_map = {}
                for memory in memories:
                    event_time = getattr(memory, 'event_time', None)
                    if event_time is not None:
                        # 将datetime转换为ISO格式字符串
                        event_time_map[memory.vector_id] = event_time.isoformat()
                    else:
                        # 如果没有event_time，使用created_at作为默认值
                        created_at = getattr(memory, 'created_at', None)
                        if created_at is not None:
                            event_time_map[memory.vector_id] = created_at.isoformat()
                    
                    # 创建vector_id到memory_id的映射
                    memory_id_map[memory.vector_id] = memory.id
                
                # 将event_time和memory_id添加到结果中
                for result in results:
                    vector_id = result.get("id")
                    if vector_id in event_time_map:
                        result["event_time"] = event_time_map[vector_id]
                    else:
                        result["event_time"] = None
                    
                    # 将id替换为memory_id
                    if vector_id in memory_id_map:
                        result["memory_id"] = memory_id_map[vector_id]
                        # 保留原来的vector_id作为备用
                        result["vector_id"] = vector_id
                        # 移除旧的id字段
                        del result["id"]
                
                logger.debug(f"Enriched {len(event_time_map)} results with event_time and memory_id")
                
            finally:
                db.close()
            
            return results
            
        except Exception as e:
            logger.warning(f"Failed to enrich results with event_time: {e}")
            # 即使失败也返回原始结果
            return results


# 创建全局检索策略实例
retrieval_strategy = RetrievalStrategy()
