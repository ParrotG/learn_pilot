from fastapi import APIRouter

from app.api.routes import assistant, auth, calendar, credentials, documents, drive, notes

api_router = APIRouter(prefix="/api")
api_router.include_router(auth.router)
api_router.include_router(credentials.router)
api_router.include_router(documents.router)
api_router.include_router(assistant.router)
api_router.include_router(notes.router)
api_router.include_router(calendar.router)
api_router.include_router(drive.router)

