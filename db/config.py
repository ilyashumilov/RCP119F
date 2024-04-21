from pydantic import BaseSettings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class DataBaseConfig(BaseSettings):
    HOST: str = "postgres"
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    @property
    def database_url(self):
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.HOST}/{self.POSTGRES_DB}"

database_config = DataBaseConfig()

engine = create_engine(database_config.database_url)
Session = sessionmaker(bind=engine)
