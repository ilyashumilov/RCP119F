from db.config import engine
from db.models import Base
import time


def create_tables():
    Base.metadata.create_all(engine)
    print("Tables created successfully!")


if __name__ == "__main__":
    while True:
        try:
            create_tables()
            break
        except:
            time.sleep(2)
            continue
