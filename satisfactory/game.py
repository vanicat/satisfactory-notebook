from . import game_db
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from .model import Model
from .db import default_engine
from sqlalchemy import select

class Game():
    def __init__(self, name, engine = None):
        if engine is None:
            engine = default_engine()
        self.session = sessionmaker()
        self.session.configure(bind=engine)

        with self.session() as s:
            game_db.Base.metadata.create_all(engine)

            query = s.query(game_db.Game).filter(game_db.Game.name == name)
            if query.count() == 0:
                self.db_game = game_db.Game(name=name)
                s.add(self.db_game)
            else:
                self.db_game = query.one()
            print(self.db_game, self.db_game.name)
            s.commit()


    def register_factory(self, factory:Model, name = None):
        def find_or_make_factory(s, name):
            for f in self.db_game.factories:
                if f.name == name:
                    return f
            f = game_db.Factory(name=name)
            self.db_game.factories.append(f)
            s.add(f)
            s.commit()
            return f

        if name is None:
            name = factory.name

        if name is None:
            raise ValueError('Factory has no name')

        with self.session() as s:
            s.add(self.db_game)
            db_fact = find_or_make_factory(s, name)
            for result in db_fact.build_result:
                s.delete(result)
            db_fact.build_result = []

            items_set = { name for name in factory.needed }
            items_set = items_set.union(name for name in factory.available)

            for name in items_set:
                amount = factory[name]
                if amount == 0:
                    continue
                amount = float(amount)
                item = s.query(game_db.Items).filter(game_db.Items.name == name).one()
                result = game_db.BuildResult(amount = amount)
                item.build_result.append(result)
                db_fact.build_result.append(result)
            s.commit()

    def clear_all(self):
        """delete every factory for this game"""
        with self.session() as s:
            s.add(self.db_game)
            for factory in self.db_game.factories:
                for result in factory.build_result:
                    s.delete(result)
                s.delete(factory)
            s.commit()

    def delete(self):
        """Delete this game from db"""
        self.clear_all()
        with self.session() as s:
            s.add(self.db_game)
            s.delete(self.db_game)
            s.commit()
        
    def  __getitem__(self, name):
        with self.session() as s:
            item = s.query(game_db.Items).filter(game_db.Items.name == name).one()
            s.add(self.db_game)
            req = (select(func.sum(game_db.BuildResult.amount))
                .where(game_db.BuildResult.item == item)
                .where(game_db.BuildResult.factory_id == game_db.Factory.id)
                .where(game_db.Factory.game == self.db_game)
            )

            result = s.execute(req).fetchone()

            if result[0] is None:
                return 0

            return result[0]

    def factories(self):
        with self.session() as s:
            s.add(self.db_game)
            return [f.name for f in self.db_game.factories]

        
