from typing import Dict
from .utils import myround
from .db import Recipe, db
import math

class Production():
    def __init__(self, model:'Model', recipe:Recipe, constructed = 0):
        self.model = model
        self.recipe = recipe
        self.plan = 0
        self.done = constructed

    def __str__(self) -> str:
        if self.done > 0:
            return f"{self.done} of {myround(self.plan)} {self.recipe.producedIn} using {self.recipe.name}, reste {myround(self.plan - self.done)}"
        else:
            return  f"{myround(self.plan)} {self.recipe.producedIn} using {self.recipe.name}"

    def add(self, n):
        self.plan += n
        
        for item, quantity in self.ingredients(n):
            self.model.consume_product(item, quantity)
            
        for item, quantity in self.products(n):
            self.model.add_product(item, quantity)

    def set(self, n):
        diff = n - self.plan
        self.add(diff)

    def _set_quantity(self, items, wanted_item, wanted_quantity):
        for item, quantity in items:
            if item == wanted_item:
                n = self.recipe.time * wanted_quantity / quantity
                self.set(n)
                break

    def set_production(self, item, quantity):
        self._set_quantity(self.recipe.products, item, quantity)

    def set_consuption(self, item, quantity):
        self._set_quantity(self.recipe.ingredients, item, quantity)
    
    def build(self, n):
        self.done += n

    def _yield_quantity(self, things, n):
        if n is None:
            n = self.plan
        for item, quantity in things:
            yield (item, quantity * n / self.recipe.time)

    def ingredients(self, n = None):
        return self._yield_quantity(self.recipe.ingredients, n)

    def products(self, n = None):
        return self._yield_quantity(self.recipe.products, n)


# In[18]:
class Model:
    """Model() make an object where you can add ressource, or recipe to plan production line
    
    quantity is a quantity by minute"""
    def __init__(self, db, name = None, margin = 1):
        self.available =  {}
        self.needed =  {}
        self._recipes : Dict[str, Production] = {}
        self.name = name
        self.margin = margin
        self.db = db
        self.imported = {}
        
    def construct(self, recipe, q):
        if recipe not in self._recipes:
            raise ValueError(f"{recipe} is not a recipe of this factories")
        self._recipes[recipe].build(q)
        
    def add_product(self, p, q):
        if p in self.available:
            self.available[p] += q
        else:
            self.available[p] = q
    
    def consume_product(self, p, q):
        """Warning: you can consume products that are not there"""
        if p in self.needed:
            self.needed[p] += q
        else:
            self.needed[p] = q
    
    def add_recipe(self, name, n):
        """add n producter using recipe"""
        if name in self._recipes:
            prod = self._recipes[name]
        else:
            recipe = self.db.recipes_by_name(name)
            prod = Production(self, recipe)
            self._recipes[name] = prod

        prod.add(n)
            
    def consume_with_recipe(self, recipe_name, item, q = None, prop = 1):
        if getattr(q, '__getitem__', False):
            q = q[item]
        if q is None:
            q = self[item]
        q = q * prop

        recipe = self.db.recipes_by_name(recipe_name)
        n = 0
        for p, q2 in recipe.ingredients:
            if p == item:
                n = q / (q2 / recipe.time)
        
        self.add_recipe(recipe_name, n)
    
    def produce_with_recipe(self, recipe_name, item, q = None, prop = 1):
        if getattr(q, '__getitem__', False):
            q = -q[item]
        if q is None:
            q = -self[item]
        q = q * prop

        recipe = self.db.recipes_by_name(recipe_name)
        n = 0
        for p, q2 in recipe.products:
            if p == item:
                n = q / (q2 / recipe.time)
        
        self.add_recipe(recipe_name, n)
        
    
    def strs_products(self):
        result = []
        for p in self.items():
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
                
        try:
            result.sort()
        except TypeError:
            pass
        
        return [ st for _, st in result ]
    
    def products(self):
        result = []
        for p in self.items():
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
                
        try:
            result.sort()
        except TypeError:
            pass
        
        return (( (st, item, q) for q, st, item in result ))
    
    def recipes(self):
        for name, prod in self._recipes.items():
            q = prod.plan
            if q != 0:
                yield prod
        return None

    def building(self):
        result = {}
        for name, producer in self._recipes.items():
            q = producer.plan
            if q != 0:
                p = producer.recipe.producedIn
                c = producer.done
                q = math.ceil(q)
                if p in result:
                    old_c, old_q = result[p]
                    result[p] = (old_c + c, old_q + q)
                else:
                    result[p] = (c, q)
        return result
    
    def __getitem__(self, name):
        qa = self.available[name] if name in self.available else 0
        qn = self.needed[name] if name in self.needed else 0
        return qa - qn

    def import_from(self, factory, item, quantity = None, force = False):
        if quantity is None:
            quantity = -self[item]
        if (not force) and quantity > factory[item]:
            raise ValueError(f'the factory do not have enough {item}: {factory[item]} for {quantity}')
        if quantity <= 0:
            return
        if item in self.imported:
            self.imported[item] += quantity
        else:
            self.imported[item] = quantity
        if item in self.available:
            self.available[item] += quantity
        else:
            self.available[item] = quantity

    def importation(self, item):
        if item not in self.imported:
            return 0
        return self.imported[item]

    def import_all(self, factory):
        for item in factory.items():
            self.import_from(factory, item, factory[item])

    def items(self):
        for item in self.available:
            yield item
        for item in self.needed:
            if item not in self.available:
                yield item

    def graph_canvas(self, size = (500, 400)):
        from algorithmx import jupyter_canvas

        nodes = {}
        nbnode = 0

        canvas = jupyter_canvas(buttons=True)
        canvas.size(size)

        for it in self.items():
            nbnode += 1
            nodes[it] = nbnode
            canvas.node(nbnode).add()
            canvas.node(nbnode).label(1).add().text(it)
            canvas.node(nbnode).color('blue')
            if it in self.available:
                canvas.node(nbnode).label().text(f"{float(self.available[it]):.0f}")
            else:
                canvas.node(nbnode).label().text(f"{float(self.needed[it]):.0f}")

        for r in self.recipes():
            recipe = 'Rec: ' + r.recipe.name
            nbnode += 1
            nodes[recipe] = nbnode
            canvas.node(nbnode).add()
            canvas.node(nbnode).label(1).add().text(recipe)
            canvas.node(nbnode).label().text(f"{(math.ceil(float(r.plan))):.0f}")
            if r.plan - 0.01 <= r.done:
                canvas.node(nbnode).color('black')
            else:
                canvas.node(nbnode).color('red')
            for ingr in r.ingredients():
                name = ingr[0]
                canvas.edge((nodes[name], nbnode)).directed(True).add()

            for prod in r.products():
                name = prod[0]
                canvas.edge((nbnode, nodes[name])).directed(True).add()

        canvas.pause(1)
        return canvas

    def graph(self, size = (500, 400)):
        import networkx as nx

        G = nx.Graph()

        G.add_nodes_from(self.items())

        for r in self.recipes():
            recipe = 'Rec: ' + r.recipe.name
            G.add_node(recipe)
            for ingr in r.ingredients():
                G.add_edge(ingr[0], recipe).add()

            for prod in r.products():
                G.add_edge(recipe, prod[0]).add()

        return G




# In[20]:


