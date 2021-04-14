from satisfactory import *
from satisfactory_model import current_result
from satisfactory_db import Recipe, db
import math

def test_interactive_nuclear():
    with ResultOfProd("nuclear", margin = 0.0001) as prod:
        add_recipe('Uranium Fuel Rod in Nuclear Power Plant', 4)
        assert math.isclose(prod['Uranium Fuel Rod'], -0.8), "Incorrect prod for fuel rod: {prod['Uranium Fuel Rod']}"
        assert prod['Uranium Waste'] > 0, "No uranium waste produced"
        assert prod['electricity'] > 0, "No eletricity produced"
        produce_with_recipe('Alternate: Uranium Fuel Unit', 'Uranium Fuel Rod')
        assert prod['Uranium Fuel Rod'] == 0, "Fuel rod not produced by produce_with_recipe"
        consume_with_recipe('Alternate: Fertile Uranium', 'Uranium Waste')
        assert prod['Uranium Waste'] == 0, "Uranium Waste not consumed"

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


if __name__ == "__main__":
    import pytest
    pytest.main()
