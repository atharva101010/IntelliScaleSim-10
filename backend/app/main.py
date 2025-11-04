from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import routes_auth, routes_containers, routes_loadtest, routes_autoscale, routes_dashboard
from app.models.base import Base
from app.database.session import engine

app = FastAPI(title="IntelliScaleSim API", version="0.1.0")

# CORS (adjust origins via env in future)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "IntelliScaleSim API", "status": "ok"}


@app.get("/healthz")
def healthz():
    return {"status": "healthy"}

# Include placeholder routers
app.include_router(routes_auth.router)
app.include_router(routes_containers.router)
app.include_router(routes_loadtest.router)
app.include_router(routes_autoscale.router)
app.include_router(routes_dashboard.router)


@app.on_event("startup")
def on_startup():
    # Create tables for scaffold/demo purposes. In real app, use Alembic.
    Base.metadata.create_all(bind=engine)
