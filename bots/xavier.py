from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, SnipePriority

GUNSHIP = TowerType.GUNSHIP
BOMBER = TowerType.BOMBER
REINFORCER = TowerType.REINFORCER
SOLAR_FARM = TowerType.SOLAR_FARM
TOWERS = [GUNSHIP, BOMBER, SOLAR_FARM, REINFORCER]


class BotPlayer(Player):
    def __init__(self, mp: Map):
        super().__init__(mp)
        self.map = mp

    @staticmethod
    def in_range(tower, tower_coords, target_coords):
        difference = (tower_coords[0] - target_coords[0]) ** 2 + (tower_coords[1] - target_coords[1]) ** 2
        return difference <= tower.range

    def get_num_paths_in_range(self, tower, tower_coords):
        num = 0
        for i in self.map.path:
            if self.in_range(tower, tower_coords, i):
                num += 1
        return num

    def get_num_towers_in_range(self, tower, tower_coords, rc, towers=None):
        if towers is None:
            towers = [GUNSHIP, BOMBER, REINFORCER]
        num = 0
        for i in rc.get_towers(rc.get_ally_team()):
            if i.type in towers and self.in_range(tower, tower_coords, (i.x, i.y)):
                num += 1
        return num

    def get_optimal(self, tower, rc: RobotController):
        best_coords = (0, 0)

        if tower == GUNSHIP or tower == BOMBER:
            best_num = -1
            for x in range(self.map.width):
                for y in range(self.map.height):
                    if not rc.can_build_tower(tower, x, y):
                        continue
                    num = self.get_num_paths_in_range(tower, (x, y))
                    if num >= best_num:
                        best_num = num
                        best_coords = (x, y)

        elif tower == SOLAR_FARM:
            best_num = 10000000
            for x in range(self.map.width):
                for y in range(self.map.height):
                    if not rc.can_build_tower(tower, x, y):
                        continue
                    num = self.get_num_paths_in_range(GUNSHIP, (x, y)) \
                        - self.get_num_towers_in_range(REINFORCER, (x, y), rc, towers=[SOLAR_FARM])
                    if num < best_num:
                        best_num = num
                        best_coords = (x, y)

        else:  # REINFORCER
            best_num = -1
            for x in range(self.map.width):
                for y in range(self.map.height):
                    if not rc.can_build_tower(tower, x, y):
                        continue
                    num = self.get_num_towers_in_range(REINFORCER, (x, y), rc)
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

    @staticmethod
    def get_parity(rc: RobotController, mod):
        return len(rc.get_towers(rc.get_ally_team())) % mod

    def build_towers(self, rc: RobotController):
        # Early Game
        if rc.get_turn() < 2000:
            # order = [1, 0, 2, 1, 0, 2, 1, 0, 2]
            order = [1, 0, 2] * 2 + [3] + [1, 0, 2] * 3
            parity = self.get_parity(rc, len(order))
            tower = TOWERS[order[parity]]
            self.build_optimal_tower(tower, rc)

        # Mid Game
        else:
            # order = [0, 2]
            order = [0, 2] * 3 + [3] + [0, 2] * 4
            parity = self.get_parity(rc, len(order))
            tower = TOWERS[order[parity]]
            self.build_optimal_tower(tower, rc)

    @staticmethod
    def towers_attack(rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)
