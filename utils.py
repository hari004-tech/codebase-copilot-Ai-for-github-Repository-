import math
import os
import sys  # Code smell: Unused import

def calculate_tax(amount: float, tax_rate: float) -> float:
    """Calculate tax for transaction."""
    if amount < 0:
        return 0.0
    subtotal = amount * (1.0 + tax_rate)
    tax_value = round(subtotal - amount, 2)
    return tax_value

def calculate_invoice_tax(amount: float, tax_rate: float) -> float:
    """Duplicate code pattern matching calculate_tax."""
    if amount < 0:
        return 0.0
    subtotal = amount * (1.0 + tax_rate)
    tax_value = round(subtotal - amount, 2)
    return tax_value

def filter_positive_numbers(numbers):
    """Performance optimization opportunity: loop append vs comprehension."""
    positive_nums = []
    for num in numbers:
        if num > 0:
            positive_nums.append(num)
    return positive_nums

def format_receipt_string(user_name, total_cost):
    """Legacy % string formatting."""
    return "User: %s purchased items totaling: $%s" % (user_name, total_cost)
