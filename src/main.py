from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database import engine, Base
from src.routers import auth, batches, sessions, attendance, institutions, programme
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SkillBridge Attendance API",
    description="Backend API for the SkillBridge state-level skilling programme attendance management system.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(institutions.router)
app.include_router(programme.router)


@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "message": "SkillBridge Attendance API is running"}


@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}
