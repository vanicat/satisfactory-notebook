import json
import os

from sqlalchemy import create_engine, Table, Column, Integer, String, Boolean, MetaData, Float

def add_or_update_elem(engine, table, elem):
    req = table.select().where(table.c.className == elem['className'])
    it = engine.execute(req).fetchone()
    if it is None:
        ins = table.insert().values(elem)
        a = engine.execute(ins)
        return a.inserted_primary_key[0]
    
    table.update().where(table.c.className == elem['className']).values(elem)
    return it[0]

def add_related(engine, items, table, recipe_id, className, amount):
    it = engine.execute(items.select().where(items.c.className == className)).fetchone()
    if it is None:
        print(f"can't find {className} in items")
        return

    prod_id = it[0]
    ins = table.insert().values(recipe = recipe_id, item = prod_id, amount = amount)
    engine.execute(ins)


def delete_row(engine, table):
    engine.execute(table.delete())

def create_db(db_path, json_path):
    recipes_src, items_src, generators_src, miners_src, buildings_src = read_json(json_path)

    engine, recipes, items, recipe_ingredients, recipe_products, buildings = connect_db(db_path)

    delete_row(engine, recipe_ingredients)
    delete_row(engine, recipe_products)

    create_items(engine, items, items_src)

    create_buildings(engine, buildings, buildings_src)
    
    create_recipes(engine, recipes, items, buildings, recipe_ingredients, recipe_products, recipes_src)

    recipes_for_generator(engine, recipes, items, recipe_ingredients, recipe_products, items_src, generators_src, buildings_src)
            
    recipes_for_nodes(engine, recipes, items, recipe_products, items_src, miners_src)

    recipes_for_extractor(engine, recipes, items, recipe_products)

def recipes_for_extractor(engine, recipes, items, recipe_products):
    fake_recipe = {
        "slug": f"water-extractor-production",
        "name": f"Extract water",
        "className": f"Recipe_WaterExtraction_C",
        "alternate": False,
        "time": 1,
        "manualTimeMultiplier": 1,
        "forBuilding": False,
        "inMachine": True,
        "inHand": False,
        "inWorkshop": False,
        "producedIn": f"Desc_WaterPump_C"
    }
    
    key = add_or_update_elem(engine, recipes, fake_recipe)
    add_related(engine, items, recipe_products, key, 'Desc_Water_C', 2)



def recipes_for_nodes(engine, recipes, items, recipe_products, items_src, miners_src):
    qualities = { 
        'impure': 0.5, 
        'normal': 1,
        'pure': 2
    }
    for miner in miners_src.values():
        #print(miner)
        for ressource in miner['allowedResources']:
            ressource = items_src[ressource]
            liquid_mult = 1000 if miner['allowLiquids'] else 1
            for qua in qualities:
                fake_recipe = {
                    "slug": f"{miner['className'].lower()[6:-2]}-{ressource['slug']}-{qua}",
                    "name": f"{qua} {ressource['name']} with {miner['className'][6:-2]}",
                    "className": f"Recipe_{miner['className'][6:-2]}{ressource['className'][4:-1]}{qua}_C",
                    "alternate": False,
                    "time": miner['extractCycleTime'] / qualities[qua] / (miner['itemsPerCycle'] / liquid_mult),
                    "manualTimeMultiplier": 1,
                    "forBuilding": False,
                    "inMachine": True,
                    "inHand": False,
                    "inWorkshop": False,
                    "producedIn": f"Desc{miner['className'][5:]}"
                }
                key = add_or_update_elem(engine, recipes, fake_recipe)
                add_related(engine, items, recipe_products, key, ressource['className'], 1)

def recipes_for_generator(engine, recipes, items, recipe_ingredients, recipe_products, items_src, generators_src, buildings_src):
    special_case = {
        'Build_GeneratorNuclear_C': {
            'Desc_NuclearFuelRod_C': ("Desc_NuclearWaste_C", 50),
            'Desc_PlutoniumFuelRod_C': ("Desc_PlutoniumWaste_C", 10)
        }
    }
    for gen in generators_src.values():
        desc_class = 'Desc_' + gen['className'][6:]
        desc = buildings_src[desc_class]

        for fuel in gen['fuel']:
            desc_fuel = items_src[fuel]
            if desc_fuel['energyValue'] == 0:
                continue
            time = desc_fuel['energyValue'] / gen['powerProduction']
            fake_recipe = {
                "slug": f"{desc_fuel['slug']}-{desc['slug']}",
                "name": f"{desc_fuel['name']} in {desc['name']}",
                "className": f"Recipe_{desc_fuel['className'][5:-2]}_{desc_class[5:]}",
                "alternate": False,
                "time": time,
                "manualTimeMultiplier": 1,
                "forBuilding": False,
                "inMachine": True,
                "inHand": False,
                "inWorkshop": False,
                "producedIn": desc_class
            }
            key = add_or_update_elem(engine, recipes, fake_recipe)
            add_related(engine, items, recipe_ingredients, key, fuel, 1)
            if gen['waterToPowerRatio'] > 0:
                water_cons = time * gen['powerProduction'] * gen['waterToPowerRatio'] / 1000
                add_related(engine, items, recipe_ingredients, key, 'Desc_Water_C', water_cons)
            add_related(engine, items, recipe_products, key, 'BP_Electricity_C', desc_fuel['energyValue']/60)

            if gen['className'] in special_case:
                waste, amount = special_case[gen['className']][fuel]
                add_related(engine, items, recipe_products, key, waste, amount)

def create_recipes(engine, recipes, items, buildings, recipe_ingredients, recipe_products, recipes_src):
    for r in recipes_src.values():
        c = dict(r)
        del c['ingredients']
        del c['products']
        if len(c['producedIn']) > 0:
            if len(c['producedIn']) > 1:
                print(f"severall producer for {c['slug']}?")
            c['producedIn'] = c['producedIn'][0]
        else:
            c['producedIn'] = None
        
        key = add_or_update_elem(engine, recipes, c)
        for ing in r['ingredients']:
            add_related(engine, items, recipe_ingredients, key, ing['item'], ing['amount'])
        if r['forBuilding']:
            for prod in r['products']:
                assert prod['amount'] == 1, "in create_recipes: the prod amount should be one"
                ins = (buildings.update()
                    .where(buildings.c.className == prod['item'])
                    .values(recipe = key))
                engine.execute(ins)
        else:
            for prod in r['products']:
                add_related(engine, items, recipe_products, key, prod['item'], prod['amount'])

def create_buildings(engine, buildings, buildings_src):
    for b in buildings_src.values():
        if 'categories' in b:
            del b['categories']
        if 'metadata' in b:
            del b['metadata']
        if 'size' in b:
            for desc in b['size']:
                b[desc] = b['size'][desc]
            del b['size']
        add_or_update_elem(engine, buildings, b)

def create_items(engine, items, items_src):
    def add_item(it):
        if 'fluidColor' in it: del it['fluidColor']
        if it['liquid']:
            it['energyValue'] *= 1000
        add_or_update_elem(engine, items, it)

    for i in items_src.values():
        add_item(i)

    add_item({
        "slug": "plutonium-waste",
        "className": "Desc_PlutoniumWaste_C",
        "name": "Plutonium Waste",
        "sinkPoints": 0,
        "description": "The by-product of consuming Plutonium Fuel Rods in the Nuclear Power Plant.\n\nCaution: HIGHLY Radioactive.",
        "stackSize": 500,
        "energyValue": 0,
        "radioactiveDecay": 20,
        "liquid": False
    })
    add_item({
        'slug': 'electricity',
        'className': 'BP_Electricity_C', 
        'name': 'electricity',
        'sinkPoints': 0,
        'description': 'to Power everything',
        'stackSize': 0,
        'energyValue': 1,
        'radioactiveDecay': 0,
        'liquid': False
    })

def read_json(json_path):
    with open(json_path) as datas:
        datas = json.load(datas)
    #for i in datas:,    #    print(i)recipes_src = datas['recipes']
    items_src = datas['items']
    recipes_src = datas['recipes']
    generators_src = datas['generators']
    miners_src = datas['miners']
    buildings_src = datas['buildings']
    return recipes_src,items_src,generators_src,miners_src,buildings_src

def connect_db(db_path):
    engine = create_engine(f'sqlite:///{db_path}')
    meta = MetaData()
    recipes = Table(
        'recipes', meta, 
        Column('id', Integer, primary_key = True), 
        Column('slug', String), 
        Column('name', String), 
        Column('className', String), 
        Column('alternate', Boolean), 
        Column('time', Float), 
        Column('manualTimeMultiplier', Integer), 
        Column('forBuilding', Boolean), 
        Column('inMachine', Boolean), 
        Column('inHand', Boolean), 
        Column('inWorkshop', Boolean),
        Column('producedIn', String)
    )
    items = Table(
        'items', meta,
        Column('id', Integer, primary_key = True),
        Column('slug', String), 
        Column('name', String), 
        Column('className', String), 
        Column('sinkPoints', Integer),
        Column('description', String),
        Column('stackSize', Integer),
        Column('energyValue', Integer),
        Column('radioactiveDecay', Integer),
        Column('liquid', Boolean)
    )
    recipe_ingredients = Table(
        'recipe_ingredients', meta,
        Column('id', Integer, primary_key = True),
        Column('recipe', Integer),
        Column('item', Integer),
        Column('amount', Integer)
    )
    recipe_products = Table(
        'recipe_products', meta,
        Column('id', Integer, primary_key = True),
        Column('recipe', Integer),
        Column('item', Integer),
        Column('amount', Integer)
    )
    buildings = Table(
        'buildings', meta,
        Column('id', Integer, primary_key = True),
        Column('slug', String), 
        Column('name', String), 
        Column('description', String), 
        # Not categories
        Column('buildMenuPriority', Integer),
        Column('className', String),
        # Not metadata
        # Not size but: (0 for now in source !) 
        Column('width', Integer),
        Column('length', Integer),
        Column('height', Integer),
        Column('recipe', Integer)
    )
    meta.create_all(engine)
    return engine,recipes,items,recipe_ingredients,recipe_products,buildings