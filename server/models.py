from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.orm import validates
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy_serializer import SerializerMixin

metadata = MetaData(
    naming_convention={
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",# Foreign key
        "pk": "pk_%(table_name)s"  # Primary key
    }
)

db = SQLAlchemy(metadata=metadata)


class Restaurant(db.Model, SerializerMixin):
    #  This model represents a restaurant that can serve multiple pizzas
    __tablename__ = "restaurants"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    address = db.Column(db.String)

    #  One-to-many relationship with RestaurantPizza
    # A restaurant can have many restaurant_pizzas (menu items)
    # When a restaurant is deleted, all its restaurant_pizzas are deleted too (cascade)
    restaurant_pizzas = db.relationship("RestaurantPizza", back_populates="restaurant", cascade="all, delete")

    #  Serialization rules to control what data is included when converting to dict
    # We include restaurant_pizzas but only show pizza_id in each item to avoid deep recursion
    serialize_rules = ("-restaurant_pizzas.restaurant", "-restaurant_pizzas.pizza")

    def __repr__(self):
        return f"<Restaurant {self.name}>"


class Pizza(db.Model, SerializerMixin):
    #  This model represents a pizza that can be served at multiple restaurants
    __tablename__ = "pizzas"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    ingredients = db.Column(db.String)

    #  One-to-many relationship with RestaurantPizza
    # A pizza can be served at many restaurants through restaurant_pizzas
    # When a pizza is deleted, all its restaurant_pizzas are deleted too (cascade)
    restaurant_pizzas = db.relationship("RestaurantPizza", back_populates="pizza", cascade="all, delete")

    #  Simple serialization - just include basic pizza info
    serialize_rules = ("-restaurant_pizzas.pizza", "-restaurant_pizzas.restaurant")

    def __repr__(self):
        return f"<Pizza {self.name}, {self.ingredients}>"


class RestaurantPizza(db.Model, SerializerMixin):
    #  This model represents the link between restaurants and pizzas
    # It stores which pizzas are available at which restaurants and their prices
    __tablename__ = "restaurant_pizzas"

    id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Integer, nullable=False)

    #  Foreign key to restaurant table
    restaurant_id = db.Column(db.Integer, db.ForeignKey("restaurants.id"))
    #  Foreign key to pizza table
    pizza_id = db.Column(db.Integer, db.ForeignKey("pizzas.id"))

    #  Relationships to both parent models
    restaurant = db.relationship("Restaurant", back_populates="restaurant_pizzas")
    pizza = db.relationship("Pizza", back_populates="restaurant_pizzas")

    #  Serialization rules for RestaurantPizza
    # We include the full pizza and restaurant objects (not just IDs)
    # This is what the POST response wants
    serialize_rules = ("-restaurant.restaurant_pizzas", "-pizza.restaurant_pizzas")

    #  Validation method to ensure price is between 1 and 30 inclusive
    @validates("price")
    def validate_price(self, key, price):
        #  Check if price is provided
        if price is None:
            raise ValueError("Price is required")
        #  Check if price is within valid range
        if not (1 <= price <= 30):
            raise ValueError("Price must be between 1 and 30 inclusive")
        return price

    def __repr__(self):
        return f"<RestaurantPizza ${self.price}>"
