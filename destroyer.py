from agent import Agent, WEAPON_LIFETIMES, WEAPON_SPEEDS

class Destroyer(Agent):
    def __init__(self, team, world, weapon='plasma cannon', scale=10.0, mass=60.0):
        super().__init__(team, 60, world, scale, mass)
        self.weapon_type = weapon
        self.firing_range = WEAPON_LIFETIMES[self.weapon_type] * WEAPON_SPEEDS[self.weapon_type]
        self.aggro_range = self.firing_range * 1.75

        self.ship_class = 'destroyer'


    def update(self, delta):
        self.get_target()
        self.update_mode(delta)
        super().update(delta)

        if self.target is not None and self.target.is_alive():
            self.mode = 'engage'
        else:
            self.mode = 'patrol'

        if self.mode == 'engage' and self.engagement_mode == 'ready' and self.target is not None:
            self.shoot()

    def update_mode(self, delta):
        if self.target is not None:
            self.mode = 'engage'
            self.track(self.target)

        if self.reload_time_remaining <= 0:
            self.engagement_mode = 'ready'
        else:
            self.reload_time_remaining -= delta

    def get_target(self):
        # Priority 1: Attack anyone attacking me
        if self.attacker is not None:
            self.target = self.attacker

        # Offensive target priority
        # Priority 2: Attack team target if it's in range
        if self.goal_mode == 'attack' and (self.target is None or not self.target.is_alive()):
            if self.atk_target.is_alive() and (
                        self.pos - self.atk_target.pos).length() < self.firing_range:  # if the target is in range
                self.target = self.atk_target

        # Defensive target priority
        # Priority 2: Attack anyone attacking team defensive target
        if self.target is None or not self.target.is_alive():
            if self.def_target is not None and self.def_target.get_attacker() is not None:
                target = self.def_target.get_attacker()

                if target.ship_class == 'bomber' or target.ship_class == 'fighter':
                    self.target = target

        # Priority 3: Attack nearest bomber
        if self.target is None or not self.target.is_alive():
            self.target = self.get_nearest_target('bomber')

        # Priority 4: Attack nearest fighter
        if self.target is None or not self.target.is_alive():
            self.target = self.get_nearest_target('fighter')

        # Priority 4: Attack nearest destroyer
        if self.target is None or not self.target.is_alive():
            self.target = self.get_nearest_target('destroyer')

        # Priority 6: Attack anyone attacking any ally
        if self.target is None or not self.target.is_alive():
            for agent in self.world.teams[self.team].agents:
                if agent.get_attacker() is not None:
                    self.target = agent.attacker