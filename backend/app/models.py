from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base


# ===== Master catalog: products =====

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    unit = Column(String, default="г")               # «кг», «пачка», «банка», «г», ...
    grams_in_package = Column(Float, default=1000.0) # 0 если не применимо (специи, кофе...)
    price_per_unit = Column(Float, default=0.0)      # ₽ за упаковку
    storage_term = Column(String, default="Долгосрочный")  # «Краткосрочный» / «Долгосрочный»
    category = Column(String, default="прочее")            # «овощи-фрукты», «мясо», «молочка», «крупы», «приправы», «прочее»
    product_link = Column(String, default="")


# ===== Catalog: dishes =====

class Dish(Base):
    __tablename__ = "dishes"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    ingredients = relationship(
        "DishIngredient",
        back_populates="dish",
        cascade="all, delete-orphan",
        order_by="DishIngredient.id",
    )


class DishIngredient(Base):
    __tablename__ = "dish_ingredients"
    id = Column(Integer, primary_key=True)
    dish_id = Column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    grams_per_portion = Column(Float, default=0.0)

    dish = relationship("Dish", back_populates="ingredients")
    product = relationship("Product")


# ===== People =====

class Person(Base):
    __tablename__ = "people"
    id = Column(Integer, primary_key=True)
    full_name = Column(String, nullable=False)
    role = Column(String, default="")
    present = Column(Boolean, default=True)


# ===== Event (smeta) =====

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    markup_percent = Column(Float, default=0.0)

    days = relationship(
        "EventDay",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="EventDay.sort_order",
    )
    misc_items = relationship(
        "EventMiscItem",
        cascade="all, delete-orphan",
        order_by="EventMiscItem.id",
    )
    misc_participants = relationship(
        "EventMiscParticipant",
        cascade="all, delete-orphan",
    )
    payments = relationship(
        "EventPayment",
        cascade="all, delete-orphan",
    )


class EventDay(Base):
    __tablename__ = "event_days"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    short_name = Column(String, default="")
    sort_order = Column(Integer, default=0)

    event = relationship("Event", back_populates="days")
    meals = relationship(
        "EventMeal",
        back_populates="day",
        cascade="all, delete-orphan",
        order_by="EventMeal.sort_order",
    )


class EventMeal(Base):
    __tablename__ = "event_meals"
    id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey("event_days.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)
    # Если задано — берём это число вместо count(participants). Удобно для забросов с большим числом
    # людей, где имена не нужны (например, общий заезд участников).
    portions_override = Column(Integer, nullable=True)

    day = relationship("EventDay", back_populates="meals")
    dishes = relationship(
        "EventDish",
        back_populates="meal",
        cascade="all, delete-orphan",
        order_by="EventDish.sort_order",
    )
    participants = relationship(
        "EventMealParticipant",
        cascade="all, delete-orphan",
    )


class EventDish(Base):
    __tablename__ = "event_dishes"
    id = Column(Integer, primary_key=True)
    meal_id = Column(Integer, ForeignKey("event_meals.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    sort_order = Column(Integer, default=0)

    meal = relationship("EventMeal", back_populates="dishes")
    ingredients = relationship(
        "EventDishIngredient",
        back_populates="dish",
        cascade="all, delete-orphan",
        order_by="EventDishIngredient.id",
    )


class EventDishIngredient(Base):
    __tablename__ = "event_dish_ingredients"
    id = Column(Integer, primary_key=True)
    dish_id = Column(Integer, ForeignKey("event_dishes.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    grams_per_portion = Column(Float, default=0.0)
    taken = Column(Boolean, default=False)

    dish = relationship("EventDish", back_populates="ingredients")
    product = relationship("Product")


class EventMealParticipant(Base):
    __tablename__ = "event_meal_participants"
    id = Column(Integer, primary_key=True)
    meal_id = Column(Integer, ForeignKey("event_meals.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint("meal_id", "person_id", name="uniq_meal_person"),)


class EventMiscItem(Base):
    """Прочее / РАЗНОЕ: продукт + количество (в единицах продукта)."""
    __tablename__ = "event_misc_items"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity = Column(Float, default=0.0)  # уже в единицах продукта (упаковки / банки / кг)
    taken = Column(Boolean, default=False)

    product = relationship("Product")


class EventMiscParticipant(Base):
    __tablename__ = "event_misc_participants"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    __table_args__ = (UniqueConstraint("event_id", "person_id", name="uniq_event_person_misc"),)


class EventPayment(Base):
    __tablename__ = "event_payments"
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(Integer, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    paid_amount = Column(Float, default=0.0)
    __table_args__ = (UniqueConstraint("event_id", "person_id", name="uniq_event_person_pay"),)
