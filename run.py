'''
Created on Oct 19, 2014

@author: Adam
'''

import itertools
import multiprocessing
import random
import re

def rouletteWheel(selections, key=lambda weight: weight):
    if len(selections) == 0:
        print 'rouletteWheel: no selections'
        return None
    weights = [key(selection) for selection in selections]
    sumWeights = sum(weights)
    draw = random.uniform(0, sumWeights)
    pick = -1
    while draw > 0:
        pick += 1
        draw -= weights[pick]
    
    return selections[pick]
        

class PlayerData:
    def __init__(self, name, value, cost):
        self.name = name
        self.value = value
        self.cost = cost
        
    def __eq__(self, other):
        return self.name == other.name
    
    def __hash__(self):
        return hash(self.name)

def affordableCombinations(players, budget, k = 1):
    if k == 1:
        endIndex = len(players)
        sortedPlayers = sorted(players, key=lambda playerData: playerData.cost)
        while endIndex > 0 and sortedPlayers[endIndex-1].cost > budget:
            endIndex -= 1
        return sortedPlayers[:endIndex]
    else:
        singlePlayerBudget = budget - sum([player.cost for player in players[:k-1]])
        affordablePlayers = affordableCombinations(players, singlePlayerBudget, 1)
        playerCombinations = itertools.combinations(affordablePlayers, k)
        sortedPlayerCombinations = sorted(playerCombinations, key=lambda combination: sum([player.cost for player in combination]))
        endIndex = len(sortedPlayerCombinations)
        while endIndex > 0 and sum([player.cost for player in sortedPlayerCombinations[endIndex-1]]) > budget:
            endIndex -= 1
        return sortedPlayerCombinations[:endIndex]

class Team:
    def __init__(self, qb, rbs, wrs, te, flex, d):
        self.qb = qb
        self.rbs = rbs
        self.wrs = wrs
        self.te = te
        self.flex = flex
        self.d = d
        
    def __str__(self):
        output = self.qb.name + ','
        for rb in self.rbs:
            output += rb.name + ','
        for wr in self.wrs:
            output += wr.name + ','
        output += self.te.name + ','
        output += self.flex.name + ','
        output += self.d.name + ' - ' + str(self.value())
        output += ' - ' + str(self.cost())
        return output
    
    def __eq__(self, other):
        if other is None:
            return False
        eq = self.qb == other.qb
        for rb in self.rbs:
            eq = eq and rb in list(other.rbs) + [other.flex]
        for wr in self.wrs:
            eq = eq and wr in list(other.wrs) + [other.flex]
        eq = eq and self.te in [other.te, other.flex]
        eq = eq and self.flex in list(other.rbs) + list(other.wrs) + [other.te, other.flex]
        eq = eq and self.d == other.d
        return eq
        
    def value(self):
        return self.qb.value + self.rbs[0].value + self.rbs[1].value + self.wrs[0].value + self.wrs[1].value + self.wrs[2].value + self.te.value + self.flex.value + self.d.value

    def cost(self):
        return self.qb.cost + self.rbs[0].cost + self.rbs[1].cost + self.wrs[0].cost + self.wrs[1].cost + self.wrs[2].cost + self.te.cost + self.flex.cost + self.d.cost
        
def createAllTeamCombinations(qbs, rbs, wrs, tes, ds, budget):
    teams = []
    minWRCombinationCost = wrs[0].cost + wrs[1].cost + wrs[2].cost
    minRBCombinationCost = rbs[0].cost + rbs[1].cost
    minFLEXCost = min(wrs[2].cost, rbs[1].cost, tes[0].cost)
    currentBudget = budget - minWRCombinationCost - minRBCombinationCost - tes[0].cost - minFLEXCost - ds[0].cost
    for qb in affordableCombinations(qbs, currentBudget):
        budgetAfterQB = budget - qb.cost
        currentBudget = budgetAfterQB - minRBCombinationCost - tes[0].cost - minFLEXCost - ds[0].cost
        for rbCombo in affordableCombinations(rbs, currentBudget, 2):
            budgetAfterRBS = budgetAfterQB - rbCombo[0].cost - rbCombo[1].cost
            currentBudget = budgetAfterRBS - tes[0].cost - minFLEXCost - ds[0].cost
            for wrCombo in affordableCombinations(wrs, currentBudget, 3):
                budgetAfterWRS = budgetAfterRBS - wrCombo[0].cost - wrCombo[1].cost - wrCombo[2].cost
                currentBudget = budgetAfterWRS - minFLEXCost - ds[0].cost
                for te in affordableCombinations(tes, currentBudget):
                    budgetAfterTE = budgetAfterWRS - te.cost
                    currentBudget = budgetAfterTE - ds[0].cost
                    flexOptions =  [player for player in \
                                   rbs + wrs + tes \
                                   if player not in list(rbCombo) + list(wrCombo) + [te]]
                    for flex in affordableCombinations(flexOptions, currentBudget):
                        budgetAfterFLEX = budgetAfterTE - flex.cost
                        for d in affordableCombinations(ds,budgetAfterFLEX):
                            teams.append(Team(qb, rbCombo, wrCombo, te, flex, d))
    if not teams:
        print 'no teams'
    return teams

def createRandomTeam(qbs, rbs, wrs, tes, ds, budget):
    minRBCombinationCost = rbs[0].cost + rbs[1].cost
    minWRCombinationCost = wrs[0].cost + wrs[1].cost + wrs[2].cost
    minFLEXCost = min(rbs[1].cost, wrs[2].cost, tes[0].cost)
    currentBudget = budget - minRBCombinationCost - minWRCombinationCost - tes[0].cost - minFLEXCost - ds[0].cost
    qbPick = random.choice(affordableCombinations(qbs, currentBudget))
    budgetAfterQB = budget - qbPick.cost
    currentBudget = budgetAfterQB - minWRCombinationCost - tes[0].cost - minFLEXCost - ds[0].cost
    rbPicks = random.choice(affordableCombinations(rbs, currentBudget, 2))
    budgetAfterRBS = budgetAfterQB - rbPicks[0].cost - rbPicks[1].cost
    currentBudget = budgetAfterRBS - tes[0].cost - minFLEXCost - ds[0].cost
    wrPicks = random.choice(affordableCombinations(wrs, currentBudget, 3))
    budgetAfterWRS = budgetAfterRBS - wrPicks[0].cost - wrPicks[1].cost - wrPicks[2].cost
    currentBudget = budgetAfterWRS - minFLEXCost - ds[0].cost
    tePick = random.choice(affordableCombinations(tes, currentBudget))
    budgetAfterTE = budgetAfterWRS - tePick.cost
    currentBudget = budgetAfterTE - ds[0].cost
    flexOptions =  [player for player in \
                    rbs + wrs + tes \
                    if player not in list(rbPicks) + list(wrPicks) + [tePick]]
    flexPick = random.choice(affordableCombinations(flexOptions, currentBudget))
    budgetAfterFLEX = budgetAfterTE - flexPick.cost
    dPick = random.choice(affordableCombinations(ds, budgetAfterFLEX))
    
    return Team(qbPick, rbPicks, wrPicks, tePick, flexPick, dPick)

def cleanPlayers(players, numNeeded=1):
    index = len(players)-1
    values = [player.value for player in players]
    while(index>(numNeeded-1)):
        if max(values[:index-numNeeded+1]) >= players[index].value:
            del players[index]
        index -= 1
    
    print str(len(values) -len(players)) + ' players deleted, ' + str(len(players)) + ' players left'
    
def selectRouletteCombo(args):
    qbs, rbs, wrs, tes, ds = args
    return rouletteWheel(createAllTeamCombinations(qbs, rbs, wrs, tes, ds, 50000), key=lambda team: team.value())
    
if __name__ == '__main__':
    datafile = open('qb.txt')
    qbs = []
    for line in datafile:
        results = re.match('(?P<name>.+?)\t.+?\t\d+\t\d+\t.+?\t(?P<value>.+?)\spts\t\$(?P<cost>.+?)\t.+', line)
        if results:
            qbs.append(PlayerData(results.group('name'), 
                                  float(results.group('value')), 
                                  int(results.group('cost').replace(',',''))))
    qbs = sorted(qbs, key=lambda player: player.cost)
    cleanPlayers(qbs)
    
    datafile = open('rb.txt')
    rbs = []
    for line in datafile:
        results = re.match('(?P<name>.+?)\t.+?\t\d+\t\d+\t.+?\t(?P<value>.+?)\spts\t\$(?P<cost>.+?)\t.+', line)
        if results:
            rbs.append(PlayerData(results.group('name'), 
                                  float(results.group('value')), 
                                  int(results.group('cost').replace(',',''))))
    rbs = sorted(rbs, key=lambda player: player.cost)
    cleanPlayers(rbs, 3)
    
    datafile = open('wr.txt')
    wrs = []
    for line in datafile:
        results = re.match('(?P<name>.+?)\t.+?\t\d+\t\d+\t.+?\t(?P<value>.+?)\spts\t\$(?P<cost>.+?)\t.+', line)
        if results:
            wrs.append(PlayerData(results.group('name'), 
                                  float(results.group('value')), 
                                  int(results.group('cost').replace(',',''))))
    wrs = sorted(wrs, key=lambda player: player.cost)
    cleanPlayers(wrs, 4)
    
    datafile = open('te.txt')
    tes = []
    for line in datafile:
        results = re.match('(?P<name>.+?)\t.+?\t\d+\t\d+\t.+?\t(?P<value>.+?)\spts\t\$(?P<cost>.+?)\t.+', line)
        if results:
            tes.append(PlayerData(results.group('name'), 
                                  float(results.group('value')), 
                                  int(results.group('cost').replace(',',''))))
    tes = sorted(tes, key=lambda player: player.cost)
    cleanPlayers(tes, 2)
    
    datafile = open('d.txt')
    ds = []
    for line in datafile:
        results = re.match('(?P<name>.+?)\t.+?\t\d+\t\d+\t.+?\t(?P<value>.+?)\spts\t\$(?P<cost>.+?)\t.+', line)
        ds.append(PlayerData(results.group('name'), 
                             float(results.group('value')), 
                             int(results.group('cost').replace(',',''))))
    ds = sorted(ds, key=lambda player: player.cost)
    cleanPlayers(ds)
    
    playersPicked = {'qbs' : dict([(player, False) for player in qbs]),
                     'rbs' : dict([(player, False) for player in rbs]),
                     'wrs' : dict([(player, False) for player in wrs]),
                     'tes' : dict([(player, False) for player in tes]),
                     'ds'  : dict([(player, False) for player in ds])}
    
    teams = []
    print 'Setting up starting population'
    while True in [False in picked.values() for picked in playersPicked.values()] or len(teams) < 50:
        team = createRandomTeam(qbs, rbs, wrs, tes, ds, 50000)
        playersPicked['qbs'][team.qb] = True
        playersPicked['rbs'][team.rbs[0]] = True
        playersPicked['rbs'][team.rbs[1]] = True
        playersPicked['wrs'][team.wrs[0]] = True
        playersPicked['wrs'][team.wrs[1]] = True
        playersPicked['wrs'][team.wrs[2]] = True
        playersPicked['tes'][team.te] = True
        if team.flex in rbs:
            playersPicked['rbs'][team.flex] = True
        elif team.flex in wrs:
            playersPicked['wrs'][team.flex] = True
        elif team.flex in tes:
            playersPicked['tes'][team.flex] = True
        playersPicked['ds'][team.d] = True
        teams.append(team)
    
    teams = sorted(teams, key=lambda team: team.value())
    print 'Population size is : ' + str(len(teams))
    print 'Best team is : ' + str(teams[-1])
    bestTeam = teams[-1]
    pool = multiprocessing.Pool()
    for i in xrange(100000):
        print 'Creating generation ' + str(i)
        pairings = []
        for j in xrange(len(teams)):
            parent1 = rouletteWheel(teams, key=lambda team: team.value())
            parent2 = rouletteWheel(teams, key=lambda team: team.value())
            while parent2 == parent1:
                parent2 = rouletteWheel(teams, key=lambda team: team.value())
            qbOptions = [parent1.qb]
            qbOptions +=  [qb for qb in [parent2.qb] if qb not in qbOptions]
            rbOptions = list(parent1.rbs)
            rbOptions += [rb for rb in list(parent2.rbs) if rb not in rbOptions]
            wrOptions = list(parent1.wrs)
            wrOptions += [wr for wr in list(parent2.wrs) if wr not in wrOptions]
            teOptions = [parent1.te]
            teOptions +=  [te for te in [parent2.te] if te not in teOptions]
            dOptions = [parent1.d]
            dOptions +=  [d for d in [parent2.d] if d not in dOptions]
            if parent1.flex in rbs and parent1.flex not in rbOptions:
                rbOptions.append(parent1.flex)
            elif parent1.flex in wrs and parent1.flex not in wrOptions:
                wrOptions.append(parent1.flex)
            elif parent1.flex in tes and parent1.flex not in teOptions:
                teOptions.append(parent1.flex)
            if parent2.flex in rbs and parent2.flex not in rbOptions:
                rbOptions.append(parent2.flex)
            elif parent2.flex in wrs and parent2.flex not in wrOptions:
                wrOptions.append(parent2.flex)
            elif parent2.flex in tes and parent2.flex not in teOptions:
                teOptions.append(parent2.flex)
            pick = random.randint(0, 4)
            if pick == 0:
                qbOptions += [qb for qb in [random.choice(qbs)] if qb not in qbOptions]
            elif pick == 1:
                rbOptions += [rb for rb in [random.choice(rbs)] if rb not in rbOptions]
            elif pick == 2:
                wrOptions += [wr for wr in [random.choice(wrs)] if wr not in wrOptions]
            elif pick == 3:
                teOptions += [te for te in [random.choice(tes)] if te not in teOptions]
            elif pick == 4:
                dOptions += [d for d in [random.choice(ds)] if d not in dOptions]
                
            pairings.append((sorted(qbOptions, key=lambda player: player.cost), 
                             sorted(rbOptions, key=lambda player: player.cost), 
                             sorted(wrOptions, key=lambda player: player.cost), 
                             sorted(teOptions, key=lambda player: player.cost), 
                             sorted(dOptions, key=lambda player: player.cost)))
            
        
        teams = pool.map(selectRouletteCombo, pairings)
        for j in xrange(1, len(teams) - 1):
            while teams[j] is None or teams[j] in teams[j+1:] or teams[j] in teams[:j-1]:
                teams[j] = createRandomTeam(qbs, rbs, wrs, tes, ds, 50000)
                print 'random team created'
        teams = sorted(teams, key=lambda team: team.value())
        if teams[-1].value() > bestTeam.value():
            bestTeam = teams[-1]
        
        print 'Best of generation : ' + str(teams[-1]) 
        print 'Best team is : ' + str(bestTeam)