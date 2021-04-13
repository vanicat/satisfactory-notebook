from satifactory import *

def test_read_db():
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

