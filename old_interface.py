from collections import namedtuple
from typing import OrderedDict
import networkx as nx
from satisfactory_model import db
from IPython.display import display, Markdown, clear_output
import math
import ipywidgets as widgets

ProducedItem = namedtuple('ProducedItem', ['quantity', 'recipe'])

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
        ingredients = [(product, q * self.tick_per_m(amount)) for (product, q) in self.ingredients]
        products = [(product, q * self.tick_per_m(amount)) for (product, q) in self.subproduct]
        return ingredients, products

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
