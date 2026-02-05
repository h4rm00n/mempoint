"""
辅助函数
"""
import uuid
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import math


def get_current_datetime() -> datetime:
    """获取当前时间（带时区）"""
    return datetime.now(timezone.utc)


def datetime_to_ms(dt: datetime) -> int:
    """将datetime转换为毫秒时间戳"""
    if dt is None:
        return 0
    return int(dt.timestamp() * 1000)


def ms_to_datetime(ms: int) -> datetime:
    """将毫秒时间戳转换为datetime"""
    if ms is None or ms == 0:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def generate_id() -> str:
    """
    生成唯一ID
    
    Returns:
        唯一ID字符串
    """
    return str(uuid.uuid4())


def get_current_timestamp_ms() -> int:
    """
    获取当前时间戳（毫秒）
    
    Returns:
        当前时间戳（毫秒）
    """
    return int(time.time() * 1000)


def calculate_similarity_score(
    similarity: float,
    access_count: int,
    max_access_count: int,
    last_accessed_at: int,
    created_at: int,
    lambda_decay: float = 0.0001,
    graph_score: float = 0.0
) -> float:
    """
    计算记忆的综合评分

    Args:
        similarity: 相似度评分 (0-1)
        access_count: 访问次数
        max_access_count: 最大访问次数
        last_accessed_at: 最后访问时间戳（毫秒）
        created_at: 创建时间戳（毫秒）
        lambda_decay: 时间衰减系数
        graph_score: 图谱评分 (0-1)

    Returns:
        综合评分 (0-1)
    """
    current_time = get_current_timestamp_ms()

    # 确保参数不为None
    similarity = similarity or 0.0
    access_count = access_count or 0
    last_accessed_at = last_accessed_at or current_time
    created_at = created_at or current_time
    graph_score = graph_score or 0.0

    # 1. 相似度评分 (40%)
    similarity_score = max(0.0, min(similarity, 1.0))

    # 2. 访问评分 (30%)
    access_score = min(access_count / max(max_access_count, 1), 1.0)

    # 3. 时效性评分 (20%)
    time_diff = current_time - last_accessed_at
    recency_score = math.exp(-lambda_decay * time_diff)

    # 4. 图谱评分 (10%)
    graph_score = max(0.0, min(graph_score, 1.0))

    # 综合评分
    final_score = (
        similarity_score * 0.4 +
        access_score * 0.3 +
        recency_score * 0.2 +
        graph_score * 0.1
    )

    return max(0.0, min(final_score, 1.0))


def chunk_text(text: str, max_length: int = 500, overlap: int = 50) -> List[str]:
    """
    将文本分块
    
    Args:
        text: 原始文本
        max_length: 每块最大长度
        overlap: 块之间的重叠长度
    
    Returns:
        文本块列表
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + max_length
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    
    return chunks


def normalize_text(text: str) -> str:
    """
    标准化文本
    
    Args:
        text: 原始文本
    
    Returns:
        标准化后的文本
    """
    # 去除首尾空白
    text = text.strip()
    # 替换多个空格为单个空格
    text = ' '.join(text.split())
    return text


def extract_entities(text: str) -> List[str]:
    """
    从文本中提取实体（简化版）
    
    Args:
        text: 输入文本
    
    Returns:
        实体列表
    """
    # 这里是一个简化的实现
    # 实际应用中可以使用更复杂的NLP模型
    entities = []
    
    # 简单的规则：提取大写开头的词
    words = text.split()
    for word in words:
        if word and word[0].isupper() and len(word) > 1:
            entities.append(word)
    
    return list(set(entities))  # 去重


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并多个字典
    
    Args:
        *dicts: 要合并的字典
    
    Returns:
        合并后的字典
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全地解析JSON字符串
    
    Args:
        json_str: JSON字符串
        default: 解析失败时的默认值
    
    Returns:
        解析结果或默认值
    """
    import json
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def truncate_text(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    截断文本
    
    Args:
        text: 原始文本
        max_length: 最大长度
        suffix: 截断后缀
    
    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
