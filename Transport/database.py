from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

import settings

engine = create_engine(settings.constr)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    #Connect to the db, and create the tables.
    #Most useful when importing within IDLE and executing in a standalone manner.
    import models
    Base.metadata.create_all(engine)

if __name__ == '__main__':
    msg = 'Database code for use with the NoticeMe Web App.'
    print msg