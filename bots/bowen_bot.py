from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower

from collections import Counter
import heapq

DEBRIS_COST = [200,
209,
253,
300,
353,
409,
469,
534,
580,
646,
716,
789,
946,
1116,
1388,
1586,
1796,
2017,
2250,
2494,
2748,
3014,
3578,
4185,
4833,
5523,
6253,
7023,
7833,
8682,
9569,
10495,
11458,
12459,
13497,
14571,
15682,
16829,
18012,
19231,
20484,
21773,
23097,
24455,
25848,
27275,
28736,
30231,
31759,
33321,
34916,
36543,
38204,
39898,
41624,
43383,
45173,
46996,
48851,50738,52657,54607,64826,75818,87567,100063,113294,127251,141923,157302,173380,190150,207605,225738,244542,264012,284142]

def dist2(x1, y1, x2, y2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2
class BotPlayer(Player):
    def __init__(self, map: Map):
        super().__init__(map)
        self.offense = False
        self.isRush = False
        self.rushDebrisCost = 0
        self.rushDebrisHealth = 0
        self.bomber_pq = []
        self.other_pq = []
        self.bomber_score = Counter()
        # find bomber tiles
        for x in range(map.width):
            for y in range(map.height):
                if not map.is_space(x, y):
                    continue
                for (px, py) in map.path:
                    if dist2(x, y, px, py) <= 10:
                        self.bomber_score[(x, y)] += 1
        for ((x, y), score) in self.bomber_score.most_common():
            heapq.heappush(self.bomber_pq, (-score, x, y))
            heapq.heappush(self.other_pq, (score, x, y))

    def play_turn(self, rc: RobotController):
        if self.isRush:
            self.rush(rc, self.rushDebrisCost, self.rushDebrisHealth)
        us = rc.get_ally_team()
        cash = rc.get_balance(us)
        while cash >= 1750 and self.bomber_pq and not self.offense:
            if self.bomber_pq[0][0] >= -2:
                self.offense = True
            (s, x, y) = heapq.heappop(self.bomber_pq)
            rc.build_tower(TowerType.BOMBER, x, y)
            cash -= 1750
        if self.offense:
            while cash >= 53:
                rc.send_debris(1, 25)
                cash -= 53
        towers = rc.get_towers(us)
        for tower in towers:
            if rc.can_bomb(tower.id):
                rc.bomb(tower.id)
    
    #determines our attack capability
    def check_our_attack(self, rc: RobotController):
        us = rc.get_ally_team()
        towers = rc.get_towers(us)
        our_balance = rc.get_balance(us)
        scale = 1.2 #buffer scale

        #calculates the balance if every tower is sold
        for tower in towers:
            if tower.type == TowerType.BOMBER:
                our_balance += TowerType.BOMBER.cost*0.8
            elif tower.type == TowerType.GUNSHIP:
                our_balance += TowerType.GUNSHIP.cost*0.8
            elif tower.type == TowerType.SOLAR_FARM:
                our_balance += TowerType.SOLAR_FARM.cost*0.8
            else:
                our_balance += TowerType.REINFORCER.cost*0.8
        
        opp_defense, opp_bb, opp_gs = self.check_opp_def(rc)
        # opp_bb*TowerType.BOMBER.damage 

        #calculate our attack capability based on opp_bb and opp_gs
        map_length = self.check_map_length(rc)
        expected_damage_per_debris = map_length*opp_defense*scale #buffer
        health_debris = expected_damage_per_debris
        num_debris = 2500 // health_debris
        if health_debris < 24:
            expected_cost = DEBRIS_COST[0]*num_debris
        else:
            expected_cost = DEBRIS_COST[health_debris-24]*num_debris

        if expected_cost < our_balance:
            self.isRush = True
            self.rushDebrisCost = expected_cost
            self.rushDebrisHealth = health_debris
    
    def rush(self, rc: RobotController, debrisCost, debrisHealth):
        #priority is to sell solar farms
        us = rc.get_ally_team()
        towers = rc.get_towers(us)
        our_balance = rc.get_balance(us)
        if debrisCost>our_balance:
            shortage = debrisCost - our_balance
            numSolarNeeded = shortage // TowerType.SOLAR_FARM.cost + 1
            numGunshipNeeded = shortage // TowerType.GUNSHIP.cost + 1
            numBomberNeeded = shortage // TowerType.BOMBER.cost + 1
            numReinforcerqNeeded = shortage // TowerType.REINFORCER.cost + 1
        solarCount = 0
        gunshipCount = 0
        bomberCount = 0
        reinforcerCount = 0
        for tower in towers:
            if tower.type == TowerType.SOLAR_FARM:
                solarCount += 1
            elif tower.type == TowerType.GUNSHIP:
                gunshipCount += 1
            elif tower.type == TowerType.BOMBER:
                bomberCount += 1
            else:
                reinforcerCount += 1
        
        #iniitate selling
        solarSold = 0
        gunshipSold = 0
        bomberSold = 0
        reinforcerSold = 0

        #sell solar farms
        if solarCount >= numSolarNeeded:
            for tower in towers:
                if solarSold  == numSolarNeeded:
                    break
                if tower.type == TowerType.SOLAR_FARM:
                    rc.sell_tower(tower.id)
                    solarCount -= 1
                    solarSold += 1
            rc.send_debris(1, debrisHealth)
        elif bomberCount >= numBomberNeeded:
            for tower in towers:
                if bomberSold  == numBomberNeeded:
                    break
                if tower.type == TowerType.BOMBER:
                    rc.sell_tower(tower.id)
                    bomberCount -= 1
                    bomberSold += 1
        
        elif gunshipCount >= numGunshipNeeded:
            for tower in towers:
                if gunshipSold  == numGunshipNeeded:
                    break
                if tower.type == TowerType.GUNSHIP:
                    rc.sell_tower(tower.id)
                    gunshipCount -= 1
                    gunshipSold += 1



        #




        
        
    
    
    #determine opponent defense capability
    #returns (estimated_defense, number of bombers, number of gunships)
    def check_opp_def(self, rc: RobotController):
        them = rc.get_enemy_team()
        towers = rc.get_towers(them)
        defense = 0
        opp_bb = 0
        opp_gs = 0
        scale = 1.5

        #calculates the defense capability based on current towers (DPS)
        for tower in towers:
            if tower.type == TowerType.BOMBER:
                defense += TowerType.BOMBER.damage/TowerType.BOMBER.cooldown
                opp_bb += 1
            elif tower.type == TowerType.GUNSHIP:
                defense += TowerType.GUNSHIP.damage/TowerType.GUNSHIP.cooldown
                opp_gs += 1
        
        #calculates the defense capability based on balance
        #opp_balance = rc.get_balance(them)
        #potential_defense = opp_balance/((TowerType.BOMBER.cost + TowerType.GUNSHIP.cost)/2) * (TowerType.BOMBER.damage/TowerType.BOMBER.cooldown + TowerType.GUNSHIP/TowerType.Gunship.cooldown)/2
        
        #estimated_defense = (defense + potential_defense + rc.get_health(them))*scale  #with buffer of factor of 2      
        defense *= scale                                                                             
        return defense, opp_bb, opp_gs

    def check_map_length(self, rc: RobotController):
        return len(self.map.path)


