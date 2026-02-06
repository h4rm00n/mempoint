# 图谱增强讨论记录

## 概述

本文档记录了关于记忆系统中图谱增强功能的讨论，包括当前实现、改进方案和技术分析。

## 一、当前实现分析

### 1.1 图谱增强的流程

```
用户输入 → 向量检索 → 补充event_time → 图谱增强 → 计算评分 → 排序 → 注入
```

### 1.2 图谱增强的实际作用

**关键发现：图谱数据并没有注入到最终的记忆内容中，只通过评分影响排序。**

#### 代码证据

1. **图谱数据被添加到结果** (`_enhance_with_graph`):
```python
result["graph_data"] = graph_data  # 添加图谱数据
result["graph_score"] = graph_score  # 添加图谱评分
```

2. **图谱评分影响排序** (`_rescore_with_memory_score`):
```python
final_score = calculate_similarity_score(
    similarity=similarity,
    access_count=access_count,
    max_access_count=100,
    last_accessed_at=last_accessed_at,
    created_at=created_at,
    lambda_decay=self.lambda_decay,
    graph_score=graph_score  # 图谱评分影响综合评分
)
```

3. **记忆注入时只使用content和event_time** (`_format_memory_context`):
```python
for i, memory in enumerate(long_term_memories, 1):
    content = memory.get('content', '')
    event_time = memory.get('event_time')
    
    # 只使用content和event_time
    xml_parts.append(f"    <memory index=\"{i}\">")
    xml_parts.append(f"      <content>{content_escaped}</content>")
    xml_parts.append(f"      <event_time>{time_str}</event_time>")
    xml_parts.append(f"    </memory>")
```

### 1.3 图谱评分计算

```python
def _calculate_graph_score(self, graph_data: Dict[str, Any]) -> float:
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
```

**图谱评分组成：**

| 评分项 | 权重 | 计算方式 | 说明 |
|--------|------|----------|------|
| 节点评分 | 40% | `min(len(nodes) / 10.0, 1.0)` | 节点越多，实体关联越丰富 |
| 边评分 | 30% | `min(len(edges) / 20.0, 1.0)` | 边越多，关系网络越复杂 |
| 权重评分 | 30% | `min(avg_weight, 1.0)` | 关系权重平均值 |

### 1.4 当前设计的局限性

1. **图谱信息丢失**：丰富的实体关系信息没有被利用
2. **LLM无法感知图谱**：LLM只能看到记忆的文本内容，看不到实体关系
3. **上下文不完整**：图谱中的关联实体和关系对LLM不可见

## 二、改进方案：图谱扩展记忆

### 2.1 方案概述

**核心思想：** 通过图谱推理，将一跳邻居节点也作为记忆注入，而不仅仅是影响排序。

```
用户输入 → 向量检索最相似记忆 → 获取记忆标题 → 标题作为图谱节点 
→ 图谱推理 → 选择一跳邻居 → 将邻居作为记忆注入 → 发送给LLM
```

### 2.2 方案优势

#### 1. 图谱推理真正发挥作用
- **当前方案**：图谱只影响排序，内容不传递
- **改进方案**：图谱扩展记忆，邻居节点直接注入

#### 2. 语义关联扩展
通过图谱关系可以找到**语义不相关但逻辑相关**的记忆：

**示例：**
```
用户问："我想吃点什么？"

向量检索：
- "用户喜欢吃辣的食物" (similarity=0.9)

图谱推理（节点="辣的食物"）：
- 一跳邻居：
  - "火锅" --属于--> "川菜"
  - "麻婆豆腐" --属于--> "川菜"
  - "用户上周吃了麻辣烫"

注入的记忆：
1. "用户喜欢吃辣的食物" (原始记忆)
2. "用户上周吃了麻辣烫" (图谱邻居)
3. "火锅" (实体节点，可转换为"用户喜欢火锅")
```

#### 3. 知识网络利用
利用图谱的关系网络，可以：
- 发现隐式关联
- 激活相关但被遗忘的记忆
- 提供更完整的上下文

### 2.3 技术实现

#### 1. 数据结构修改

需要给Memory表添加title字段：

```python
class Memory(Base):
    id = Column(String, primary_key=True)
    title = Column(String, nullable=True)  # 新增：记忆标题
    content = Column(String)
    vector_id = Column(String)
    entity_id = Column(String)
    # ... 其他字段
```

#### 2. 记忆提取时生成标题

修改记忆提取提示词，让LLM同时生成标题：

```python
MEMORY_EXTRACTION_PROMPT = """
返回JSON格式：
{
  "memories": [
    {
      "title": "记忆标题（简短摘要）",  # 新增
      "content": "记忆详细内容",
      "event_time": "..."
    }
  ],
  "entities": [...],
  "relations": [...]
}
```

**示例输出：**
```json
{
  "memories": [
    {
      "title": "饮食偏好",
      "content": "用户喜欢吃辣的食物，特别是川菜和火锅",
      "event_time": "2024-01-15T14:30:00"
    }
  ]
}
```

#### 3. 图谱推理实现

```python
async def _retrieve_with_graph_expansion(
    self,
    query_embedding: List[float],
    query_text: str,
    persona_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """带图谱扩展的检索"""
    
    # 1. 向量检索top K
    results = await vector_store.search_knowledge(
        embedding=query_embedding,
        top_k=5,  # 检索更多候选
        persona_id=persona_id
    )
    
    # 2. 补充event_time和title
    results = await self._enrich_with_event_time_and_title(results)
    
    # 3. 图谱扩展
    expanded_memories = []
    for result in results:
        title = result.get('title')
        if not title:
            continue
        
        # 查询一跳邻居
        graph_data = await graph_store.query_entity(
            entity_name=title,
            max_depth=1
        )
        
        # 选择邻居记忆
        neighbor_memories = self._select_neighbor_memories(
            graph_data,
            result
        )
        
        expanded_memories.extend(neighbor_memories)
    
    # 4. 去重和评分
    unique_memories = self._deduplicate_memories(
        results + expanded_memories
    )
    
    # 5. 重新评分和排序
    scored_memories = self._rescore_with_memory_score(
        unique_memories
    )
    
    return scored_memories[:3]  # 返回top 3
```

#### 4. 邻居选择策略

```python
def _select_neighbor_memories(
    self,
    graph_data: Dict[str, Any],
    original_memory: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """选择邻居记忆"""
    
    neighbor_memories = []
    
    # 策略1：直接关联的实体节点
    for edge in graph_data.get('edges', []):
        to_entity = edge.get('to_entity')
        relation_type = edge.get('relation_type')
        
        # 如果是RELATED_TO关系，可能是相关记忆
        if relation_type == 'RELATED_TO':
            # 查询是否有以该实体为entity_id的记忆
            related_memories = await self._query_memories_by_entity(
                entity_id=to_entity
            )
            neighbor_memories.extend(related_memories)
    
    # 策略2：根据关系权重排序
    neighbor_memories.sort(
        key=lambda x: x.get('graph_weight', 0),
        reverse=True
    )
    
    # 限制数量
    return neighbor_memories[:2]  # 每个原始记忆扩展2个邻居
```

### 2.4 方案优化建议

#### 1. 混合策略

结合当前方案和改进方案：

```python
async def retrieve(
    self,
    query_embedding: List[float],
    query_text: str,
    persona_id: Optional[str] = None,
    use_graph_expansion: bool = True  # 可配置
) -> List[Dict[str, Any]]:
    """混合检索策略"""
    
    # 基础向量检索
    base_results = await vector_store.search_knowledge(...)
    
    if use_graph_expansion:
        # 图谱扩展
        expanded = await self._graph_expansion(base_results)
        results = base_results + expanded
    else:
        # 当前方案：只评分
        results = await self._enhance_with_graph(base_results)
    
    # 去重、评分、排序
    return self._finalize_results(results)
```

#### 2. 智能邻居选择

```python
def _select_neighbor_memories(
    self,
    graph_data: Dict[str, Any],
    original_memory: Dict[str, Any],
    query_text: str
) -> List[Dict[str, Any]]:
    """智能选择邻居记忆"""
    
    candidates = []
    
    for edge in graph_data.get('edges', []):
        to_entity = edge.get('to_entity')
        weight = edge.get('weight', 0)
        
        # 查询相关记忆
        related_memories = await self._query_memories_by_entity(
            entity_id=to_entity
        )
        
        for mem in related_memories:
            # 计算与查询的相关性
            relevance = self._calculate_relevance(
                mem.get('content', ''),
                query_text
            )
            
            candidates.append({
                'memory': mem,
                'graph_weight': weight,
                'relevance': relevance
            })
    
    # 综合评分
    for candidate in candidates:
        candidate['score'] = (
            candidate['graph_weight'] * 0.6 +
            candidate['relevance'] * 0.4
        )
    
    # 选择top N
    candidates.sort(key=lambda x: x['score'], reverse=True)
    return [c['memory'] for c in candidates[:2]]
```

#### 3. 分层注入

```python
def _format_memory_context(
    self,
    memories: List[Dict[str, Any]]
) -> str:
    """分层格式化记忆上下文"""
    
    xml_parts = ["<memory_context>"]
    
    # 第一层：直接检索的记忆
    xml_parts.append("  <direct_memories>")
    for i, mem in enumerate(memories[:2], 1):
        xml_parts.append(f"    <memory index=\"{i}\">")
        xml_parts.append(f"      <content>{mem['content']}</content>")
        xml_parts.append(f"    </memory>")
    xml_parts.append("  </direct_memories>")
    
    # 第二层：图谱扩展的记忆
    xml_parts.append("  <related_memories>")
    for i, mem in enumerate(memories[2:], 3):
        xml_parts.append(f"    <memory index=\"{i}\">")
        xml_parts.append(f"      <content>{mem['content']}</content>")
        xml_parts.append(f"      <source>graph_expansion</source>")
        xml_parts.append(f"    </memory>")
    xml_parts.append("  </related_memories>")
    
    xml_parts.append("</memory_context>")
    
    return "\n".join(xml_parts)
```

### 2.5 潜在问题与解决方案

#### 问题1：噪音引入
**问题**：图谱邻居可能不相关
**解决**：
- 设置相关性阈值
- 使用LLM判断相关性
- 限制扩展深度和数量

#### 问题2：循环引用
**问题**：图谱中可能存在循环
**解决**：
- 记忆已访问节点
- 限制跳数
- 使用去重机制

#### 问题3：性能开销
**问题**：多次图谱查询影响性能
**解决**：
- 批量查询优化
- 缓存图谱数据
- 异步并发查询

#### 问题4：上下文长度
**问题**：扩展后记忆过多
**解决**：
- 限制总记忆数量
- 使用记忆摘要
- 动态调整数量

## 三、云端场景下的价值分析

### 3.1 两种场景的本质区别

```
手机端场景：
本地向量数据库弱 → 检索质量差 → 需要图谱扩展补充 → 目的：提升检索覆盖率

云端场景：
云端向量模型强 → 检索质量好 → 是否需要图谱扩展? → 目的：发现隐式关联
```

### 3.2 向量相似度的局限性

向量相似度只能捕获**语义相似**，无法捕获**逻辑相关**。

#### 示例1：语义相似 vs 逻辑相关

```
用户问："我想吃点什么？"

向量检索（语义相似）：
1. "用户喜欢吃辣的食物" (similarity=0.95)
2. "用户昨天吃了火锅" (similarity=0.85)
3. "用户的工作是程序员" (similarity=0.3)

图谱扩展（逻辑相关）：
- 节点："辣的食物"
- 一跳邻居：
  - "火锅" --属于--> "川菜"
  - "麻婆豆腐" --属于--> "川菜"
  - "用户上周吃了麻辣烫"
  - "用户喜欢日本料理"
  - "用户对海鲜过敏"

扩展后的记忆：
1. "用户喜欢吃辣的食物" (语义相关)
2. "用户上周吃了麻辣烫" (语义相关)
3. "用户喜欢日本料理" (逻辑相关，通过"辣的食物"关联)
4. "用户对海鲜过敏" (逻辑相关，通过"食物"关联)
```

**关键区别：**
- "用户喜欢日本料理" 与 "我想吃点什么？" 语义相似度可能只有 0.4
- 但通过图谱关系（辣的食物 → 日本料理），它是逻辑相关的
- 向量检索无法找到它，但图谱扩展可以

#### 示例2：隐式关联发现

```
用户问："最近有什么电影推荐？"

向量检索：
1. "用户喜欢科幻电影" (similarity=0.9)
2. "用户上周看了《沙丘》" (similarity=0.8)

图谱扩展：
- 节点："科幻电影"
- 一跳邻居：
  - "《星际穿越》" --属于--> "科幻电影"
  - "《流浪地球》" --属于--> "科幻电影"
  - "用户喜欢诺兰导演"
  - "用户喜欢太空题材"

扩展后的记忆：
1. "用户喜欢科幻电影"
2. "用户喜欢诺兰导演" (逻辑相关)
3. "用户喜欢太空题材" (逻辑相关)
```

### 3.3 实际价值对比

| 维度 | 手机端场景 | 云端场景 |
|------|-----------|---------|
| 向量检索质量 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 图谱扩展价值 | ⭐⭐⭐⭐⭐ (补充检索) | ⭐⭐⭐ (发现关联) |
| 主要目的 | 提升覆盖率 | 发现隐式关联 |
| 适用场景 | 所有查询 | 逻辑关联查询 |

### 3.4 针对云端场景的优化建议

既然使用云端向量模型，建议采用**混合策略**：

#### 1. 智能判断是否需要图谱扩展

```python
async def retrieve(
    self,
    query_embedding: List[float],
    query_text: str,
    persona_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """智能检索策略"""
    
    # 1. 向量检索
    base_results = await vector_store.search_knowledge(
        embedding=query_embedding,
        top_k=5,
        persona_id=persona_id
    )
    
    # 2. 判断是否需要图谱扩展
    need_expansion = self._should_use_graph_expansion(
        query_text,
        base_results
    )
    
    if need_expansion:
        # 3. 图谱扩展
        expanded = await self._graph_expansion(base_results)
        results = base_results + expanded
    else:
        # 4. 只使用向量检索
        results = base_results
    
    # 5. 去重、评分、排序
    return self._finalize_results(results)
```

#### 2. 判断逻辑

```python
def _should_use_graph_expansion(
    self,
    query_text: str,
    base_results: List[Dict[str, Any]]
) -> bool:
    """判断是否需要图谱扩展"""
    
    # 条件1：查询包含关联词
    expansion_keywords = [
        "建议", "推荐", "什么", "怎么样", 
        "还有", "其他", "相关的"
    ]
    if any(kw in query_text for kw in expansion_keywords):
        return True
    
    # 条件2：向量检索结果相似度不高
    avg_similarity = sum(
        r.get('similarity', 0) for r in base_results
    ) / len(base_results)
    if avg_similarity < 0.7:
        return True
    
    # 条件3：查询涉及多个领域
    # (可以通过LLM判断)
    
    return False
```

#### 3. 分层注入策略

```python
def _format_memory_context(
    self,
    memories: List[Dict[str, Any]]
) -> str:
    """分层格式化记忆"""
    
    xml_parts = ["<memory_context>"]
    
    # 第一层：高相似度记忆（向量检索）
    xml_parts.append("  <direct_matches>")
    for i, mem in enumerate(memories[:2], 1):
        xml_parts.append(f"    <memory index=\"{i}\">")
        xml_parts.append(f"      <content>{mem['content']}</content>")
        xml_parts.append(f"      <relevance>high</relevance>")
        xml_parts.append(f"    </memory>")
    xml_parts.append("  </direct_matches>")
    
    # 第二层：图谱扩展记忆（逻辑相关）
    if len(memories) > 2:
        xml_parts.append("  <related_context>")
        for i, mem in enumerate(memories[2:], 3):
            xml_parts.append(f"    <memory index=\"{i}\">")
            xml_parts.append(f"      <content>{mem['content']}</content>")
            xml_parts.append(f"      <relevance>related</relevance>")
            xml_parts.append(f"      <source>graph</source>")
            xml_parts.append(f"    </memory>")
        xml_parts.append("  </related_context>")
    
    xml_parts.append("</memory_context>")
    
    return "\n".join(xml_parts)
```

## 四、实施建议

### 4.1 方案评分

| 维度 | 评分 | 说明 |
|------|------|------|
| 创新性 | ⭐⭐⭐⭐⭐ | 让图谱真正发挥作用 |
| 实用性 | ⭐⭐⭐⭐ | 提升记忆的关联性 |
| 复杂度 | ⭐⭐⭐ | 需要较多修改 |
| 效果预期 | ⭐⭐⭐⭐⭐ | 可能显著提升检索质量 |

### 4.2 实施步骤

1. ✅ 采用图谱扩展方案，让图谱真正发挥作用
2. ✅ 添加记忆标题字段
3. ✅ 实现智能邻居选择
4. ⚠️ 可配置开关，允许回退到当前方案
5. ⚠️ 先小范围测试，评估效果

### 4.3 关键结论

**向量相似度** = 语义层面的相似
- "我喜欢吃辣" ≈ "我喜欢火锅" (高相似度)
- "我喜欢吃辣" ≈ "我喜欢日本料理" (低相似度)

**图谱扩展** = 逻辑层面的关联
- "辣的食物" --属于--> "川菜" --包含--> "火锅"
- "辣的食物" --关联--> "日本料理" (通过用户偏好)

**在云端场景下：**
- ✅ 向量检索质量已经很好，不需要图谱扩展来"补充"
- ✅ 但图谱扩展可以"发现"向量检索找不到的逻辑关联
- ⚠️ 价值不如手机端场景那么大，但仍然有意义

**建议：**
- 采用**混合策略**，根据查询类型智能判断
- 对于纯语义查询，只用向量检索
- 对于需要关联的查询，使用图谱扩展
- 这样既能发挥云端向量模型的优势，又能利用图谱的逻辑关联能力

## 五、相关文件

- `backend/memory/retrieval.py` - 检索策略实现
- `backend/memory/graph_store.py` - 图谱存储实现
- `backend/core/memory_engine.py` - 记忆注入引擎
- `backend/config.exp.py` - 配置文件
- `backend/utils/helpers.py` - 辅助函数（评分计算）
