from utils import gold

budget = 10000 * gold  # Maximum gold spend, slightly increases runtime
simplicity = 25  # How many lines of output / distinct operations, keep this low~ish for speed, or just very large for omegaspeed
days = 7  # How many days of buy/sell are you fetching?
days_tag = "7d"  # How many days of buy/sell are you fetching?
hours = 12 / 24  # How much of daily buy/sell can you get
sanity = 50000  # How much of one single thing can we do, effectively limits buys
safetyprice = 0.95  # Adjust sell prices slightly, this helps prevent silly 1-2% flips that might technically be optimal, but are rarely great in practice
min_move_per_day = 10 * gold # Do not try to sell and item if we can't sell for more than x gold a day, higher means more speed but less flexibility
min_velocity = 1  # Do not try to buy/sell an item if we can get less than this amount of it in the alotted time, higher means more speed but less flexibility
click_weight = 10  # Up this if you waint less lines but larger chunks

solveroptions = {"threads": 8, "fracGap": 0.1,
                 "maxSeconds": 240}  # Options for the cbc solver

# put your own api key here obvs
apikey = '-'
