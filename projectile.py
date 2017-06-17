from vector2d import Vector2D
from graphics import egi
from random import randint

class Projectile(object):
    def __init__(self, world, speed, pos, target, heading, deviation, src, dmg, lifetime, color):
        self.world = world
        self.speed = speed
        self.color = color

        self.target = target

        self.pos = pos
        self.heading = heading
        self.heading.x += randint((0 - deviation), deviation)
        self.heading.y += randint((0 - deviation), deviation)
        self.vel = Vector2D()

        self.src = src

        self.damage = dmg

        self.lifetime = lifetime
        self.time_alive = 0

    def render(self):
        egi.set_pen_color(self.color, self.color)
        egi.dot(self.pos.x, self.pos.y, self.pos, egi.curr_color)

    def update(self, delta):
        self.time_alive += delta

        if self.time_alive > self.lifetime:
            self.world.projectiles.remove(self)
            return

        # remove the projectile if it has left the game world
        if self.pos.x > self.world.cx or self.pos.x < 0:
            self.world.projectiles.remove(self)
            return
        elif self.pos.y > self.world.cy or self.pos.y < 0:
            self.world.projectiles.remove(self)
            return

        to_target = self.heading
        to_target = to_target.get_normalised() * self.speed

        force = to_target * self.speed
        self.vel = force * delta
        self.vel.truncate(self.speed)
        self.pos += self.vel * delta

        # collision check
        for agent in self.world.agents:
            if agent.team is not self.src.team: # avoid friendly fire
                if (self.pos - agent.pos).length() < agent.bRadius and agent is not self.src:
                    agent.health -= self.damage
                    agent.color = "WHITE"

                    self.world.projectiles.remove(self)

                    if agent.health <= 0: # should this be handled in agent.update()?
                        self.world.agents.remove(agent)
                        self.world.teams[agent.team].agents.remove(agent)

                        if hasattr(agent, 'squadron') and agent.squadron is not None:
                            agent.squadron.remove(agent)
                    else:
                        agent.attacker = self.src # inform the agent who attacked it

                        agent.critical_hit(self.damage)

                    return

