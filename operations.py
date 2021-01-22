import options
import utils
import json
from collections import defaultdict
import glob
import csv


class Operation:
    def __init__(self, cost, profit, inputs, outputs, limit, description, limiter, chunk_size, output_hint):
        self.cost = cost
        self.profit = profit
        self.inputs = inputs
        self.outputs = outputs
        self.limit = min(limit, options.budget // cost if cost else options.sanity)
        self.description = description
        self.limiter = limiter
        self.chunk_size = chunk_size
        self.output_hint = output_hint

        self.lpvariable = None
        self.value = None
        self.indicator = None


def FlipBuy(items):
    results = []

    for item in items:
        # Sanity
        if 'buy_price' not in item or item['buy_price'] == 0 or ('vendor_value' in item and item['buy_price'] < item['vendor_value']):
            continue

        # Reduce variance a bit
        if item['adjusted_buy'] < options.min_velocity:
            continue

        results.append(Operation(
            (item['buy_price'] + 1),
            0,
            {},
            {item['id']: 1},
            min(options.sanity, item['adjusted_buy']),
            f'Buy {item["name"]} ({item["id"]}) @ {utils.coins(item["buy_price"] + 1)}',
            True,
            250 * options.click_weight,
            item['id']
        ))

    return results


def FlipSell(items):
    results = []
    for item in items:
        # Sanity
        if 'sell_price' not in item:
            continue

        # Reduce variance a bit
        if item['adjusted_sell'] < options.min_velocity:
            continue

        # save some computation speed
        if item['adjusted_sell'] * item['sell_price'] < options.min_move_per_day:
            continue

        results.append(Operation(
            0,
            int((item['sell_price'] - 1)*0.85*options.safetyprice),
            {item['id']: 1},
            {},
            min(options.sanity, item['adjusted_sell']),
            f'Sell {item["name"]} ({item["id"]}) @ {utils.coins(item["sell_price"] - 1)}',
            False,
            250 * options.click_weight,
            item['id']
        ))

    return results


def SpecialCrafting(recipes, names):
    daily = ['-260']
    results = []
    for recipe in recipes:
        # Remove Amalgamated Spam
        if recipe['name'] == "Amalgamated Gemstone":
            continue
        op = Operation(
            0,
            0,
            {i['item_id']: i['count'] for i in recipe['ingredients']},
            {recipe['output_item_id']: recipe['output_item_count']},
            1 if recipe['id'] in daily else options.sanity,
            f'Craft {recipe["name"]} from {", ".join(names.get(i["item_id"], "???") for i in recipe["ingredients"])} ({recipe["id"]})',
            False,
            1000 * options.click_weight,
            recipe['output_item_id']
        )
        # Gold is handled as id -1
        if -1 in op.inputs:
            op.cost = op.inputs[-1]
            op.description = f'Buy {recipe["name"]} from vendor ({recipe["id"]})'
            op.chunk_size = options.sanity
            op.limiter = False
            del op.inputs[-1]
        results.append(op)
    return results


def Crafting(recipes, names, account_recipes):
    daily = [66913, 79795, 66993, 66917, 66923, 67377, 79726,
             79817, 79790, 46744, 79763, 46742, 46740, 46745, 67015]
    account_recipes = set(account_recipes)
    results = []

    for recipe in recipes:

        # skip duplicate mithrilium recipe
        if recipe['id'] == 12053:
            continue

        # skip unlearned recipes
        if recipe['id'] not in account_recipes and "LearnedFromItem" in recipe['flags']:
            continue

        results.append(Operation(
            0,
            0,
            {i['item_id']: i['count'] for i in recipe['ingredients']},
            {recipe['output_item_id']: recipe['output_item_count']},
            1 if recipe['output_item_id'] in daily else options.sanity,
            f'Craft {names.get(recipe["output_item_id"], "???")} from {", ".join(names.get(i["item_id"], "???") for i in recipe["ingredients"])} ({recipe["id"]})',
            recipe['type'] != 'Refinement',
            1000 * options.click_weight,
            recipe['output_item_id']
        ))
    return results


def EctoSalvage():
    return [Operation(
        60,
        0,
        {19721: 1},
        {24277: 1.85},
        options.sanity,
        f'Salvage Ecto',
        False,
        options.sanity,
        19721
    )]


def Gemstones(names):
    stones = [24773, 24502, 24884, 24516, 24508, 24522, 72504, 70957, 72315, 76179, 74988,
              24515, 75654, 24510, 24512, 76491, 24520, 42010, 72436, 24524, 24533, 24532, 24518, 24514]
    return [Operation(
        0,
        0,
        {19721: 5, stone: 75},
        {68063: 11.5},
        options.sanity,
        f'Make gemstones from ecto and {names[stone]}',
        False,
        5*options.click_weight,
        stone
    ) for stone in stones] + [
        Operation(
            0,
            0,
            {24325: 10,
             24340: 10,
             24330: 10,
             70842: 10},
            {92687: 1},
            options.sanity,
            f'Make draconic lodestones from lodestones (Mordrem Lodestone)',
            False,
            25*options.click_weight,
            92687)
    ] + [
        Operation(
            0,
            0,
            {24325: 10,
             24340: 10,
             24330: 10,
             24335: 10},
            {92687: 1},
            options.sanity,
            f'Make draconic lodestones from lodestones (Pile of Putrid Essence)',
            False,
            25*options.click_weight,
            92687)
    ]


def Data(lookup):
    files = glob.glob("Data/*.json")
    results = []
    for datafile in files:
        with open(datafile, 'r') as jsonfile:
            data = json.load(jsonfile)
            divisor = data['Input']['Quantity']
            outputs = defaultdict(int)
            for o in data['Outputs']:
                outputs[o['ID']] += o['Quantity']

            item = lookup[data['Input']['ID']]
            # Debug Info
            cost = (lookup[data['Input']['ID']]["buy_price"] +
                    1 + data['Cost']) * data['Input']['Quantity']
            profit_buy = sum((lookup[k]["buy_price"] + 1) * v for k, v in outputs.items(
            ) if k in lookup) + data['Profit'] * data['Input']['Quantity']
            profit_sell = sum((lookup[k]["sell_price"] + 1)*0.85 * v for k, v in outputs.items(
            ) if k in lookup) + data['Profit'] * data['Input']['Quantity']

            print(lookup[data['Input']['ID']]["name"], 100 *
                  (profit_buy-cost)/cost, 100*(profit_sell-cost)/cost)

            results.append(Operation(
                data['Cost'],
                data['Profit'],
                {data['Input']['ID']: 1},
                {k: v/divisor for k, v in outputs.items()},
                options.sanity,
                f'{data["Verb"]} {data["Input"]["Name"]}',
                False,
                options.sanity,
                data['Input']['ID']
            ))
    return results


def Fractal():
    t5 = [24276, 24299, 24282, 24341, 24294, 24356, 24350, 24288]
    outputs = {
        49424: 2.25,  # infusion
        74268: 0.015,  # mew
        46735: 1,  # t7
        46731: 1,  # t7
        46733: 1  # t7
    }
    outputs.update({i: 0.348 for i in t5})

    return [
        Operation(
            0,
            43*utils.silver,
            {
                75919: 1,  # encryption
                73248: 0.9  # matrix
            },
            outputs,
            options.sanity,
            "Crack fractal Encryptions",
            False,
            250 * options.click_weight,
            75919
        )
    ]


def Dump():
    with open("inventory.csv", 'r') as csvfile:
        data = csv.DictReader(csvfile)
        return [Operation(
            0,
            0,
            {},
            {
                int(d['ID']):int(d['Total'])
            },
            1,
            f'Use {d["Name"]} ({d["ID"]})',
            False,
            options.sanity,
            int(d['ID'])
        )
            for d in data]


def Dyes(dyes, lookup):
    results = []

    hues = {
        'Brown': [74982],
        'White': [75862],
        'Blue': [75694],
        'Black': [70426],
        'Gray': [75862, 70426],
        'Red': [71692],
        'Orange': [75270],
        'Purple': [77112],
        'Yellow': [71952],
        'Green': [76799]
    }

    rarities = {

        'Fine': 3,
        'Masterwork': 6.5,
        'Rare': 10.4
    }

    for dye in dyes:
        if 'item' not in dye or dye['hue'] not in hues or dye['item'] not in lookup:
            continue
        item = lookup[dye['item']]
        if item['rarity'] not in rarities:
            continue
        results.append(
            Operation(
                3,
                0,
                {
                    item['id']: 0.01
                },
                {
                    hue: rarities[item['rarity']]/len(hues[dye['hue']]) for hue in hues[dye['hue']]
                },
                options.sanity,
                f'Salvage {item["name"]}',
                False,
                options.sanity,
                item['id']
            )
        )

    return results


def Salvaging(items, tplookup, lookup):
    results = []

    champ_items = (44978, 44980, 44983, 72191, 44982, 44960, 44977, 44991, 44984, 44985, 44967, 44964, 44974, 44965, 44971, 44976, 44962,
                   44961, 44986, 44973, 44969, 44988, 44992, 44968, 44987, 44963, 44990, 44966, 44972, 44975, 44989, 44979, 44981, 44999, 44970)
    stats = ("Solder's", "Rabid", "Dire", "Cavalier's", "Shaman's")
    insignias = {lookup[i]['name'].split()[0]: i for i in (
        46712, 46710, 49522, 46709, 46708)}
    inscriptions = {lookup[i]['name'].split()[0]: i for i in (
        46688, 46686, 46690, 46685, 46684)}

    for item in items:
        if item['id'] not in lookup or "NoSalvage" in lookup[item['id']]['flags']:
            continue

        if item['rarity'] == 'Rare' and \
           item['type'] in ['Armor', 'Weapon', 'Trinket'] and \
           item['level'] >= 68:

            operation = Operation(
                60,
                0,
                {item['id']: 1},
                {19721: 0.875},
                options.sanity,
                f'Extract and salvage {item["name"]} ({item["id"]})',
                False,
                options.sanity,
                item['id']
            )

            if 'upgrade1' in item:
                operation.outputs[item['upgrade1']] = 1

            results.append(operation)

        if item['rarity'] == 'Exotic' and \
           item['type'] in ['Armor', 'Weapon', 'Trinket'] and \
           item['level'] >= 68:

            operation = Operation(
                60,
                0,
                {item['id']: 1},
                {19721: 1.2, 46681:0.5},
                options.sanity,
                f'Extract and salvage {item["name"]} ({item["id"]})',
                False,
                options.sanity,
                item['id']
            )

            if 'upgrade1' in item:
                operation.outputs[item['upgrade1']] = 1

                # We keep this in here for now to avoid craftables
                if item['id'] not in champ_items and 'statName' in item and item['statName'] in stats:
                    if item['type'] == 'Weapon':
                        operation.outputs[inscriptions[item['statName']]] = 0.4
                    elif item['type'] == 'Armor':
                        operation.outputs[insignias[item['statName']]] = 0.4

            results.append(operation)

    return results
