from src.player import Player
from src.map import Map
from src.robot_controller import RobotController


class BotPlayer(Player):
    def __init__(self, mp: Map):
        super().__init__(mp)
        self.map = mp

    def play_turn(self, rc: RobotController):
        debris = (1, 45)

        if rc.can_send_debris(*debris):
            rc.send_debris(*debris)

