from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import TowerType, Team, Tile, GameConstants, SnipePriority, get_debris_schedule
from src.debris import Debris
from src.tower import Tower

from collections import Counter
import heapq

def dist2(x1, y1, x2, y2):
    return (x1 - x2) ** 2 + (y1 - y2) ** 2
class BotPlayer(Player):
    def __init__(self, map: Map):
        super().__init__(map)
        self.bomber_pq = []
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

    def play_turn(self, rc: RobotController):
        us = rc.get_ally_team()
        cash = rc.get_balance(us)
        while cash >= 1750 and self.bomber_pq:
            (s, x, y) = heapq.heappop(self.bomber_pq)
            rc.build_tower(TowerType.BOMBER, x, y)
        towers = rc.get_towers(us)
        for tower in towers:
            if rc.can_bomb(tower.id):
                rc.bomb(tower.id)

