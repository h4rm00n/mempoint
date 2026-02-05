"""
图谱存储 - KùzuDB操作
"""
from typing import List, Dict, Any, Optional
import kuzu
import threading

from config import settings
from utils.logger import logger
from utils.helpers import get_current_timestamp_ms


def _escape_string(value: str) -> str:
    """
    转义字符串以防止SQL注入

    Args:
        value: 需要转义的字符串

    Returns:
        转义后的字符串
    """
    if not value:
        return ""
    # 转义单引号和反斜杠
    return value.replace("'", "''").replace("\\", "\\\\")


def _validate_entity_name(name: str, max_length: int = 100) -> bool:
    """
    验证实体名称

    Args:
        name: 实体名称
        max_length: 最大长度

    Returns:
        是否有效
    """
    if not name or not isinstance(name, str):
        return False
    if len(name) > max_length:
        return False
    # 检查非法字符（已转义，但仍需验证基本格式）
    # 这里不做严格限制，因为已经转义了特殊字符
    return True


def _validate_entity_type(type: str, max_length: int = 50) -> bool:
    """
    验证实体类型

    Args:
        type: 实体类型
        max_length: 最大长度

    Returns:
        是否有效
    """
    if not type or not isinstance(type, str):
        return False
    if len(type) > max_length:
        return False
    return True


def _validate_description(description: Optional[str], max_length: int = 1000) -> str:
    """
    验证并截断描述

    Args:
        description: 描述文本
        max_length: 最大长度

    Returns:
        验证后的描述
    """
    if not description:
        return ""
    if not isinstance(description, str):
        return ""
    if len(description) > max_length:
        logger.warning(f"Description too long, truncating: {len(description)}")
        return description[:max_length]
    return description


class GraphStore:
    """
    图谱存储类
    使用KùzuDB进行图数据存储和查询
    """
    
    def __init__(self):
        """初始化图谱存储"""
        self.db_path = settings.KUZU_DB_PATH
        self.db = None
        self.conn = None
        
        # 连接到KùzuDB
        self._connect()
        
        # 初始化schema
        self._init_schema()
        
        logger.info(f"GraphStore initialized: path={self.db_path}")
    
    def _connect(self):
        """连接到KùzuDB"""
        try:
            self.db = kuzu.Database(self.db_path)
            self.conn = kuzu.Connection(self.db)
            logger.info("Connected to KùzuDB")
        except Exception as e:
            logger.error(f"Failed to connect to KùzuDB: {e}")
            raise
    
    def _init_schema(self):
        """初始化schema"""
        try:
            # 创建节点表
            self._create_node_tables()
            
            # 创建关系表
            self._create_relation_tables()
            
            logger.info("KùzuDB schema initialized")
        except Exception as e:
            logger.error(f"Failed to initialize KùzuDB schema: {e}")
            raise
    
    def _create_node_tables(self):
        """创建节点表"""
        # User节点表
        self.conn.execute(f"""
            CREATE NODE TABLE IF NOT EXISTS {settings.KUZU_NODE_TABLE_USER}(
                name STRING,
                id STRING,
                PRIMARY KEY (id)
            )
        """)
        
        # Entity节点表
        self.conn.execute(f"""
            CREATE NODE TABLE IF NOT EXISTS {settings.KUZU_NODE_TABLE_ENTITY}(
                name STRING,
                type STRING,
                description STRING,
                created_at INT64,
                last_accessed_at INT64,
                PRIMARY KEY (name)
            )
        """)
        
        # Concept节点表
        self.conn.execute(f"""
            CREATE NODE TABLE IF NOT EXISTS {settings.KUZU_NODE_TABLE_CONCEPT}(
                name STRING,
                description STRING,
                created_at INT64,
                PRIMARY KEY (name)
            )
        """)
        
        logger.info("Created node tables")
    
    def _create_relation_tables(self):
        """创建关系表"""
        # MENTIONS关系表
        self.conn.execute(f"""
            CREATE REL TABLE IF NOT EXISTS {settings.KUZU_REL_TABLE_MENTIONS}(
                FROM {settings.KUZU_NODE_TABLE_USER} TO {settings.KUZU_NODE_TABLE_ENTITY},
                timestamp INT64
            )
        """)
        
        # RELATED_TO关系表
        self.conn.execute(f"""
            CREATE REL TABLE IF NOT EXISTS {settings.KUZU_REL_TABLE_RELATED_TO}(
                FROM {settings.KUZU_NODE_TABLE_ENTITY} TO {settings.KUZU_NODE_TABLE_ENTITY},
                weight DOUBLE,
                created_at INT64
            )
        """)
        
        # BELONGS_TO关系表
        self.conn.execute(f"""
            CREATE REL TABLE IF NOT EXISTS {settings.KUZU_REL_TABLE_BELONGS_TO}(
                FROM {settings.KUZU_NODE_TABLE_ENTITY} TO {settings.KUZU_NODE_TABLE_CONCEPT},
                created_at INT64
            )
        """)
        
        logger.info("Created relation tables")
    
    async def create_entity(
        self,
        name: str,
        type: str,
        description: Optional[str] = None
    ) -> bool:
        """
        创建实体节点

        Args:
            name: 实体名称
            type: 实体类型
            description: 实体描述

        Returns:
            是否成功
        """
        # 输入验证
        if not _validate_entity_name(name):
            logger.error(f"Invalid entity name: {name}")
            return False

        if not _validate_entity_type(type):
            logger.error(f"Invalid entity type: {type}")
            return False

        # 验证并截断描述
        description = _validate_description(description)

        current_time = get_current_timestamp_ms()

        try:
            # 使用转义后的字符串
            escaped_name = _escape_string(name)
            escaped_type = _escape_string(type)
            escaped_description = _escape_string(description)

            self.conn.execute(f"""
                MERGE (e:{settings.KUZU_NODE_TABLE_ENTITY} {{name: '{escaped_name}'}})
                ON CREATE SET
                    e.type = '{escaped_type}',
                    e.description = '{escaped_description}',
                    e.created_at = {current_time},
                    e.last_accessed_at = {current_time}
            """)

            logger.debug(f"Created entity: name={name}, type={type}")
            return True

        except Exception as e:
            logger.error(f"Failed to create entity: {e}")
            return False
    
    async def create_user(
        self,
        id: str,
        name: str
    ) -> bool:
        """
        创建用户节点

        Args:
            id: 用户ID
            name: 用户名

        Returns:
            是否成功
        """
        # 输入验证
        if not id or not isinstance(id, str):
            logger.error(f"Invalid user id: {id}")
            return False

        if not name or not isinstance(name, str):
            logger.error(f"Invalid user name: {name}")
            return False

        if len(name) > 100:
            logger.warning(f"User name too long, truncating: {len(name)}")
            name = name[:100]

        try:
            # 使用转义后的字符串
            escaped_id = _escape_string(id)
            escaped_name = _escape_string(name)

            self.conn.execute(f"""
                MERGE (u:{settings.KUZU_NODE_TABLE_USER} {{id: '{escaped_id}'}})
                ON CREATE SET u.name = '{escaped_name}'
            """)

            logger.debug(f"Created user: id={id}, name={name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return False
    
    async def create_concept(
        self,
        name: str,
        description: Optional[str] = None
    ) -> bool:
        """
        创建概念节点

        Args:
            name: 概念名称
            description: 概念描述

        Returns:
            是否成功
        """
        # 输入验证
        if not name or not isinstance(name, str):
            logger.error(f"Invalid concept name: {name}")
            return False

        if len(name) > 100:
            logger.error(f"Concept name too long: {len(name)}")
            return False

        # 验证并截断描述
        description = _validate_description(description)

        current_time = get_current_timestamp_ms()

        try:
            # 使用转义后的字符串
            escaped_name = _escape_string(name)
            escaped_description = _escape_string(description)

            self.conn.execute(f"""
                MERGE (c:{settings.KUZU_NODE_TABLE_CONCEPT} {{name: '{escaped_name}'}})
                ON CREATE SET
                    c.description = '{escaped_description}',
                    c.created_at = {current_time}
            """)

            logger.debug(f"Created concept: name={name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create concept: {e}")
            return False
    
    async def create_relation(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str,
        weight: Optional[float] = None
    ) -> bool:
        """
        创建实体间的关系

        Args:
            from_entity: 起始实体名称
            to_entity: 目标实体名称
            relation_type: 关系类型
            weight: 关系权重

        Returns:
            是否成功
        """
        # 输入验证
        if not _validate_entity_name(from_entity):
            logger.error(f"Invalid from_entity: {from_entity}")
            return False

        if not _validate_entity_name(to_entity):
            logger.error(f"Invalid to_entity: {to_entity}")
            return False

        if not relation_type or not isinstance(relation_type, str):
            logger.error(f"Invalid relation_type: {relation_type}")
            return False

        current_time = get_current_timestamp_ms()

        try:
            # 使用转义后的字符串
            escaped_from_entity = _escape_string(from_entity)
            escaped_to_entity = _escape_string(to_entity)

            # 降级处理：将未知的关系类型映射为RELATED_TO
            if relation_type not in [settings.KUZU_REL_TABLE_RELATED_TO, settings.KUZU_REL_TABLE_BELONGS_TO]:
                logger.warning(f"Unknown relation type '{relation_type}', mapping to RELATED_TO")
                relation_type = settings.KUZU_REL_TABLE_RELATED_TO

            if relation_type == settings.KUZU_REL_TABLE_RELATED_TO:
                self.conn.execute(f"""
                    MERGE (e1:{settings.KUZU_NODE_TABLE_ENTITY} {{name: '{escaped_from_entity}'}})
                    MERGE (e2:{settings.KUZU_NODE_TABLE_ENTITY} {{name: '{escaped_to_entity}'}})
                    MERGE (e1)-[r:{settings.KUZU_REL_TABLE_RELATED_TO}]->(e2)
                    ON CREATE SET
                        r.weight = {weight or 0.0},
                        r.created_at = {current_time}
                """)
            elif relation_type == settings.KUZU_REL_TABLE_BELONGS_TO:
                self.conn.execute(f"""
                    MERGE (e:{settings.KUZU_NODE_TABLE_ENTITY} {{name: '{escaped_from_entity}'}})
                    MERGE (c:{settings.KUZU_NODE_TABLE_CONCEPT} {{name: '{escaped_to_entity}'}})
                    MERGE (e)-[r:{settings.KUZU_REL_TABLE_BELONGS_TO}]->(c)
                    ON CREATE SET r.created_at = {current_time}
                """)

            logger.debug(f"Created relation: {from_entity} -> {to_entity} ({relation_type})")
            return True

        except Exception as e:
            logger.error(f"Failed to create relation: {e}")
            return False
    
    async def create_mentions(
        self,
        user_id: str,
        entity_name: str
    ) -> bool:
        """
        创建用户提及实体的关系

        Args:
            user_id: 用户ID
            entity_name: 实体名称

        Returns:
            是否成功
        """
        # 输入验证
        if not user_id or not isinstance(user_id, str):
            logger.error(f"Invalid user_id: {user_id}")
            return False

        if not _validate_entity_name(entity_name):
            logger.error(f"Invalid entity_name: {entity_name}")
            return False

        current_time = get_current_timestamp_ms()

        try:
            # 使用转义后的字符串
            escaped_user_id = _escape_string(user_id)
            escaped_entity_name = _escape_string(entity_name)

            self.conn.execute(f"""
                MERGE (u:{settings.KUZU_NODE_TABLE_USER} {{id: '{escaped_user_id}'}})
                MERGE (e:{settings.KUZU_NODE_TABLE_ENTITY} {{name: '{escaped_entity_name}'}})
                MERGE (u)-[r:{settings.KUZU_REL_TABLE_MENTIONS}]->(e)
                ON CREATE SET r.timestamp = {current_time}
            """)

            logger.debug(f"Created mention: user={user_id} -> entity={entity_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create mention: {e}")
            return False
    
    async def query_entity(
        self,
        entity_name: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        查询实体及其关联节点

        Args:
            entity_name: 实体名称
            max_depth: 最大查询深度

        Returns:
            查询结果（包含节点和边）
        """
        # 输入验证
        if not _validate_entity_name(entity_name):
            logger.error(f"Invalid entity_name: {entity_name}")
            return {"nodes": [], "edges": []}

        if not isinstance(max_depth, int) or max_depth < 1 or max_depth > 5:
            logger.error(f"Invalid max_depth: {max_depth}")
            return {"nodes": [], "edges": []}

        try:
            # 使用转义后的字符串
            escaped_entity_name = _escape_string(entity_name)

            # 查询实体及其关联
            result = self.conn.execute(f"""
                MATCH (e:{settings.KUZU_NODE_TABLE_ENTITY} {{name: '{escaped_entity_name}'}})
                CALL (e) *1..{max_depth} {{bfs: true}} (related)
                RETURN e, related
            """)

            nodes = []
            edges = []
            seen_nodes = set()
            seen_edges = set()

            for row in result:
                entity = row[0]
                related = row[1]

                # 添加实体节点
                if entity not in seen_nodes:
                    nodes.append({
                        "name": entity.get("name"),
                        "type": entity.get("type"),
                        "description": entity.get("description"),
                        "created_at": entity.get("created_at"),
                        "last_accessed_at": entity.get("last_accessed_at")
                    })
                    seen_nodes.add(entity)

                # 添加关联节点
                if related not in seen_nodes:
                    nodes.append({
                        "name": related.get("name"),
                        "type": related.get("type"),
                        "description": related.get("description"),
                        "created_at": related.get("created_at"),
                        "last_accessed_at": related.get("last_accessed_at")
                    })
                    seen_nodes.add(related)

                # 添加边
                edge_key = (entity.get("name"), related.get("name"))
                if edge_key not in seen_edges:
                    edges.append({
                        "from_entity": entity.get("name"),
                        "to_entity": related.get("name"),
                        "relation_type": "RELATED_TO",
                        "weight": related.get("weight"),
                        "created_at": related.get("created_at")
                    })
                    seen_edges.add(edge_key)

            logger.debug(f"Queried entity: {entity_name}, found {len(nodes)} nodes and {len(edges)} edges")

            return {
                "nodes": nodes,
                "edges": edges
            }

        except Exception as e:
            logger.error(f"Failed to query entity: {e}")
            return {"nodes": [], "edges": []}
    
    async def update_entity_access(self, entity_name: str) -> bool:
        """
        更新实体的最后访问时间

        Args:
            entity_name: 实体名称

        Returns:
            是否成功
        """
        # 输入验证
        if not _validate_entity_name(entity_name):
            logger.error(f"Invalid entity_name: {entity_name}")
            return False

        current_time = get_current_timestamp_ms()

        try:
            # 使用转义后的字符串
            escaped_entity_name = _escape_string(entity_name)

            self.conn.execute(f"""
                MATCH (e:{settings.KUZU_NODE_TABLE_ENTITY} {{name: '{escaped_entity_name}'}})
                SET e.last_accessed_at = {current_time}
            """)

            logger.debug(f"Updated entity access: {entity_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update entity access: {e}")
            return False
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
        if self.db:
            self.db.close()
        logger.info("Disconnected from KùzuDB")


# 全局图谱存储实例 - 使用懒加载
_graph_store = None
_graph_store_lock = threading.Lock()


def get_graph_store() -> GraphStore:
    """获取图谱存储实例（线程安全的懒加载）"""
    global _graph_store
    if _graph_store is None:
        with _graph_store_lock:
            if _graph_store is None:  # 双重检查锁定
                _graph_store = GraphStore()
    return _graph_store


# 向后兼容的属性访问器
class GraphStoreProxy:
    """图谱存储代理类，支持懒加载"""
    
    def __getattr__(self, name):
        return getattr(get_graph_store(), name)


graph_store = GraphStoreProxy()
