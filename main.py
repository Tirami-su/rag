from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI(title="RAG Agent API", description="企业内部知识库助手API", version="1.0.0")

# 添加CORS中间件，允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(router)


@app.get("/")
async def root():
    """根路径，返回API信息"""
    return {
        "name": "RAG Agent API",
        "version": "1.0.0",
        "description": "企业内部知识库助手API",
        "endpoints": {"chat": "/api/chat", "session_history": "/api/sessions/{session_id}/history"},
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
