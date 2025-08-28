from app.database import SessionLocal
from app.models import User

db = SessionLocal()

new_user = User(
    username="testuser",
    email="testuser@example.com",
    hashed_password="fakehashedpassword",
    role="admin"
)

db.add(new_user)
db.commit()
db.refresh(new_user)
print(f"Created user: {new_user.id} - {new_user.username}")
db.close()

