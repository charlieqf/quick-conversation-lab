import sys
import os
import argparse
from sqlalchemy.orm import Session

# Add parent dir to path to allow importing app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import User
from app.core.security import get_password_hash

def create_user(username, password, is_admin):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"Error: User '{username}' already exists.")
            return

        role = "admin" if is_admin else "user"
        hashed = get_password_hash(password)
        
        user = User(
            username=username, 
            hashed_password=hashed,
            role=role,
            is_active=True,
            settings={"theme": "light"}
        )
        db.add(user)
        db.commit()
        print(f"User '{username}' created successfully. Role: {role}")
    except Exception as e:
        print(f"Error creating user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a new user")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--password", required=True, help="Password")
    parser.add_argument("--admin", action="store_true", help="Set role to admin")
    
    args = parser.parse_args()
    create_user(args.username, args.password, args.admin)
