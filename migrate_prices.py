from app import app
from models import db
from sqlalchemy import text, inspect

def migrate():
    with app.app_context():
        print("Starting Postgres/SQLAlchemy migration...")
        
        inspector = inspect(db.engine)
        existing_columns = [c['name'] for c in inspector.get_columns('price_items')]
        
        columns_to_add = [
            ("name", "VARCHAR(120)"),
            ("network", "VARCHAR(20)"),
            ("plan_type", "VARCHAR(40)"),
            ("validity", "VARCHAR(40)")
        ]

        with db.engine.connect() as conn:
            for col_name, col_type in columns_to_add:
                if col_name not in existing_columns:
                    print(f"Adding column {col_name} to price_items...")
                    try:
                        conn.execute(text(f"ALTER TABLE price_items ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                        print(f"Column {col_name} added successfully.")
                    except Exception as e:
                        print(f"Error adding {col_name}: {e}")
                else:
                    print(f"Column {col_name} already exists.")
            
        print("Migration process finished.")

if __name__ == "__main__":
    migrate()
