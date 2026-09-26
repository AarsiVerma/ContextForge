"""TaskFlow - Simple Task Management API with deliberate bugs for debugging demo."""

from fastapi import FastAPI
from auth.endpoints import router as auth_router
from tasks.endpoints import router as tasks_router

app = FastAPI(
    title="TaskFlow API",
    description="Simple task management API with deliberate bugs for debugging demo",
    version="1.0.0"
)

app.include_router(auth_router, tags=["authentication"])
app.include_router(tasks_router, tags=["tasks"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "taskflow"}


@app.get("/")
async def root():
    return {
        "service": "TaskFlow",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }