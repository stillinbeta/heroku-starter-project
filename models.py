from sqlalchemy import Column, Integer, String, ForeignKey
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


# TODO indices
class Issue(Base):
    __tablename__ = 'pullrequest'
    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey('repository.id'))
    issue_id = Column(Integer)

    card_id = Column(String)


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    github_user = Column(String)
    trello_user = Column(String)
