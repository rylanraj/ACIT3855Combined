from models import Base
from app import engine


def create_db():
    Base.metadata.create_all(engine)


def drop_db():
    Base.metadata.drop_all(engine)


# Make the script take an argument to specify the action
if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: manage.py [create|drop]")
        sys.exit(1)

    action = sys.argv[1]
    if action == "create":
        create_db()
    elif action == "drop":
        drop_db()
    else:
        print("Usage: manage.py [create|drop]")
        sys.exit(1)
