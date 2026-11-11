"""
Database Models for Ecommerce Demo Application.
"""

class User:
    """Represents an application user account with permissions and profile."""
    def __init__(self, user_id: int, username: str, email: str, role: str = "customer"):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.role = role

    def get_display_name(self) -> str:
        """Return formatted display name."""
        return f"{self.username} ({self.role})"

    def is_admin(self) -> bool:
        """Check if user has administrative rights."""
        return self.role == "admin"


class Product:
    """Represents a store catalog inventory item."""
    def __init__(self, product_id: int, title: str, price: float, stock_quantity: int):
        self.product_id = product_id
        self.title = title
        self.price = price
        self.stock_quantity = stock_quantity

    def is_in_stock(self) -> bool:
        """Check inventory availability."""
        return self.stock_quantity > 0

    def deduct_inventory(self, quantity: int) -> bool:
        """Deduct purchased units from inventory."""
        if quantity <= self.stock_quantity:
            self.stock_quantity -= quantity
            return True
        return False
