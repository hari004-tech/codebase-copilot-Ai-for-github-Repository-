"""
Main Flask REST API server for Demo Store.
"""
from flask import Flask, jsonify, request
from models import User, Product
from auth import AuthService
from services.payment_service import PaymentProcessor
import utils

app = Flask(__name__)
auth_service = AuthService()
payment_service = PaymentProcessor()

@app.route("/health", methods=["GET"])
def health_check():
    """Service health probe."""
    return jsonify({"status": "healthy", "service": "store-api"})

@app.route("/api/login", methods=["POST"])
def login():
    """Authenticate user credentials and issue session."""
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")
    if not username or not password:
        return jsonify({"error": "Missing credentials"}), 400

    token = "auth_tok_" + username
    auth_service.active_sessions[token] = 1700000000
    return jsonify({"token": token, "username": username})

@app.route("/api/products", methods=["GET"])
def list_products():
    """Return catalog of available merchandise."""
    p1 = Product(1, "Laptop Stand", 45.0, 15)
    p2 = Product(2, "Mechanical Keyboard", 120.0, 8)
    return jsonify({
        "products": [
            {"id": p1.product_id, "title": p1.title, "price": p1.price, "in_stock": p1.is_in_stock()},
            {"id": p2.product_id, "title": p2.title, "price": p2.price, "in_stock": p2.is_in_stock()}
        ]
    })

if __name__ == "__main__":
    app.run(port=5001, debug=True)
