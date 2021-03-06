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


    def find_or_make_factory(self, s, name):
        for f in self.db_game.factories:
            if f.name == name:
                return f
        f = game_db.Factory(name=name)
        self.db_game.factories.append(f)
        s.add(f)
        s.commit()
        return f

    def register_factory(self, factory:Model, name = None):
        if name is None:
            name = factory.name

        if name is None:
            raise ValueError('Factory has no name')

        with self.session() as s:
            s.add(self.db_game)
            db_fact = self.find_or_make_factory(s, name)
            for result in db_fact.build_result:
                s.delete(result)
            db_fact.build_result = []

            for name in factory.items():
                amount = factory[name] - factory.importation(name)
                if amount == 0:
                    continue
                amount = float(amount)
                item = s.query(game_db.Items).filter(game_db.Items.name == name).one()
                result = game_db.BuildResult(amount = amount)
                item.build_result.append(result)
                db_fact.build_result.append(result)
            s.commit()

    def clear_factory(self, factory:Model, name = None):
        if name is None:
            name = factory.name

        if name is None:
            raise ValueError('Factory has no name')

        with self.session() as s:
            s.add(self.db_game)
            db_fact = self.find_or_make_factory(s, name)
            for result in db_fact.build_result:
                s.delete(result)
            db_fact.build_result = []
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

    def items(self):
        with self.session() as s:
            s.add(self.db_game)
            req = (select(game_db.Items.name)
                .where(game_db.Items.id == game_db.BuildResult.item_id)
                .where(game_db.BuildResult.factory_id == game_db.Factory.id)
                .where(game_db.Factory.game == self.db_game)
            )

            result = s.execute(req).fetchall()

            return (it[0] for it in result)

    

    def items_production(self):
        items_builds = {}

        with self.session() as s:
            s.add(self.db_game)

            for f in s.query(game_db.Factory).filter(game_db.Factory.game == self.db_game).all():
                for it in f.build_result:
                    li = items_builds.setdefault(it.item.name, [])
                    li.append((f.name, it.amount))
                    #print(f"{f.name} as build {it.amount} of {it.item.name}")

            return items_builds

    @property
    def factories(self):
        return Factories(self)

    


class Factories:
    def __init__(self, game: Game) -> None:
        self.game = game

    def __iter__(self):
        with self.game.session() as s:
            s.add(self.game.db_game)
            return (f for f in self.game.db_game.factories)

    def __getitem__(self, name):
        # should use select
        with self.game.session() as s:
            s.add(self.game.db_game)
            for f in self.game.db_game.factories:
                if f.name == name:
                    return f

        raise KeyError(name)