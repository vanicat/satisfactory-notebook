#!/usr/bin/env python
# coding: utf-8

# In[1]:

from typing import Callable
from ipywidgets.widgets.widget_box import VBox
from IPython.display import clear_output
import ipywidgets as widgets
import satisfactory_model as sm
import satisfactory_db as sdb
#import matplotlib.pyplot as plt
import sympy
from sympy import nsimplify, simplify
from sympy.parsing.sympy_parser import parse_expr


# In[5]:
def print_recipe(recipe: sdb.Recipe, n: float) -> None:
    print('    ingredient:')
    for ing, q in recipe.ingredient:
        print(f"        {ing}: {simplify(n*q/recipe.time)}/min")
    print('    product')
    for ing, q in recipe.product:
        print(f"        {ing}: {simplify(n*q/recipe.time)}/min")


def interactive_search(search: Callable, add_buttons: list) -> widgets.Widget:
    """search for items or recipe"""

    def on_search(_):
        result = search(search_widget.value)
        choose_options.options = result
    
    search_widget = widgets.Text()
    search_button = widgets.Button(description = "search")
    
    search_button.on_click(on_search)
    search_widget.on_submit(on_search)
    search_box = widgets.HBox((search_widget, search_button))

    buttons = [widgets.Button(description = b["name"]) for b in add_buttons]

    for b, desc in zip(buttons, add_buttons):
        def make_callback(call):
            return lambda _: call(choose_options.value)
        b.on_click(make_callback(desc["callback"]))

    choose_options = widgets.Select()
    #choose_button = widgets.Button(description = "Choose")
    choose_box = widgets.HBox((choose_options, widgets.VBox(buttons)))
    
    # choose_options.on_submit(on_choose)
    #choose_button.on_click(on_choose)
    
    result = widgets.VBox((search_box, choose_box))
    result.choose_options = choose_options
    result.search_box = search_box
    
    return result


# In[20]:
def interactiveOfProduction(result: 'sm.ResultOfProd', name: str, db: 'sdb.SatisfactoryDb', margin=1) -> widgets.Widget:
    buttonLayout = widgets.Layout(width='80%', align='left', align_items='flex-start')

    def log_it(it):
        with log:
            if name:
                print(f"{name}.", end ='')
            print(it)

    def set_quantity(q):
        if isinstance(q, sympy.Number) or isinstance(q, float) or isinstance(q, int):
            quantityItem.value = str(abs(q))
        else:
            quantityItem.value = str(q)

    def get_quantity():
        if (not quantityItem.value) or quantityItem.value.isspace():
            return None
        return parse_expr(quantityItem.value)

    
    def selectItemFun(item, q):
        def callback(_):
            set_quantity(q)
            searchItem.choose_options.options = [ item ]
            searchItem.choose_options.value = item
        return callback
    
    def selectRecipeFun(recipe, n, output):
        def callback(_):
            set_quantity(n)
            searchRecipe.choose_options.options = [ recipe ]
            searchRecipe.choose_options.value = recipe
            if output.collapse:
                output.collapse = False
                with output:
                    print_recipe(sdb.db.recipes_by_name(recipe), n)
            else:
                output.collapse = True
                with output:
                    clear_output()

        
        return callback
    
    def update():
        with output:
            clear_output()
            children = [] 
            for line, item, q in result.products():
                try:
                    if q > margin:
                        button_style=''
                    elif q > -margin:
                        button_style='success'
                    else:
                        button_style='warning'
                except TypeError:
                    button_style='warning'
                
                button = widgets.Button(description = line, layout=buttonLayout, button_style=button_style)
                button.on_click(selectItemFun(item, q))
                children.append(button)
                
            itemBox.children = tuple(children)
            
            print('recipes:')
            children = [] 
            
            for line, recipe, q in result.recipes():
                try:
                    if q > 0:
                        button_style=''
                    else:
                        button_style='success'
                except TypeError:
                    button_style=''

                button = widgets.Button(description = line, layout=buttonLayout, button_style=button_style)
                button_output = widgets.Output()               
                button_box = widgets.VBox([button, button_output])
                button_output.collapse = True
                button.on_click(selectRecipeFun(recipe, q, button_output))
                children.append(button_box)
                
            recipeBox.children = children
            
    def on_add_item(v):
        result.add_product(selectItem.value, get_quantity() or 0)
        log_it(f"add_product({repr(selectItem.value)}, {get_quantity() or 0})")
        update()
            
    def on_add_factory(v):
        result.add_recipe(selectRecipe.value, get_quantity() or 0)
        log_it(f"add_recipe({repr(selectRecipe.value)}, {get_quantity() or 0})")
        update()
        
    def on_consume(_):
        if selectItem.value is not None and selectRecipe.value is not None:
            result.consume_with_recipe(selectRecipe.value, selectItem.value, get_quantity())
            log_it(f"consume_with_recipe({repr(selectRecipe.value)}, {repr(selectItem.value)}, {get_quantity()})")
        update()
            
    def on_produce(_):
        if selectItem.value is not None and selectRecipe.value is not None:
            result.produce_with_recipe(selectRecipe.value, selectItem.value, get_quantity())
            log_it(f"produce_with_recipe({repr(selectRecipe.value)}, {repr(selectItem.value)}, {get_quantity()})")
        update()
        
    def on_construct(_):
        if selectRecipe.value is not None:
            result.construct(selectRecipe.value, get_quantity() or 0)
            log_it(f"construct({repr(selectRecipe.value)}, {get_quantity() or 0})")
        update()

    def on_recipes_by_product(item):
        recipes = db.search_recipes_by_product(item)
        selectRecipe.options = recipes
        
    def on_recipes_by_ingredient(item):
        recipes = db.search_recipes_by_ingredients(item)
        selectRecipe.options = recipes
        
    def on_products_by_recipe(recipe):
        items = db.search_products_by_recipes(recipe)
        selectItem.options = items

    def on_ingredients_by_recipe(recipe):
        items = db.search_ingredients_by_recipes(recipe)
        selectItem.options = items

    def on_recipe_desc(recipe):
        with desc:
            recipe = db.recipes_by_name(recipe)
            print(f"{recipe.name} in {recipe.producedIn}:")
            print_recipe(recipe, 1)
    
    def on_recipe_options_change(_):
        with desc:
            clear_output()

    output = widgets.Output()
    desc = widgets.Output()
    itemBox = widgets.VBox(description = 'items')
    recipeBox = widgets.VBox(description = 'recipe')
    
    log = widgets.Output()
    searchItem = interactive_search(db.search_items_name, add_buttons=[
        {
            'name': 'product',
            'callback': on_recipes_by_product
        },
        {
            'name': 'ingredient',
            'callback': on_recipes_by_ingredient
        }
    ])
    selectItem = searchItem.choose_options
    searchRecipe = interactive_search(db.search_recipes_name, add_buttons=[
        {
            'name': 'product',
            'callback': on_products_by_recipe
        },
        {
            'name': 'ingred',
            'callback': on_ingredients_by_recipe
        },
        {
            'name': 'description',
            'callback': on_recipe_desc
        }
    ])
    selectRecipe = searchRecipe.choose_options

    selectRecipe.observe(on_recipe_options_change, "options")

    quantityItem = widgets.Text(description = "quantity")
    validateAdd = widgets.Button(description='Add')
    validateAdd.on_click(on_add_item)
    
    consumeButton = widgets.Button(description='Consume with recipe')
    consumeButton.on_click(on_consume)
    
    produceButton = widgets.Button(description='Produce with recipe')
    produceButton.on_click(on_produce)
    
    validateRecipe = widgets.Button(description='Add Factory')
    validateRecipe.on_click(on_add_factory)
    
    buildFactory = widgets.Button(description='Build Factory')
    buildFactory.on_click(on_construct)
        
    update()
    
    return widgets.VBox([
        widgets.HBox([
            widgets.VBox([
                widgets.Label(f"Items"),
                searchItem
            ]),
            widgets.VBox([
                widgets.Label(f"Recipes"),
                searchRecipe
            ]),
        ]),
        widgets.HBox([quantityItem, validateAdd, consumeButton, produceButton, validateRecipe, buildFactory]),
        desc,
        widgets.Label("Item produced"),
        itemBox,
        widgets.Label("Recipe used"),
        recipeBox,
        output,
        widgets.Label("logs"),
        log
    ])
