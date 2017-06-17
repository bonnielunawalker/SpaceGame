from random import randrange
from agent import Agent
from fighter import Fighter
from bomber import Bomber
from vector2d import Vector2D
from graphics import COLOR_NAMES

fighter_modes = [
    'defend bomber',
    'attack bomber',
    'defend carrier',
    'attack fighter'
]

class Carrier(Agent):
    def __init__(self, team, world, scale=50.0, mass=8000.0):
        super().__init__(team, 150, world, scale, mass)

        self.fighter_squadrons = []
        self.bomber_squadrons = []

        self.fighter_mode = ['defend', 'bomber']

        for i in range(1):
            self.create_fighter_squadron()
            self.create_bomber_squadron()

        self.ship_class = 'carrier'

    def create_fighter_squadron(self, size=5):
        squadron = []

        for i in range(size):
            a = Fighter(self.team, self.world, self, squadron)
            a.parent = self

            if i == 0:
                a.is_squadron_leader = True

            # spawn the fighter at the carrier, slightly randomised
            a.pos = Vector2D(randrange(int(self.pos.x - 10), int(self.pos.x + 10)), randrange(int(self.pos.y - 10), int(self.pos.y + 10)))
            a.fighter_mode = self.fighter_mode

            squadron.append(a)
            self.world.teams[self.color].agents.append(a)

            if self.world.teams[self.team].goal is not None:
                a.set_goal(self.world.teams[self.team].goal)

        self.fighter_squadrons.append(squadron)

    def create_bomber_squadron(self, size=5):
        squadron = []

        for i in range(size):
            a = Bomber(self.team, self.world, self, squadron)
            a.parent = self

            if i == 0:
                a.is_squadron_leader = True

            a.pos = Vector2D(randrange(int(self.pos.x - 10), int(self.pos.x + 10)),
                             randrange(int(self.pos.y - 10), int(self.pos.y + 10)))

            squadron.append(a)
            self.world.teams[self.color].agents.append(a)

            if self.world.teams[self.team].goal is not None:
                a.set_goal(self.world.teams[self.team].goal)

        self.bomber_squadrons.append(squadron)

    def update(self, delta):
        super().update(delta)

        attacker = None

        for squadron in self.bomber_squadrons:
            if len(squadron) > 0:
                if not squadron[0].is_squadron_leader:
                    squadron[0].is_squadron_leader = True

                for agent in squadron:
                    if agent.get_attacker() is not None:
                        attacker = agent.get_attacker()
            else:
                self.bomber_squadrons.remove(squadron)
                self.create_bomber_squadron()

        if attacker is not None:
            self.fighter_mode = 'defend bomber'

        for squadron in self.fighter_squadrons:
            if len(squadron) > 0:
                if not squadron[0].is_squadron_leader:
                    squadron[0].is_squadron_leader = True

                for agent in squadron:
                    agent.fighter_mode = self.fighter_mode

            else:
                self.fighter_squadrons.remove(squadron)
                self.create_fighter_squadron()

    def render(self, color=None):
        super().render(self.color)

    def get_target(self):
        return self.atk_target