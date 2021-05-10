from . import db as sdb
from .db import db, init
from .model import Model, Production
from .ui import interactiveOfProduction, display_game
from IPython.display import display

__all__ = [
    'db', 'Model', 'interactiveOfProduction', 'display_game', 'ResultOfProd', 'shopping_list',
    'Production', 'construct', 'add_product', 'consume_product', 'add_recipe',
    'consume_with_recipe', 'produce_with_recipe', 'products',
    'recipes', 'building', 'import_from', 'items', 'init', 'import_all'
]

def shopping_list(buildings_dict):
    return db().shopping_list(buildings_dict)

current_result = None

class ResultOfProd(Model):
    """A wraper for model and interactive display of it"""
    def __init__(self, name = None, margin = 1, db = None, game = None):
        self.game = game
        if db is None:
            db = sdb.db()
        super().__init__(db, name, margin)
        
    def __enter__(self):
        global current_result
        current_result = self
        if self.game and self.name:
            self.game.clear_factory(self)
        return self
    
    def __exit__(self, *args):
        if self.name and self.game:
            self.game.register_factory(self)
        display(interactiveOfProduction(self, None, self.db, self.margin))

def make_function_from_method(m):
    return lambda *args, **kwargs: getattr(current_result, m)(*args, **kwargs)

construct = make_function_from_method('construct')
add_product = make_function_from_method('add_product')
consume_product = make_function_from_method('consume_product')
add_recipe = make_function_from_method('add_recipe')
consume_with_recipe = make_function_from_method('consume_with_recipe')
produce_with_recipe = make_function_from_method('produce_with_recipe')
products = make_function_from_method('products')
recipes = make_function_from_method('recipes')
building = make_function_from_method('building')
import_from = make_function_from_method('import_from')
import_from = make_function_from_method('import_all')

def items(it):
    return current_result[it]