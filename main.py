import random
from faker import Faker
from sqlalchemy import create_engine, MetaData, select
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

faker = Faker(['en_US'])
tables = [
    'AspNetUsers',
    'AspNetUserRoles',
    'AspNetRoles',
    'Events',
    'Assistance',
    'Categories',
]

server_images = '/images/'

def get_core():
    url = os.getenv("DB_URL")

    # Engine requires an url like postgresql://ip:port/dbname?password=password&user=user
    engine = create_engine(url)

    Session: sessionmaker = sessionmaker(bind=engine)
    session = Session()

    metadata: MetaData = MetaData()
    metadata.reflect(bind=engine)

    return engine, session, metadata

def validate_db(metadata: MetaData):
    for table in tables:
        if table not in metadata.tables:
            raise ValueError(f"Table {table} does not exist in the database.")

def gen_users(metadata: MetaData, session: Session):
    users_table = metadata.tables[tables[0]]

    for _ in range(200):
        created_at = faker.date()
        user = {
            'Id': faker.uuid4(),
            'CreatedAt': created_at,
            'UpdatedAt': created_at,
            'DeletedAt': None,
            'Active': random.choice([True, False]),
            'UserName': faker.user_name(),
            'NormalizedUserName': faker.user_name().upper(),
            'Email': faker.email(),
            'NormalizedEmail': faker.email().upper(),
            'EmailConfirmed': True,
            'PasswordHash': faker.sha256(),
            'SecurityStamp': faker.uuid4(),
            'ConcurrencyStamp': faker.uuid4(),
            'PhoneNumber': faker.phone_number(),
            'PhoneNumberConfirmed': False,  # This was missing and causing the error
            'TwoFactorEnabled': False,
            'LockoutEnd': None,
            'LockoutEnabled': True,
            'AccessFailedCount': 0,
            'Balance': random.uniform(0.0, 70.0),
        }

        session.execute(users_table.insert().values(user))
    session.commit()

def gen_roles(metadata: MetaData, session: Session):
    # Get tables
    roles_table = metadata.tables[tables[2]]  # AspNetRoles
    user_roles_table = metadata.tables[tables[1]]  # AspNetUserRoles
    users_table = metadata.tables[tables[0]]  # AspNetUsers

    # Get all existing roles from the database
    roles_query = select(roles_table.c.Id)
    existing_roles = [row[0] for row in session.execute(roles_query).fetchall()]

    if not existing_roles:
        print("No roles found in the database to assign to users")
        return

    # Get all users
    users_query = select(users_table.c.Id)
    users = [row[0] for row in session.execute(users_query).fetchall()]

    # Assign roles to users
    for user_id in users:
        # Assign 1-3 random roles to each user
        role_id = random.choice(existing_roles)

        user_role = {
            'UserId': user_id,
            'RoleId': role_id
        }
        session.execute(user_roles_table.insert().values(user_role))

    session.commit()

def gen_categories(metadata: MetaData, session: Session):
    categories_table = metadata.tables[tables[5]]

    for _ in range(10):
        created_at = faker.date()
        category = {
            'Id': faker.uuid4(),
            'Name': faker.name(),
            'CreatedAt': created_at,
            'UpdatedAt': created_at,
            'DeletedAt': None,
            'Active': True
        }

        session.execute(categories_table.insert().values(category))
    session.commit()

def gen_events(metadata: MetaData, session: Session):
    users_table = metadata.tables[tables[0]]
    users_role = metadata.tables[tables[1]]
    roles_table = metadata.tables[tables[2]]

    organizer_role_query = select(roles_table.c.Id).where(roles_table.c.Name == 'Organizer')
    organizer_role_id = session.execute(organizer_role_query).scalar()

    if not organizer_role_id:
        raise ValueError("Organizer role does not exist in the database.")

    organizer_users_query = (
        select(users_table)
        .join(users_role, users_table.c.Id == users_role.c.UserId)
        .where(users_role.c.RoleId == organizer_role_id)
    )

    organizer_users = session.execute(organizer_users_query).fetchall()

    if not organizer_users:
        raise ValueError("No users with the Organizer role found in the database.")

    events_table = metadata.tables[tables[3]]
    events_images = [
        'event_1.jpeg',
        'event_2.jpeg',
        'event_3.jpeg',
        'food-festival.jpg',
        'music-festival.jpg',
        'symphony.jpg',
        'tech-conference.jpeg',
        'art-exhibition.jpeg',
    ]
    for _ in range(100):
        date = faker.date()

        event = {
            'Id': faker.uuid4(),
            'Title': faker.name(),
            'ImageUrl': server_images + random.choice(events_images),
            'Description': faker.text(max_nb_chars=200),
            'Date': faker.date_time_between(start_date='+5d', end_date='+20d'),
            'IsPublished': True,
            'RequireAcceptance': False,
            'LimitParticipants': random.randint(20, 100),
            'CreatedAt': date,
            'UpdatedAt': date,
            'Address': faker.address(),
            'Duration': random.randint(1, 10),
            'Price': random.uniform(5.0, 100.0),
            'OrganizerId': random.choice(organizer_users).Id,
            'CategoryId': random.choice([cat.Id for cat in session.execute(select(metadata.tables[tables[5]].c.Id)).fetchall()]),
            'Active': True
        }

        session.execute(events_table.insert().values(event))
    session.commit()


def gen_data():
    engine, session, metadata = get_core()

    validate_db(metadata)

    gen_users(metadata, session)
    gen_roles(metadata, session)
    gen_categories(metadata, session)
    gen_events(metadata, session)




if __name__ == '__main__':
    gen_data()