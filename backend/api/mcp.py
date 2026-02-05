"""
MCP (Model Context Protocol) Streamable HTTP 实现
基于 MCP Streamable HTTP 标准
"""
import json
from typing import List, Dict, Any, Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, status, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import asyncio

from config import settings
from utils.memory_tools import get_memory_tools
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


class MCPTool(BaseModel):
    """MCP 工具定义"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MCPResource(BaseModel):
    """MCP 资源定义"""
    uri: str
    name: str
    description: str
    mimeType: Optional[str] = None


class MCPServerInfo(BaseModel):
    """MCP 服务器信息"""
    name: str
    version: str
    protocolVersion: str = "2024-11-05"


class MCPListToolsResponse(BaseModel):
    """MCP 工具列表响应"""
    tools: List[MCPTool]


class MCPListResourcesResponse(BaseModel):
    """MCP 资源列表响应"""
    resources: List[MCPResource]


# JSON-RPC 2.0 请求模型
class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 请求"""
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    method: str
    params: Optional[Dict[str, Any]] = None


# JSON-RPC 2.0 响应模型
class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 响应"""
    jsonrpc: str = "2.0"
    id: Optional[Any] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


async def handle_jsonrpc_request(request: JSONRPCRequest) -> Optional[JSONRPCResponse]:
    """
    处理 JSON-RPC 请求

    Args:
        request: JSON-RPC 请求对象

    Returns:
        JSON-RPC 响应对象，如果是通知类型则返回 None
    """
    # 检查是否是通知类型（没有 id）
    is_notification = request.id is None

    try:
        if request.method == "initialize":
            # 初始化请求
            result = {
                "protocolVersion": "2024-11-05",
                "serverInfo": {
                    "name": "MemPoint Memory Server",
                    "version": "0.1.0"
                },
                "capabilities": {
                    "tools": {},
                    "resources": {}
                }
            }
            if is_notification:
                logger.info("Initialize notification received (no response)")
                return None
            return JSONRPCResponse(id=request.id, result=result)

        elif request.method == "tools/list":
            # 列出工具
            memory_tools = get_memory_tools()
            mcp_tools = []
            for tool in memory_tools:
                function = tool.get("function", {})
                mcp_tool = MCPTool(
                    name=function.get("name"),
                    description=function.get("description", ""),
                    inputSchema=function.get("parameters", {})
                )
                mcp_tools.append(mcp_tool)

            logger.info(f"Listed {len(mcp_tools)} MCP tools")
            result = {"tools": [tool.dict() for tool in mcp_tools]}
            if is_notification:
                logger.info("tools/list notification received (no response)")
                return None
            return JSONRPCResponse(id=request.id, result=result)

        elif request.method == "resources/list":
            # 列出资源
            resources = [
                {
                    "uri": "memory://list",
                    "name": "列出记忆",
                    "description": "列出所有记忆，支持按记忆体和类型过滤"
                },
                {
                    "uri": "memory://get",
                    "name": "获取记忆详情",
                    "description": "根据记忆ID获取详细信息"
                },
                {
                    "uri": "memory://search",
                    "name": "搜索记忆",
                    "description": "基于语义搜索相关记忆"
                }
            ]

            logger.info(f"Listed {len(resources)} MCP resources")
            result = {"resources": resources}
            if is_notification:
                logger.info("resources/list notification received (no response)")
                return None
            return JSONRPCResponse(id=request.id, result=result)

        elif request.method == "tools/call":
            # 调用工具
            params = request.params or {}
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if not tool_name:
                error = {
                    "code": -32602,
                    "message": "Invalid params: tool name is required"
                }
                if is_notification:
                    logger.warning(f"tools/call notification failed: {error['message']}")
                    return None
                return JSONRPCResponse(id=request.id, error=error)

            # 导入记忆服务
            from services.memory_service import get_memory_service
            memory_service = get_memory_service()

            if tool_name == "save_memory":
                content = arguments.get("content")
                entity_id = arguments.get("entity_id")
                importance = arguments.get("importance", 5)

                if not content:
                    error = {
                        "code": -32602,
                        "message": "Invalid params: content is required"
                    }
                    if is_notification:
                        logger.warning(f"save_memory notification failed: {error['message']}")
                        return None
                    return JSONRPCResponse(id=request.id, error=error)

                # 创建记忆
                from models.schemas import MemoryCreate
                from utils.helpers import generate_id

                memory_data = MemoryCreate(
                    persona_id=settings.DEFAULT_PERSONA_ID,
                    vector_id=generate_id(),
                    type="long_term",
                    content=content,
                    entity_id=entity_id,
                    metadata={"importance": importance}
                )

                memory = await memory_service.create_memory(
                    memory_data=memory_data,
                    content=content
                )

                if not memory:
                    error = {
                        "code": -32603,
                        "message": "Failed to create memory"
                    }
                    if is_notification:
                        logger.warning(f"save_memory notification failed: {error['message']}")
                        return None
                    return JSONRPCResponse(id=request.id, error=error)

                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "success": True,
                                "memory_id": memory.id,
                                "message": "记忆已保存"
                            }, ensure_ascii=False)
                        }
                    ]
                }
                if is_notification:
                    logger.info("save_memory notification succeeded (no response)")
                    return None
                return JSONRPCResponse(id=request.id, result=result)

            elif tool_name == "update_memory":
                memory_id = arguments.get("memory_id")
                new_content = arguments.get("new_content")

                if not memory_id or not new_content:
                    error = {
                        "code": -32602,
                        "message": "Invalid params: memory_id and new_content are required"
                    }
                    if is_notification:
                        logger.warning(f"update_memory notification failed: {error['message']}")
                        return None
                    return JSONRPCResponse(id=request.id, error=error)

                # 更新记忆
                from models.schemas import MemoryUpdate

                memory = await memory_service.update_memory(
                    memory_id=memory_id,
                    memory_data=MemoryUpdate(content=new_content)
                )

                if not memory:
                    error = {
                        "code": -32603,
                        "message": f"Memory not found: {memory_id}"
                    }
                    if is_notification:
                        logger.warning(f"update_memory notification failed: {error['message']}")
                        return None
                    return JSONRPCResponse(id=request.id, error=error)

                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "success": True,
                                "memory_id": memory_id,
                                "message": "记忆已更新"
                            }, ensure_ascii=False)
                        }
                    ]
                }
                if is_notification:
                    logger.info("update_memory notification succeeded (no response)")
                    return None
                return JSONRPCResponse(id=request.id, result=result)

            elif tool_name == "delete_memory":
                memory_id = arguments.get("memory_id")

                if not memory_id:
                    error = {
                        "code": -32602,
                        "message": "Invalid params: memory_id is required"
                    }
                    if is_notification:
                        logger.warning(f"delete_memory notification failed: {error['message']}")
                        return None
                    return JSONRPCResponse(id=request.id, error=error)

                # 删除记忆
                success = await memory_service.delete_memory(memory_id)

                if not success:
                    error = {
                        "code": -32603,
                        "message": f"Memory not found: {memory_id}"
                    }
                    if is_notification:
                        logger.warning(f"delete_memory notification failed: {error['message']}")
                        return None
                    return JSONRPCResponse(id=request.id, error=error)

                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "success": True,
                                "memory_id": memory_id,
                                "message": "记忆已删除"
                            }, ensure_ascii=False)
                        }
                    ]
                }
                if is_notification:
                    logger.info("delete_memory notification succeeded (no response)")
                    return None
                return JSONRPCResponse(id=request.id, result=result)

            elif tool_name == "search_memories":
                query = arguments.get("query")

                if not query:
                    error = {
                        "code": -32602,
                        "message": "Invalid params: query is required"
                    }
                    if is_notification:
                        logger.warning(f"search_memories notification failed: {error['message']}")
                        return None
                    return JSONRPCResponse(id=request.id, error=error)

                # 搜索记忆
                from models.schemas import MemorySearchRequest

                search_request = MemorySearchRequest(
                    query=query,
                    top_k=10,
                    metadata={"persona_id": settings.DEFAULT_PERSONA_ID}
                )

                results = await memory_service.search_memories(search_request)

                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "success": True,
                                "results": results,
                                "count": len(results)
                            }, ensure_ascii=False)
                        }
                    ]
                }
                if is_notification:
                    logger.info("search_memories notification succeeded (no response)")
                    return None
                return JSONRPCResponse(id=request.id, result=result)

            else:
                error = {
                    "code": -32601,
                    "message": f"Tool not found: {tool_name}"
                }
                if is_notification:
                    logger.warning(f"tools/call notification failed: {error['message']}")
                    return None
                return JSONRPCResponse(id=request.id, error=error)

        else:
            error = {
                "code": -32601,
                "message": f"Method not found: {request.method}"
            }
            if is_notification:
                logger.warning(f"Notification for unknown method: {request.method}")
                return None
            return JSONRPCResponse(id=request.id, error=error)

    except HTTPException as e:
        error = {
            "code": e.status_code,
            "message": e.detail
        }
        if is_notification:
            logger.warning(f"Notification failed with HTTPException: {e.detail}")
            return None
        return JSONRPCResponse(id=request.id, error=error)
    except Exception as e:
        logger.error(f"Error handling JSON-RPC request: {e}")
        error = {
            "code": -32603,
            "message": str(e)
        }
        if is_notification:
            logger.warning(f"Notification failed with exception: {str(e)}")
            return None
        return JSONRPCResponse(id=request.id, error=error)


async def sse_generator(response: JSONRPCResponse) -> AsyncGenerator[str, None]:
    """
    生成 SSE 流

    Args:
        response: JSON-RPC 响应对象

    Yields:
        SSE 格式的字符串
    """
    # 发送事件
    event_data = json.dumps(response.dict(exclude_none=True), ensure_ascii=False)
    yield f"event: message\ndata: {event_data}\n\n"
    # 结束事件
    yield "event: end\ndata: {}\n\n"


async def sse_generator_empty() -> AsyncGenerator[str, None]:
    """
    生成空的 SSE 流（用于通知类型的请求）

    Yields:
        SSE 格式的字符串
    """
    # 只发送结束事件
    yield "event: end\ndata: {}\n\n"


@router.post("/mcp")
async def mcp_streamable_http(
    request: Request,
    authorization: Optional[str] = Header(None)
):
    """
    MCP Streamable HTTP 端点

    支持 JSON-RPC 2.0 协议的 MCP 请求，使用 SSE 返回响应

    请求格式:
    {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }

    支持的方法:
    - initialize: 初始化连接
    - tools/list: 列出可用工具
    - resources/list: 列出可用资源
    - tools/call: 调用工具

    注意：通知类型的请求（没有 id 字段）不会返回响应数据
    """
    verify_api_key(authorization)

    try:
        # 解析请求体
        body = await request.body()
        request_data = json.loads(body.decode("utf-8"))

        # 创建 JSON-RPC 请求对象
        jsonrpc_request = JSONRPCRequest(**request_data)

        logger.info(f"Received MCP request: method={jsonrpc_request.method}, id={jsonrpc_request.id}")

        # 处理请求
        jsonrpc_response = await handle_jsonrpc_request(jsonrpc_request)

        # 如果是通知类型，返回空的 SSE 流
        if jsonrpc_response is None:
            return StreamingResponse(
                sse_generator_empty(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )

        # 返回 SSE 流
        return StreamingResponse(
            sse_generator(jsonrpc_response),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON request: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# 保留旧的端点以兼容现有测试
@router.get("/mcp/tools", response_model=MCPListToolsResponse)
async def list_mcp_tools(authorization: Optional[str] = Header(None)):
    """
    列出所有可用的 MCP 工具（兼容旧版）

    这些工具可以通过 MCP 协议被 LLM 调用
    """
    verify_api_key(authorization)

    try:
        # 获取记忆工具定义
        memory_tools = get_memory_tools()

        # 转换为 MCP 格式
        mcp_tools = []
        for tool in memory_tools:
            function = tool.get("function", {})
            mcp_tool = MCPTool(
                name=function.get("name"),
                description=function.get("description", ""),
                inputSchema=function.get("parameters", {})
            )
            mcp_tools.append(mcp_tool)

        logger.info(f"Listed {len(mcp_tools)} MCP tools")
        return MCPListToolsResponse(tools=mcp_tools)

    except Exception as e:
        logger.error(f"Error listing MCP tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/mcp/resources", response_model=MCPListResourcesResponse)
async def list_mcp_resources(authorization: Optional[str] = Header(None)):
    """
    列出所有可用的 MCP 资源（兼容旧版）

    这些资源可以通过 MCP 协议被 LLM 访问
    """
    verify_api_key(authorization)

    try:
        # 定义记忆资源
        resources = [
            MCPResource(
                uri="memory://list",
                name="列出记忆",
                description="列出所有记忆，支持按记忆体和类型过滤"
            ),
            MCPResource(
                uri="memory://get",
                name="获取记忆详情",
                description="根据记忆ID获取详细信息"
            ),
            MCPResource(
                uri="memory://search",
                name="搜索记忆",
                description="基于语义搜索相关记忆"
            )
        ]

        logger.info(f"Listed {len(resources)} MCP resources")
        return MCPListResourcesResponse(resources=resources)

    except Exception as e:
        logger.error(f"Error listing MCP resources: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/mcp/info", response_model=MCPServerInfo)
async def get_mcp_info(authorization: Optional[str] = Header(None)):
    """
    获取 MCP 服务器信息（兼容旧版）

    返回服务器的基本信息和协议版本
    """
    verify_api_key(authorization)

    try:
        info = MCPServerInfo(
            name="MemPoint Memory Server",
            version="0.1.0",
            protocolVersion="2024-11-05"
        )

        logger.info("MCP server info requested")
        return info

    except Exception as e:
        logger.error(f"Error getting MCP info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/mcp/tools/{tool_name}")
async def call_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    authorization: Optional[str] = Header(None)
):
    """
    调用 MCP 工具（兼容旧版）

    Args:
        tool_name: 工具名称
        arguments: 工具参数
        authorization: Authorization header，格式为 'Bearer <token>'

    Returns:
        工具执行结果
    """
    verify_api_key(authorization)

    try:
        # 导入记忆服务
        from services.memory_service import get_memory_service

        memory_service = get_memory_service()

        # 根据工具名称调用相应的服务方法
        if tool_name == "save_memory":
            content = arguments.get("content")
            entity_id = arguments.get("entity_id")
            importance = arguments.get("importance", 5)

            if not content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="content is required"
                )

            # 创建记忆
            from models.schemas import MemoryCreate
            from utils.helpers import generate_id

            memory_data = MemoryCreate(
                persona_id=settings.DEFAULT_PERSONA_ID,  # 使用默认记忆体ID
                vector_id=generate_id(),
                type="long_term",
                content=content,
                entity_id=entity_id,
                metadata={"importance": importance}
            )

            memory = await memory_service.create_memory(
                memory_data=memory_data,
                content=content
            )

            if not memory:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create memory"
                )

            return {
                "success": True,
                "memory_id": memory.id,
                "message": "记忆已保存"
            }

        elif tool_name == "update_memory":
            memory_id = arguments.get("memory_id")
            new_content = arguments.get("new_content")

            if not memory_id or not new_content:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="memory_id and new_content are required"
                )

            # 更新记忆
            from models.schemas import MemoryUpdate

            memory = await memory_service.update_memory(
                memory_id=memory_id,
                memory_data=MemoryUpdate(content=new_content)
            )

            if not memory:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Memory not found: {memory_id}"
                )

            return {
                "success": True,
                "memory_id": memory_id,
                "message": "记忆已更新"
            }

        elif tool_name == "delete_memory":
            memory_id = arguments.get("memory_id")

            if not memory_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="memory_id is required"
                )

            # 删除记忆
            success = await memory_service.delete_memory(memory_id)

            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Memory not found: {memory_id}"
                )

            return {
                "success": True,
                "memory_id": memory_id,
                "message": "记忆已删除"
            }

        elif tool_name == "search_memories":
            query = arguments.get("query")

            if not query:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="query is required"
                )

            # 搜索记忆
            from models.schemas import MemorySearchRequest

            search_request = MemorySearchRequest(
                query=query,
                top_k=10,
                metadata={"persona_id": settings.DEFAULT_PERSONA_ID}  # 使用默认记忆体ID
            )

            results = await memory_service.search_memories(search_request)

            return {
                "success": True,
                "results": results,
                "count": len(results)
            }

        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool not found: {tool_name}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calling MCP tool {tool_name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
