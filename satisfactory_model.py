from interactive_satisfactory import interactiveOfProduction
from utils import myround
from satisfactory_db import SatisfactoryDb
from IPython.display import display
import math

db = SatisfactoryDb()

# In[18]:
current_result = None

class ResultOfProd:
    """ResultOfProd() make an object where you can add ressource, or recipe to plan production line
    
    quantity is a quantity by minute"""
    def __init__(self, name = "None", sort = True, margin = 1):
        self.available =  {}
        self.needed =  {}
        self._recipes = {}
        self.constructed = {}
        self.name = name
        self.sort = sort
        self.margin = margin
        
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
        if name in self._recipes:
            self._recipes[name] += n
        else:
            self._recipes[name] = n
        
        recipe = db.recipes_by_name(name)

        for item, quantity in recipe.ingredient:
            self.consume_product(item, quantity * n / recipe.time)
            
        for item, quantity in recipe.product:
            self.add_product(item, quantity * n / recipe.time)
            
    def consume_with_recipe(self, recipe_name, product, q = None):
        if getattr(q, '__getitem__', False):
            q = q[product]
        if q is None:
            q = self[product]
        recipe = db.recipes_by_name(recipe_name)
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
        recipe = db.recipes_by_name(recipe_name)
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
                    sts = f"{myround(self.constructed[recipe])} of {myround(q)} {db.recipes_by_name(recipe).producedIn} using {recipe}, reste {myround(q - self.constructed[recipe])}"
                    if self.constructed[recipe] >= q:
                        sts = '# ' + sts
                    result.append(sts)
                else:
                    result.append(f"{myround(q)} {db.recipes_by_name(recipe).producedIn} using {recipe}")
        return result
    
    def recipes(self):
        for recipe, q in self._recipes.items():
            if q != 0:
                if recipe in self.constructed:
                    sts = f"{self.constructed[recipe]} of {myround(q)} {db.recipes_by_name(recipe).producedIn} using {recipe}, reste {myround(q - self.constructed[recipe])}"
                    if self.constructed[recipe] >= q:
                        sts = '# ' + sts
                    yield sts, recipe, q - self.constructed[recipe]
                else:
                    yield f"{myround(q)} {db.recipes_by_name(recipe).producedIn} using {recipe}", recipe, q
        return None

    def building(self):
        result = {}
        for recipe, q in self._recipes.items():
            if q != 0:
                p = db.recipes_by_name(recipe).producedIn
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
        display(interactiveOfProduction(self, name, db, self.margin))
    
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

