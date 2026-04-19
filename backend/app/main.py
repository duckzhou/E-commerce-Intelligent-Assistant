from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from .config import settings
from .database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的生命周期管理"""
    # 启动时初始化数据库
    init_db()
    print("数据库初始化完成")
    yield
    # 关闭时清理资源
    print("应用关闭")


app = FastAPI(
    title="主播智能问答助手",
    description="基于RAG的主播智能问答系统，支持文档检索、多轮对话、流式输出",
    version="0.1.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "message": "服务运行中"}


# 导入路由
from .routers import docs as docs_router
from .routers import chat as chat_router
from .routers import conversations as conversations_router
from .routers import auth as auth_router

# 注册路由
app.include_router(auth_router.router, tags=["认证"])
app.include_router(docs_router.router, prefix="/docs", tags=["文档管理"])
app.include_router(chat_router.router, prefix="/chat", tags=["智能问答"])
app.include_router(conversations_router.router, prefix="/conversations", tags=["会话管理"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )