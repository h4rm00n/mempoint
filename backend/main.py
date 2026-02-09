"""
FastAPI应用入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import importlib
import os

from config import settings, initialize_configurations, initialize_default_persona
from models.database import init_db
from utils.logger import logger
from api import chat, completions, models


# 动态导入config模块
try:
    config_module = importlib.import_module("api.config")
    config_router = config_module.router
except ImportError:
    config_router = None
    logger.warning("Failed to import config module")


# 动态导入memory模块
try:
    memory_module = importlib.import_module("api.memory")
    memory_router = memory_module.router
except ImportError:
    memory_router = None
    logger.warning("Failed to import memory module")


# 动态导入persona模块
try:
    persona_module = importlib.import_module("api.persona")
    persona_router = persona_module.router
except ImportError:
    persona_router = None
    logger.warning("Failed to import persona module")


# 动态导入mcp模块
try:
    mcp_module = importlib.import_module("api.mcp")
    mcp_router = mcp_module.router
except ImportError:
    mcp_router = None
    logger.warning("Failed to import mcp module")


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="带记忆注入的OpenAI风格API (KùzuDB版)",
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS配置
origins = [
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",  # Vite 默认端口
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源（开发环境）
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

# 注册路由
app.include_router(chat.router, prefix=settings.API_V1_STR)
app.include_router(completions.router, prefix=settings.API_V1_STR)
app.include_router(models.router, prefix=settings.API_V1_STR)
if memory_router:
    app.include_router(memory_router, prefix=settings.API_V1_STR)
if persona_router:
    app.include_router(persona_router, prefix=settings.API_V1_STR)
if mcp_router:
    app.include_router(mcp_router, prefix=settings.API_V1_STR)
if config_router:
    app.include_router(config_router, prefix=settings.API_V1_STR)

# 静态文件服务 - 服务前端构建的dist目录
FRONTEND_DIST_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(FRONTEND_DIST_PATH):
    # 挂载静态资源目录（assets, js, css等）
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST_PATH, "assets")), name="assets")
    logger.info(f"Serving static files from: {FRONTEND_DIST_PATH}")
else:
    logger.warning(f"Frontend dist directory not found: {FRONTEND_DIST_PATH}")


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    # 确保数据目录存在
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(settings.MILVUS_URI), exist_ok=True)
    os.makedirs(os.path.dirname(settings.KUZU_DB_PATH), exist_ok=True)
    
    # 确保SQLite数据库目录存在
    sqlite_dir = os.path.dirname(settings.SQLITE_DB_PATH)
    if sqlite_dir and sqlite_dir != settings.DATA_DIR:
        os.makedirs(sqlite_dir, exist_ok=True)

    # 初始化SQLite数据库
    init_db()
    
    # 初始化配置到数据库
    initialize_configurations()
    
    # 初始化默认人格
    initialize_default_persona()
    
    # 验证数据库文件已创建
    if os.path.exists(settings.SQLITE_DB_PATH):
        logger.info(f"SQLite database initialized: {settings.SQLITE_DB_PATH}")
    else:
        logger.warning(f"SQLite database file not found: {settings.SQLITE_DB_PATH}")

    # 初始化存储服务 - 触发懒加载,创建数据库文件
    try:
        from memory.vector_store import get_vector_store
        from memory.graph_store import get_graph_store
        
        # 主动初始化,触发数据库文件创建
        get_vector_store()
        logger.info("Vector store initialized")
        
        get_graph_store()
        logger.info("Graph store initialized")
    except Exception as e:
        logger.error(f"Failed to initialize stores: {e}")
        raise

    logger.info(f"Server started. Data directory: {settings.DATA_DIR}")
    logger.info(f"SQLite DB path: {settings.SQLITE_DB_PATH}")
    logger.info(f"Milvus DB path: {settings.MILVUS_URI}")
    logger.info(f"KùzuDB path: {settings.KUZU_DB_PATH}")
    logger.info(f"LLM API: {settings.LLM_BASE_URL}, Model: {settings.LLM_MODEL}")
    logger.info(f"Embedding API: {settings.EMBEDDING_BASE_URL}, Model: {settings.EMBEDDING_MODEL}")
    logger.info(f"Memory Tools API: GET {settings.API_V1_STR}/memory-tools")
    logger.info(f"Memory Management API: POST/GET/PUT/DELETE {settings.API_V1_STR}/memories")
    logger.info(f"MCP Tools API: GET {settings.API_V1_STR}/mcp/tools")
    logger.info(f"MCP Resources API: GET {settings.API_V1_STR}/mcp/resources")
    logger.info(f"MCP Tool Call API: POST {settings.API_V1_STR}/mcp/tools/{{tool_name}}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("Shutdown signal received, closing connections...")
    
    # 关闭数据库连接
    try:
        from memory.vector_store import get_vector_store, _vector_store
        from memory.graph_store import get_graph_store, _graph_store
        from services.persona_service import get_persona_service, _persona_service
        from services.memory_service import get_memory_service, _memory_service
        from memory.memory_manager import get_memory_manager, _memory_manager

        # 只有在vector_store已经初始化的情况下才关闭
        if _vector_store is not None:
            get_vector_store().close()
            logger.info("Vector store closed")
        
        # 只有在graph_store已经初始化的情况下才关闭
        if _graph_store is not None:
            get_graph_store().close()
            logger.info("Graph store closed")
        
        # 只有在persona_service已经初始化的情况下才关闭
        if _persona_service is not None:
            get_persona_service().close()
            logger.info("Persona service closed")
        
        # 只有在memory_service已经初始化的情况下才关闭
        if _memory_service is not None:
            get_memory_service().close()
            logger.info("Memory service closed")
        
        # 只有在memory_manager已经初始化的情况下才关闭
        if _memory_manager is not None:
            get_memory_manager().close()
            logger.info("Memory manager closed")

        # 只有在auto_memory_service已经初始化的情况下才关闭
        try:
            from services.auto_memory_service import get_auto_memory_service, _auto_memory_service
            if _auto_memory_service is not None:
                get_auto_memory_service().close()
                logger.info("Auto memory service closed")
        except ImportError:
            pass
            
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("Server shutting down...")


@app.get("/")
def read_root():
    """根路径 - 服务前端页面或返回API信息"""
    # 如果存在frontend/dist/index.html，则服务前端页面
    if os.path.exists(FRONTEND_DIST_PATH):
        index_path = os.path.join(FRONTEND_DIST_PATH, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    
    # 如果前端页面不存在，返回API信息
    return {
        "message": "Welcome to MemPoint API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME
    }
