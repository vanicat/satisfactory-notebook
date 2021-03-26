from enum import Enum, auto

class R(Enum):
    IronOre = auto()
    CopperOre = auto()
    Limestone = auto()
    CateriumOre = auto()

    Sulfur = auto()
    Coal = auto()
    
    IronIngot = auto()
    IronPlate = auto()
    ReinforcedIronPlace = auto()
    IronRod = auto()
    Screw = auto()
    ModularFrame = auto()
    
    SteelIngot = auto()
    SteelBeam = auto()
    SteelPipe = auto()
    
    Concrete = auto()
    EncasedIndustrialBeam = auto()
    
    CopperIngot = auto()
    CopperSheet = auto()
    Wire = auto()
    Cable = auto()
    
    CateriumIngot = auto()
    QuickWire = auto()
    AILimiter = auto()
    
    Rotor = auto()
    Stator = auto()
    Motor = auto()
    
    HeavyModularFrame = auto()
    
    Rubber = auto()
    
ore = [R.IronOre, R.Limestone, R.Coal, R.CateriumOre, R.CopperOre]

#False ore
ore.append(R.Rubber)


production = {}

def add_production(product : R, rates, ressource: dict, subproduct = {}):
    production[product] = (rates, ressource, subproduct)

for i in  ore:
    add_production(i, 60, {})

add_production(R.IronIngot, 30, {R.IronOre: 1})
add_production(R.IronPlate, 20, {R.IronIngot: 3/2})
add_production(R.IronRod, 15, {R.IronIngot: 1})
add_production(R.ReinforcedIronPlace, 5, {R.IronPlate: 6, R.Screw: 12})
add_production(R.Screw, 40, {R.IronRod: 1/4})

add_production(R.CopperIngot, 30, {R.CopperOre: 1})
add_production(R.Wire, 30, {R.CopperIngot: 1/2})
add_production(R.Cable, 30, {R.CopperIngot: 2})
add_production(R.Cable, 30, {R.CopperIngot: 2})
add_production(R.CopperSheet, 10, {R.CopperIngot: 2})

add_production(R.SteelBeam, 15, {R.SteelIngot: 4})
add_production(R.SteelPipe, 20, {R.SteelIngot: 3/2})
add_production(R.SteelIngot, 45, {R.IronOre: 1, R.Coal: 1})

add_production(R.Concrete, 15, {R.Limestone: 3})
add_production(R.EncasedIndustrialBeam,6,{R.SteelBeam: 4, R.Concrete: 5})

add_production(R.CateriumIngot, 15, {R.CateriumOre: 1/3})
add_production(R.QuickWire, 60, {R.CateriumIngot: 1/5})
add_production(R.AILimiter, 5, {R.QuickWire: 20, R.CopperSheet: 5 })

add_production(R.Stator, 5, {R.SteelPipe: 3, R.Wire: 8})
add_production(R.Rotor, 5, {R.IronRod: 5, R.Screw: 25})
add_production(R.Motor, 5, {R.Rotor: 2, R.Stator: 2})

add_production(R.ModularFrame, 2, {R.ReinforcedIronPlace: 3/2, R.IronRod: 12/2})
add_production(R.HeavyModularFrame, 3.75, {R.ModularFrame: 5, R.EncasedIndustrialBeam: 3, R.Rubber: 20, R.Screw: 104})

def prod(*args):
    result = {}
    if len(args) == 1:
        rest = args[0][:]
    else:
        product, rate = args
        rest = [(product, rate)]
    subproduct = []
    while rest:
        p, rate = rest.pop()
        e_rate, needed, subprod = production[p]
        for ress in needed:
            rest.append((ress, needed[ress] * rate))
        
        if p not in result:
            result[p] = (0, 0)
        usine, prod = result[p]
        result[p] = (usine + rate/e_rate, prod + rate)
    
    # il faudrait retirer les sousproduits qui sont utilisé
    return result, subproduct
    
def add_needed(n1, n2):
    items = set(n1).union(set(n2))
    result = {}
    for i in items:
        if i in n1:
            if i in n2:
                u1, p1 = n1[i]
                u2, p2 = n2[i]
                result[i] = (u1 + u2, p1 + p2)
            else:
                result[i] = n1[i]
        else:
            assert i in n2
            result[i] = n2[i]
    return result

def sub_needed(n1, n2):
    items = set(n1).union(set(n2))
    result = {}
    for i in items:
        if i in n1:
            if i in n2:
                u1, p1 = n1[i]
                u2, p2 = n2[i]
                if p1 - p2 != 0:
                    result[i] = (u1 - u2, p1 - p2)
            else:
                result[i] = n1[i]
        else:
            assert i in n2
            u2, p2 = n2[i]
            result[i] = (- u2, - p2)
    return result


def pourcentage(needed):
    return {i: needed[i][0] / math.ceil(needed[i][0]) for i in needed }


hmf = prod(R.HeavyModularFrame, 3.75)

hmf



