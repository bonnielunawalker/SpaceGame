from agent import *
from vector2d import Vector2D
from projectile import Projectile

TRAVEL_FORMATION = [Vector2D(-5, 10), Vector2D(-10, -10), Vector2D(-15, 20), Vector2D(-20, -20),
                    Vector2D(-25, 30), Vector2D(-30, -30), Vector2D(-35, 40), Vector2D(-40, -40),
                    Vector2D(-45, 50), Vector2D(-50, -50), Vector2D(-55, 60), Vector2D(-60, -60),
                    Vector2D(-65, 70), Vector2D(-70, -70), Vector2D(-75, 80), Vector2D(-80, -80)]

COMBAT_FORMATION = [Vector2D(-10, 20), Vector2D(-20, -20), Vector2D(-30, 40), Vector2D(-40, -40),
                    Vector2D(-50, 60), Vector2D(-60, -60), Vector2D(-70, 80), Vector2D(-80, -80),
                    Vector2D(-40, 20), Vector2D(-50, -20), Vector2D(-60, 40), Vector2D(-70, -40),
                    Vector2D(-80, 60), Vector2D(-90, -60), Vector2D(-100, 80), Vector2D(-110, -80)]

class Fighter(Agent):
    def __init__(self, team, world, parent=None, squadron=None, scale=3.0, mass=3):
        super().__init__(team, 3, world, scale, mass)
        self.parent = parent
        self.squadron = squadron
        self.is_squadron_leader = False
        self.weapon_type = 'blaster cannon'

        self.firing_range = WEAPON_LIFETIMES[self.weapon_type] * WEAPON_SPEEDS[self.weapon_type]
        self.aggro_range = self.firing_range * 2

        self.fighter_mode = ['attack', 'bomber']

        self.formation_pos = None

        self.ship_class = 'fighter'


    def update(self, delta):
        self.get_target()
        self.update_mode(delta)
        super().update(delta)

        if self.mode == 'engage' and self.engagement_mode == 'ready' and\
            self.target is not None and self.target.is_alive():
            self.shoot()

    def calculate(self, delta):
        # calculate the current steering force
        mode = self.mode
        if mode == 'patrol':
            if not self.is_squadron_leader:
                self.path = self.squadron[0].path
            force = self.follow_path()
        elif mode == 'engage':
            self.track(self.target)
            force = self.seek(self.look_ahead_pos)
        elif mode == 'rtb':
            force = self.arrive(self.parent.pos, 'fast')
        else:
            force = Vector2D()

        if self.parent not in self.world.agents:
            self.join_nearest_squadron()

        force += self.formation(self.squadron)

        self.force = force
        return force

    def update_mode(self, delta):
        # update mode and track target
        if self.target is not None and self.target.is_alive():
            self.mode = 'engage'
            self.track(self.target)
        else:
            self.mode = 'rtb'

        if self.reload_time_remaining <= 0:
            self.engagement_mode = 'ready'
        else:
            self.reload_time_remaining -= delta

        # repair when at carrier
        if (self.pos - self.parent.pos).length() < self.parent.bRadius and self.health < self.max_health:
            self.health += 0.01

    def get_target(self):
        # 1st priority, defend squadron leader
        if self.is_squadron_leader and self.attacker is not None and self.attacker.is_alive():
            self.target = self.attacker
            return

        # 2nd priority, attack enemy bombers
        if self.target is None or not self.target.is_alive():
            self.target = self.get_nearest_target('bomber')
            if self.target is not None and self.target.is_alive():
                return

        # 3rd priority, defend friendly carrier
        if (self.target is None or not self.target.is_alive()) and\
                        self.parent.get_attacker() is not None:
            self.target = self.parent.get_attacker()
            return

        # 4th priority, attack enemy fighters
        if self.target is None or not self.target.is_alive():
            self.target = self.get_nearest_target('fighter')
            if self.target is not None and self.target.is_alive():
                return

        # 4th priority, defend friendly bombers from enemy fighters
        if self.target is None or not self.target.is_alive():
            for squadron in self.parent.bomber_squadrons:
                for agent in squadron:
                    if agent.get_attacker() is not None:
                        self.target = agent.get_attacker()
                        return

        # 5th priority, defend friendly ships from bombers
        if self.target is None or not self.target.is_alive():
            for agent in self.world.teams[self.team].agents:
                if agent.get_attacker() is not None:
                    attacker = agent.attacker
                    if attacker.ship_class == 'bomber':
                        self.target = attacker
                        return

        # non-targeting priorities are handled in other methods

    def shoot(self):
        dist_to_target = (self.pos - self.target.pos).length()

        if dist_to_target <= self.firing_range:
            weapon_type = self.weapon_type
            weapon_speed = WEAPON_SPEEDS[weapon_type]
            deviation = WEAPON_DEVIATION[weapon_type]
            damage = WEAPON_DAMAGE[weapon_type]
            lifetime = WEAPON_LIFETIMES[weapon_type]
            color = WEAPON_COLORS[weapon_type]

            projectile_pos = Vector2D(self.pos.x, self.pos.y)

            to_target = self.heading.copy()

            p = Projectile(self.world, weapon_speed, projectile_pos, self.target, to_target, deviation, self,
                           damage, lifetime, color)
            self.world.projectiles.append(p)

            self.reload_time_remaining = RELOAD_TIMES[weapon_type]
            self.engagement_mode = 'reloading'

    def formation(self, squadron):
        if self.is_squadron_leader:
            return Vector2D()
        else:
            leader = squadron[0]
            if squadron.index(self) > len(COMBAT_FORMATION):
                return self.arrive(self.squadron[0].pos, 'normal') # default behaviour in case formation position does not exist
            if leader.mode == 'engage' and leader.target is not None and\
                            (leader.target.pos - leader.pos).length() < leader.aggro_range:
                formation_pos = COMBAT_FORMATION[squadron.index(self) - 1]
            else:
                formation_pos = TRAVEL_FORMATION[squadron.index(self) - 1]

            world_offset_pos = self.world.transform_point(formation_pos, leader.pos, leader.heading, leader.side)
            self.formation_pos = world_offset_pos  # for use in rendering
            to_offset = world_offset_pos - self.pos
            look_ahead_time = to_offset.length() / (self.max_speed + leader.speed())

            return self.arrive(world_offset_pos + leader.vel * look_ahead_time, 'fast')

    def join_nearest_squadron(self):
        nearest = None
        nearest_dist = Vector2D(sys.maxsize, sys.maxsize)

        for agent in self.world.agents:
            if agent.team == self.team and agent.ship_class == 'fighter':
                dist = self.pos - agent.pos
                if dist.length() < nearest_dist.length() and agent.parent in self.world.agents:
                    nearest_dist = dist
                    nearest = agent

        if nearest is None:
            return

        self.parent = nearest.parent
        self.squadron = nearest.squadron
        self.squadron.append(self)