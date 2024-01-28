from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower

from collections import Counter

def dist2(x1, y1, x2, y2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2

class BotPlayer(Player):

    def __init__(self, map: Map):
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
        us = rc.get_ally_team()
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
                (x, y) = self.gs_poss[-1] if self.gs_poss else (0, 0)
                if rc.can_build_tower(TowerType.GUNSHIP, x, y):
                    self.next_action += 1
                    self.gs_poss.pop()
                    rc.build_tower(TowerType.GUNSHIP, x, y)
                else:
                    break
            elif self.next_action >= 3:
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


