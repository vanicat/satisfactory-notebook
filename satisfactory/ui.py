#!/usr/bin/env python
# coding: utf-8

# In[1]:

from typing import Callable
from ipywidgets.widgets.widget_box import VBox
from IPython.display import clear_output
import ipywidgets as widgets

from satisfactory.game import Game
from .model import Production, Model
from .db import Recipe, SatisfactoryDb
#import matplotlib.pyplot as plt
import sympy
from sympy import nsimplify, simplify
from sympy.parsing.sympy_parser import parse_expr


# In[5]:
def print_recipe(recipe: Recipe, n: float) -> None:
    print('    ingredients:')
    for ing, q in recipe.ingredients:
        print(f"        {ing}: {simplify(n*q/recipe.time)}/min")
    print('    products')
    for ing, q in recipe.products:
        print(f"        {ing}: {simplify(n*q/recipe.time)}/min")


def make_items_list(label_text, items, setter, update): 
    def make_observer(item):
        def observer(event):
            if event['type'] == 'change':
                setter(item, parse_expr(event['new']))
                update()
        return observer
    
    label = widgets.Label(label_text)
    widget_list = [label]
    for item, q in items:
        text = widgets.Text(description = item, value = str(q))
        text.layout.margin = "5px"
        text.style.description_width = 'initial'
        text.continuous_update = False
        text.observe(make_observer(item), names="value")
        widget_list.append(text)
    box = widgets.VBox(widget_list)
    box.layout.border = "solid black 2px"
    box.layout.margin = '0px 10px 4px 10px'
    return box

def interactive_production_display(production: 'Production', update):
    def change_planned(event):
        if event['type'] == 'change':
            production.set(parse_expr(event['new']))
            update()

    num_text = widgets.Text(value=str(production.plan))
    num_text.continuous_update = False
    num_text.observe(change_planned, names="value")

    num_box = widgets.VBox([widgets.Label("Planned"), num_text])

    i_box = make_items_list("ingredients:", production.ingredients(), production.set_consuption, update)
    p_box = make_items_list("products:", production.products(), production.set_production, update)

    box = widgets.HBox([num_box, i_box, p_box])
    return box


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
def interactiveOfProduction(result: 'Model', name: str, db: 'SatisfactoryDb', margin=1) -> widgets.Widget:
    buttonLayout = widgets.Layout(width='80%', align='left', align_items='flex-start')

    def log_it(it):
        with log:
            print('    ', end='')
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
    
    def selectRecipeFun(production: 'Production', output):
        def callback(_):
            set_quantity(production.plan)
            searchRecipe.choose_options.options = [ production.recipe.name ]
            searchRecipe.choose_options.value = production.recipe.name
            #TODO: maybe not create a widget on uncollpasing, just hide it.
            if output.collapse:
                output.collapse = False
                output.children = [interactive_production_display(production, update)]
            else:
                output.collapse = True
                output.children = []

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
            
            for prod in result.recipes():
                q = prod.plan - prod.done
                try:
                    if q > 0:
                        button_style=''
                    else:
                        button_style='success'
                except TypeError:
                    button_style=''

                button = widgets.Button(description = str(prod), layout=buttonLayout, button_style=button_style)
                button_output = widgets.Box()               
                button_box = widgets.VBox([button, button_output])
                button_output.collapse = True
                button.on_click(selectRecipeFun(prod, button_output))
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
            'name': 'products',
            'callback': on_recipes_by_product
        },
        {
            'name': 'ingredients',
            'callback': on_recipes_by_ingredient
        }
    ])
    selectItem = searchItem.choose_options
    searchRecipe = interactive_search(db.search_recipes_name, add_buttons=[
        {
            'name': 'products',
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


def display_game(mygame: Game):
    """Display items global production"""
    output = widgets.Output()
    with output:
        for name in mygame.items():
            print(f'{name}: {mygame[name]}')

    return output

def display_game_production(game: Game):
    """Create an interactive widget to display game production
    
You can search for items, select one and see factories that produce and consume it."""
    prods = game.items_production()

    def search(prefix):
        return [name for name in prods if prefix in name]

    def on_select(item):
        print(prods[item])

        opt = [f"<b>production of {item}</b>"]
        total = 0
        for usine, q in prods[item]:
            opt.append(f"{usine}: {q}")
            total += q

        #opt.append("")
        opt.append(f"<b>total: {total}</b>")

        output.value = "<br>".join(opt)

    output = widgets.HTML()
    int_search = interactive_search(search, [
        {
            'name': 'select',
            'callback': on_select
        }
    ])

    def observe_options(event):
        if event['name'] == 'index':
            on_select(event['owner'].value)

    int_search.choose_options.observe(observe_options)

    result = widgets.HBox([
        int_search,
        output
    ])
    result.search = int_search
    result.output = output

    return result