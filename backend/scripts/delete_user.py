import sys
import os
import argparse
from sqlalchemy.orm import Session

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from app.models import User

def delete_user(username):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"Error: User '{username}' not found.")
            return

        # Confirm?
        # In a script, maybe force or interactive. We'll just do it for simplicity of requested spec.
        db.delete(user)
        db.commit()
        print(f"User '{username}' deleted.")
    except Exception as e:
        print(f"Error deleting user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete a user")
    parser.add_argument("--username", required=True, help="Username to delete")
    args = parser.parse_args()
    delete_user(args.username)
