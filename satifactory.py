from satisfactory_model import (db, ResultOfProd, 
    construct, add_product, add_node, add_recipe, 
    consume_with_recipe, produce_with_recipe,
    products, recipes, building, items, current_result)


def shopping_list(buildings_dict):
    return db.shopping_list(buildings_dict)