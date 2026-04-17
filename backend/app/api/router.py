from fastapi import APIRouter

from app.api.routes import (
    assistant,
    auth,
    calendar,
    conversations,
    credentials,
    documents,
    drive,
    exports,
    messages,
    notes,
    runs,
    tool_calls,
    workspace,
)

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(credentials.router)
api_router.include_router(conversations.router)
api_router.include_router(messages.router)
api_router.include_router(workspace.router)
api_router.include_router(runs.router)
api_router.include_router(tool_calls.router)
api_router.include_router(documents.router)
api_router.include_router(assistant.router)
api_router.include_router(notes.router)
api_router.include_router(calendar.router)
api_router.include_router(drive.router)
api_router.include_router(exports.router)
