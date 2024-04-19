from pydantic import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DataBaseConfig(BaseSettings):
    HOST: str = "postgres"
    USERNAME: str = "postgres"
    PASSWORD: str = "postgres"
    DATABASE: str = "postgres"

    @property
    def database_url(self):
        return f"postgresql://{self.USERNAME}:{self.PASSWORD}@{self.HOST}/{self.DATABASE}"

database_config = DataBaseConfig()

engine = create_engine(database_config.database_url)
Session = sessionmaker(bind=engine)
