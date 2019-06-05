'''
CIS 510: Multiagent Systems
HW3
Adib Mosharrof

max vDefender
    s.t.
    r1 -> z1+z2+z3 ... zn = 1 --- number of targets
    r2 -> q1+q2+q3 ... qn >= 1 
    r3 -> x1+x2+x3 ....xn <=2 --- coverage probability of each target, 
                            sum should be less than number of resources
    
    r4 to r8
    Find attacker optimal targets
    vA + (UAU - UAC)xt' >= UAU
    r9 to r13
    vA + (UAU - UAC)xt' + M zt <= M + UAU
    
    Find E-optimal targets
    r14 to r18
    vA + (UAU - UAC)xt' + Eqt >= E + UAU
    r19 to r23
    vA + (UAU - UAC)xt' + Mqt < E+M+UAU
    
    Perceived strategy
    x't + (Alpha -1)xt = Alpha/NumTargets
    
    Defender worst case utility
    vD + (UDU - UDC)xt + Mqt < M+ UDU

'''

import sys
import csv
import cplex
import copy
from decimal import *

numOfTargets = None
numOfResources = None
M = 1000
alpha = None
E = None

payoffMatrix = []

def loadData():
    global numOfTargets,numOfResources,alpha, E
    
    with open('param.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in spamreader:
            numOfTargets = int(row[0])
            numOfResources = int(row[1])
            alpha = float(row[2])
            E = float(row[3])

    with open('payoff.csv', newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in spamreader:
            row.pop(0)
            for i in range(len(row)):
                row[i] = int(row[i])
            payoffMatrix.append(row)

def getObjective():
    #updated
    #objective function is to maximize vDefender, so only vDefender coefficient will be 1,
    #rest will be 0
    objective = []
    #making coefficients of all z, q, x and x' 0
    for i in range(numOfTargets*4):
        objective.append(0.0)

    #vDefender is 1
    objective.append(1.0)
    #vAttacker is 0
    objective.append(0.0)
    return objective

def getUpperBounds():
    #updated
    upperBounds = []

    #upper bound for z,q, x and x' is 1
    for i in range(numOfTargets*4):
        upperBounds.append(1.0)

    #upper bounds for vDefender and vAttacker is infinity
    upperBounds.append(cplex.infinity)
    upperBounds.append(cplex.infinity)
    return upperBounds

def getLowerBounds():
    #updated
    lowerBounds = []
    #upper bound for z, q, x and x' is 1
    for i in range(numOfTargets*4):
        lowerBounds.append(0.0)

    #upper bounds for vDefender and vAttacker is infinity
    lowerBounds.append(-1* cplex.infinity)
    lowerBounds.append(-1* cplex.infinity)
    return lowerBounds

def getCTypes():
    #updated
    cTypes = ''
    
    #z is an integer {0,1} which represents whether a target will be attacked or not
    cTypes += numOfTargets*'I'
    #q is an integer {0,1}, which represents the targets within E of optimal target
    cTypes += numOfTargets*'I'
    #x is the probabilty distribution [0,1]
    cTypes += numOfTargets*'C'
    #x' is the probabilty distribution [0,1]
    cTypes += numOfTargets*'C'
    
    #continues values for vDefender and vAttacker
    cTypes +='CC'
    return cTypes;

def getColumnNames():
    #updated
    columnNames = []
    names = ['z', 'q', 'x', 'x\'']
    for name in names:
        for i in range(numOfTargets):
            columnNames.append(name+str(i+1))

    
    columnNames.append('vDefender')    
    columnNames.append('vAttacker')
    return columnNames

def getRightHandSide():
    rhs = []

    #r1
    rhs.append(1.0)
    #r2
    rhs.append(1.0)
    #r3
    rhs.append(numOfResources)

    #attacker optimal target
    #utility of AttackerUncovered is at index 2
    for i in range(numOfTargets):
        rhs.append(payoffMatrix[i][2])
    for i in range(numOfTargets):
        rhs.append(M+payoffMatrix[i][2])
        
    #attacker E-optimal target
    for i in range(numOfTargets):
        rhs.append(E+payoffMatrix[i][2])
    for i in range(numOfTargets):
        rhs.append(E+M+payoffMatrix[i][2])
        
    #perceived strategy
    for i in range(numOfTargets):
        rhs.append(alpha/numOfTargets)
        
    #defender worst case utility
    for i in range(numOfTargets):
        rhs.append(M+payoffMatrix[i][1])    

    return rhs

def getRowNames():
    numOfContstraints = numOfTargets*6 + 3
    rowNames = []
    for i in range(numOfContstraints):
        rowNames.append("r"+str(i+1))
    return rowNames

def getSense():
    #sense is used to denote inequality of each constraint, 
    sense = ''
    #sum of z has an equal constraint
    sense += 'E'
    #sum of q is greater than
    sense += 'G'
    #sum of x has less than constraint
    sense += 'L'
    #attacker optimal target
    sense += numOfTargets *'G'
    sense += numOfTargets*'L'
    #attacker E-optimal target
    sense += numOfTargets *'G'
    sense += numOfTargets*'L'
    #perceived strategy
    sense += numOfTargets*'E'
    #defender worst case utility
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
    qNames = []
    qCoefficients = []
    xNames = []
    xCoefficients = []

    for i in range(numOfTargets):
        zNames.append("z"+ str(i+1))
        zCoefficients.append(1.0)
        
        qNames.append("q"+ str(i+1))
        qCoefficients.append(1.0)
        
        xNames.append("x"+ str(i+1))
        xCoefficients.append(1.0)

    rows.append([zNames, zCoefficients])
    rows.append([qNames, qCoefficients])
    rows.append([xNames, xCoefficients])

    variables = []
    coefficients = []

    #attacker optimal target
    #vA + (UAU - UAC)xt' >= UAU
    for i in range(numOfTargets):
        variables = ['vAttacker', "x'"+str(i+1)]
        coefficients = [1.0, payoffMatrix[i][2]- payoffMatrix[i][3]]
        addDataToRows(rows, variables, coefficients)


    #attacker optimal target
    #vA + (UAU - UAC)xt' + M zt <= M + UAU
    for i in range(numOfTargets):
        variables = ['vAttacker', "x'"+str(i+1), "z"+str(i+1)]
        coefficients = [1.0, payoffMatrix[i][2] - payoffMatrix[i][3], M]
        addDataToRows(rows, variables, coefficients)
    
    #attacker E-optimal target
    #vA + (UAU - UAC)xt' + Eqt >= E + UAU
    for i in range(numOfTargets):
        variables = ['vAttacker', "x'"+str(i+1), "q"+str(i+1)]
        coefficients = [1.0, payoffMatrix[i][2]- payoffMatrix[i][3], E]
        addDataToRows(rows, variables, coefficients)


    #attacker E-optimal target
    #vA + (UAU - UAC)xt' + Mqt < E+M+UAU
    for i in range(numOfTargets):
        variables = ['vAttacker', "x'"+str(i+1), "q"+str(i+1)]
        coefficients = [1.0, payoffMatrix[i][2] - payoffMatrix[i][3], M]
        addDataToRows(rows, variables, coefficients)

    #perceived strategy
    #x't + (Alpha -1)xt = Alpha/NumTargets
    for i in range(numOfTargets):
        variables = ["x'"+str(i+1), "x"+str(i+1)]
        coefficients = [1.0, alpha-1]
        addDataToRows(rows, variables, coefficients)
        
    #Defender worst case utility
    #vD + (UDU - UDC)xt + Mqt < M+ UDU
    for i in range(numOfTargets):
        variables = ['vDefender', "x"+str(i+1), "q"+str(i+1)]
        coefficients = [1.0, payoffMatrix[i][1] - payoffMatrix[i][0], M]
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
                writer.writerow( [str(i + 1), str(values[i + numOfTargets*2])])

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