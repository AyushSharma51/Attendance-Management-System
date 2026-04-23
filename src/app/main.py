from fastapi import FastAPI
from contextlib import asynccontextmanager
from .database import create_tables
from .routes import auth
from .routes import batches
from .routes import sessions
from .routes import attendance
from .routes import summary


# -----------------------------
#  Lifespan (Startup / Shutdown)
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    #  Startup
    await create_tables()
    print(" Database connected & tables created")

    yield

    #  Shutdown (optional)
    print(" Application shutting down")


# -----------------------------
#  FastAPI App
# -----------------------------
app = FastAPI(
    title="Attendance Management System",
    version="1.0.0",
    lifespan=lifespan
)


# -----------------------------
#  Health Check
# -----------------------------
@app.get("/health")
async def health_check():

    return {"status": "System is running!"}


# -----------------------------
#  Include Routers
# -----------------------------
app.include_router(auth.router)
app.include_router(batches.router)
app.include_router(sessions.router)
app.include_router(attendance.router)
app.include_router(summary.router)