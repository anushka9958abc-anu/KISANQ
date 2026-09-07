from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import admin, auth, centres, iot, oauth, procurements, queue
from app.seed import seed

app = FastAPI(title="KISANQ", version="1.0.0", description="Agriculture procurement status platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(oauth.router)
app.include_router(centres.router)
app.include_router(procurements.router)
app.include_router(queue.router)
app.include_router(admin.router)
app.include_router(iot.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    seed()


@app.get("/api/health")
def health():
    return {"ok": True, "service": "kisanq-api"}
