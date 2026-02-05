"""
LLM客户端 - OpenAI风格API
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
import httpx
import json

from config import settings
from utils.logger import logger


class LLMClient:
    """
    LLM客户端类
    用于调用OpenAI风格的LLM API
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        初始化LLM客户端
        
        Args:
            base_url: API基础URL
            api_key: API密钥
            model: 模型名称
            timeout: 超时时间（秒）
        """
        self.base_url = base_url or settings.LLM_BASE_URL
        self.api_key = api_key or settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout or settings.LLM_TIMEOUT
        
        # 创建HTTP客户端
        self.client = httpx.Client(timeout=self.timeout)
        
        logger.info(f"LLMClient initialized: model={self.model}, base_url={self.base_url}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: Optional[bool] = False,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        response_format: Optional[Dict[str, str]] = None,
        model: Optional[str] = None,
        **kwargs  # 支持传递其他参数（如top_k, thinking等）
    ) -> Dict[str, Any]:
        """
        聊天补全

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            tools: 工具列表
            tool_choice: 工具选择策略
            response_format: 响应格式（如 {"type": "json_object"}）
            model: 模型名称（可选，覆盖默认模型）
            **kwargs: 其他参数（如top_k, thinking等）

        Returns:
            API响应
        """
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": stream
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        # 添加其他参数（如top_k, thinking等）
        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value
        if response_format is not None:
            payload["response_format"] = response_format
        # 添加其他参数（如top_k, thinking等）
        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value

        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()

            data = response.json()
            logger.debug(f"Successfully completed chat request")

            return data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during chat completion: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during chat completion: {e}")
            raise
    
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, Any]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[Any] = None,
        model: Optional[str] = None,
        **kwargs  # 支持传递其他参数（如top_k, thinking等）
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        聊天补全（流式）

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            tools: 工具列表
            tool_choice: 工具选择策略
            model: 模型名称（可选，覆盖默认模型）
            **kwargs: 其他参数（如top_k, thinking等）

        Yields:
            流式响应的chunk数据
        """
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": True
        }

        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools is not None:
            payload["tools"] = tools
        if tool_choice is not None:
            payload["tool_choice"] = tool_choice
        # 添加其他参数（如top_k, thinking等）
        for key, value in kwargs.items():
            if value is not None:
                payload[key] = value

        try:
            with self.client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._get_headers()
            ) as response:
                response.raise_for_status()

                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                yield data
                        except json.JSONDecodeError:
                            continue

            logger.debug(f"Successfully completed streaming chat request")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error during streaming chat completion: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during streaming chat completion: {e}")
            raise
    
    async def completion(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: Optional[bool] = False
    ) -> Dict[str, Any]:
        """
        文本补全
        
        Args:
            prompt: 提示文本
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
        
        Returns:
            API响应
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream
        }
        
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        
        try:
            response = self.client.post(
                f"{self.base_url}/completions",
                json=payload,
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Successfully completed completion request")
            
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during completion: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during completion: {e}")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        列出可用模型
        
        Returns:
            模型列表
        """
        try:
            response = self.client.get(
                f"{self.base_url}/models",
                headers=self._get_headers()
            )
            response.raise_for_status()
            
            data = response.json()
            models = data.get("data", [])
            
            logger.debug(f"Successfully retrieved {len(models)} models")
            
            return models
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error during listing models: {e}")
            raise
        except Exception as e:
            logger.error(f"Error during listing models: {e}")
            raise
    
    def _get_headers(self) -> dict:
        """
        获取请求头
        
        Returns:
            请求头字典
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def close(self):
        """关闭HTTP客户端"""
        self.client.close()
        logger.info("LLMClient closed")


# 创建全局LLM客户端实例
llm_client = LLMClient()


# 创建全局记忆提取LLM客户端实例（独立于主LLM配置）
class MemoryExtractionLLMClient(LLMClient):
    """
    记忆提取专用LLM客户端
    使用独立的配置，与主LLM完全分离
    """
    
    def __init__(self):
        """初始化记忆提取LLM客户端"""
        super().__init__(
            base_url=settings.MEMORY_EXTRACTION_BASE_URL,
            api_key=settings.MEMORY_EXTRACTION_API_KEY,
            model=settings.MEMORY_EXTRACTION_MODEL,
            timeout=settings.MEMORY_EXTRACTION_TIMEOUT
        )
        logger.info(f"MemoryExtractionLLMClient initialized: model={self.model}")


memory_extraction_llm_client = MemoryExtractionLLMClient()
