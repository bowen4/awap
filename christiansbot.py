import random
from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower

class BotPlayer(Player):
    
    def __init__(self, map: Map):
        self.map = map

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
            return totalHP / (10*k)
        else: return 0

    def build_towers(self, rc: RobotController):
        us = rc.get_ally_team()
        them = rc.get_enemy_team()
        r = self.xDamage(us, rc)
        f = self.enemyHP(us, rc)
        #print(r, f)
        future = self.scheduled_observer(rc.get_turn(), rc)
        prob_sniper = min(future, 100) / 100
        print(r, f, prob_sniper)
        x = random.randint(0, self.map.height-1)
        y = random.randint(0, self.map.height-1)
        val = random.randrange(0, 1) # randomly select a tower
        if r < f:
            if val < prob_sniper: tower = 1
            else: tower = 2
            if (rc.can_build_tower(TowerType.GUNSHIP, x, y) and 
                rc.can_build_tower(TowerType.BOMBER, x, y) and
                rc.can_build_tower(TowerType.SOLAR_FARM, x, y) and
                rc.can_build_tower(TowerType.REINFORCER, x, y)
            ) and (r < f):
                if tower == 1:
                    rc.build_tower(TowerType.BOMBER, x, y)
                elif tower == 2:
                    rc.build_tower(TowerType.GUNSHIP, x, y)
        elif r >= f:
            if val < prob_sniper: tower = 3
            else: tower = 4
            if (rc.can_build_tower(TowerType.GUNSHIP, x, y) and 
                rc.can_build_tower(TowerType.BOMBER, x, y) and
                rc.can_build_tower(TowerType.SOLAR_FARM, x, y) and
                rc.can_build_tower(TowerType.REINFORCER, x, y)
            ) and (r < f):
                if tower == 3:
                    rc.build_tower(TowerType.SOLAR_FARM, x, y)
                elif tower == 4:
                    rc.build_tower(TowerType.REINFORCER, x, y)
        
    
    def towers_attack(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

