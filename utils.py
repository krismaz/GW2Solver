gold = 100 * 100
silver = 100 

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def coins(value):
    result = ""
    if value >= gold:
        result += f"{value//gold}g"
    if value >= silver:
        result += f"{(value%gold)//silver}s"
    result += f"{value%silver}c"
    return result