"""
seed.py — development database seeder

IMPORTANT RULES:
  1. NEVER run this against production — it is for local development only.
  2. NEVER call this from a deploy script or startup command.
  3. Run manually when you need a fresh local environment:
       python seed.py

The key difference from the old version: this file NO LONGER calls
db.drop_all(). Think of the old version like a bulldozer that flattened
everything before building — useful for a blank lot, destructive on an
occupied building. This version is like a careful decorator who only
touches empty rooms and leaves furnished ones exactly as they are.
"""

from server.app import app
from server.config import db
from server.models import Volunteer, Project, Donation, User
from faker import Faker
import random

fake = Faker()

donation_types = ["money", "clothes", "food", "other"]

# Real project data — descriptions and targets match what the live site shows.
# No more faker.text() for descriptions — if we're seeding, we seed properly.
projects_data = [
    {
        "type": "Health",
        "image": "https://picsum.photos/id/33/1170/780",
        "target_amount": 500000,
        "description": (
            "Delivering free medical outreach across urban and rural Kenya, "
            "including health screenings, maternal care support, and medicine "
            "distribution to underserved communities in Nairobi's informal "
            "settlements and remote counties. We partner with local clinics and "
            "community health workers to ensure no one is turned away due to cost."
        ),
    },
    {
        "type": "Education",
        "image": "https://picsum.photos/id/159/1170/780",
        "target_amount": 350000,
        "description": (
            "Keeping children in school by funding school fees, uniforms, books, "
            "and sanitary supplies for learners from low-income families across Kenya. "
            "We work directly with public primary and secondary schools in Kibera, "
            "Mathare, Turkana, and Kilifi to identify children at risk of dropping out."
        ),
    },
    {
        "type": "Environment",
        "image": "https://picsum.photos/id/292/1170/780",
        "target_amount": 280000,
        "description": (
            "Restoring Kenya's natural ecosystems through tree planting, river "
            "clean-up drives, and community-led conservation education in both urban "
            "neighbourhoods and rural farmland. We have planted over 8,000 trees "
            "across 12 counties and trained 400+ community environmental champions."
        ),
    },
    {
        "type": "Community",
        "image": "https://picsum.photos/id/338/1170/780",
        "target_amount": 420000,
        "description": (
            "Strengthening the social fabric of vulnerable communities through skills "
            "training, mental health awareness, women's empowerment programs, and youth "
            "mentorship. We run regular community forums, vocational workshops, and peer "
            "support groups that give people practical tools to improve their circumstances."
        ),
    },
    {
        "type": "Emergency",
        "image": "https://picsum.photos/id/244/1170/780",
        "target_amount": 600000,
        "description": (
            "Responding rapidly when disaster strikes — floods, drought, fire, "
            "displacement. Our emergency response team mobilises within 48 hours to "
            "deliver food parcels, clean water, temporary shelter, and trauma support "
            "to affected families across Kenya. Funds raised here are deployed immediately."
        ),
    },
    {
        "type": "Sports",
        "image": "https://picsum.photos/id/416/1170/780",
        "target_amount": 180000,
        "description": (
            "Using sport as a tool for youth development, mental health, and community "
            "cohesion in underserved areas. We fund football pitches, athletics equipment, "
            "coaching programs, and inter-county tournaments for young people aged 10-24 "
            "who would otherwise have no safe space for physical activity."
        ),
    },
]


def seed_users():
    """Only create users if the table is empty."""
    if User.query.count() > 0:
        print("  Users already exist — skipping.")
        return []

    print("  Creating users...")
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
        email="admin@hopeconnect.org",
        first_name="Admin",
        last_name="HopeConnect",
        role="admin"
    )
    admin_user.password_hash = "adminpass"
    users.append(admin_user)

    db.session.add_all(users)
    db.session.commit()
    print(f"  Created {len(users)} users.")
    return users


def seed_projects():
    """
    For each project type, update if it already exists (preserving its id
    and any donations linked to it), or create it if it doesn't exist yet.
    This is the safe pattern — upsert, not replace.
    """
    print("  Seeding projects...")
    projects = []
    for item in projects_data:
        existing = Project.query.filter_by(type=item["type"]).first()
        if existing:
            # Update real content but never touch the id — donation foreign
            # keys point at this id, changing it would orphan real donations.
            existing.description = item["description"]
            existing.target_amount = item["target_amount"]
            existing.image_url = item["image"]
            projects.append(existing)
            print(f"  Updated existing project: {item['type']}")
        else:
            project = Project(
                type=item["type"],
                image_url=item["image"],
                description=item["description"],
                target_amount=item["target_amount"],
            )
            db.session.add(project)
            projects.append(project)
            print(f"  Created new project: {item['type']}")

    db.session.commit()
    return projects


def seed_donations(users, projects):
    """Only create donations if the table is empty."""
    if Donation.query.count() > 0:
        print("  Donations already exist — skipping.")
        return

    if not users or not projects:
        print("  No users or projects to link donations to — skipping.")
        return

    print("  Creating donations...")
    donations = []
    for user in users[:10]:
        dtype = random.choice(donation_types)
        donation = Donation(
            type=dtype,
            group=random.choice([p.type for p in projects]),
            details=fake.sentence() if dtype != "money" else "HopeConnect Donation",
            phone_number=fake.msisdn()[:10],
            amount=random.randint(100, 5000) if dtype == "money" else None,
            user_id=user.id,
            project_id=random.choice(projects).id,
            status='completed',
        )
        donations.append(donation)

    db.session.add_all(donations)
    db.session.commit()
    print(f"  Created {len(donations)} donations.")


def seed_volunteers(users, projects):
    """Only create volunteers if the table is empty."""
    if Volunteer.query.count() > 0:
        print("  Volunteers already exist — skipping.")
        return

    if not users or not projects:
        print("  No users or projects to link volunteers to — skipping.")
        return

    print("  Creating volunteers...")
    volunteers = []
    seen = set()  # prevent duplicate user+project combinations
    for _ in range(10):
        user = random.choice(users[:10])
        project = random.choice(projects)
        key = (user.id, project.id)
        if key in seen:
            continue
        seen.add(key)
        volunteer = Volunteer(
            event_id=project.id,
            user_id=user.id,
            email=user.email,
            full_name=f"{user.first_name} {user.last_name}",
            phone_number="0700000000",
            availability="flexible",
        )
        volunteers.append(volunteer)

    db.session.add_all(volunteers)
    db.session.commit()
    print(f"  Created {len(volunteers)} volunteers.")


with app.app_context():
    print("\nSeeding database...")
    print("NOTE: This script never drops existing data.")
    print("If you need a completely fresh database, manually run:")
    print("  flask shell → db.drop_all() → db.create_all()\n")

    db.create_all()  # create tables if they don't exist, safe to run always

    users = seed_users()
    if not users:
        users = User.query.all()  # use existing users for other seeds

    projects = seed_projects()
    seed_donations(users, projects)
    seed_volunteers(users, projects)

    print("\nSeeding complete!")
    print(f"  Users:      {User.query.count()}")
    print(f"  Projects:   {Project.query.count()}")
    print(f"  Donations:  {Donation.query.count()}")
    print(f"  Volunteers: {Volunteer.query.count()}")