from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower
import random

GUNSHIP = TowerType.GUNSHIP
BOMBER = TowerType.BOMBER
REINFORCER = TowerType.REINFORCER
SOLAR_FARM = TowerType.SOLAR_FARM


class BotPlayer(Player):
    def __init__(self, mp: Map):
        super().__init__(mp)
        self.map = mp

    @staticmethod
    def in_range(tower, tower_coords, target_coords):
        difference = (tower_coords[0] - target_coords[0]) ** 2 + (tower_coords[1] - target_coords[1]) ** 2
        return difference <= tower.range

    def get_num_in_range(self, tower, tower_coords):
        num = 0
        for i in self.map.path:
            if self.in_range(tower, tower_coords, i):
                num += 1
        return num

    def get_optimal(self, tower, rc: RobotController):
        best_num = -1
        best_coords = (0, 0)

        for x in range(self.map.width):
            for y in range(self.map.height):
                if not rc.can_build_tower(tower, x, y):
                    continue
                num = self.get_num_in_range(tower, (x, y))
                if num >= best_num:
                    best_num = num
                    best_coords = (x, y)

        return best_coords[0], best_coords[1]

    def play_turn(self, rc: RobotController):
        self.build_towers(rc)
        self.towers_attack(rc)

    def build_optimal_tower(self, tower, rc):
        x, y = self.get_optimal(tower, rc)
        if rc.can_build_tower(tower, x, y):
            rc.build_tower(tower, x, y)

    def build_towers(self, rc: RobotController):
        if rc.get_turn() == 1:
            for i in range(2):
                self.build_optimal_tower(GUNSHIP, rc)
        else:
            parity = len(rc.get_towers(rc.get_ally_team())) % 2

            if parity == 0:
                self.build_optimal_tower(GUNSHIP, rc)
            else:
                self.build_optimal_tower(BOMBER, rc)

    @staticmethod
    def towers_attack(rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)
