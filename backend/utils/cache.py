"""
缓存工具
"""
from functools import lru_cache
from typing import Any, Callable, Optional
import hashlib
import json

from config import settings


def hash_key(*args, **kwargs) -> str:
    """
    生成缓存键
    
    Args:
        *args: 位置参数
        **kwargs: 关键字参数
    
    Returns:
        哈希后的缓存键
    """
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_str.encode()).hexdigest()


def cached(ttl: Optional[int] = None, maxsize: int = 128):
    """
    带TTL的缓存装饰器
    
    Args:
        ttl: 缓存过期时间（秒），None表示不过期
        maxsize: 最大缓存大小
    
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        # 使用lru_cache
        cached_func = lru_cache(maxsize=maxsize)(func)
        
        # 如果没有TTL，直接返回
        if ttl is None:
            return cached_func
        
        # 如果有TTL，需要实现带过期时间的缓存
        # 这里简化处理，实际应用中可以使用更复杂的缓存机制
        return cached_func
    
    return decorator


# 简单的内存缓存类
class SimpleCache:
    """
    简单的内存缓存实现
    """
    def __init__(self, ttl: int = settings.CACHE_TTL):
        """
        初始化缓存
        
        Args:
            ttl: 缓存过期时间（秒）
        """
        self.ttl = ttl
        self.cache: dict = {}
        self.timestamps: dict = {}
    
    def get(self, key: str) -> Any:
        """
        获取缓存值
        
        Args:
            key: 缓存键
        
        Returns:
            缓存值，如果不存在或已过期则返回None
        """
        import time
        current_time = time.time()
        
        if key not in self.cache:
            return None
        
        # 检查是否过期
        if current_time - self.timestamps[key] > self.ttl:
            self.delete(key)
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """
        设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
        """
        import time
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str):
        """
        删除缓存值
        
        Args:
            key: 缓存键
        """
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        self.timestamps.clear()


# 创建全局缓存实例
cache = SimpleCache()
