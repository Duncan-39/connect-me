"""Optional: create a few demo users (password: password123, no photos)."""
from werkzeug.security import generate_password_hash

from app import User, app, db

DEMO = [
    ("alice", "Alice", 27, "Woman", "Climber, coffee snob, dog person."),
    ("bob", "Bob", 31, "Man", "Cooks too much pasta. Plays bad guitar."),
    ("sam", "Sam", 24, "Non-binary", "Board games and long walks."),
    ("dana", "Dana", 35, "Prefer not to say", "Looking for someone to explore new cafes with."),
]

with app.app_context():
    for username, name, age, gender, bio in DEMO:
        if User.query.filter_by(username=username).first():
            continue
        db.session.add(User(username=username, email=f"{username}@example.com",
                            password_hash=generate_password_hash("password123"),
                            display_name=name, age=age, gender=gender, bio=bio))
    db.session.commit()
    print("Demo users ready (password: password123).")
