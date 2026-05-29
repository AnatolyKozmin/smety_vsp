from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect

from .database import Base, engine, SessionLocal
from . import models  # noqa: F401  — register tables
from .categorize import categorize
from .routes_dishes import router as dishes_router
from .routes_people import router as people_router
from .routes_events import router as events_router
from .routes_products import router as products_router


def _ensure_category_column():
    """Если колонки products.category ещё нет (старая БД) — добавить и заполнить."""
    insp = inspect(engine)
    if "products" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("products")}
    with engine.begin() as conn:
        if "category" not in cols:
            conn.execute(text("ALTER TABLE products ADD COLUMN category VARCHAR DEFAULT 'прочее'"))
    db = SessionLocal()
    try:
        changed = 0
        for p in db.query(models.Product).all():
            cat = categorize(p.name)
            if (p.category or "") in ("", "прочее") and cat != "прочее":
                p.category = cat
                changed += 1
            elif not p.category:
                p.category = "прочее"
                changed += 1
        if changed:
            db.commit()
    finally:
        db.close()


def _ensure_guests_count_column():
    """Колонка event_meals.guests_count: либо переименовать старую portions_override, либо добавить."""
    insp = inspect(engine)
    if "event_meals" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("event_meals")}
    with engine.begin() as conn:
        if "guests_count" not in cols:
            if "portions_override" in cols:
                # SQLite 3.25+ умеет RENAME COLUMN; семантика теперь другая, но число сохраняем
                conn.execute(text("ALTER TABLE event_meals RENAME COLUMN portions_override TO guests_count"))
            else:
                conn.execute(text("ALTER TABLE event_meals ADD COLUMN guests_count INTEGER DEFAULT 0"))


def _backfill_event_participants():
    """Для существующих забросов заполняет event_participants из meal_participants."""
    insp = inspect(engine)
    if "event_participants" not in insp.get_table_names():
        return
    db = SessionLocal()
    try:
        events = db.query(models.Event).all()
        for event in events:
            already = db.query(models.EventParticipant).filter(
                models.EventParticipant.event_id == event.id
            ).count()
            if already > 0:
                continue
            # Собираем уникальных участников из всех приёмов пищи этого заброса
            pids = set()
            for day in event.days:
                for meal in day.meals:
                    for mp in meal.participants:
                        pids.add(mp.person_id)
            for pid in pids:
                db.add(models.EventParticipant(event_id=event.id, person_id=pid))
        db.commit()
    finally:
        db.close()


Base.metadata.create_all(bind=engine)
_ensure_category_column()
_ensure_guests_count_column()
_backfill_event_participants()

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
