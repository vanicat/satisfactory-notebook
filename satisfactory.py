import satisfactory_db as db
import satisfactory_model as model
import interactive_satisfactory as interactive

from satisfactory_model import (ResultOfProd, 
    construct, add_product, add_node, add_recipe, 
    consume_with_recipe, produce_with_recipe,
    products, recipes, building, items, current_result)

db = db.db

def shopping_list(buildings_dict):
    return db.shopping_list(buildings_dict)