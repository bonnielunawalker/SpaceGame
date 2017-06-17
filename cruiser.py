from agent import Agent, WEAPON_LIFETIMES, WEAPON_SPEEDS

class Cruiser(Agent):
    def __init__(self, team, world, weapon='he shell', scale=25.0, mass=150.0):
        super().__init__(team, 110, world, scale, mass)
        self.weapon_type = weapon
        self.aggro_range = WEAPON_LIFETIMES[self.weapon_type] * WEAPON_SPEEDS[self.weapon_type]
        self.firing_range = WEAPON_LIFETIMES[self.weapon_type] * WEAPON_SPEEDS[self.weapon_type]

        self.max_speed = 50

        self.ship_class = 'cruiser'

    def update(self, delta):
        self.get_target()
        self.update_mode(delta)
        super().update(delta)

        if self.goal_mode == 'attack' and self.atk_target in self.world.agents:
            self.target = self.atk_target

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
        # 1st priority, defend def_target
        if self.goal_mode == 'defend':
            if self.def_target is not None and self.def_target.is_alive():
                attacker = self.def_target.get_attacker()
                if attacker is not None and (attacker.ship_class == 'destroyer' or attacker.ship_class == 'cruiser'):
                    self.target = attacker

        # 2nd priority, attack atk_target if in range
        elif self.goal_mode == 'attack':
            if self.atk_target is not None and self.atk_target.is_alive():
                if (self.pos - self.atk_target.pos).length() < self.aggro_range:
                    self.target = self.atk_target

        # 3rd priority, attack nearest cruiser
        if self.target is None or not self.target.is_alive():
            self.target = self.get_nearest_target('cruiser')

        # 4th priority, defend self against destroyers or cruisers
        if self.attacker is not None and self.target is None:
            if self.attacker.ship_class == 'cruiser' or self.attacker.ship_class == 'destroyer':
                self.target = self.attacker

        # 6th priority, attack nearest carrier
        if self.target is None or not self.target.is_alive():
            self.target = self.get_nearest_target('carrier')

        # 5th priority, attack nearest destroyer
        if self.target is None or not self.target.is_alive():
            self.target = self.get_nearest_target('destroyer')