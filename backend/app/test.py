from sqlalchemy import create_engine, text

# DATABASE_URL = "postgresql://internlog_app:postgresinternlog@localhost:5432/internlog_db"
DATABASE_URL="postgresql://postgres:postgres%402008@localhost:5432/InternMonitor_db"

engine = create_engine(DATABASE_URL)

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT current_user, current_database();"))
        print("Connected as:", result.fetchall())
except Exception as e:
    print("Connection failed:", e)
