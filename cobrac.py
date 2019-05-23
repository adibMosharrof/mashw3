'''
CIS 510: Multiagent Systems
HW1
Adib Mosharrof

Note:
Trevor Bergstorm and I solved this problem together, but then we each refactored
it in our own style. So there might be some similarities in our codebase.

max vDefender
    s.t.
    z1+z2+z3 ... zn = 1 --- number of targets
    x1+x2+x3 ....xn <=2 --- coverage probability of each target, 
                            sum should be less than number of resources
    
    defender strategy constraint
    vDefender + (uDu - uDc)xi + Mzi M= M + uDu

    attacker strategy constraint
    vAttacker + (uAu - uAc)xi >= uAu
       attacker utility constraint 
    vAttacker + (uAu - uAc)xi + Mzi  <= M + uAu 

'''

import sys
import csv
import cplex
import copy

numOfTargets = None
numOfResources = None
M = 1000

payoffMatrix = []

def loadData():
    global numOfTargets
    global numOfResources
    with open('param.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in spamreader:
            numOfTargets = int(row[0])
            numOfResources = int(row[1])

    with open('payoff.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in spamreader:
            row.pop(0)
            for i in range(len(row)):
                row[i] = int(row[i])
            payoffMatrix.append(row)

def getObjective():
    #objective function is to maximize vDefender, so only vDefender coefficient will be 1,
    #rest will be 0
    objective = []
    #making coefficients of all z and x 0
    for i in range(numOfTargets*2):
        objective.append(0.0)

    #vDefender is 1
    objective.append(1.0)
    #vAttacker is 0
    objective.append(0.0)
    return objective

def getUpperBounds():
    upperBounds = []

    #upper bound for z and x is 1
    for i in range(numOfTargets*2):
        upperBounds.append(1.0)

    #upper bounds for vDefender and vAttacker is infinity
    upperBounds.append(cplex.infinity)
    upperBounds.append(cplex.infinity)
    return upperBounds

def getLowerBounds():
    lowerBounds = []
    #upper bound for z and x is 1
    for i in range(numOfTargets*2):
        lowerBounds.append(0.0)

    #upper bounds for vDefender and vAttacker is infinity
    lowerBounds.append(-1* cplex.infinity)
    lowerBounds.append(-1* cplex.infinity)
    return lowerBounds

def getCTypes():
    cTypes = ''
    
    #z is an integer {0,1} which represents whether a target will be attacked or not
    cTypes += numOfTargets*'I'
    #x is the probabilty distribution [0,1]
    cTypes += numOfTargets*'C'
    
    #continues values for vDefender and vAttacker
    cTypes +='CC'
    return cTypes;

def getColumnNames():
    columnNames = []

    for i in range(numOfTargets):
        columnNames.append('z'+str(i+1))

    for i in range(numOfTargets):
        columnNames.append('x'+str(i+1))
    
    columnNames.append('vDefender')    
    columnNames.append('vAttacker')
    return columnNames

def getRightHandSide():
    '''
    r1 -> z1+z2+z3 ... zn = 1 --- number of targets
    r2 -> x1+x2+x3 ....xn <=2 --- coverage probability of each target, 
                            sum should be less than number of resources
    
    defender strategy constraint
    vDefender + (uDu - uDc)xi + Mzi M= M + uDu
    r3 to r(3 +numOfTargets)  M + uDu

    attacker strategy constraint
    vAttacker + (uAu - uAc)xi >= uAu
    r(4+numOfTargets) to r(4 +numOfTargets*2)  uAu

       attacker utility constraint 
    vAttacker + (uAu - uAc)xi + Mzi  <= M + uAu 
    r(5+numOfTargets*2) to r(5 +numOfTargets*3)  M + uAu 
    '''

    rhs = []

    #r1
    rhs.append(1.0)
    #r2
    rhs.append(numOfResources)

    #defender strategy
    for i in range(numOfTargets):
        #utility of DefenderUncovered is at index 1
        rhs.append(M+ payoffMatrix[i][1])

    #attacker strategy
    for i in range(numOfTargets):
        #utility of DefenderUncovered is at index 2
        rhs.append(payoffMatrix[i][2])

    #attacker utility
    for i in range(numOfTargets):
        rhs.append(M+ payoffMatrix[i][2])

    return rhs

def getRowNames():
    numOfContstraints = numOfTargets*3 + 2
    rowNames = []
    for i in range(numOfContstraints):
        rowNames.append("r"+str(i+1))
    return rowNames

def getSense():
    #sense is used to denote inequality of each constraint, 
    sense = ''

    #sum of z has an equal constraint
    sense += 'E'
    #sum of x has less than constraint
    sense += 'L'

    #defender utility has less than constraint
    sense += numOfTargets*'L'
    #attacker strategy has greater than constraint
    sense += numOfTargets*'G'
    #attacker utility has less than constraint
    sense += numOfTargets*'L'

    return sense;

def getRows():
    '''
    the rows of data needs to be added to a list in the following format
    [
        [
            [variableNames], [variableCoefficients],
            .....
        ]
    ]
    '''

    rows = []

    #the first two constraints those of z and x
    #for both the coefficient is 1
    zNames = []
    zCoefficients = []
    xNames = []
    xCoefficients = []

    for i in range(numOfTargets):
        zNames.append("z"+ str(i+1))
        zCoefficients.append(1.0)

        xNames.append("x"+ str(i+1))
        xCoefficients.append(1.0)

    rows.append([zNames, zCoefficients])
    rows.append([xNames, xCoefficients])


    variables = []
    coefficients = []

    #defender strategy constraint
    #vDefender + (uDu - uDc)xi + Mzi M= M + uDu
    for i in range(numOfTargets):
        variables = ['vDefender', 'x'+str(i+1), 'z'+str(i+1)]
        coefficients = [1.0, payoffMatrix[i][1]- payoffMatrix[i][0], M]
        addDataToRows(rows, variables, coefficients)


    #attacker strategy
    #vAttacker + (uAu - uAc)xi >= uAu
    for i in range(numOfTargets):
        variables = ['vAttacker', "x"+str(i+1)]
        coefficients = [1.0, payoffMatrix[i][2] - payoffMatrix[i][3]]
        addDataToRows(rows, variables, coefficients)

    #attacker utility
    #vAttacker + (uAu - uAc)xi + Mzi  <= M + uAu 
    for i in range(numOfTargets):
        variables = ['vAttacker', "x"+str(i+1), "z"+str(i+1)]
        coefficients = [1.0, payoffMatrix[i][2] - payoffMatrix[i][3], M]
        addDataToRows(rows, variables, coefficients)

    return rows

def addDataToRows(rows, variables, coefficients):    
        rows.append([copy.deepcopy(variables), copy.deepcopy(coefficients)])
        variables.clear()
        coefficients.clear()

def writeToFile(values):
    with open('solution.csv', mode = 'w+') as outputFile:
            writer = csv.writer(outputFile, delimiter=',')

            for i in range(numOfTargets):
                writer.writerow( [str(i + 1), str(values[i + numOfTargets])])

def runCobrac():
    
    loadData()
    objective = getObjective()
    upperBounds = getUpperBounds()
    lowerBounds = getLowerBounds()
    cTypes = getCTypes()
    columnNames = getColumnNames()
    rightHandSide = getRightHandSide()
    rowNames = getRowNames()
    senses = getSense()
    rows = getRows()

    problem = cplex.Cplex()
    #creating a maximization problem
    problem.objective.set_sense(problem.objective.sense.maximize)
    #setting the variables of the MILP
    problem.variables.add(obj = objective, lb = lowerBounds, ub = upperBounds, types =cTypes, names = columnNames)
    #setting the constraints
    problem.linear_constraints.add(lin_expr = rows, senses= senses, rhs = rightHandSide, names = rowNames)

    problem.solve()
    print("Solution status = " + str(problem.solution.get_status()) + ":")
    print(str(problem.solution.status[problem.solution.get_status()]))
    print("Solution value = " + str(problem.solution.get_objective_value()))

    numcols = problem.variables.get_num()
    numrows = problem.linear_constraints.get_num()

    solutionValues =  problem.solution.get_values()
    writeToFile(solutionValues);
            
if __name__ == "__main__":
    runCobrac()