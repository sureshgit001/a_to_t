from flask import Blueprint, jsonify
from urls import ROUTE_HOME

home_routes = Blueprint("home_routes", __name__)

@home_routes.route(ROUTE_HOME, methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "info": "Flask app for chat service"
    })
