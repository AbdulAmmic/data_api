import sqlite3
import os

DEFAULT_DB_FILE = "instance/app.db"

def migrate():
    db_path = DEFAULT_DB_FILE
    
    if not os.path.exists(db_path):
        print(f"No database file found at {db_path}")
        if os.path.exists("app.db"):
             db_path = "app.db"
             print(f"Found at {db_path}")
        else:
             print("Aborting migration: database not found.")
             return

    print(f"Migrating {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if transaction_pin_hash exists in users
        cursor.execute("PRAGMA table_info(users)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "transaction_pin_hash" not in columns:
            print("Adding transaction_pin_hash to users...")
            cursor.execute("ALTER TABLE users ADD COLUMN transaction_pin_hash VARCHAR(255)")
            conn.commit()
            print("Done.")
        else:
            print("transaction_pin_hash already exists.")

    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
