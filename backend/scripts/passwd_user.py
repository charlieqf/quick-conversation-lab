import sys
import os
import argparse
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User
from app.core.security import get_password_hash

def change_password(username, new_password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"Error: User '{username}' not found.")
            return

        user.hashed_password = get_password_hash(new_password)
        db.commit()
        print(f"Password for user '{username}' updated successfully.")
    except Exception as e:
        print(f"Error updating password: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Change user password")
    parser.add_argument("--username", required=True, help="Username")
    parser.add_argument("--password", required=True, help="New Password")
    
    args = parser.parse_args()
    change_password(args.username, args.password)
