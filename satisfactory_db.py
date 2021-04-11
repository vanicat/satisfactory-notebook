from sqlalchemy import create_engine, Table, select, MetaData, and_

class SatisfactoryDb:
    def __init__(self) -> None:
        self.meta = MetaData()
        self.engine = create_engine('sqlite:///satisfactory.db')

        self.recipes = Table('recipes', self.meta, autoload=True, autoload_with=self.engine)
        self.items = Table('items', self.meta, autoload=True, autoload_with=self.engine)
        self.recipe_ingredients = Table('recipe_ingredients', self.meta, autoload=True, autoload_with=self.engine)
        self.recipe_products = Table('recipe_products', self.meta, autoload=True, autoload_with=self.engine)
        self.buildings = Table('buildings', self.meta, autoload=True, autoload_with=self.engine)

        # TODO: realy fetch on init ? maybe more gc friendly has to be done.
        request = self.engine.execute(self.recipes.select())
        self.list_all_recipes = request.fetchall()

    def search_recipes(self, pattern) -> list:
        request = self.recipes.select().where(self.recipes.c.name.like(f"%{pattern}%"))
        result = self.engine.execute(request).fetchall()
        return [ it[2] for it in result ]

    def search_items(self, pattern):
        request = self.items.select().where(self.items.c.name.like(f"%{pattern}%"))
        result = self.engine.execute(request).fetchall()
        return [ it[2] for it in result ]

    def search_recipes_by_product(self, pattern):
        request = select([self.recipes, self.recipe_products, self.items])
        request = request.where(self.recipes.c.id == self.recipe_products.c.recipe)
        request = request.where(self.recipe_products.c.item == self.items.c.id)
        request = request.where(self.items.c.name == pattern)
        result = self.engine.execute(request).fetchall()
        return [ it[2] for it in result ]

    def search_recipes_by_ingredients(self, pattern):
        request = select([self.recipes, self.recipe_ingredients, self.items])
        request = request.where(self.recipes.c.id == self.recipe_ingredients.c.recipe)
        request = request.where(self.recipe_ingredients.c.item == self.items.c.id)
        request = request.where(self.items.c.name == pattern)
        result = self.engine.execute(request).fetchall()
        return [ it[2] for it in result ]

    def search_ingredients_by_recipes(self, pattern):
        request = select([self.items, self.recipe_ingredients, self.recipes])
        request = request.where(self.recipes.c.id == self.recipe_ingredients.c.recipe)
        request = request.where(self.recipe_ingredients.c.item == self.items.c.id)
        request = request.where(self.recipes.c.name == pattern)
        result = self.engine.execute(request).fetchall()
        return [ it[2] for it in result ]

    def search_products_by_self(self, pattern):
        request = select([self.items, self.recipe_products, self.recipes])
        request = request.where(self.recipes.c.id == self.recipe_products.c.recipe)
        request = request.where(self.recipe_products.c.item == self.items.c.id)
        request = request.where(self.recipes.c.name == pattern)
        result = self.engine.execute(request).fetchall()
        return [ it[2] for it in result ]

    def search_possibility_by_product(self, product):
        request = select([self.recipes.c.id, self.recipes.c.name, self.recipes.c.time, self.recipe_products.c.amount]).where(
                and_(
                    self.recipes.c.id == self.recipe_products.c.recipe,
                    self.recipe_products.c.item == self.items.c.id,
                    self.items.c.name == product
                ))
        possibility = self.engine.execute(request).fetchall()
        return possibility

    def get_ingredients(self, r_id) -> list:
        request = select([self.items.c.name, self.recipe_ingredients.c.amount]).where(
                    and_(
                        self.recipe_ingredients.c.recipe == r_id,
                        self.recipe_ingredients.c.item == self.items.c.id,
                    )
                )
        return self.engine.execute(request).fetchall()
    
    def get_subproducts(self, r_id) -> list:
        request = select([self.items.c.name, self.recipe_products.c.amount]).where(
                    and_(
                        self.recipe_products.c.recipe == r_id,
                        self.recipe_products.c.item == self.items.c.id,
                    )
                )
        return self.engine.execute(request).fetchall()

    def shopping_list(self, buildings_dict):
        def add(dict1, k, value):
            if k in dict1:
                dict1[k] += value
            else:
                dict1[k] = value
        
        shopping_list = {}
        
        for b, q in buildings_dict.items():
            done, tot = q
            request = select([self.buildings]).where(self.buildings.c.name == b)
            recipe = self.engine.execute(request).fetchone()["recipe"]
            request = select([self.items, self.recipe_ingredients])
            request = request.where(self.recipe_ingredients.c.recipe == recipe)
            request = request.where(self.recipe_ingredients.c.item == self.items.c.id)
            result = self.engine.execute(request).fetchall()
            for item in result:

                add(shopping_list, item[self.items.c.name], (tot - done) * item[self.recipe_ingredients.c.amount])
        
        return shopping_list
