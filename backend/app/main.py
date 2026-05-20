from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from . import models  # noqa: F401  — register tables
from .routes_dishes import router as dishes_router
from .routes_people import router as people_router
from .routes_events import router as events_router
from .routes_products import router as products_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Сметы забросов")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(dishes_router)
app.include_router(people_router)
app.include_router(events_router)


@app.get("/api/health")
def health():
    return {"ok": True}
