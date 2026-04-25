from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database import engine, Base
from src.routers import auth, batches, sessions, attendance, institutions, programme

app = FastAPI(
    title="SkillBridge Attendance API",
    description="Backend API for the SkillBridge state-level skilling programme attendance management system.",
    version="1.0.0",
)

# ✅ CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # change in production if needed
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include Routers
app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(institutions.router)
app.include_router(programme.router)

# ✅ Startup Event (VERY IMPORTANT FOR RENDER)
@app.on_event("startup")
def startup():
    try:
        print("🚀 Starting application...")

        # Create tables (optional but useful)
        Base.metadata.create_all(bind=engine)

        print("✅ Database connected successfully")

    except Exception as e:
        print("❌ Startup failed:", str(e))
        raise e  # This will show real error in logs

# ✅ Root endpoint
@app.get("/", tags=["health"])
def root():
    return {
        "status": "ok",
        "message": "SkillBridge Attendance API is running 🚀"
    }

# ✅ Health check
@app.get("/health", tags=["health"])
def health():
    return {"status": "healthy"}