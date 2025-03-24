from models import Base
from app import engine


def create_db():
    Base.metadata.create_all(engine)


def drop_db():
    Base.metadata.drop_all(engine)


# Make the script take an argument to specify the action
if __name__ == "__main__":
    create_db()
    import sys
    action = sys.argv[1]
    if action == "drop":
        print("Dropping tables")
        drop_db()