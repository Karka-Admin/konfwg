from konfwg.database.base import Base
from konfwg.database.engine import engine
from konfwg.database import models

def init_database() -> None:
    Base.metadata.create_all(bind=engine)
    