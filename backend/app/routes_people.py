from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .database import get_db
from . import models, schemas

router = APIRouter(prefix="/api/people", tags=["people"])


@router.get("", response_model=List[schemas.PersonOut])
def list_people(db: Session = Depends(get_db)):
    return db.query(models.Person).order_by(models.Person.role, models.Person.full_name).all()


@router.post("", response_model=schemas.PersonOut)
def create_person(payload: schemas.PersonIn, db: Session = Depends(get_db)):
    p = models.Person(**payload.model_dump())
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.put("/{person_id}", response_model=schemas.PersonOut)
def update_person(person_id: int, payload: schemas.PersonIn, db: Session = Depends(get_db)):
    p = db.get(models.Person, person_id)
    if not p:
        raise HTTPException(404, "Не найдено")
    for k, v in payload.model_dump().items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{person_id}")
def delete_person(person_id: int, db: Session = Depends(get_db)):
    p = db.get(models.Person, person_id)
    if not p:
        raise HTTPException(404, "Не найдено")
    db.delete(p)
    db.commit()
    return {"ok": True}
