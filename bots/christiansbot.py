import random
from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower

from collections import Counter

import numpy as np

def dist2(x1, y1, x2, y2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2

class BotPlayer(Player):
    
    def __init__(self, map: Map):
        self.map = map
        self.next_action = 0
        self.bb_poss = set()
        self.gs_poss = set()
        self.sf_poss = set()
        self.enemyTowerCount = []
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
            if cnt < 9:
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
        self.build_towers(rc)
        self.towers_attack(rc)
    
    def scheduled_observer(self, turn, rc: RobotController):
        upper = turn + 100
        totHP = 0
        k = 0
        for i in range(turn, upper):
            if get_debris_schedule(i) != None:
                x, y = get_debris_schedule(i)
                totHP += y
                k += 1
        if k != 0: return totHP/ k
        else: return 0

    def xDamage(self, team, rc: RobotController):
        towers = rc.get_towers(team)
        xD = 0
        k = 0
        if len(towers) != 0:
            for i in towers:
                #print("yes")
                number = i.type
                #print(number.damage)
                if number.damage != 0:
                    xD += number.damage/number.cooldown
                    k += 1
            return xD * k
        else: return 0
    
    def enemyHP(self, enemy, rc: RobotController):
        enemies = rc.get_debris(enemy)
        numEnemies = len(enemies)
        totalHP = 0
        k = 0
        if numEnemies != 0:
            for i in enemies:
                if i.health != 0:
                    totalHP += i.health
                    k += 1
            return totalHP / k
        else: return 0

    def enemyTower(self, team, rc:RobotController):
        enemyTowers = rc.get_towers(team)
        self.enemyTowerCount.append(len(enemyTowers))
        if len(self.enemyTowerCount) > 40:
            self.enemyTowerCount.pop(0)
        return np.gradient(np.array(self.enemyTowerCount, dtype=float)).tolist()

    def counter(self, rc: RobotController):
        them = rc.get_enemy_team()
        gradients = self.enemyTower(them)
        for i in range(30, 40):
            if gradients[i] < 0:
                EXPECTED_DAMAGE -= 1
                PROBABILITY_SNIPER -= 0.01

    def build_towers(self, rc: RobotController):
        us = rc.get_ally_team()
        them = rc.get_enemy_team()
        r = self.xDamage(us, rc)
        f = self.enemyHP(us, rc)
        #print(r, f)
        future = self.scheduled_observer(rc.get_turn(), rc)
        prob_sniper = min(future, 50) / 50
        print(r, f, prob_sniper)
        #print(self.bb_poss)
        val = random.randrange(0, 1) # randomly select a tower
        if r - 35< f:
            if val < prob_sniper:
                (x, y) = self.gs_poss[-1]
                if rc.can_build_tower(TowerType.GUNSHIP, x, y):
                    self.gs_poss.pop()
                    rc.build_tower(TowerType.GUNSHIP, x, y)         
            else:
                (x, y) = self.bb_poss[-1]
                if rc.can_build_tower(TowerType.BOMBER, x, y):
                    self.bb_poss.pop()
                    rc.build_tower(TowerType.BOMBER, x, y)  
        elif r -35>= f:
            if val < prob_sniper:
                (x, y) = self.sf_poss[-1]
                if rc.can_build_tower(TowerType.SOLAR_FARM, x, y):
                    self.sf_poss.pop()
                    rc.build_tower(TowerType.SOLAR_FARM, x, y)  
        
    
    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)
    
    def player_attack(self, rc: RobotController):
        enemy = rc.get_enemy_team()
        r = self.xDamage(enemy, rc)
        f = self.enemyHP(enemy, rc)
        g = 0
        b = 0
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                g += 1
            elif tower.type == TowerType.BOMBER:
                b += 1
        if g > b and r < f and rc.can_send_debris(10, 1000):
            rc.send_debris(10, 1000)


