from pulp import LpVariable, LpProblem, value, LpMaximize, lpSum, LpStatus, COIN_CMD
from collections import defaultdict
from time import time
import utils
import options


def solve(operations, budget, simplicity):
    start = time()
    if simplicity <= 0:
        for operation in operations:
            operation.limiter = False
    
    operations = [op for op in operations if op.limit > 0]
    
    outputs = set()
    inputs = set()
    for operation in operations:
        outputs = outputs.union(operation.outputs.keys())
        inputs = inputs.union(operation.inputs.keys())
        

    operations = [op for op in operations if not set(op.inputs.keys()).difference(outputs)]
    operations = [op for op in operations if op.profit > 0 or set(op.outputs.keys()).intersection(inputs)]
    
    print(len(operations), 'Operations after filtering')

    lookup = defaultdict(list)
    for op in operations:
        op.lpvariable = LpVariable(
            op.description, 0, int(op.limit), cat=('Integer' if op.outputs else 'Continuous'))
        for id in op.inputs.keys():
            lookup[id].append(op)
        for id in op.outputs.keys():
            lookup[id].append(op)
        if op.limiter:
            op.indicator = LpVariable(
                op.description + '_indicator', 0, op.limit//op.chunk_size + 1, cat='Integer')

    prob = LpProblem("SCIENCE!", LpMaximize)
    prob += lpSum([(op.profit - op.cost) *
                   op.lpvariable for op in operations]), "PROFIT!"

    for item, ops in lookup.items():
        prob += lpSum([(op.outputs.get(item, 0) - op.inputs.get(item, 0))
                       * op.lpvariable for op in ops]) >= 0

    for op in operations:
        if simplicity and op.limiter:
            prob += op.lpvariable <= op.indicator * op.chunk_size

       # if options.min_move_per_day and not op.outputs:
       #    indicator = LpVariable(op.description + '_move_indicator', 0, 1, cat='Binary')
       #     prob += op.lpvariable <= indicator * options.sanity
       #     prob += op.lpvariable * op.profit >= indicator * options.min_move_per_day
                                

    prob += lpSum(op.cost * op.lpvariable for op in operations if op.cost) <= budget
    if simplicity:
        prob += lpSum(op.indicator for op in operations if op.limiter) <= simplicity



    print('Pulp setup took', time() - start, 'seconds')
    print('Starting actual solve now!')
    start = time()

    solution = prob.solve(COIN_CMD('D:\\cbc\\bin\\cbc.exe', **options.solveroptions))


    print('Solution status:', LpStatus[solution],
          'in', time() - start, 'seconds')

    print(utils.coins(int(prob.objective.value())),' expected profit')

    for operation in operations:
        operation.value = value(operation.lpvariable)
