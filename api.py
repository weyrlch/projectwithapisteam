import itertools
APIS = ['1', '2']
api = itertools.cycle(APIS)
SMARTAPI = next(api)
debuglogic = True