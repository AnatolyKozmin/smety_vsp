from pydantic import BaseModel, ConfigDict
from typing import List, Optional


# ===== Products =====

class ProductBase(BaseModel):
    name: str
    unit: str = "г"
    grams_in_package: float = 1000.0
    price_per_unit: float = 0.0
    storage_term: str = "Долгосрочный"
    category: str = "прочее"
    product_link: str = ""


class ProductIn(ProductBase):
    pass


class ProductOut(ProductBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ===== Dishes =====

class DishIngredientIn(BaseModel):
    product_id: int
    grams_per_portion: float = 0.0


class DishIngredientOut(BaseModel):
    id: int
    product_id: int
    grams_per_portion: float
    product: ProductOut
    model_config = ConfigDict(from_attributes=True)


class DishIn(BaseModel):
    name: str
    ingredients: List[DishIngredientIn] = []


class DishOut(BaseModel):
    id: int
    name: str
    ingredients: List[DishIngredientOut] = []
    model_config = ConfigDict(from_attributes=True)


# ===== People =====

class PersonIn(BaseModel):
    full_name: str
    role: str = ""
    present: bool = True


class PersonOut(PersonIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


# ===== Events =====

class EventIn(BaseModel):
    name: str
    markup_percent: float = 0.0


class EventDayIn(BaseModel):
    name: str
    short_name: str = ""
    sort_order: int = 0


class EventDayOut(EventDayIn):
    id: int
    model_config = ConfigDict(from_attributes=True)


class EventMealIn(BaseModel):
    name: str
    sort_order: int = 0
    guests_count: int = 0


class EventMealOut(EventMealIn):
    id: int
    day_id: int
    model_config = ConfigDict(from_attributes=True)


class EventDishIngredientIn(BaseModel):
    product_id: int
    grams_per_portion: float = 0.0
    taken: bool = False


class EventDishIngredientOut(EventDishIngredientIn):
    id: int
    product: ProductOut
    model_config = ConfigDict(from_attributes=True)


class EventDishIn(BaseModel):
    name: str
    sort_order: int = 0
    ingredients: List[EventDishIngredientIn] = []


class EventDishOut(BaseModel):
    id: int
    meal_id: int
    name: str
    sort_order: int = 0
    ingredients: List[EventDishIngredientOut] = []
    model_config = ConfigDict(from_attributes=True)


class EventMiscItemIn(BaseModel):
    product_id: int
    quantity: float = 0.0
    taken: bool = False


class EventMiscItemOut(EventMiscItemIn):
    id: int
    product: ProductOut
    model_config = ConfigDict(from_attributes=True)


class EventOut(BaseModel):
    id: int
    name: str
    markup_percent: float = 0.0
    model_config = ConfigDict(from_attributes=True)


# ===== Estimate calculation =====

class IngredientCalc(BaseModel):
    id: int
    product_id: int
    product_name: str
    grams_per_portion: float
    portions: int
    total_grams: float
    unit: str
    grams_in_package: float
    price_per_unit: float
    product_link: str
    storage_term: str
    packages_needed: float
    total_price: float
    taken: bool


class DishCalc(BaseModel):
    id: int
    name: str
    portions: int
    ingredients: List[IngredientCalc] = []
    total_price: float


class MealCalc(BaseModel):
    id: int
    name: str
    sort_order: int
    portions: int                       # = len(participant_ids) + guests_count
    guests_count: int = 0
    participant_ids: List[int] = []
    dishes: List[DishCalc] = []
    total_price: float


class DayCalc(BaseModel):
    id: int
    name: str
    short_name: str
    sort_order: int
    meals: List[MealCalc] = []
    total_price: float


class MiscCalc(BaseModel):
    id: int
    product_id: int
    product_name: str
    unit: str
    storage_term: str
    quantity: float
    price_per_unit: float
    total_price: float
    taken: bool


class ContributionRow(BaseModel):
    person_id: int
    full_name: str
    role: str
    meals_count: int
    misc: bool
    base_amount: float
    amount: float
    paid_amount: float
    balance: float
    status: str


class EstimateOut(BaseModel):
    event: EventOut
    days: List[DayCalc] = []
    misc: List[MiscCalc] = []
    misc_participant_ids: List[int] = []
    food_total: float
    misc_total: float
    base_total: float
    total_with_markup: float
    per_person_misc: float
    contributions: List[ContributionRow] = []
    summary: dict


class ShoppingRow(BaseModel):
    product_id: int
    product_name: str
    unit: str
    storage_term: str
    grams_in_package: float
    total_grams: float        # для grams-based продуктов
    total_units: float        # для не-grams продуктов (упаковки/банки) — кол-во из misc
    packages_needed: float    # сколько упаковок брать
    price_per_unit: float
    total_price: float
    product_link: str


class ShoppingListOut(BaseModel):
    event: EventOut
    short_term: List[ShoppingRow] = []
    long_term: List[ShoppingRow] = []
    short_total: float
    long_total: float
    grand_total: float


class PaymentUpdate(BaseModel):
    person_id: int
    paid_amount: float
