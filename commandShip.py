from agent import *

class CommandShip(Agent):
    def __init__(self, team, world, scale=60.0, mass=8000.0):
        super().__init__(team, 400, world, scale, mass)

        self.ship_class = 'command ship'