'''An agent with Seek, Flee, Arrive, Pursuit behaviours

Created for COS30002 AI for Games by Clinton Woodward cwoodward@swin.edu.au

'''

import sys
from vector2d import Vector2D
from vector2d import Point2D
from graphics import egi, KEY
from math import sin, cos, radians
from random import random, randrange, uniform
from path import Path
from projectile import Projectile

AGENT_GOALS = [
    'defend',
    'attack',
    'patrol',
    'rtb'
]

AGENT_MODES = [
    'patrol',
    'engage'
]

ENGAGEMENT_MODES = [
    'ready',
    'reloading'
]

WEAPON_TYPE = [
    'blaster cannon',
    'plasma cannon',
    'gatling laser',
    'he shell',
    'proton torpedo'
]

WEAPON_SPEEDS = {
    'blaster cannon': 700,
    'plasma cannon': 400,
    'gatling laser': 600,
    'he shell': 100,
    'proton torpedo': 150
}

WEAPON_DEVIATION = {
    'blaster cannon': 0,
    'plasma cannon': 20,
    'gatling laser': 7,
    'he shell': 20,
    'proton torpedo': 0
}

RELOAD_TIMES = {
    'blaster cannon': 0.3,
    'plasma cannon': 3,
    'gatling laser': 0.1,
    'he shell': 8,
    'proton torpedo': 30
}

WEAPON_DAMAGE = {
    'blaster cannon': 1,
    'plasma cannon': 4,
    'gatling laser': 0.2,
    'he shell': 20,
    'proton torpedo': 20
}

WEAPON_LIFETIMES = {
    'blaster cannon': 0.3,
    'plasma cannon': 3,
    'gatling laser': 0.6,
    'he shell': 6,
    'proton torpedo': 2
}

WEAPON_COLORS = {
    'blaster cannon': 'ORANGE',
    'plasma cannon': 'BLUE',
    'gatling laser': 'GREEN',
    'he shell': 'RED',
    'proton torpedo': 'PURPLE'
}

class Agent(object):

    # NOTE: Class Object (not *instance*) variables!
    DECELERATION_SPEEDS = {
        'slow': 0.9,
        'normal': 0.5,
        'fast': 0.2
    }

    def __init__(self, team, health, world=None, scale=10.0, mass=1.0, mode='seek'):
        # keep a reference to the world object
        self.scale = scale
        self.world = world
        self.mode = mode
        # where am i and where am i going? random start pos


        if team == "BLUE":
            dir = radians(0)
            self.pos = Vector2D(randrange(100, world.cx - 100), randrange(100, 200))
        else:
            dir = radians(180)
            self.pos = Vector2D(randrange(100, world.cx - 100), randrange(world.cy - 200, world.cy - 100))

        self.vel = Vector2D()
        self.heading = Vector2D(sin(dir), cos(dir))
        self.side = self.heading.perp()
        self.scale = Vector2D(scale, scale)  # easy scaling of agent size
        self.force = Vector2D()  # current steering force
        self.accel = Vector2D() # current acceleration due to force
        self.mass = mass
        self.panic_distance = 100

        # data for drawing this agent
        self.color = team
        self.basecolor = team # base color is the color the agent will revert to after color changes (eg. taking damage)
        self.vehicle_shape = [
            Point2D(-1.0,  0.6),
            Point2D( 1.0,  0.0),
            Point2D(-1.0, -0.6)
        ]

        # pathing details
        self.path = Path()
        self.randomise_path(self.world.cx, self.world.cy)
        self.waypoint_threshold = 40

        # wander details
        self.wander_target = Vector2D(1, 0)
        self.wander_dist = 3 * scale
        self.wander_radius = 1.5 * scale
        self.wander_jitter = 20.0 * scale
        self.bRadius = scale

        self.neighbour_radius = 200

        # Force and speed limiting code
        self.max_force = 500.0
        self.max_speed = 20.0 * scale

        self.seperation_amount = 3
        self.cohesion_amount = 1000
        self.alignment_amount = 100

        # debug draw info?
        self.show_targeting_info = False
        self.show_position_info = False
        self.show_range_info = False

        # team information
        self.team = team
        self.tagged = False

        # combat information
        self.look_ahead_pos = Vector2D()
        self.target = None

        self.engagement_mode = 'ready'
        self.reload_time_remaining = 0

        self.max_health = health
        self.health = health

        self.aggro_range = 0 # default target acquisition range that should be overwritten

        # goal information
        self.goal = None
        self.goal_mode = None
        self.def_target = None
        self.atk_target = None
        self.target_pos = None

        # after setting everything up, add self to the world
        self.world.agents.append(self)

        # broadcast details
        self.attacker = None

        # ship class details
        self.ship_class = ''

    def calculate(self, delta):
        # calculate the current steering force
        mode = self.mode

        force = self.wander(delta) # default behaviour
        if mode == 'patrol':
            force = self.follow_path()
        elif mode == 'engage':
            if self.target is not None and self.target.is_alive(): # just to make sure
                force = self.seek(self.look_ahead_pos)
            else:
                self.mode = 'patrol'
                self.force = self.follow_path()

        self.force = force
        return force

    def update(self, delta):
        ''' update vehicle position and orientation '''
        # calculate and set self.force to be applied
        force = self.calculate(delta)
        force.truncate(self.max_force)  # <-- new force limiting code
        # determine the new acceleration
        self.accel = force / self.mass  # not needed if mass = 1.0
        # new velocity
        self.vel += self.accel * delta
        # check for limits of new velocity
        self.vel.truncate(self.max_speed)
        # update position
        self.pos += self.vel * delta
        # update heading is non-zero velocity (moving)
        if self.vel.length_sq() > 0.00000001:
            self.heading = self.vel.get_normalised()
            self.side = self.heading.perp()
        # treat world as continuous space - wrap new position if needed
        # self.world.wrap_around(self.pos)

    def update_mode(self, delta):
        pass # abstract method

    def render(self, color=None):
        ''' Draw the triangle agent with color'''
        # draw the path if it exists and the mode is follow
        # if self.mode == 'patrol':
            # self.path.render()

        # update colour if i'm my team's defensive target
        # needs to be in render because this may not be known at time of object creation
        if self is self.world.teams[self.team].def_target:
            if self.team == 'BLUE':
                self.basecolor = 'PURPLE'
            else:
                self.basecolor = 'ORANGE'

        # draw the ship
        egi.set_pen_color(name=self.color)
        pts = self.world.transform_points(self.vehicle_shape, self.pos,
                                          self.heading, self.side, self.scale)
        # draw it!
        egi.closed_shape(pts)
        if self.show_range_info:
            # targeting radius
            egi.set_pen_color(self.team, self.team)
            egi.circle(self.pos, self.aggro_range / 2)

        if self.show_targeting_info:
            # line to target
            if self.target is not None and self.target.is_alive():
                egi.set_pen_color(self.team, self.team)
                egi.line(self.pos.x, self.pos.y, self.target.pos.x, self.target.pos.y)

        if self.show_position_info:
            # line to formation position
            if hasattr(self, 'formation_pos'):
                if self.formation_pos is not None and not self.is_squadron_leader:
                    egi.orange_pen()
                    egi.cross(self.formation_pos, 3)
                    egi.line(self.pos.x, self.pos.y, self.formation_pos.x, self.formation_pos.y)

        self.color = self.basecolor

    def speed(self):
        return self.vel.length()

    #--------------------------------------------------------------------------

    def randomise_path(self, x, y):
        self.path.create_random_path(10, x / 4, y / 4, x / 1.5, y / 1.5)

    def follow_path(self):
        if self.path.is_finished():
            return self.arrive(self.path.current_pt(), 'normal')
        elif self.pos.distance(self.path.current_pt()) < self.waypoint_threshold:
            self.path.inc_current_pt()
            return self.seek(self.path.current_pt())
        else:
            return self.seek(self.path.current_pt())

    def seek(self, target_pos):
        ''' move towards target position '''
        desired_vel = (target_pos - self.pos).normalise() * self.max_speed
        return (desired_vel - self.vel)

    def flee(self, hunter_pos):
        ''' move away from hunter position '''
        if self.pos.distance(hunter_pos) < self.panic_distance:
            desired_vel = (self.pos - hunter_pos).normalise() * self.max_speed
        else:
            desired_vel = Vector2D(0, 0)
        return (desired_vel - self.vel)

    def arrive(self, target_pos, speed):
        ''' this behaviour is similar to seek() but it attempts to arrive at
            the target position with a zero velocity'''
        decel_rate = self.DECELERATION_SPEEDS[speed]
        to_target = target_pos - self.pos
        dist = to_target.length()
        if dist > 0:
            # calculate the speed required to reach the target given the
            # desired deceleration rate
            speed = dist / decel_rate
            # make sure the velocity does not exceed the max
            speed = min(speed, self.max_speed)
            # from here proceed just like Seek except we don't need to
            # normalize the to_target vector because we have already gone to the
            # trouble of calculating its length for dist.
            desired_vel = to_target * (speed / dist)
            return (desired_vel - self.vel)
        return Vector2D(0, 0)

    def wander(self, delta):
        ''' random wandering using a projected jitter circle '''
        wt = self.wander_target
        # this behaviour is dependent on the update rate, so this line must
        # be included when using time independent framerate.
        jitter_tts = self.wander_jitter * delta  # this time slice
        # first, add a small random vector to the target's position
        wt += Vector2D(uniform(-1, 1) * jitter_tts, uniform(-1, 1) * jitter_tts)
        # re-project this new vector back on to a unit circle
        wt.normalise()
        # increase the length of the vector to the same as the radius
        # of the wander circle
        wt *= self.wander_radius
        # move the target into a position WanderDist in front of the agent
        target = wt + Vector2D(self.wander_dist, 0)
        # project the target into world space
        wld_target = self.world.transform_point(target, self.pos, self.heading, self.side)
        # and steer towards it
        return self.seek(wld_target)

    # ------------------------------------------------------------------------------------------------------------------

    def track(self, target):
        weapon_type = self.weapon_type
        weapon_speed = WEAPON_SPEEDS[weapon_type]

        to_target = target.pos - self.pos

        look_ahead_time = to_target.length() / (weapon_speed + target.max_speed)

        look_ahead_pos = target.pos + look_ahead_time * target.vel

        self.look_ahead_pos = look_ahead_pos

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

            to_target = self.look_ahead_pos - self.pos

            p = Projectile(self.world, weapon_speed, projectile_pos, self.target, to_target, deviation, self,
                           damage, lifetime, color)
            self.world.projectiles.append(p)

            self.reload_time_remaining = RELOAD_TIMES[weapon_type]
            self.engagement_mode = 'reloading'

    def get_best_target(self, range):
        nearest = None
        nearest_dist = Vector2D(sys.maxsize, sys.maxsize)

        for agent in self.world.agents:
            if agent.team is not self.team:
                dist = self.pos - agent.pos
                if dist.length() < nearest_dist.length() and dist.length() <= range:
                    nearest_dist = dist
                    nearest = agent

        return nearest

    def set_goal(self, goal_args):
        self.goal = goal_args
        self.goal_mode = goal_args[0]

        if self.goal_mode == 'defend':
            self.def_target = goal_args[1]
        elif self.goal_mode == 'attack':
            self.atk_target = goal_args[1]
        elif self.goal_mode == 'patrol':
            self.target_pos = goal_args[1]
            self.randomise_path(self.target_pos.x, self.target_pos.y)
            self.mode = 'patrol'

    def get_attacker(self):
        if self.attacker in self.world.agents and self.attacker.is_alive():
            return self.attacker
        else:
            return None

    def critical_hit(self, damage):
        chance = int(100 - damage)
        hit = randrange(1, chance)

        if hit == 1:
            self.max_speed -= self.max_speed / 3
        elif hit == 2:
            self.aggro_range -= self.aggro_range / 3
        elif hit == 3:
            self.vel.x /= 2
            self.vel.y /= 2
        elif hit == 4:
            self.max_force /= 2

        if hit > 0 and hit < 5: # if a critical hit has been struck
            if hasattr(self, 'squadron'):
                self.squadron.append(self.squadron.pop(self.squadron.index(self))) # put yourself at the end of the squadron formation
                self.squadron[0].is_squadron_leader = True # update squadron leader

    def is_alive(self):
        return self in self.world.agents

    def get_nearest_target(self, target_type):
        closest = None
        closest_dist = None

        for agent in self.world.agents:
            if agent.team is not self.team and agent.ship_class == target_type and (
                        self.pos - agent.pos).length() < self.aggro_range:
                current = agent

                current_dist = (self.pos - current.pos).length()
                if closest_dist is None or current_dist < closest_dist:
                    closest_dist = current_dist
                    closest = agent

        return closest