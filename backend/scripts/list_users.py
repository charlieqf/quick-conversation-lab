import sys
import os
import argparse
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User

def list_users():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print(f"{'ID':<38} {'Username':<20} {'Role':<10} {'Active'}")
        print("-" * 80)
        for u in users:
            print(f"{u.id:<38} {u.username:<20} {u.role:<10} {u.is_active}")
    finally:
        db.close()

if __name__ == "__main__":
    list_users()
