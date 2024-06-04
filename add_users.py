from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create the database
    db.create_all()

    # Add a teacher
    teacher = User(email='teacher@vemanait.edu.in', password=generate_password_hash('password'), role='teacher')
    db.session.add(teacher)

    # Add a student
    student = User(email='student@vemanait.edu.in', password=generate_password_hash('password'), role='student')
    db.session.add(student)

    # Commit the changes
    db.session.commit()

    print('Users added successfully.')
