from satisfactory import *
from satisfactory_model import db, current_result
from satisfactory_db import Recipe

def test_interactive_nuclear():
    with ResultOfProd("nuclear", margin = 0.0001):
        add_recipe('Uranium Fuel Rod in Nuclear Power Plant', 4)
        produce_with_recipe('Alternate: Uranium Fuel Unit', 'Uranium Fuel Rod')
        produce_with_recipe('Encased Uranium Cell', 'Encased Uranium Cell')
        produce_with_recipe('Sulfuric Acid', 'Sulfuric Acid')
        produce_with_recipe('Crystal Oscillator', 'Crystal Oscillator')
        produce_with_recipe('Beacon', 'Beacon')
        produce_with_recipe('Electromagnetic Control Rod', 'Electromagnetic Control Rod')
        produce_with_recipe('Concrete', 'Concrete')
        produce_with_recipe('Alternate: Stitched Iron Plate', 'Reinforced Iron Plate')
        produce_with_recipe('Iron Plate', 'Iron Plate')
        produce_with_recipe('Cable', 'Cable')
        produce_with_recipe('Wire', 'Wire')
        produce_with_recipe('Alternate: Quickwire Stator', 'Stator')
        produce_with_recipe('AI Limiter', 'AI Limiter')
        produce_with_recipe('Alternate: Fused Quickwire', 'Quickwire')
        produce_with_recipe('Steel Pipe', 'Steel Pipe')


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
