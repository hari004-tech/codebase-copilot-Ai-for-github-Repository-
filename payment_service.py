"""
Payment Processing Service Module.
"""
import sqlite3

class PaymentProcessor:
    """Handles credit card authorization, ledger updates, and batch settlements."""

    def __init__(self, db_path: str = "store.db"):
        self.db_path = db_path

    # Bug: Mutable default argument batch_items=[]
    def process_batch(self, customer_id: int, batch_items: list = []):
        """Process multiple transactions in a batch."""
        total = 0.0
        for item in batch_items:
            total += item.get("amount", 0)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Bug: SQL Injection vector with f-string formatting
        cursor.execute(f"SELECT balance FROM accounts WHERE customer_id = '{customer_id}'")
        row = cursor.fetchone()

        if row:
            current_balance = row[0]
            if current_balance >= total:
                # Deduct
                cursor.execute(f"UPDATE accounts SET balance = balance - {total} WHERE customer_id = '{customer_id}'")
                conn.commit()
                conn.close()
                return True
        conn.close()
        return False
