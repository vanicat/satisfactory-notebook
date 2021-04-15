from satisfactory import *
from satisfactory_model import Production
from satisfactory_db import Recipe, db
from interactive_satisfactory import interactive_production_display
import sympy
import math

def test_interactive_nuclear():
    with ResultOfProd("nuclear", margin = 0.0001) as prod:
        add_recipe('Uranium Fuel Rod in Nuclear Power Plant', 2)
        add_recipe('Uranium Fuel Rod in Nuclear Power Plant', 2)
        assert math.isclose(prod['Water'], -300 * 4), "Incorrect use of water"
        assert math.isclose(prod['Uranium Fuel Rod'], -0.8), "Incorrect prod for fuel rod: {prod['Uranium Fuel Rod']}"
        assert prod['Uranium Waste'] > 0, "No uranium waste produced"
        assert prod['electricity'] > 0, "No eletricity produced"
        produce_with_recipe('Alternate: Uranium Fuel Unit', 'Uranium Fuel Rod')
        assert prod['Uranium Fuel Rod'] == 0, "Fuel rod not produced by produce_with_recipe"
        consume_with_recipe('Alternate: Fertile Uranium', 'Uranium Waste')
        assert prod['Uranium Waste'] == 0, "Uranium Waste not consumed"

        building = prod.building()
        assert 'Nuclear Power Plant' in building

def test_interactive_turbofuel():
    prod = ResultOfProd("prod")
    x = sympy.Symbol('x')
    prod.add_product('Turbofuel', x)
    prod.consume_with_recipe('Turbofuel in Fuel Generator', 'Turbofuel')
    assert prod['Turbofuel'] == 0
    assert sympy.nsimplify(prod['electricity']) == 2 * 150 * x / 9

def test_db():
    wire = db.recipes_by_name("Wire")
    assert wire, "Wire recipe not found"
    assert isinstance(wire, Recipe), "Bad type for recipe"
    assert wire.name == "Wire", "Incorrect recipe found"



def test_get_building_by_class():
    building = db.building_name_by_class('NoneClass')
    assert building is None
    building = db.building_name_by_class('Desc_Foundation_Frame_01_C')
    assert building == "Frame Foundation 8m x 4m"


def test_production():
    prod = ResultOfProd("prod")
    wire = db.recipes_by_name("Wire")
    wireProd = Production(prod, wire)
    wireProd.add(3)
    ingredients = list(wireProd.ingredients(3))
    interactive_production_display(wireProd, lambda *args: None)
    assert ('Copper Ingot', 45) in ingredients
    wireProd.set_production("Wire", 10)
    assert math.isclose(prod['Wire'], 10)
    wireProd.set_consuption("Copper Ingot", 20)
    assert math.isclose(prod['Copper Ingot'], -20)

if __name__ == "__main__":
    import pytest
    pytest.main()
