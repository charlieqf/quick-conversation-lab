import sys
import os
from sqlalchemy import text

# Add parent dir to path to allow importing app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine

def migrate():
    print(f"Starting migration on: {engine.url}")
    
    with engine.connect() as conn:
        # Check current columns in 'users' table
        # This raw SQL works on both MySQL (TiDB) and SQLite
        
        # 1. Hashed Password
        try:
            conn.execute(text("SELECT hashed_password FROM users LIMIT 1"))
            print("Column 'hashed_password' already exists.")
        except Exception:
            print("Adding 'hashed_password' column...")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN hashed_password VARCHAR(255)"))
                conn.commit()
            except Exception as e:
                print(f"Error adding column: {e}")

        # 2. Role
        try:
            conn.execute(text("SELECT role FROM users LIMIT 1"))
            print("Column 'role' already exists.")
        except Exception:
            print("Adding 'role' column...")
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'"))
                conn.commit()
            except Exception as e:
                print(f"Error adding column: {e}")

        # 3. Is Active
        try:
            conn.execute(text("SELECT is_active FROM users LIMIT 1"))
            print("Column 'is_active' already exists.")
        except Exception:
            print("Adding 'is_active' column...")
            try:
                 # SQLite uses INTEGER for Boolean, MySQL uses TINYINT(1)
                 # Boolean type in SQLA usually maps correctly, but for raw SQL we use BOOLEAN or TINYINT
                 # 'BOOLEAN' works in both generally as alias
                conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                conn.commit()
            except Exception as e:
                print(f"Error adding column: {e}")

        # 4. Update 'admin' user
        try:
            # Check if admin exists
            result = conn.execute(text("SELECT id FROM users WHERE username='admin'"))
            if result.first():
                print("Updating 'admin' user role to 'admin'...")
                conn.execute(text("UPDATE users SET role='admin' WHERE username='admin'"))
                conn.commit()
        except Exception as e:
            print(f"Error updating admin: {e}")

        print("Migration check completed.")

if __name__ == "__main__":
    migrate()
