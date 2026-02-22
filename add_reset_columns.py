from app import app, db
from sqlalchemy import text

def add_columns():
    with app.app_context():
        print("Adding reset_token and reset_token_expiry columns to users table...")
        try:
            # Using session.execute for textual SQL
            # We use a transaction block
            with db.session.begin():
                db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token VARCHAR(100)"))
                db.session.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS reset_token_expiry TIMESTAMP"))
            
            print("Columns added successfully.")
            
        except Exception as e:
            print(f"Error updating database: {e}")
            # If the column already exists, some DBs error even with IF NOT EXISTS if not supported, 
            # but Postgres supports it (user error said psycopg2).
            # If it fails, let's print detailed error.

if __name__ == "__main__":
    add_columns()
