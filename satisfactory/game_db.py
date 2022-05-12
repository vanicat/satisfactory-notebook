from typing import Counter
from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql.coercions import ColumnArgumentOrKeyImpl

Base = declarative_base()

class Game(Base):
    __tablename__ = "game"
    id = Column(Integer, primary_key=True)
    name = Column(String)

class Factory(Base):
    __tablename__ = "factory"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    game_id = Column(Integer, ForeignKey('game.id'))
    game = relationship(Game, backref=backref('factories', uselist = True))
    
    def delete(self, session):
        """delete the factories and its build result"""
        for br in self.build_result:
            session.delete(br)
        session.delete(self)

class Items(Base):
    __tablename__ = 'items'
    id = Column(Integer, primary_key = True)
    slug = Column(String)
    name = Column( String)
    className = Column(String)
    sinkPoints = Column(Integer)
    description = Column(String)
    stackSize = Column(Integer)
    energyValue = Column(Integer)
    radioactiveDecay = Column(Integer)
    liquid = Column(Boolean)

class BuildResult(Base):
    __tablename__ = "build_result"
    id = Column(Integer, primary_key=True)
    factory_id = Column(Integer, ForeignKey('factory.id'))
    factory = relationship(Factory, backref=backref('build_result', uselist = True))
    amount = Column(Float)
    item_id = Column(Integer, ForeignKey('items.id'))
    item = relationship(Items, backref=backref('build_result', uselist = True))

