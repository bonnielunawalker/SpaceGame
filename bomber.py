from agent import *

TRAVEL_FORMATION = [Vector2D(-5, 10), Vector2D(-10, -10), Vector2D(-15, 20), Vector2D(-20, -20),
                    Vector2D(-25, 30), Vector2D(-30, -30), Vector2D(-35, 40), Vector2D(-40, -40),
                    Vector2D(-45, 50), Vector2D(-50, -50), Vector2D(-55, 60), Vector2D(-60, -60),
                    Vector2D(-65, 70), Vector2D(-70, -70), Vector2D(-75, 80), Vector2D(-80, -80)]

COMBAT_FORMATION = [Vector2D(-10, 20), Vector2D(-20, -20), Vector2D(-30, 40), Vector2D(-40, -40),
                    Vector2D(-50, 60), Vector2D(-60, -60), Vector2D(-70, 80), Vector2D(-80, -80),
                    Vector2D(-40, 20), Vector2D(-50, -20), Vector2D(-60, 40), Vector2D(-70, -40),
                    Vector2D(-80, 60), Vector2D(-90, -60), Vector2D(-100, 80), Vector2D(-110, -80)]

class Bomber(Agent):
    def __init__(self, team, world, parent=None, squadron=None, scale=3.0, mass=8):
        super().__init__(team, 4, world, scale, mass)

        self.vehicle_shape = [
            Point2D(-0.8,  1.9),
            Point2D( 1.0,  0.0),
            Point2D(-0.8, -1.9)
        ]

        self.parent = parent
        self.squadron = squadron
        self.is_squadron_leader = False
        self.weapon_type = 'proton torpedo'

        self.firing_range = WEAPON_LIFETIMES[self.weapon_type] * WEAPON_SPEEDS[self.weapon_type]
        self.aggro_range = 800

        self.max_speed /= 2

        self.target = self.parent.get_target()

        self.formation_pos = None

        self.ship_class = 'bomber'

    def update(self, delta):
        self.get_target()
        self.update_mode(delta)
        super().update(delta)

        if self.target is not None and self.target.is_alive():
            self.mode = 'engage'
            self.track(self.target)

        if self.mode == 'engage' and self.engagement_mode == 'ready' and\
            self.target is not None and self.target.is_alive():
            self.shoot()

    def calculate(self, delta):
        # calculate the current steering force
        mode = self.mode
        if mode == 'patrol':
            force = self.follow_path()
        elif mode == 'rtb':
            force = self.arrive(self.parent.pos, 'slow')
        elif mode == 'engage':
            if self.target is not None: # just to make sure
                self.track(self.target)

                force = self.seek(self.look_ahead_pos)
            else:
                self.mode = 'patrol'
                force = self.follow_path()
        else:
            force = Vector2D()

        if self.parent in self.world.agents:
            force += self.formation(self.squadron)
        else:
            self.join_nearest_squadron()

        self.force = force
        return force

    def update_mode(self, delta):
        # Priority 1: Return to base to repair
        if self.health < self.max_health / 2:
            for bomber in self.squadron:
                bomber.mode = 'rtb' # all bombers fall back to the carrier

        # Priority 2: Return to base to rearm
        if self.mode != 'rtb':
            count = 0

            for bomber in self.squadron:
                if bomber.engagement_mode == 'reloading':
                    count += 1

                if count == len(self.squadron):
                    for bomber in self.squadron:
                        bomber.mode = 'rtb'

        # repair and rearm when at carrier
        if (self.pos - self.parent.pos).length() < self.parent.bRadius and self.health < self.max_health:
            self.health += 0.01
            self.engagement_mode = 'ready'

            count = 0

            for bomber in self.squadron:
                if bomber.health == bomber.max_health:
                    count += 1

                if count == len(self.squadron):
                    for bomber in self.squadron:
                        bomber.mode = 'engage'

    def get_target(self):
        # Offensive targeting priority
        # Priority 3: Attack team target
        if self.goal_mode == 'attack' and self.atk_target in self.world.agents:
            if not hasattr(self.atk_target, 'squadron'):
                self.target = self.atk_target

        # Defensive targeting priority
        # Priority 3: Attack any cruisers attacking defensive target
        elif self.goal_mode == 'defend' and self.def_target in self.world.agents:
            if self.def_target.get_attacker() is not None:
                attacker = self.def_target.attacker

                if attacker.ship_class == 'cruiser':
                    self.target = attacker

        # Patrol targeting priority
        # Priority 3: Attack any cruisers attacking any carriers on my team
        else:
            for agent in self.world.teams[self.team].agents:
                if hasattr(agent, 'bomber_squadrons'):
                    if agent.get_attacker() is not None and agent.attacker.ship_class == 'cruiser':
                        self.target = agent.attacker

        # Priority 4: Attack any enemy cruisers
        if self.target is None:
            for agent in self.world.agents:
                if agent.team is not self.team and agent.ship_class == 'cruiser' and\
                                (self.pos - agent.pos).length() < self.aggro_range:
                    self.target = agent

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

            self.engagement_mode = 'reloading'

    def formation(self, squadron):
        if self.is_squadron_leader:
            return Vector2D()
        else:
            leader = squadron[0]
            if squadron.index(self) > len(COMBAT_FORMATION):
                return self.arrive(self.squadron[0].pos, 'normal') # default behaviour in case formation position does not exist
            elif self.mode == 'rtb':
                formation_pos = TRAVEL_FORMATION[squadron.index(self) - 1]
            else:
                formation_pos = COMBAT_FORMATION[squadron.index(self) - 1]

            world_offset_pos = self.world.transform_point(formation_pos, leader.pos, leader.heading, leader.side)
            self.formation_pos = world_offset_pos  # for use in rendering
            to_offset = world_offset_pos - self.pos
            look_ahead_time = to_offset.length() / (self.max_speed + leader.speed())

            return self.arrive(world_offset_pos + leader.vel * look_ahead_time, 'fast')

    def join_nearest_squadron(self):
        nearest = None
        nearest_dist = Vector2D(sys.maxsize, sys.maxsize)

        for agent in self.world.agents:
            if agent.team == self.team and agent.ship_class == 'bomber':
                dist = self.pos - agent.pos
                if dist.length() < nearest_dist.length() and agent.parent in self.world.agents:
                    nearest_dist = dist
                    nearest = agent

        if nearest is None:
            return

        self.parent = nearest.parent
        self.squadron = nearest.squadron
        self.squadron.append(self)
        self.target = self.squadron[0].target

    def get_attacker(self):
        return super().get_attacker()