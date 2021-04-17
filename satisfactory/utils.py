STD_ROUND = 3

def myround(v, x = STD_ROUND):
    try:
        return round(v, x)
    except TypeError:
        return v
