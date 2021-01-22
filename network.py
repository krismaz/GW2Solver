import requests
import json
import options
import utils
from collections import defaultdict

headers = {'user-agent': 'GW2Tradz LPSolver Testing (Krismaz.1250)'}


def tp_items():
    headers = {'user-agent': 'GW2Tradz LPSolver Testing (Krismaz.1250)'}
    r = requests.get(
        f'https://api.silveress.ie/gw2/v1/items/json?beautify=min&fields=id,buy_price,sell_price,name,{options.days_tag}_sell_sold,{options.days_tag}_buy_sold,1d_buy_sold,1d_sell_sold,vendor_value,rarity,type,upgrade1,level,statName', headers=headers)
    items = r.json()

    for item in items:
        item['daily_buy_sold'] = min(
            item.get(f'{options.days_tag}_sell_sold', 0)/options.days,
            item.get(f'1d_buy_sold', 0)*2) # Tends to spike-bouht low-level stuff
        item['daily_sell_sold'] = min(
            item.get(f'{options.days_tag}_sell_sold', 0)/options.days,
            item.get(f'1d_sell_sold', 0)*2) # Tends to spike-bouht low-level stuff

        # -.-'
        if item['id'] in [93371, 93516, 93619, 93522, 93499]:
            item['vendor_value'] = 5*utils.silver
    
    return items


def special_recipes():
    r = requests.get(
        'http://gw2profits.com/json/v3', headers=headers)
    return r.json()

def account_recipes():
    r = requests.get(
        'https://api.guildwars2.com/v2/account/recipes?access_token=' + options.apikey, headers=headers)
    return r.json()


def recipes():
    r = requests.get(
        'https://api.guildwars2.com/v2/recipes', headers=headers)
    ids = r.json()
    result = []
    for chunk in utils.chunks(ids, 200):
        r = requests.get(
            'https://api.guildwars2.com/v2/recipes?ids=' + ','.join(map(str, chunk)), headers=headers)
        result += r.json()
    return result

def items():
    r = requests.get(
        'https://api.guildwars2.com/v2/items', headers=headers)
    ids = r.json()
    result = []
    for chunk in utils.chunks(ids, 200):
        r = requests.get(
            'https://api.guildwars2.com/v2/items?ids=' + ','.join(map(str, chunk)), headers=headers)
        result += r.json()
    return result

def currentsells():
    page, maxpage = 0, 0
    results = []
    while page <= maxpage:
        r = requests.get(
        f'https://api.guildwars2.com/v2/commerce/transactions/current/sells?access_token={options.apikey}&page={page}', headers=headers)
        maxpage = int(r.headers['X-Page-Total']) - 1
        results += r.json()
        page += 1
    counts = defaultdict(int)
    for result in results:
        counts[result['item_id']] += result['quantity']
    return counts



def cache(func):
    try:
        with open('cache/' + func.__name__+'.json', 'r') as cachefile:
            print("Cache hit for", func.__name__)
            return json.load(cachefile)
    except:
        print("Cache miss for", func.__name__)
        with open('cache/' + func.__name__+'.json', 'w') as cachefile:
            result = func()
            json.dump(result, cachefile)
            return result


def dyes():
    r = requests.get(
        f'https://api.guildwars2.com/v2/colors?ids=all', headers=headers)
    return r.json()