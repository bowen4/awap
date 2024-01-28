from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, SnipePriority

GUNSHIP = TowerType.GUNSHIP
BOMBER = TowerType.BOMBER
REINFORCER = TowerType.REINFORCER
SOLAR_FARM = TowerType.SOLAR_FARM
TOWERS = [GUNSHIP, BOMBER, SOLAR_FARM, REINFORCER]
OFFENSE_SIZE = 20


class BotPlayer(Player):
    def __init__(self, mp: Map):
        super().__init__(mp)
        self.map = mp
        self.launch = 0
        self.towers = [0, 0, 0, 0]
        self.min_towers_in_reinforce = 15
        self.late_game = False
        self.next = None

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

    def get_reinforcer_in_range(self, rc, tower_type=SOLAR_FARM):
        for cand_tower in rc.get_towers(rc.get_ally_team()):
            if cand_tower.type == tower_type:
                towers_in_range = rc.sense_towers_within_radius_squared(rc.get_ally_team(), cand_tower.x,
                                                                        cand_tower.y, REINFORCER.range)
                towers_in_range = list(filter(lambda t: t.type == tower_type, towers_in_range))
                index = TOWERS.index(tower_type)
                if len(towers_in_range) > self.min_towers_in_reinforce:
                    best_coords = (cand_tower.x, cand_tower.y)
                    return best_coords[0], best_coords[1], cand_tower
        return None

    def get_optimal(self, tower, rc: RobotController):
        best_coords = (0, 0)

        if tower != REINFORCER:
            results = self.get_reinforcer_in_range(rc, tower)
            if results:
                return results[0], results[1], results[2]

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

        return best_coords[0], best_coords[1], None

    def play_turn(self, rc: RobotController):
        self.build_towers(rc)
        self.towers_attack(rc)
        self.replace_farm(rc)
        if self.late_game:
            self.attack(rc)

    def build_optimal_tower(self, tower, rc):
        x, y, cand_tower = self.get_optimal(tower, rc)
        if rc.can_build_tower(tower, x, y):
            rc.build_tower(tower, x, y)
        elif cand_tower and rc.get_balance(rc.get_ally_team()) > REINFORCER.cost:
            rc.sell_tower(cand_tower.id)
            index = TOWERS.index(tower)
            self.towers[index] -= 1
            rc.build_tower(REINFORCER, x, y)

    @staticmethod
    def get_parity(rc: RobotController, mod):
        return len(rc.get_towers(rc.get_ally_team())) % mod

    def build_towers(self, rc: RobotController):
        # Early Game
        if rc.get_turn() < 2000:
            # order = [1, 0, 2, 1, 0, 2, 1, 0, 2]
            order = [1, 0, 2] * 2 + [3] + [1, 0, 2] * 3
            order = [1, 2] + [0, 2] + [1, 2] + [0, 2] + [3] + [0, 2] + [1, 2] + [0, 2]
            parity = self.get_parity(rc, len(order))
            tower = TOWERS[order[parity]]
            self.towers[order[parity]] += 1
            self.build_optimal_tower(tower, rc)

        # Mid Game
        else:
            # order = [0, 2]
            order = [0, 2] * 3 + [3] + [0, 2] * 4
            parity = self.get_parity(rc, len(order))
            tower = TOWERS[order[parity]]
            self.towers[order[parity]] += 1
            self.build_optimal_tower(tower, rc)

    @staticmethod
    def towers_attack(rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == TowerType.GUNSHIP:
                rc.auto_snipe(tower.id, SnipePriority.FIRST)
            elif tower.type == TowerType.BOMBER:
                rc.auto_bomb(tower.id)

    def sell_farm(self, rc: RobotController, num=1):
        towers = rc.get_towers(rc.get_ally_team())
        for tower in towers:
            if tower.type == SOLAR_FARM:
                rc.sell_tower(tower.id)
                num -= 1
                if num == 0:
                    break

    def get_farm_count(self, rc: RobotController):
        towers = rc.get_towers(rc.get_ally_team())
        count = 0
        for tower in towers:
            if tower.type == SOLAR_FARM:
                count += 1
        return count

    def replace_farm(self, rc: RobotController):
        num_spaces = self.map.height * self.map.width - len(self.map.path) - len(rc.get_towers(rc.get_ally_team()))

        if num_spaces > 0:
            return

        best_coords = (0, 0)
        candidate = None
        best_num = -1
        build_tower = GUNSHIP

        for tower in rc.get_towers(rc.get_ally_team()):
            if tower.type == SOLAR_FARM:
                num = self.get_num_paths_in_range(build_tower, (tower.x, tower.y))
                if num >= best_num:
                    best_num = num
                    candidate = tower
                    best_coords = (tower.x, tower.y)

        if candidate and rc.get_balance(rc.get_ally_team()) > build_tower.cost:
            rc.sell_tower(candidate.id)
            rc.build_tower(build_tower, *best_coords)

        if candidate is None:
            self.late_game = True
            print("LATE GAME?")

    def attack(self, rc: RobotController):
        num_spaces = self.map.height * self.map.width - len(self.map.path) - len(rc.get_towers(rc.get_ally_team()))

        debris = (7, 1000)

        balance = rc.get_balance(rc.get_ally_team())

        offense_cost = OFFENSE_SIZE * rc.get_debris_cost(*debris)

        if balance > offense_cost and num_spaces == 0:
            self.launch = OFFENSE_SIZE

        if self.launch > 0:
            self.launch -= 1
            if rc.can_send_debris(*debris):
                rc.send_debris(*debris)
