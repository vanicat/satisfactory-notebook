from .db import db
from .model import Model, Production
from .ui import interactiveOfProduction
from IPython.display import display

__all__ = [
    'db', 'Model', 'interactiveOfProduction', 'ResultOfProd', 'shopping_list',
    'Production', 'construct', 'add_product', 'consume_product', 'add_recipe',
    'consume_with_recipe', 'produce_with_recipe', 'products',
    'recipes', 'building', 'items'
]

def shopping_list(buildings_dict):
    return db.shopping_list(buildings_dict)

current_result = None

class ResultOfProd(Model):
    """A wraper for model and interactive display of it"""
        
    def __enter__(self):
        global current_result
        current_result = self
        return self
    
    def __exit__(self, *args):
        if self.name is not None:
            name = self.name.strip()
        else:
            name = None
        display(interactiveOfProduction(self, name, db, self.margin))

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

def items(it):
    return current_result[it]