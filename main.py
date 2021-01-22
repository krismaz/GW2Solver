import network
import operations
import solver
import options
from datetime import datetime
import json

timestamp = datetime.now().isoformat().replace(':', '_').replace('.', '_')


print(f"Fetching Data...")

tp_items = network.tp_items()
special_recipes = network.cache(network.special_recipes)
recipes = network.cache(network.recipes)
items = network.cache(network.items)
account_recipes = network.account_recipes()
currentsells = network.currentsells()
dyes = network.cache(network.dyes)[1:] #Skip dye remover

for item in tp_items:
    item['adjusted_buy'] = int(item['daily_buy_sold'] * options.hours)
    item['adjusted_sell'] = max(0, int((item['daily_sell_sold'] - currentsells[item['id']]) * options.hours))

print("Generating Operations...")

names = {item['id']: item['name'] for item in items}
lookup = {item['id']: item for item in items}
tplookup = {item['id']: item for item in tp_items}
for dye in dyes:
    dye['hue'] = dye['categories'][0]

operations =    operations.FlipBuy(tp_items) + \
                operations.EctoSalvage() +  \
                operations.Gemstones(names) +  \
                operations.Data(tplookup) +  \
                operations.SpecialCrafting(special_recipes, names) +  \
                operations.Crafting(recipes, names, account_recipes) +  \
                operations.Fractal() +  \
                operations.Dyes(dyes, lookup) + \
                operations.Salvaging(tp_items, tplookup, lookup) + \
                operations.FlipSell(tp_items) 

print("Preparing Solver...")

solver.solve(operations, options.budget, options.simplicity)


with open(f'results/{timestamp}.txt', 'w+') as resultfile:
    for operation in operations:
        if operation.value:
            # print(f'{operation.value} x {operation.description}')
            print(f'{operation.value} x {operation.description}', file=resultfile)

with open(f'operations.json', 'w+') as resultdatafile:
    json.dump([
        {
            "ID": op.output_hint,
            "Name": names.get(op.output_hint, "???"),
            "Description": op.description,
            "Quantity": int(op.value)
        }
    for op in operations if op.value], resultdatafile)


