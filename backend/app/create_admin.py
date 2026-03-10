from app.database import SessionLocal
from app.models import User
from app.security import hash_password

def create_admin():
    db = SessionLocal()

    email = "admin@internmonitor.local"
    username = "admin"
    password = "Admin@123"  # CHANGE AFTER FIRST LOGIN

    # Check if admin already exists
    existing = db.query(User).filter(
        (User.email == email) | (User.username == username)
    ).first()

    if existing:
        print("❌ Admin user already exists")
        db.close()
        return

    # Changed: Removed manual 'id' assignment. 
    # The database will auto-increment the Integer primary key.
    admin = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role="admin",
        is_active=True,
        is_verified=True,
    )

    try:
        db.add(admin)
        db.commit()
        print("✅ Admin user created successfully")
        print(f"Username: {username}")
        print(f"Password: {password}")
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to create admin: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
