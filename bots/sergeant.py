from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower

from collections import Counter

DEBRIS_DICT = {45: 200, 50: 209, 55: 253, 60: 300, 65: 353, 70: 409, 75: 469, 80: 534, 85: 580, 90: 646, 95: 716, 100: 789, 110: 946, 120: 1116, 130: 1388, 140: 1586, 150: 1796, 160: 2017, 170: 2250, 180: 2494, 190: 2748, 200: 3014, 220: 3578, 240: 4185, 260: 4833, 280: 5523, 300: 6253, 320: 7023, 340: 7833, 360: 8682, 380: 9569, 400: 10495, 420: 11458, 440: 12459, 460: 13497, 480: 14571, 500: 15682, 520: 16829, 540: 18012, 560: 19231, 580: 20484, 600: 21773, 620: 23097, 640: 24455, 660: 25848, 680: 27275, 700: 28736, 720: 30231, 740: 31759, 760: 33321, 780: 34916, 800: 36543, 820: 38204, 840: 39898, 860: 41624, 880: 43383, 900: 45173, 920: 46996, 940: 48851, 960: 50738, 980: 52657, 1000: 54607, 1100: 64826, 1200: 75818, 1300: 87567, 1400: 100063, 1500: 113294, 1600: 127251, 1700: 141923, 1800: 157302, 1900: 173380, 2000: 190150, 2100: 207605, 2200: 225738, 2300: 244542, 2400: 264012, 2500: 284142}

def dist2(x1, y1, x2, y2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2

class BotPlayer(Player):

    def __init__(self, map: Map):
        self.isRush = False
        self.map = map
        self.rushDebrisCost = 0
        self.rushDebrisHealth = 0
        self.next_action = 0
        self.bb_poss = set()
        self.gs_poss = set()
        self.sf_poss = set()
        for (x, y) in map.path:
            if map.is_space(x + 1, y):
                self.bb_poss.add((x + 1, y))
            if map.is_space(x, y + 1):
                self.bb_poss.add((x, y + 1))
            if map.is_space(x - 1, y):
                self.bb_poss.add((x - 1, y))
            if map.is_space(x, y - 1):
                self.bb_poss.add((x, y - 1))
        c = Counter()
        for (x, y) in self.bb_poss:
            for px, py in map.path:
                if dist2(x, y, px, py) <= 10:
                    c[(x, y)] += 1
        self.bb_poss = []
        for ((x, y), cnt) in c.most_common():
            if cnt < 14:
                break
            self.bb_poss.append((x, y))
        self.bb_poss.reverse()
        for (x, y) in map.path:
            if map.is_space(x + 2, y) and not (x + 2, y) in self.bb_poss:
                self.gs_poss.add((x + 2, y))
            if map.is_space(x - 2, y) and not (x - 2, y) in self.bb_poss:
                self.gs_poss.add((x - 2, y))
            if map.is_space(x, y - 2) and not (x, y - 2) in self.bb_poss:
                self.gs_poss.add((x, y - 2))
            if map.is_space(x, y + 2) and not (x, y + 2) in self.bb_poss:
                self.gs_poss.add((x, y + 2))
            if map.is_space(x + 1, y + 1) and not (x + 1, y + 1) in self.bb_poss:
                self.gs_poss.add((x + 1, y + 1))
            if map.is_space(x - 1, y + 1) and not (x - 1, y + 1) in self.bb_poss:
                self.gs_poss.add((x - 1, y + 1))
            if map.is_space(x + 1, y - 1) and not (x + 1, y - 1) in self.bb_poss:
                self.gs_poss.add((x + 1, y - 1))
            if map.is_space(x - 1, y - 1) and not (x - 1, y - 1) in self.bb_poss:
                self.gs_poss.add((x - 1, y - 1))
        c = Counter()
        for (x, y) in self.gs_poss:
            earliest = -1
            latest = -1
            for i in range(len(map.path)):
                px, py = map.path[i]
                if dist2(x, y, px, py) <= 60:
                    if earliest < 0:
                        earliest = i
                    latest = i
                c[(x, y)] = latest - earliest
        self.gs_poss = []
        for ((x, y), cnt) in c.most_common():
            self.gs_poss.append((x, y))
        self.gs_poss.reverse()
        for x in range(map.width):
            for y in range(map.height):
                tile = map.tiles[x][y]
                if map.is_space(x, y) and not (x, y) in self.bb_poss and not (x, y) in self.gs_poss:
                    self.sf_poss.add((x, y))
        self.sf_poss = list(self.sf_poss)

    def play_turn(self, rc: RobotController):
        if self.isRush:
            self.rush(rc, self.rushDebrisCost, self.rushDebrisHealth)
            return
        us = rc.get_ally_team()
        self.check_our_attack(rc)
        while True:
            if self.next_action == 0:
                if not self.bb_poss:
                    self.next_action = 1
                    continue
                (x, y) = self.bb_poss[-1]
                if rc.can_build_tower(TowerType.BOMBER, x, y):
                    self.next_action = 1
                    self.bb_poss.pop()
                    rc.build_tower(TowerType.BOMBER, x, y)
                else:
                    break
            elif 1 <= self.next_action <= 2:
                if not self.gs_poss:
                    self.next_action += 1
                    continue
                (x, y) = self.gs_poss[-1] if self.gs_poss else (0, 0)
                if rc.can_build_tower(TowerType.GUNSHIP, x, y):
                    self.next_action += 1
                    self.gs_poss.pop()
                    rc.build_tower(TowerType.GUNSHIP, x, y)
                else:
                    break
            elif self.next_action >= 3:
                if not self.sf_poss:
                    self.next_action = (self.next_action + 1) % 5
                    continue
                (x, y) = self.sf_poss[-1] if self.sf_poss else (0, 0)
                if rc.can_build_tower(TowerType.SOLAR_FARM, x, y):
                    self.next_action = (self.next_action + 1) % 5
                    self.sf_poss.pop()
                    rc.build_tower(TowerType.SOLAR_FARM, x, y)
                else:
                    break
        towers = rc.get_towers(us)
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

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
        
        #opp_defense, opp_bb, opp_gs = self.check_opp_def(rc)
        #print(f'opp defense{opp_defense}')
        # opp_bb*TowerType.BOMBER.damage 
        #debrisSchedule = get_debris_schedule(rc.get_turn())
        #if debrisSchedule != None:
        #    naturalDebrisCooldown, naturalDebrisHealth = debrisSchedule
        #    opp_defense-=naturalDebrisHealth/naturalDebrisCooldown

        attack_duration = 40
        cost_per_debris = our_balance // attack_duration
        use_health = 0
        for health, cost in DEBRIS_DICT.items():
            if cost > cost_per_debris:
                break
            use_health = health
        expected_damage = 20 * use_health
        if self.estimate_damage(rc, use_health, 40) >= 2500:
            self.isRush = True
            self.rushDebrisCost = DEBRIS_DICT[use_health]
            self.rushDebrisHealth = use_health
            print("RUSHHHHHHH")
        return
        #calculate our attack capability based on opp_bb and opp_gs
        map_length = self.check_map_length(rc)
        expected_damage_per_debris = int(map_length*opp_defense*scale) #buffer
        #print(map_length, opp_defense)
        if expected_damage_per_debris < 45:
            health_debris = 45
        else:
            while expected_damage_per_debris not in DEBRIS_DICT:
                expected_damage_per_debris += 1
            health_debris = expected_damage_per_debris
        health_debris *= 2 #experiment
        # health_debris = 500 #experiment
        num_debris = 2500 // health_debris
        #print(f'debris{health_debris}')
        expected_cost = DEBRIS_DICT[health_debris]*num_debris
        print(expected_cost, our_balance)
        if expected_cost < our_balance:
            self.isRush = True
            self.rushDebrisCost = expected_cost
            self.rushDebrisHealth = health_debris*5 #experiment
            print("RUSHHHHHHH")
    
    def rush(self, rc: RobotController, debrisCost, debrisHealth):
        #priority is to sell solar farms
        us = rc.get_ally_team()
        towers = rc.get_towers(us)
        our_balance = rc.get_balance(us)
        towers = rc.get_towers(us)
        while rc.get_balance(us) < debrisCost and towers:
            back = towers.pop()
            rc.sell_tower(back.id)
        if rc.can_send_debris(1, debrisHealth):
            rc.send_debris(1, debrisHealth)
        return
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
                        if rc.can_send_debris(1, debrisHealth):
                            rc.send_debris(1, debrisHealth)
            elif bomberCount >= numBomberNeeded:
                for tower in towers:
                    if bomberSold  == numBomberNeeded:
                        break
                    if tower.type == TowerType.BOMBER:
                        rc.sell_tower(tower.id)
                        bomberCount -= 1
                        bomberSold += 1
                        if rc.can_send_debris(1, debrisHealth):
                            rc.send_debris(1, debrisHealth)
            
            elif gunshipCount >= numGunshipNeeded:
                for tower in towers:
                    if gunshipSold  == numGunshipNeeded:
                        break
                    if tower.type == TowerType.GUNSHIP:
                        rc.sell_tower(tower.id)
                        gunshipCount -= 1
                        gunshipSold += 1
                        if rc.can_send_debris(1, debrisHealth):
                            rc.send_debris(1, debrisHealth)
        else:
            if rc.can_send_debris(1, debrisHealth):
                rc.send_debris(1, debrisHealth)


    #determine opponent defense capability
    #returns (estimated_defense, number of bombers, number of gunships)
    def estimate_damage(self, rc: RobotController, debrisHealth, numDebris):
        them = rc.get_enemy_team()
        towers = rc.get_towers(them)
        plength = self.check_map_length(rc)

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

        eff_health = debrisHealth - opp_bb * 6.0
        if eff_health <= 0:
            return 0
        eff_num = ((eff_health * numDebris) - (opp_gs * 25.0 * plength / 20.0)) / eff_health
        eff_damage = eff_num * debrisHealth
        print(eff_damage)
        return eff_damage
        #calculates the defense capability based on balance
        #opp_balance = rc.get_balance(them)
        #potential_defense = opp_balance/((TowerType.BOMBER.cost + TowerType.GUNSHIP.cost)/2) * (TowerType.BOMBER.damage/TowerType.BOMBER.cooldown + TowerType.GUNSHIP/TowerType.Gunship.cooldown)/2
        
        #estimated_defense = (defense + potential_defense + rc.get_health(them))*scale  #with buffer of factor of 2      
        defense *= scale                                                                             
        return defense, opp_bb, opp_gs

    def check_map_length(self, rc: RobotController):
        return len(self.map.path)


