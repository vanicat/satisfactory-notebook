#!/usr/bin/env python
# coding: utf-8

# In[1]:

from ipywidgets.widgets.widget_box import VBox
from IPython.display import clear_output
import ipywidgets as widgets
#import matplotlib.pyplot as plt


# In[5]:

def interactive_search(callback, search, add_buttons):
    """search for items or recipe"""
    
    def on_search(_):
        result = search(search_widget.value)
        choose_options.options = result
        
    def on_choose(_):
        if callback is not None:
            callback(choose_options.value)
        
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
    choose_button = widgets.Button(description = "Choose")
    choose_box = widgets.HBox((choose_options, widgets.VBox([choose_button] + buttons)))
    
    # choose_options.on_submit(on_choose)
    choose_button.on_click(on_choose)
    
    result = widgets.VBox((search_box, choose_box))
    result.choose_options = choose_options
    result.search_box = search_box
    
    return result


# In[20]:
def interactiveOfProduction(result, name, db, margin=1):
    buttonLayout = widgets.Layout(width='80%', align='left', align_items='flex-start')
    
    def selectItemFun(item, q):
        def callback(_):
            quantityItem.value = abs(q)
            searchItem.choose_options.options = [ item ]
            searchItem.choose_options.value = item
        return callback
    
    def selectRecipeFun(item, q):
        def callback(_):
            quantityItem.value = abs(q)
            searchRecipe.choose_options.options = [ item ]
            searchRecipe.choose_options.value = item
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
                button.on_click(selectRecipeFun(recipe, q))
                children.append(button)
                
            recipeBox.children = children
            
    def on_add_item(v):
        result.add_product(selectItem.value, quantityItem.value)
        with log:
            print(f"{name}.add_product({repr(selectItem.value)}, {quantityItem.value})")
        update()
            
    def on_add_factory(v):
        result.add_recipe(selectRecipe.value, quantityItem.value)
        with log:
            print(f"{name}.add_recipe({repr(selectRecipe.value)}, {quantityItem.value})")
        update()
                   
    def on_select_item(item):
        update()
    
    def on_select_recipe(recipe):
        update()
        
    def on_consume(_):
        if selectItem.value is not None and selectRecipe.value is not None:
            result.consume_with_recipe(selectRecipe.value, selectItem.value, quantityItem.value)
            with log:
                print(f"{name}.consume_with_recipe({repr(selectRecipe.value)}, {repr(selectItem.value)}, {quantityItem.value})")
        update()
            
    def on_produce(_):
        if selectItem.value is not None and selectRecipe.value is not None:
            result.produce_with_recipe(selectRecipe.value, selectItem.value, quantityItem.value)
            with log:
                print(f"{name}.produce_with_recipe({repr(selectRecipe.value)}, {repr(selectItem.value)}, {quantityItem.value})")
        update()
        
    def on_construct(_):
        if selectRecipe.value is not None:
            result.construct(selectRecipe.value, quantityItem.value)
            with log:
                print(f"{name}.construct({repr(selectRecipe.value)}, {quantityItem.value})")
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
    
    output = widgets.Output()
    itemBox = widgets.VBox(description = 'items')
    recipeBox = widgets.VBox(description = 'recipe')
    
    log = widgets.Output()
    searchItem = interactive_search(on_select_item, db.search_items, add_buttons=[
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
    searchRecipe = interactive_search(on_select_recipe, db.search_recipes, add_buttons=[
        {
            'name': 'product',
            'callback': on_products_by_recipe
        },
        {
            'name': 'ingred',
            'callback': on_ingredients_by_recipe
        }
    ])
    selectRecipe = searchRecipe.choose_options
    addBox = widgets.HBox()

    quantityItem = widgets.FloatText(description = "quantity")
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
    
    consumeRecipe = widgets.FloatText()
    
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
        widgets.Label("Item produced"),
        itemBox,
        widgets.Label("Recipe used"),
        recipeBox,
        output,
        widgets.Label("logs"),
        log
    ])
