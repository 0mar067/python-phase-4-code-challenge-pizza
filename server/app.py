#!/usr/bin/env python3
from models import db, Restaurant, RestaurantPizza, Pizza
from flask_migrate import Migrate
from flask import Flask, request, make_response
from flask_restful import Api, Resource
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.environ.get("DB_URI", f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)


# BEGINNER COMMENT: Resource for handling restaurant list operations
# GET /restaurants - list all restaurants (id, name, address only)
class RestaurantListResource(Resource):
    # BEGINNER COMMENT: Get all restaurants - only return id, name, address
    def get(self):
        restaurants = Restaurant.query.all()
        return [restaurant.to_dict(rules=("-restaurant_pizzas",)) for restaurant in restaurants], 200


# BEGINNER COMMENT: Resource for handling single restaurant operations
# GET /restaurants/<id> - get single restaurant with its pizzas
# DELETE /restaurants/<id> - delete restaurant and cascade delete its pizzas
class RestaurantResource(Resource):
    # BEGINNER COMMENT: Get single restaurant by ID with its restaurant_pizzas
    def get(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant is None:
            return {"error": "Restaurant not found"}, 404
        return restaurant.to_dict(), 200

    # BEGINNER COMMENT: Delete restaurant - this will cascade delete its restaurant_pizzas
    def delete(self, id):
        restaurant = Restaurant.query.get(id)
        if restaurant is None:
            return {"error": "Restaurant not found"}, 404

        db.session.delete(restaurant)
        db.session.commit()
        return {}, 204


# BEGINNER COMMENT: Resource for handling pizza operations
# GET /pizzas - list all pizzas with id, name, ingredients
class PizzaResource(Resource):
    # BEGINNER COMMENT: Get all pizzas - return id, name, ingredients
    def get(self):
        pizzas = Pizza.query.all()
        return [pizza.to_dict(rules=("-restaurant_pizzas",)) for pizza in pizzas], 200


# BEGINNER COMMENT: Resource for handling restaurant-pizza relationships
# POST /restaurant_pizzas - create new restaurant-pizza link with price validation
class RestaurantPizzaResource(Resource):
    # BEGINNER COMMENT: Create new restaurant-pizza relationship
    def post(self):
        data = request.get_json()

        # BEGINNER COMMENT: Validate required fields are present
        if not data or not all(key in data for key in ["price", "pizza_id", "restaurant_id"]):
            return {"errors": ["Missing required fields: price, pizza_id, restaurant_id"]}, 400

        try:
            # BEGINNER COMMENT: Create new RestaurantPizza with validation
            restaurant_pizza = RestaurantPizza(
                price=data["price"],
                pizza_id=data["pizza_id"],
                restaurant_id=data["restaurant_id"]
            )

            # BEGINNER COMMENT: Validate the price (1-30) and check if pizza/restaurant exist
            db.session.add(restaurant_pizza)
            db.session.commit()

            # BEGINNER COMMENT: Return the new RestaurantPizza with nested objects
            return restaurant_pizza.to_dict(), 201

        except ValueError as e:
            # BEGINNER COMMENT: Handle validation errors (like price out of range)
            db.session.rollback()
            return {"errors": ["validation errors"]}, 400
        except Exception as e:
            # BEGINNER COMMENT: Handle other errors (like invalid pizza_id or restaurant_id)
            db.session.rollback()
            return {"errors": ["validation errors"]}, 400


# BEGINNER COMMENT: Register all resources with the API
api.add_resource(RestaurantListResource, "/restaurants")
api.add_resource(RestaurantResource, "/restaurants/<int:id>")
api.add_resource(PizzaResource, "/pizzas")
api.add_resource(RestaurantPizzaResource, "/restaurant_pizzas")


@app.route("/")
def index():
    return "<h1>Code challenge</h1>"


if __name__ == "__main__":
    app.run(port=5555, debug=True)
