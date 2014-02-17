import sqlalchemy
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

def create_tables(engine):
    Base.metadata.create_all(engine)

class Repository(Base):
    __tablename__ = 'repository'

    id = Column(Integer, primary_key=True, autoincrement=True)
    owner = Column(String)
    repo = Column(String)
    board = Column(String)
    new_list = Column(String)
