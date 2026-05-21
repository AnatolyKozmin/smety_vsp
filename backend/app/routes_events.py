from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from typing import List
import math

from .database import get_db
from . import models, schemas

router = APIRouter(prefix="/api/events", tags=["events"])


# ===== Events CRUD =====

@router.get("", response_model=List[schemas.EventOut])
def list_events(db: Session = Depends(get_db)):
    return db.query(models.Event).order_by(models.Event.id.desc()).all()


@router.post("", response_model=schemas.EventOut)
def create_event(payload: schemas.EventIn, db: Session = Depends(get_db)):
    e = models.Event(**payload.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@router.put("/{event_id}", response_model=schemas.EventOut)
def update_event(event_id: int, payload: schemas.EventIn, db: Session = Depends(get_db)):
    e = db.get(models.Event, event_id)
    if not e:
        raise HTTPException(404, "Заброс не найден")
    for k, v in payload.model_dump().items():
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return e


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    e = db.get(models.Event, event_id)
    if not e:
        raise HTTPException(404, "Заброс не найден")
    db.delete(e)
    db.commit()
    return {"ok": True}


# ===== Days =====

@router.get("/{event_id}/days", response_model=List[schemas.EventDayOut])
def list_days(event_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.EventDay)
        .filter(models.EventDay.event_id == event_id)
        .order_by(models.EventDay.sort_order)
        .all()
    )


@router.post("/{event_id}/days", response_model=schemas.EventDayOut)
def create_day(event_id: int, payload: schemas.EventDayIn, db: Session = Depends(get_db)):
    e = db.get(models.Event, event_id)
    if not e:
        raise HTTPException(404, "Заброс не найден")
    d = models.EventDay(event_id=event_id, **payload.model_dump())
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.put("/days/{day_id}", response_model=schemas.EventDayOut)
def update_day(day_id: int, payload: schemas.EventDayIn, db: Session = Depends(get_db)):
    d = db.get(models.EventDay, day_id)
    if not d:
        raise HTTPException(404, "День не найден")
    for k, v in payload.model_dump().items():
        setattr(d, k, v)
    db.commit()
    db.refresh(d)
    return d


@router.delete("/days/{day_id}")
def delete_day(day_id: int, db: Session = Depends(get_db)):
    d = db.get(models.EventDay, day_id)
    if not d:
        raise HTTPException(404, "День не найден")
    db.delete(d)
    db.commit()
    return {"ok": True}


# ===== Meals =====

@router.post("/days/{day_id}/meals", response_model=schemas.EventMealOut)
def create_meal(day_id: int, payload: schemas.EventMealIn, db: Session = Depends(get_db)):
    d = db.get(models.EventDay, day_id)
    if not d:
        raise HTTPException(404, "День не найден")
    m = models.EventMeal(day_id=day_id, **payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.put("/meals/{meal_id}", response_model=schemas.EventMealOut)
def update_meal(meal_id: int, payload: schemas.EventMealIn, db: Session = Depends(get_db)):
    m = db.get(models.EventMeal, meal_id)
    if not m:
        raise HTTPException(404, "Приём пищи не найден")
    for k, v in payload.model_dump().items():
        setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return m


@router.put("/{event_id}/set-all-portions")
def set_all_portions(event_id: int, n: int, db: Session = Depends(get_db)):
    """Проставить portions_override = n на все приёмы пищи всех дней заброса.
    Передайте n=0, чтобы сбросить (вернуться к расчёту по участникам)."""
    e = db.get(models.Event, event_id)
    if not e:
        raise HTTPException(404, "Заброс не найден")
    value = None if n <= 0 else int(n)
    count = 0
    for d in e.days:
        for m in d.meals:
            m.portions_override = value
            count += 1
    db.commit()
    return {"ok": True, "meals_updated": count, "value": value}


@router.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    m = db.get(models.EventMeal, meal_id)
    if not m:
        raise HTTPException(404, "Приём пищи не найден")
    db.delete(m)
    db.commit()
    return {"ok": True}


# ===== Meal participants =====

@router.get("/meals/{meal_id}/participants", response_model=List[int])
def list_meal_participants(meal_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.EventMealParticipant.person_id)
        .filter(models.EventMealParticipant.meal_id == meal_id)
        .all()
    )
    return [r[0] for r in rows]


@router.put("/meals/{meal_id}/participants")
def set_meal_participants(meal_id: int, person_ids: List[int], db: Session = Depends(get_db)):
    m = db.get(models.EventMeal, meal_id)
    if not m:
        raise HTTPException(404, "Приём пищи не найден")
    db.query(models.EventMealParticipant).filter(
        models.EventMealParticipant.meal_id == meal_id
    ).delete()
    seen = set()
    for pid in person_ids:
        if pid in seen:
            continue
        seen.add(pid)
        db.add(models.EventMealParticipant(meal_id=meal_id, person_id=pid))
    db.commit()
    return {"ok": True, "count": len(seen)}


# ===== Dishes inside meal =====

@router.post("/meals/{meal_id}/dishes", response_model=schemas.EventDishOut)
def add_dish_to_meal(meal_id: int, payload: schemas.EventDishIn, db: Session = Depends(get_db)):
    m = db.get(models.EventMeal, meal_id)
    if not m:
        raise HTTPException(404, "Приём пищи не найден")
    d = models.EventDish(meal_id=meal_id, name=payload.name, sort_order=payload.sort_order)
    for ing in payload.ingredients:
        d.ingredients.append(models.EventDishIngredient(**ing.model_dump()))
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.post("/meals/{meal_id}/dishes/from-catalog/{dish_id}", response_model=schemas.EventDishOut)
def add_dish_from_catalog(meal_id: int, dish_id: int, db: Session = Depends(get_db)):
    m = db.get(models.EventMeal, meal_id)
    if not m:
        raise HTTPException(404, "Приём пищи не найден")
    src = db.get(models.Dish, dish_id)
    if not src:
        raise HTTPException(404, "Блюдо не найдено")
    d = models.EventDish(meal_id=meal_id, name=src.name, sort_order=len(m.dishes))
    for ing in src.ingredients:
        d.ingredients.append(models.EventDishIngredient(
            product_id=ing.product_id,
            grams_per_portion=ing.grams_per_portion,
        ))
    db.add(d)
    db.commit()
    db.refresh(d)
    return d


@router.put("/dishes/{dish_id}", response_model=schemas.EventDishOut)
def update_event_dish(dish_id: int, payload: schemas.EventDishIn, db: Session = Depends(get_db)):
    d = db.get(models.EventDish, dish_id)
    if not d:
        raise HTTPException(404, "Блюдо не найдено")
    d.name = payload.name
    d.sort_order = payload.sort_order
    for ing in list(d.ingredients):
        db.delete(ing)
    db.flush()
    for ing in payload.ingredients:
        d.ingredients.append(models.EventDishIngredient(**ing.model_dump()))
    db.commit()
    db.refresh(d)
    return d


@router.delete("/dishes/{dish_id}")
def delete_event_dish(dish_id: int, db: Session = Depends(get_db)):
    d = db.get(models.EventDish, dish_id)
    if not d:
        raise HTTPException(404, "Блюдо не найдено")
    db.delete(d)
    db.commit()
    return {"ok": True}


@router.patch("/ingredients/{ing_id}/taken")
def toggle_taken(ing_id: int, taken: bool, db: Session = Depends(get_db)):
    ing = db.get(models.EventDishIngredient, ing_id)
    if not ing:
        raise HTTPException(404, "Ингредиент не найден")
    ing.taken = taken
    db.commit()
    return {"ok": True, "taken": ing.taken}


# ===== Misc items =====

@router.get("/{event_id}/misc", response_model=List[schemas.EventMiscItemOut])
def list_misc(event_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.EventMiscItem)
        .options(selectinload(models.EventMiscItem.product))
        .filter(models.EventMiscItem.event_id == event_id)
        .order_by(models.EventMiscItem.id)
        .all()
    )


@router.post("/{event_id}/misc", response_model=schemas.EventMiscItemOut)
def add_misc(event_id: int, payload: schemas.EventMiscItemIn, db: Session = Depends(get_db)):
    e = db.get(models.Event, event_id)
    if not e:
        raise HTTPException(404, "Заброс не найден")
    item = models.EventMiscItem(event_id=event_id, **payload.model_dump())
    db.add(item)
    db.commit()
    return (
        db.query(models.EventMiscItem)
        .options(selectinload(models.EventMiscItem.product))
        .filter(models.EventMiscItem.id == item.id)
        .one()
    )


@router.put("/misc/{item_id}", response_model=schemas.EventMiscItemOut)
def update_misc(item_id: int, payload: schemas.EventMiscItemIn, db: Session = Depends(get_db)):
    item = db.get(models.EventMiscItem, item_id)
    if not item:
        raise HTTPException(404, "Не найдено")
    for k, v in payload.model_dump().items():
        setattr(item, k, v)
    db.commit()
    return (
        db.query(models.EventMiscItem)
        .options(selectinload(models.EventMiscItem.product))
        .filter(models.EventMiscItem.id == item.id)
        .one()
    )


@router.delete("/misc/{item_id}")
def delete_misc(item_id: int, db: Session = Depends(get_db)):
    item = db.get(models.EventMiscItem, item_id)
    if not item:
        raise HTTPException(404, "Не найдено")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.get("/{event_id}/misc/participants", response_model=List[int])
def list_misc_participants(event_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(models.EventMiscParticipant.person_id)
        .filter(models.EventMiscParticipant.event_id == event_id)
        .all()
    )
    return [r[0] for r in rows]


@router.put("/{event_id}/misc/participants")
def set_misc_participants(event_id: int, person_ids: List[int], db: Session = Depends(get_db)):
    e = db.get(models.Event, event_id)
    if not e:
        raise HTTPException(404, "Заброс не найден")
    db.query(models.EventMiscParticipant).filter(
        models.EventMiscParticipant.event_id == event_id
    ).delete()
    seen = set()
    for pid in person_ids:
        if pid in seen:
            continue
        seen.add(pid)
        db.add(models.EventMiscParticipant(event_id=event_id, person_id=pid))
    db.commit()
    return {"ok": True, "count": len(seen)}


# ===== Payments =====

@router.put("/{event_id}/payments")
def upsert_payment(event_id: int, payload: schemas.PaymentUpdate, db: Session = Depends(get_db)):
    e = db.get(models.Event, event_id)
    if not e:
        raise HTTPException(404, "Заброс не найден")
    row = (
        db.query(models.EventPayment)
        .filter(
            models.EventPayment.event_id == event_id,
            models.EventPayment.person_id == payload.person_id,
        )
        .one_or_none()
    )
    if row is None:
        row = models.EventPayment(
            event_id=event_id,
            person_id=payload.person_id,
            paid_amount=payload.paid_amount,
        )
        db.add(row)
    else:
        row.paid_amount = payload.paid_amount
    db.commit()
    return {"ok": True}


# ===== Full event (for editor) =====

def _full_query(db, event_id):
    return (
        db.query(models.Event)
        .options(
            selectinload(models.Event.days)
            .selectinload(models.EventDay.meals)
            .selectinload(models.EventMeal.dishes)
            .selectinload(models.EventDish.ingredients)
            .selectinload(models.EventDishIngredient.product),
            selectinload(models.Event.days)
            .selectinload(models.EventDay.meals)
            .selectinload(models.EventMeal.participants),
            selectinload(models.Event.misc_items).selectinload(models.EventMiscItem.product),
            selectinload(models.Event.misc_participants),
            selectinload(models.Event.payments),
        )
        .filter(models.Event.id == event_id)
    )


@router.get("/{event_id}/full")
def get_event_full(event_id: int, db: Session = Depends(get_db)):
    e = _full_query(db, event_id).one_or_none()
    if not e:
        raise HTTPException(404, "Заброс не найден")

    def ing_dict(ing):
        return {
            "id": ing.id,
            "product_id": ing.product_id,
            "grams_per_portion": ing.grams_per_portion,
            "taken": ing.taken,
            "product": _product_dict(ing.product),
        }

    return {
        "id": e.id,
        "name": e.name,
        "markup_percent": e.markup_percent,
        "days": [
            {
                "id": d.id,
                "name": d.name,
                "short_name": d.short_name,
                "sort_order": d.sort_order,
                "meals": [
                    {
                        "id": m.id,
                        "name": m.name,
                        "sort_order": m.sort_order,
                        "portions_override": m.portions_override,
                        "participant_ids": [p.person_id for p in m.participants],
                        "dishes": [
                            {
                                "id": dsh.id,
                                "name": dsh.name,
                                "sort_order": dsh.sort_order,
                                "ingredients": [ing_dict(ing) for ing in dsh.ingredients],
                            }
                            for dsh in sorted(m.dishes, key=lambda x: x.sort_order)
                        ],
                    }
                    for m in sorted(d.meals, key=lambda x: x.sort_order)
                ],
            }
            for d in sorted(e.days, key=lambda x: x.sort_order)
        ],
        "misc_items": [
            {
                "id": i.id,
                "product_id": i.product_id,
                "quantity": i.quantity,
                "taken": i.taken,
                "product": _product_dict(i.product),
            }
            for i in e.misc_items
        ],
        "misc_participant_ids": [p.person_id for p in e.misc_participants],
    }


def _product_dict(p):
    return {
        "id": p.id,
        "name": p.name,
        "unit": p.unit,
        "grams_in_package": p.grams_in_package,
        "price_per_unit": p.price_per_unit,
        "storage_term": p.storage_term,
        "product_link": p.product_link,
    }


# ===== Estimate calculation =====

def _packages(total_grams: float, grams_in_package: float) -> float:
    if grams_in_package and grams_in_package > 0:
        return math.ceil(total_grams / grams_in_package) if total_grams > 0 else 0
    return 0


@router.get("/{event_id}/estimate", response_model=schemas.EstimateOut)
def get_estimate(event_id: int, db: Session = Depends(get_db)):
    e = _full_query(db, event_id).one_or_none()
    if not e:
        raise HTTPException(404, "Заброс не найден")

    people = {p.id: p for p in db.query(models.Person).all()}

    days_out = []
    food_total = 0.0
    person_meals: dict = {}

    for d in sorted(e.days, key=lambda x: x.sort_order):
        meals_out = []
        day_total = 0.0
        for m in sorted(d.meals, key=lambda x: x.sort_order):
            participant_ids = [p.person_id for p in m.participants]
            # Если задан portions_override — используем его как кол-во порций, иначе count участников
            portions = m.portions_override if m.portions_override and m.portions_override > 0 else len(participant_ids)
            for pid in participant_ids:
                person_meals[pid] = person_meals.get(pid, 0) + 1
            dishes_out = []
            meal_total = 0.0
            for dish in sorted(m.dishes, key=lambda x: x.sort_order):
                ings_out = []
                dish_total = 0.0
                for ing in dish.ingredients:
                    prod = ing.product
                    total_grams = (ing.grams_per_portion or 0) * portions
                    packages = _packages(total_grams, prod.grams_in_package)
                    price = packages * (prod.price_per_unit or 0)
                    dish_total += price
                    ings_out.append(schemas.IngredientCalc(
                        id=ing.id,
                        product_id=prod.id,
                        product_name=prod.name,
                        grams_per_portion=ing.grams_per_portion or 0,
                        portions=portions,
                        total_grams=total_grams,
                        unit=prod.unit or "",
                        grams_in_package=prod.grams_in_package or 0,
                        price_per_unit=prod.price_per_unit or 0,
                        product_link=prod.product_link or "",
                        storage_term=prod.storage_term or "",
                        packages_needed=packages,
                        total_price=price,
                        taken=ing.taken,
                    ))
                meal_total += dish_total
                dishes_out.append(schemas.DishCalc(
                    id=dish.id, name=dish.name, portions=portions,
                    ingredients=ings_out, total_price=dish_total,
                ))
            day_total += meal_total
            meals_out.append(schemas.MealCalc(
                id=m.id, name=m.name, sort_order=m.sort_order,
                portions=portions, portions_override=m.portions_override,
                participant_ids=participant_ids,
                dishes=dishes_out, total_price=meal_total,
            ))
        food_total += day_total
        days_out.append(schemas.DayCalc(
            id=d.id, name=d.name, short_name=d.short_name,
            sort_order=d.sort_order, meals=meals_out, total_price=day_total,
        ))

    # Misc — quantity in units × price_per_unit
    misc_total = 0.0
    misc_list = []
    for i in e.misc_items:
        prod = i.product
        item_price = (i.quantity or 0) * (prod.price_per_unit or 0)
        misc_total += item_price
        misc_list.append(schemas.MiscCalc(
            id=i.id,
            product_id=prod.id,
            product_name=prod.name,
            unit=prod.unit or "",
            storage_term=prod.storage_term or "",
            quantity=i.quantity or 0,
            price_per_unit=prod.price_per_unit or 0,
            total_price=item_price,
            taken=i.taken,
        ))

    misc_participant_ids = [p.person_id for p in e.misc_participants]
    misc_count = len(misc_participant_ids)
    per_person_misc = (misc_total / misc_count) if misc_count > 0 else 0.0

    base_total = food_total + misc_total
    markup = e.markup_percent or 0.0
    total_with_markup = base_total * (1 + markup / 100.0)

    person_food: dict = {}
    for d in days_out:
        for m in d.meals:
            if m.portions <= 0:
                continue
            per_portion = m.total_price / m.portions
            for pid in m.participant_ids:
                person_food[pid] = person_food.get(pid, 0.0) + per_portion

    payments_map = {p.person_id: p.paid_amount for p in e.payments}

    contributions: list = []
    all_pids = set(person_food.keys()) | set(misc_participant_ids)
    for pid in all_pids:
        person = people.get(pid)
        if not person:
            continue
        base = person_food.get(pid, 0.0)
        if pid in misc_participant_ids:
            base += per_person_misc
            misc_flag = True
        else:
            misc_flag = False
        amount = base * (1 + markup / 100.0)
        paid = payments_map.get(pid, 0.0) or 0.0
        balance = amount - paid
        if amount <= 0:
            status = "—"
        elif paid >= amount - 0.5:
            status = "Оплачено"
        elif paid > 0:
            status = "Частично"
        else:
            status = "—"
        contributions.append(schemas.ContributionRow(
            person_id=pid,
            full_name=person.full_name,
            role=person.role or "",
            meals_count=person_meals.get(pid, 0),
            misc=misc_flag,
            base_amount=round(base, 2),
            amount=round(amount, 2),
            paid_amount=round(paid, 2),
            balance=round(balance, 2),
            status=status,
        ))
    contributions.sort(key=lambda x: (x.role, x.full_name))

    summary = {
        "food_total": round(food_total, 2),
        "misc_total": round(misc_total, 2),
        "base_total": round(base_total, 2),
        "total_with_markup": round(total_with_markup, 2),
        "to_collect_planned": round(sum(c.amount for c in contributions), 2),
        "collected_fact": round(sum(c.paid_amount for c in contributions), 2),
        "balance": round(sum(c.balance for c in contributions), 2),
    }

    return schemas.EstimateOut(
        event=schemas.EventOut.model_validate(e),
        days=days_out,
        misc=misc_list,
        misc_participant_ids=misc_participant_ids,
        food_total=round(food_total, 2),
        misc_total=round(misc_total, 2),
        base_total=round(base_total, 2),
        total_with_markup=round(total_with_markup, 2),
        per_person_misc=round(per_person_misc, 2),
        contributions=contributions,
        summary=summary,
    )


# ===== Aggregated shopping list (ИТОГО) =====

@router.get("/{event_id}/shopping-list", response_model=schemas.ShoppingListOut)
def get_shopping_list(event_id: int, db: Session = Depends(get_db)):
    e = _full_query(db, event_id).one_or_none()
    if not e:
        raise HTTPException(404, "Заброс не найден")

    # aggregator: product_id -> {grams, units}
    grams_by_product: dict = {}
    units_by_product: dict = {}
    products: dict = {}

    for d in e.days:
        for m in d.meals:
            portions = m.portions_override if m.portions_override and m.portions_override > 0 else len(m.participants)
            if portions <= 0:
                continue
            for dish in m.dishes:
                for ing in dish.ingredients:
                    prod = ing.product
                    products[prod.id] = prod
                    grams_by_product[prod.id] = grams_by_product.get(prod.id, 0.0) + (ing.grams_per_portion or 0) * portions

    for i in e.misc_items:
        prod = i.product
        products[prod.id] = prod
        units_by_product[prod.id] = units_by_product.get(prod.id, 0.0) + (i.quantity or 0)

    rows_short: list = []
    rows_long: list = []
    short_total = 0.0
    long_total = 0.0
    for pid, prod in products.items():
        total_grams = grams_by_product.get(pid, 0.0)
        misc_units = units_by_product.get(pid, 0.0)
        packages_from_grams = _packages(total_grams, prod.grams_in_package)
        packages_needed = packages_from_grams + misc_units
        price_per_unit = prod.price_per_unit or 0
        total_price = packages_needed * price_per_unit
        row = schemas.ShoppingRow(
            product_id=prod.id,
            product_name=prod.name,
            unit=prod.unit or "",
            storage_term=prod.storage_term or "",
            grams_in_package=prod.grams_in_package or 0,
            total_grams=total_grams,
            total_units=misc_units,
            packages_needed=packages_needed,
            price_per_unit=price_per_unit,
            total_price=total_price,
            product_link=prod.product_link or "",
        )
        is_short = (prod.storage_term or "").strip().lower().startswith("кратк")
        if is_short:
            rows_short.append(row)
            short_total += total_price
        else:
            rows_long.append(row)
            long_total += total_price

    rows_short.sort(key=lambda r: r.product_name)
    rows_long.sort(key=lambda r: r.product_name)

    return schemas.ShoppingListOut(
        event=schemas.EventOut.model_validate(e),
        short_term=rows_short,
        long_term=rows_long,
        short_total=round(short_total, 2),
        long_total=round(long_total, 2),
        grand_total=round(short_total + long_total, 2),
    )
