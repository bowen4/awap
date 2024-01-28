from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower


class BotPlayer(Player):

    def __init__(self, map: Map):
        self.next_action = 0
        self.bb_poss = []
        self.gs_poss = []
        self.sf_poss = []
        for (x, y) in map.path:
            if map.is_space(x + 1, y):
                self.bb_poss.append((x + 1, y))
            if map.is_space(x, y + 1):
                self.bb_poss.append((x, y + 1))
            if map.is_space(x - 1, y):
                self.bb_poss.append((x - 1, y))
            if map.is_space(x, y - 1):
                self.bb_poss.append((x, y - 1))
        for (x, y) in map.path:
            if map.is_space(x + 2, y) and not (x + 2, y) in self.bb_poss:
                self.gs_poss.append((x + 2, y))
            if map.is_space(x - 2, y) and not (x - 2, y) in self.bb_poss:
                self.gs_poss.append((x - 2, y))
            if map.is_space(x, y - 2) and not (x, y - 2) in self.bb_poss:
                self.gs_poss.append((x, y - 2))
            if map.is_space(x, y + 2) and not (x, y + 2) in self.bb_poss:
                self.gs_poss.append((x, y + 2))
            if map.is_space(x + 1, y + 1) and not (x + 1, y + 1) in self.bb_poss:
                self.gs_poss.append((x + 1, y + 1))
            if map.is_space(x - 1, y + 1) and not (x - 1, y + 1) in self.bb_poss:
                self.gs_poss.append((x - 1, y + 1))
            if map.is_space(x + 1, y - 1) and not (x + 1, y - 1) in self.bb_poss:
                self.gs_poss.append((x + 1, y - 1))
            if map.is_space(x - 1, y - 1) and not (x - 1, y - 1) in self.bb_poss:
                self.gs_poss.append((x - 1, y - 1))
        for x in range(map.width):
            for y in range(map.height):
                tile = map.tiles[x][y]
                if map.is_space(x, y) and not (x, y) in self.bb_poss and not (x, y) in self.gs_poss:
                    self.sf_poss.append((x, y))
        self.bb_poss.reverse()
        self.gs_poss.reverse()

    def play_turn(self, rc: RobotController):
        while True:
            if self.next_action == 0:
                (x, y) = self.bb_poss[-1] if self.bb_poss else (0, 0)
                if rc.can_build_tower(TowerType.BOMBER, x, y):
                    self.next_action = 1
                    self.bb_poss.pop()
                    rc.build_tower(TowerType.BOMBER, x, y)
                else:
                    break
            elif self.next_action == 1:
                (x, y) = self.gs_poss[-1] if self.gs_poss else (0, 0)
                if rc.can_build_tower(TowerType.GUNSHIP, x, y):
                    self.next_action = 2
                    self.gs_poss.pop()
                    rc.build_tower(TowerType.GUNSHIP, x, y)
                else:
                    break
            elif self.next_action == 2:
                (x, y) = self.sf_poss[-1] if self.sf_poss else (0, 0)
                if rc.can_build_tower(TowerType.SOLAR_FARM, x, y):
                    self.next_action = 0
                    self.sf_poss.pop()
                    rc.build_tower(TowerType.SOLAR_FARM, x, y)
                else:
                    break
        us = rc.get_ally_team()
        towers = rc.get_towers(us)
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)


