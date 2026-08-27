"""
Seed the database with demo data for local development ONLY.

This script refuses to run when APP_ENV=production, so it can never
accidentally create a demo user in a live deployment.

Usage:
    python scripts_seed_demo.py
"""
import random
import sys
from datetime import date, timedelta
from decimal import Decimal

sys.path.insert(0, ".")

from app.core.config import settings  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.account import Account, AccountType  # noqa: E402
from app.models.budget import Budget  # noqa: E402
from app.models.category import CategoryType  # noqa: E402
from app.models.transaction import Transaction, TransactionType  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.category_service import seed_default_categories  # noqa: E402

DEMO_EMAIL = "demo@finora.app"
DEMO_PASSWORD = "DemoPass123"


def main():
    if settings.is_production:
        print("Refusing to seed demo data: APP_ENV=production.")
        sys.exit(1)

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if existing:
            print(f"Demo user {DEMO_EMAIL} already exists. Skipping.")
            return

        user = User(
            full_name="Demo User",
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        seed_default_categories(db, user.id)
        db.commit()

        accounts = [
            Account(user_id=user.id, name="HBL Bank", account_type=AccountType.bank,
                     opening_balance=Decimal("150000.00"), current_balance=Decimal("150000.00"), currency="PKR"),
            Account(user_id=user.id, name="Cash Wallet", account_type=AccountType.cash,
                     opening_balance=Decimal("25000.00"), current_balance=Decimal("25000.00"), currency="PKR"),
            Account(user_id=user.id, name="Meezan Savings", account_type=AccountType.savings,
                     opening_balance=Decimal("300000.00"), current_balance=Decimal("300000.00"), currency="PKR"),
        ]
        db.add_all(accounts)
        db.commit()
        for a in accounts:
            db.refresh(a)

        expense_categories = {c.name: c for c in user.categories if c.type == CategoryType.expense}
        income_categories = {c.name: c for c in user.categories if c.type == CategoryType.income}

        today = date.today()
        random.seed(42)

        # Generate ~3 months of realistic transaction history.
        for month_offset in range(3, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=month_offset * 30)

            salary_txn = Transaction(
                user_id=user.id, account_id=accounts[0].id,
                category_id=income_categories["Salary"].id,
                transaction_type=TransactionType.income,
                amount=Decimal("120000.00"),
                description="Monthly salary",
                transaction_date=month_date.replace(day=1),
            )
            db.add(salary_txn)
            accounts[0].current_balance += salary_txn.amount

            for name, amount_range in [
                ("Rent", (35000, 35000)),
                ("Groceries", (8000, 15000)),
                ("Utilities", (4000, 9000)),
                ("Transport", (3000, 7000)),
                ("Food", (5000, 12000)),
                ("Entertainment", (2000, 6000)),
            ]:
                amount = Decimal(random.randint(*amount_range))
                # Keep the demo realistic: routine spending comes from the main
                # bank account; only small, occasional purchases hit petty cash.
                if name in ("Entertainment",) and random.random() < 0.4:
                    account = accounts[1]
                else:
                    account = accounts[0]
                txn = Transaction(
                    user_id=user.id, account_id=account.id,
                    category_id=expense_categories[name].id,
                    transaction_type=TransactionType.expense,
                    amount=amount,
                    description=f"{name} payment",
                    transaction_date=month_date + timedelta(days=random.randint(1, 27)),
                )
                db.add(txn)
                account.current_balance -= amount

        db.commit()

        budgets = [
            Budget(user_id=user.id, category_id=expense_categories["Food"].id,
                     amount=Decimal("15000.00"), month=today.month, year=today.year),
            Budget(user_id=user.id, category_id=expense_categories["Groceries"].id,
                     amount=Decimal("18000.00"), month=today.month, year=today.year),
            Budget(user_id=user.id, category_id=expense_categories["Entertainment"].id,
                     amount=Decimal("8000.00"), month=today.month, year=today.year),
        ]
        db.add_all(budgets)
        db.commit()

        print(f"Demo user created: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"Accounts: {[a.name for a in accounts]}")
        print("3 months of transaction history and this month's budgets seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
