from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension

# DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
DB_URI = 'sqlite:///stuff.db'

Session = sessionmaker(autocommit=False,
                       autoflush=False,
                       bind=create_engine(DB_URI))
session = scoped_session(Session)
Base = declarative_base()

# Note Model
class Note(Base):
    __tablename__ = 'notes'
    id      = Column(Integer, primary_key=True)
    title    = Column(String(50))
    description     = Column(String(50))
    created_at     = Column(String(50))
    created_by     = Column(String(50))
    priority     = Column(Integer)

    def __init__(self, title, description, created_at ,created_by, priority):
        self.title = title
        self.description = description
        self.created_at = created_at
        self.created_by = created_by
        self.priority = priority

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def to_json(self):
        to_serialize = ['id', 'title', 'description', 'created_at', 'created_by', 'priority']
        d = {}
        for attr_name in to_serialize:
            d[attr_name] = getattr(self, attr_name)
        return d

# creates database
if __name__ == "__main__":

    engine = create_engine(DB_URI)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)