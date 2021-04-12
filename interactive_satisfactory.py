#!/usr/bin/env python
# coding: utf-8

# In[1]:

from ipywidgets.widgets.widget_box import VBox
import math
from IPython.display import display, Markdown, clear_output
import ipywidgets as widgets
from collections import OrderedDict, namedtuple
import networkx as nx
#import matplotlib.pyplot as plt
import random as rd
import plotly.graph_objects as go
from sqlalchemy.sql.expression import desc
from utils import myround
from satisfactory_db import SatisfactoryDb

db = SatisfactoryDb()


# In[5]:

def interactive_search(callback = None, search = db.search_items, add_buttons = []):
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

# In[7]:


class Option:
    """Option(name, time, amount, ingredients, subproduct) : time is in seconde!"""
    def __init__(self, name, time, amount, ingredients, subproduct):
        self.name = name
        self.time = time / 60
        self.amount = amount
        self.ingredients = ingredients
        self.subproduct = subproduct
        
    def __iter__(self):
        return iter(self.ingredients)
        
    def __str__(self):
        result = f"{self.name} {self.amount / self.time}"
        if self.ingredients:
            result += ':'
        for name, amount in self.ingredients:
            result += f' {name}: {amount / self.time}'
        return result
    
    def __repr__(self):
        return f"Option({self.name}, {self.time}, {self.amount}, {self.ingredients})"
    
    def speed(self):
        return self.amount / self.time
        
    def tick_per_m(self, amount):
        return amount / self.amount
    
    def usines(self, amount):
        usine_tick_per_m = 1 / self.time
        usines = self.tick_per_m(amount) / usine_tick_per_m
        return usines
    
    def produce(self, amount):
        ingredient = [(product, q * self.tick_per_m(amount)) for (product, q) in self.ingredients]
        subproduct = [(product, q * self.tick_per_m(amount)) for (product, q) in self.subproduct]
        return ingredient, subproduct
    
    


# In[8]:


ProducedItem = namedtuple('ProducedItem', ['quantity', 'recipe'])

class ResultFromProd:
    """Result(product, quantity) make an object to search how to build stuff.
    
    quantity is a quantity by minute"""
    def __init__(self, product, quantity):
        self.produced =  OrderedDict()
        self.needed = {}
        self.subproduct = {}
        self.options = {}
        self.depend = nx.DiGraph()
        self.depend.add_node(product)
        self.quantity = quantity
        self.add_needed(product, 1)
        
        
    def set_quantity(self, q):
        self.quantity = q
        
    
    def add_needed(self, product, quantity):
        if product in self.subproduct:
            quantity = quantity - self.subproduct[product]
            if quantity < 0:
                self.subproduct[product] =  - quantity
                return
            elif quantity == 0:
                del self.subproduct[product]
                return
        if product in self.needed:
            self.needed[product] += quantity
        elif product in self.produced:
            self.add_produced(product, quantity)
        else:
            self.needed[product] = quantity
            possibility = db.search_possibility_by_product(product)
            
            new_options = {}
            for r_id, r_name, r_time, r_amount in possibility:
                ingredients = db.get_ingredients(r_id)
                subproducts = db.get_subproducts(r_id)
                new_options[r_name] = Option(r_name, r_time, r_amount, ingredients, subproducts)
            self.options[product] = new_options

    def show_options(self):
        return self.options

    
    def show_produced(self):
        result = {}
        for product in nx.topological_sort(self.depend):
            if product in self.produced:
                option = self.produced[product]
                q = option.quantity * self.quantity
                result[product] = (q, option.recipe and option.recipe.usines(q))
        return result

    def show_subproduct(self):
        return {p: q * self.quantity for (p, q) in self.subproduct.items()}

    def auto_option(self, product):
        return product in self.options[product] or len(self.options[product]) <= 1

        
    def choose_option(self, product, option = None):
        if product in self.produced:
            print(f'{product} already there')
            self.accept_produced(product)
            return

        if len(self.options[product]) > 0:
            if option is None and product not in self.options[product]:
                if len(self.options[product]) != 1:
                    raise ValueError(f"option cannot be None for {product}")
                _, recipe = self.options[product].popitem()
            else:
                if option is None:
                    option = product
                recipe = self.options[product][option]
                
            needed, subproduct = recipe.produce(self.needed[product])
                
            for i_name, i_q in needed:                
                self.add_needed(i_name, i_q)
                self.depend.add_node(i_name)
                self.depend.add_edge(i_name, product)
                
            for i_name, i_q in subproduct:
                if i_name != product:
                    if i_name in self.subproduct:
                        self.subproduct[i_name] += i_q
                    else:
                        self.subproduct[i_name] = i_q
            
            self.accept_produced(product, recipe)
        else:
            self.accept_produced(product)
    
    def accept_produced(self, product, recipe = None):
        assert product not in self.produced

        self.produced[product] = ProducedItem(quantity = self.needed[product], recipe = recipe)
        
        del self.options[product]
        del self.needed[product]
                
    def add_produced(self, product, quantity):
        assert product in self.produced
        old = self.produced[product]
        self.produced[product] = ProducedItem(quantity = old.quantity + quantity, recipe = old.recipe)
        
        if old.recipe: # TODO !!! tenir compte des sous produits en plus.
            for i_name, i_q in old.recipe.produce(quantity)[0]:
                self.add_needed(i_name, i_q)
        
        
    def auto(self):
        for product in self.needed:
            if self.auto_option(product):
                self.choose_option(product)
        


# In[9]:


def draw_dependency_graph(graph):
    x = 0
    pos = {}
    free = {}
    fixed = {}
    lg_path = nx.dag_longest_path(graph)
    for product in lg_path:
        pos[product] = (x, x/2)
        free[x] = x/2
        x += 1
    fixed = { 
        lg_path[0]: pos[lg_path[0]],
        lg_path[-1]: pos[lg_path[-1]],
    }
    for product in lg_path:
        x, y = pos[product]
        
        def parcour(product, x):
            for pred in graph.pred[product]:
                if pred not in pos:
                    y = free[x-1]
                    free[x-1] += 1
                    pos[pred] = (x-1, y+1)
                    parcour(pred, x-1)
        
        parcour(product, x)
    # red = nx.transitive_reduction(graph)
    layout = nx.spring_layout(graph, pos = pos, fixed = pos)
    nx.draw(graph, layout, with_labels = True)


# In[12]:


class DisplayProd:
    def __init__(self, product, quantity):
        assert False, 'going to second!'
        self.product = product
        self.quantity = quantity
        
        self.model = ResultFromProd(product, quantity)
        self.title = widgets.Label(f"Objectif: {product}: ")
        self.quantity_field = widgets.Text()
        self.quantity_field.value = str(quantity)
        self.quantity_field.on_submit(self.on_set_value)
        
        self.producing = widgets.Output()
        self.options = widgets.VBox()
        self.auto = widgets.Button(description='Auto')
        self.restart = widgets.Button(description='Restart')
        
        self.auto.on_click(self.on_auto)
        self.restart.on_click(self.on_restart)
        
        self.box = widgets.VBox([widgets.HBox((self.title, self.quantity_field)), self.producing, self.options, widgets.HBox((self.auto, self.restart)) ])
        
        self.update()
        
    def update(self):
        self.update_producing()
        self.update_options()
        
    def update_producing(self):
        with self.producing:
            clear_output()
            self.print_producing()
            self.print_subproduct()
            
    def print_producing(self):
        if self.model.show_produced():
            print(f"to produce:")
            for product, (q, u) in self.model.show_produced().items():
                if u is None:
                    print(f"  {product}: {q}")
                else:
                    print(f"  {product}: {q} dans {math.ceil(u)} usine(s) à {u/math.ceil(u)*100}%")
        else:
            print("to produce: nothing yet")
            
    def print_subproduct(self):
        if self.model.show_subproduct():
            print("\n\nResidue:")
            for (product, q) in self.model.show_subproduct().items():
                print(f"  {product}: {q}")
        
    def update_options(self):
        opt_widgets = []
        title = widgets.Label('options:')
        opt_widgets.append(title)
        
        for product, recipe_list in self.model.show_options().items():
            label = widgets.Label(product + ": ")
            
            choose = [("", None)]
            for recipe, ingredient in recipe_list.items():

                choose.append((str(ingredient), recipe))

            radio = widgets.RadioButtons(options = choose, layout = widgets.Layout(width='70%'))
        
            button_c = widgets.Button(description = "choose")
            button_c.on_click(self.on_choose(product, radio))
        
            button_p = widgets.Button(description = "produced")
            button_p.on_click(self.on_produced(product))
        
            box = widgets.HBox((label, radio, widgets.VBox((button_c, button_p))))
            
            opt_widgets.append(box)
        
        opt_widgets.reverse()
        self.options.children = tuple(opt_widgets)
        
    def on_set_value(self, _):
        self.model.set_quantity(float(self.quantity_field.value))
        self.quantity = float(self.quantity_field.value)
        self.update()
        
        
    def on_auto(self, _):
        self.model.auto()
        self.update()
        
    def on_restart(self, _):
        self.model = ResultFromProd(self.product, self.quantity)
        self.update()
        
    def on_choose(self, product, radio):
        def doit(_):
            self.model.choose_option(product, radio.value)
            print(f"choosing : {product} with {radio.value}: choose_option({repr(product)}, {repr(radio.value)})")
            self.update()
        return doit
    
    def on_produced(self, product):
        def doit(_):
            self.model.accept_produced(product)
            print(f"{product} accedeted")
            self.update()
        return doit

    @property
    def display(self):
        return self.box





# In[16]:


Recipe = namedtuple('Recipe', ['name', 'alternate', 'time', 'ingredient', 'product', 'producedIn'])


# In[17]:


builder = {
    'Desc_AssemblerMk1_C': 'Assembler',
    'Desc_ConstructorMk1_C': 'Constructor',
    'Desc_FoundryMk1_C': 'Foundry',
    'Desc_ManufacturerMk1_C': 'Manufacturer',
    'Desc_OilRefinery_C': 'Refinery',
    'Desc_SmelterMk1_C': 'Smelter',
    'Desc_Packager_C': 'Packager',
    'Desc_Blender_C': 'Blender',
    'Desc_HadronCollider_C': 'Hadron Collider',
    None: None
}


# In[18]:


all_recipes = {}

for (r_id, _, name, _, alternate, time, _, _, _, _, _, producedIn) in db.list_all_recipes:
    ingredients = db.get_ingredients(r_id)
    products = db.get_subproducts(r_id)

    if producedIn in builder:
        producedIn = builder[producedIn]
    
    if name in all_recipes and all_recipes[name] != Recipe(name, alternate, time, ingredients, products, producedIn):
        print(f"{name} déjà là: {all_recipes[name]} et {(name, alternate, time, ingredients, products, producedIn)} ")
    all_recipes[name] = Recipe(name, alternate, time / 60, ingredients, products, producedIn)

# all_recipes

# { recipe.producedIn for name, recipe in all_recipes.items()}


# In[19]:


ProducedItem = namedtuple('ProducedItem', ['quantity', 'recipe'])


current_result = None


class ResultOfProd:
    """ResultOfProd() make an object where you can add ressource, or recipe to plan production line
    
    quantity is a quantity by minute"""
    def __init__(self, name = "None", sort = True):
        self.available =  {}
        self.needed =  {}
        self._recipes = {}
        self.constructed = {}
        self.name = name
        self.sort = sort
        
    def construct(self, recipe, q):
        if recipe in self.constructed:
            self.constructed[recipe] += q
        else:
            self.constructed[recipe] = q
        
    def add_product(self, p, q):
        if p in self.available:
            self.available[p] += q
        else:
            self.available[p] = q
    
    def consume_product(self, p, q):
        """Warning: you can consume product that are not there"""
        if p in self.needed:
            self.needed[p] += q
        else:
            self.needed[p] = q
        
    def add_node(self, p, quality):
        q = 300/1
        if quality == "pure":
            q = 780/1
        elif quality == "normal":
            q = 600/1
        self.add_product(p, q)
        
    def add_recipe(self, name, n):
        """add n producter using recipe"""
        assert name in all_recipes
        if name in self._recipes:
            self._recipes[name] += n
        else:
            self._recipes[name] = n
            
        for item, quantity in all_recipes[name].ingredient:
            self.consume_product(item, quantity * n / all_recipes[name].time)
            
        for item, quantity in all_recipes[name].product:
            self.add_product(item, quantity * n / all_recipes[name].time)
            
    def consume_with_recipe(self, recipe_name, product, q = None):
        if getattr(q, '__getitem__', False):
            q = q[product]
        if q is None:
            q = self[product]
        recipe = all_recipes[recipe_name]
        n = 0
        for p, q2 in recipe.ingredient:
            if p == product:
                n = q / (q2 / recipe.time)
        
        self.add_recipe(recipe_name, n)
    
    def produce_with_recipe(self, recipe_name, product, q = None):
        if getattr(q, '__getitem__', False):
            q = -q[product]
        if q is None:
            q = -self[product]
        recipe = all_recipes[recipe_name]
        n = 0
        for p, q2 in recipe.product:
            if p == product:
                n = q / (q2 / recipe.time)
        
        self.add_recipe(recipe_name, n)
        
    
    def strs_products(self):
        products = set(self.available.keys()).union(set(self.needed.keys()))
        result = []
        for p in products:
            if p in self.available and p in self.needed:
                qa = myround(self.available[p])
                qn = myround(self.needed[p])
                result.append((qa-qn, f"{qa-qn} {p}: {qn} of {qa}"))
            elif p in self.available:
                qa = myround(self.available[p])
                result.append((qa, f"{qa} {p}: +{qa}"))
            else:
                qn = myround(self.needed[p])
                result.append((-qn, f"{-qn} {p}: -{qn}"))
                
        if self.sort:
            result.sort()
        
        return [ st for _, st in result ]
    
    def products(self):
        products = set(self.available.keys()).union(set(self.needed.keys()))
        result = []
        for p in products:
            if p in self.available and p in self.needed:
                qa = myround(self.available[p])
                qn = myround(self.needed[p])
                result.append((qa-qn, f"{qa-qn} {p}: {qn} of {qa}", p))
            elif p in self.available:
                qa = myround(self.available[p])
                result.append((qa, f"{qa} {p}: +{qa}", p))
            else:
                qn = myround(self.needed[p])
                result.append((-qn, f"{-qn} {p}: -{qn}", p))
                
        if self.sort:
            result.sort()
        
        return (( (st, item, q) for q, st, item in result ))
    
    def strs_recipes(self):
        result = []
        for recipe, q in self._recipes.items():
            if q != 0:
                if recipe in self.constructed:
                    sts = f"{myround(self.constructed[recipe])} of {myround(q)} {all_recipes[recipe].producedIn} using {recipe}, reste {myround(q - self.constructed[recipe])}"
                    if self.constructed[recipe] >= q:
                        sts = '# ' + sts
                    result.append(sts)
                else:
                    result.append(f"{myround(q)} {all_recipes[recipe].producedIn} using {recipe}")
        return result
    
    def recipes(self):
        for recipe, q in self._recipes.items():
            if q != 0:
                if recipe in self.constructed:
                    sts = f"{self.constructed[recipe]} of {myround(q)} {all_recipes[recipe].producedIn} using {recipe}, reste {myround(q - self.constructed[recipe])}"
                    if self.constructed[recipe] >= q:
                        sts = '# ' + sts
                    yield sts, recipe, q - self.constructed[recipe]
                else:
                    yield f"{myround(q)} {all_recipes[recipe].producedIn} using {recipe}", recipe, q
        return None

    def building(self):
        result = {}
        for recipe, q in self._recipes.items():
            if q != 0:
                p = all_recipes[recipe].producedIn
                c = self.constructed.get(recipe, 0)
                q = math.ceil(q)
                if p in result:
                    old_c, old_q = result[p]
                    result[p] = (old_c + c, old_q + q)
                else:
                    result[p] = (c, q)
        return result
    
    def __enter__(self):
        global current_result
        current_result = self
        return self
    
    def __exit__(self, *args):
        if len(self.name) < 4 or self.name[0:4] != '    ':
            name = '    ' + self.name
        else:
            name = self.name
        display(interactiveOfProduction(self, name))
    
    def __getitem__(self, name):
        qa = self.available[name] if name in self.available else 0
        qn = self.needed[name] if name in self.needed else 0
        return qa - qn

# In[20]:
for method in vars(ResultOfProd):
    if len(method) > 2 and method[0:2] == '__':
        continue
    def f(m):
        return lambda *args: getattr(current_result, m)(*args)
    globals()[method] = f(method)

def items(it):
    return current_result[it]


# In[20]:


def interactiveOfProduction(result, name):
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
                    if q > 1:
                        button_style=''
                    elif q > -1:
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
        
    model = result
        
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
        }])
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


# %%
def shopping_list(buildings_dict):
    return db.shopping_list(buildings_dict)