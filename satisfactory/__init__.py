from .db import db
from .model import Model
from .ui import interactiveOfProduction
from IPython.display import display

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
        name = self.name
        if self.name and (len(self.name) < 4 or self.name[0:4] != '    '):
            name = '    ' + self.name
        else:
            name = self.name
        display(interactiveOfProduction(self, name, db, self.margin))

for method in vars(Model):
    if len(method) > 2 and method[0:2] == '__':
        continue
    def f(m):
        return lambda *args, **kwargs: getattr(current_result, m)(*args, **kwargs)
    globals()[method] = f(method)

def items(it):
    return current_result[it]