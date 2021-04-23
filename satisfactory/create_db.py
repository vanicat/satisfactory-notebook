import json
import os

from sqlalchemy import create_engine, Table, Column, Integer, String, Boolean, MetaData, Float

def create_db(db_path, json_path):
    recipes_src, items_src, generators_src, miners_src, buildings_src = read_json(json_path)

    engine, recipes, items, recipe_ingredients, recipe_products, buildings = connect_db(db_path)

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
    ins = recipes.insert().values(fake_recipe)
    a = engine.execute(ins)
    key = a.inserted_primary_key[0]
    it = engine.execute(items.select().where(items.c.className == 'Desc_Water_C')).fetchone()
    assert(it is not None)
    prod_id = it[0]
    ins = recipe_products.insert().values(recipe = key, item = prod_id, amount = 2)
    engine.execute(ins)

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
                ins = recipes.insert().values(fake_recipe)
                a = engine.execute(ins)
                key = a.inserted_primary_key[0]
                it = engine.execute(items.select().where(items.c.className == ressource['className'])).fetchone()
                assert(it is not None)
                prod_id = it[0]
                ins = recipe_products.insert().values(recipe = key, item = prod_id, amount = 1)
                engine.execute(ins)

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
            ins = recipes.insert().values(fake_recipe)
            a = engine.execute(ins)
            key = a.inserted_primary_key[0]
            it = engine.execute(items.select().where(items.c.className == fuel)).fetchone()
            assert(it is not None)
            ing_id = it[0]
            ins = recipe_ingredients.insert().values(recipe = key, item = ing_id, amount = 1)
            engine.execute(ins)
            if gen['waterToPowerRatio'] > 0:
                water_cons = time * gen['powerProduction'] * gen['waterToPowerRatio'] / 1000
                it = engine.execute(items.select().where(items.c.name == "Water")).fetchone()
                assert(it is not None)
                ing_id = it[0]
                ins = recipe_ingredients.insert().values(recipe = key, item = ing_id, amount = water_cons)
                engine.execute(ins)
            it = engine.execute(items.select().where(items.c.className == 'BP_Electricity_C')).fetchone()
            assert(it is not None)
            prod_id = it[0]
            ins = recipe_products.insert().values(recipe = key, item = prod_id, amount = desc_fuel['energyValue']/60)
            engine.execute(ins)
            if gen['className'] in special_case:
                waste, amount = special_case[gen['className']][fuel]
                it = engine.execute(items.select().where(items.c.className == waste)).fetchone()
                assert(it is not None)
                prod_id = it[0]
                ins = recipe_products.insert().values(recipe = key, item = prod_id, amount = amount)
                engine.execute(ins)

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
        ins = recipes.insert().values(c)
        a = engine.execute(ins)
        key = a.inserted_primary_key[0]
        for ing in r['ingredients']:
            it = engine.execute(items.select().where(items.c.className == ing['item'])).fetchone()
            if it is not None:
                ing_id = it[0]
                ins = recipe_ingredients.insert().values(recipe = key, item = ing_id, amount = ing['amount'])
                engine.execute(ins)
        if r['forBuilding']:
            for prod in r['products']:
                assert prod['amount'] == 1
                ins = (buildings.update()
                    .where(buildings.c.className == prod['item'])
                    .values(recipe = key))
                engine.execute(ins)
        else:
            for prod in r['products']:
                it = engine.execute(items.select().where(items.c.className == prod['item'])).fetchone()
                if it is not None:
                    prod_id = it[0]
                    ins = recipe_products.insert().values(recipe = key, item = prod_id, amount = prod['amount'])
                    engine.execute(ins)

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
        ins = buildings.insert().values(b)
        engine.execute(ins)

def create_items(engine, items, items_src):
    def add_item(it):
        if 'fluidColor' in it: del i['fluidColor']
        if it['liquid']:
            it['energyValue'] *= 1000
        ins = items.insert().values(it)
        return engine.execute(ins)

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