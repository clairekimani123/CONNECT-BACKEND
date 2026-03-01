from server.app import app
from server.config import db
from server.models import Volunteer, Project, Donation, User
from faker import Faker
import random

fake = Faker()

donation_types = ["money", "clothes", "food", "other"]
projects_data = [
    {"type": "Health", "image": "https://picsum.photos/id/33/1170/780"},
    {"type": "Education", "image": "https://picsum.photos/id/159/1170/780"},
    {"type": "Environment", "image": "https://picsum.photos/id/292/1170/780"},
    {"type": "Community", "image": "https://picsum.photos/id/338/1170/780"},
    {"type": "Emergency", "image": "https://picsum.photos/id/244/1170/780"},
]

with app.app_context():
    print("Seeding database...")

    db.drop_all()
    db.create_all()

    # Create Users
    print("Creating Users...")
    users = []
    for _ in range(9):
        user = User(
            email=fake.unique.email(),
            first_name=fake.first_name(),
            last_name=fake.last_name()
        )
        user.password_hash = "password123"
        users.append(user)

    admin_user = User(
        email=fake.unique.email(),
        first_name=fake.first_name(),
        last_name=fake.last_name(),
        role="admin"
    )
    admin_user.password_hash = "adminpass"
    users.append(admin_user)

    db.session.add_all(users)
    db.session.commit()

    # Create Donations
    print("Creating Donations...")
    donations = []
    non_money_count = 0

    for user in users[:10]:
        dtype = random.choice(donation_types)
        if dtype != "money":
            non_money_count += 1

        donation = Donation(
            type=dtype,
            group=fake.word().capitalize() + " Group",
            details=fake.sentence() if dtype != "money" else None,
            phone_number=fake.msisdn()[:10],
            amount=random.randint(100, 5000) if dtype == "money" else None,
            user_id=user.id
        )
        donations.append(donation)

    while len(donations) < 15:
        dtype = random.choice(donation_types)
        
        if dtype != "money" and non_money_count >= 5:
            dtype = "money"
        if dtype != "money":
            non_money_count += 1

        donation = Donation(
            type=dtype,
            group=fake.word().capitalize() + " Group",
            details=fake.sentence() if dtype != "money" else None,
            phone_number=fake.msisdn()[:10],
            amount=random.randint(100, 5000) if dtype == "money" else None,
            user_id=random.choice(users[:10]).id
        )
        donations.append(donation)

    db.session.add_all(donations)
    db.session.commit()

    # Create Projects
    print("Creating Projects...")
    projects = []
    for item in projects_data:
        project = Project(
            type=item["type"],
            image_url=item["image"],
            description=fake.text(max_nb_chars=150)
        )
        projects.append(project)

    db.session.add_all(projects)
    db.session.commit()

    print("Creating Volunteers...")
    volunteers = []
    for _ in range(10):
        selected_user = random.choice(users[:10]) 
        selected_project = random.choice(projects)

        volunteer = Volunteer(
            event_id=selected_project.id,
            user_id=selected_user.id,
            email=selected_user.email
        )
        volunteers.append(volunteer)

    db.session.add_all(volunteers)
    db.session.commit()

    print("Seeding complete!")
