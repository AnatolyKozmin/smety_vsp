from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from typing import List

from .database import get_db
from . import models, schemas

router = APIRouter(prefix="/api/dishes", tags=["dishes"])


def _q(db):
    return (
        db.query(models.Dish)
        .options(selectinload(models.Dish.ingredients).selectinload(models.DishIngredient.product))
    )


@router.get("", response_model=List[schemas.DishOut])
def list_dishes(db: Session = Depends(get_db)):
    return _q(db).order_by(models.Dish.name).all()


@router.get("/{dish_id}", response_model=schemas.DishOut)
def get_dish(dish_id: int, db: Session = Depends(get_db)):
    dish = _q(db).filter(models.Dish.id == dish_id).one_or_none()
    if not dish:
        raise HTTPException(404, "Блюдо не найдено")
    return dish


@router.post("", response_model=schemas.DishOut)
def create_dish(payload: schemas.DishIn, db: Session = Depends(get_db)):
    dish = models.Dish(name=payload.name)
    for ing in payload.ingredients:
        dish.ingredients.append(models.DishIngredient(**ing.model_dump()))
    db.add(dish)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Блюдо с таким именем уже есть")
    return _q(db).filter(models.Dish.id == dish.id).one()


@router.put("/{dish_id}", response_model=schemas.DishOut)
def update_dish(dish_id: int, payload: schemas.DishIn, db: Session = Depends(get_db)):
    dish = db.get(models.Dish, dish_id)
    if not dish:
        raise HTTPException(404, "Блюдо не найдено")
    dish.name = payload.name
    for ing in list(dish.ingredients):
        db.delete(ing)
    db.flush()
    for ing in payload.ingredients:
        dish.ingredients.append(models.DishIngredient(**ing.model_dump()))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "Блюдо с таким именем уже есть")
    return _q(db).filter(models.Dish.id == dish.id).one()


@router.delete("/{dish_id}")
def delete_dish(dish_id: int, db: Session = Depends(get_db)):
    dish = db.get(models.Dish, dish_id)
    if not dish:
        raise HTTPException(404, "Блюдо не найдено")
    db.delete(dish)
    db.commit()
    return {"ok": True}
