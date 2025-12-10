from app.database import engine, Base
from sqlalchemy import text

# Drop table manually to force recreation by main.py
def reset_table():
    with engine.connect() as conn:
        print("Dropping session_records table...")
        conn.execute(text("DROP TABLE IF EXISTS session_records"))
        conn.commit()
        print("Dropped.")

if __name__ == "__main__":
    reset_table()
