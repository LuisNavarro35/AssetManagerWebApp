from main import db, app  # adjust if your structure is different
from main import User
from werkzeug.security import generate_password_hash

with app.app_context():
    hashed_password = generate_password_hash("adminHWS")
    new_user = User(username="admin", password_hash=hashed_password, is_admin=True)

    db.session.add(new_user)
    db.session.commit()

    print("User created successfully!")