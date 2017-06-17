'''Autonomous Agent Movement: Seek, Arrive and Flee

Created for COS30002 AI for Games, Lab 05
By Clinton Woodward cwoodward@swin.edu.au

'''
from graphics import egi, KEY
from pyglet import window, clock
from pyglet.gl import *

from vector2d import Vector2D
from world import World
from agent import Agent, AGENT_MODES  # Agent with seek, arrive, flee and pursuit

from fighter import Fighter
from carrier import Carrier
from destroyer import Destroyer
from cruiser import Cruiser
from commandShip import CommandShip

from team import Team


def on_mouse_press(x, y, button, modifiers):
    pass


def on_key_press(symbol, modifiers):
    if symbol == KEY.P:
        world.paused = not world.paused

    # Toggle debug targeting info on the agent
    elif symbol == KEY.T:
        show = not world.agents[0].show_targeting_info
        for agent in world.agents:
            agent.show_targeting_info = show
    elif symbol == KEY.F:
        show = not world.agents[0].show_position_info
        for agent in world.agents:
            agent.show_position_info = show
    elif symbol == KEY.R:
        show = not world.agents[0].show_range_info
        for agent in world.agents:
            agent.show_range_info = show



def on_resize(cx, cy):
    world.cx = cx
    world.cy = cy


if __name__ == '__main__':

    # create a pyglet window and set glOptions
    win = window.Window(width=1920, height=1080, vsync=True, resizable=True)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    # needed so that egi knows where to draw
    egi.InitWithPyglet(win)
    # prep the fps display
    fps_display = clock.ClockDisplay()
    # register key and mouse event handlers
    win.push_handlers(on_key_press)
    win.push_handlers(on_mouse_press)
    win.push_handlers(on_resize)

    # create a world for agents
    world = World(1920, 1080)

    # add two teams
    world.teams = {"BLUE": Team("BLUE"), "RED": Team("RED")}

    blueteam = world.teams['BLUE']
    redteam = world.teams['RED']


    # --- SIMPLE COMBINED ARMS SIMULATION --- #
    # # spawn carriers
    # for i in range(4):
    #     blueteam.spawn(Carrier("BLUE", world))
    #     redteam.spawn(Carrier("RED", world))
    #
    # # spawn anti-fighter destroyers
    # for i in range(5):
    #     blueteam.spawn(Destroyer("BLUE", world, 'gatling laser'))
    #     redteam.spawn(Destroyer("RED", world, 'gatling laser'))
    #
    # for i in range(4):
    #     blueteam.spawn(Cruiser("BLUE", world))
    #     redteam.spawn(Cruiser("RED", world))
    #
    # # add team goals
    # blueteam.set_goal(['attack', redteam.agents[len(redteam.agents) - 1]])
    # redteam.set_goal(['attack', blueteam.agents[len(blueteam.agents) - 1]])
    # -----------------------------------------

    # --- AS ABOVE, BUT RED TEAM DEFENDING A CRUISER --- #
    # spawn carriers
    for i in range(4):
        blueteam.spawn(Carrier("BLUE", world))
        redteam.spawn(Carrier("RED", world))

    # spawn anti-fighter destroyers
    for i in range(5):
        blueteam.spawn(Destroyer("BLUE", world, 'gatling laser'))
        redteam.spawn(Destroyer("RED", world, 'gatling laser'))

    for i in range(4):
        blueteam.spawn(Cruiser("BLUE", world))
        redteam.spawn(Cruiser("RED", world))

    # add team goals
    blueteam.set_goal(['attack', redteam.agents[len(redteam.agents) - 1]])
    redteam.set_goal(['defend', redteam.agents[len(redteam.agents) - 1]])
    # -----------------------------------------


    # --- SMALLER CARRIER BASED COMBAT WITH CRUISER TARGETS--- #
    # # spawn carriers
    # for i in range(3):
    #     blueteam.spawn(Carrier("BLUE", world))
    #     redteam.spawn(Carrier("RED", world))
    #
    # # spawn cruisers
    # for i in range(1):
    #     blueteam.spawn(Cruiser("BLUE", world))
    #     redteam.spawn(Cruiser("RED", world))
    #
    # for i in range(1):
    #     blueteam.spawn(CommandShip("BLUE", world))
    #     redteam.spawn(CommandShip("RED", world))
    #
    # blueteam.set_goal(['attack', redteam.agents[len(redteam.agents) - 1]])
    # redteam.set_goal(['attack', blueteam.agents[len(blueteam.agents) - 1]])
    # ------------------------------------


    # --- DESTROYER AND CRUISER FLEET COMBAT --- #
    # # spawn cruisers
    # for i in range(5):
    #     blueteam.spawn(Cruiser("BLUE", world))
    #     redteam.spawn(Cruiser("RED", world))
    #
    # for i in range(9):
    #     blueteam.spawn(Destroyer("BLUE", world))
    #     redteam.spawn(Destroyer("RED", world))
    #
    # blueteam.set_goal(['attack', len(redteam.agents) - 1])
    # redteam.set_goal(['attack', len(blueteam.agents) - 1])
    # -----------------------------------------


    # unpause the world ready for movement
    world.paused = False

    while not win.has_exit:
        win.dispatch_events()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # show nice FPS bottom right (default)
        delta = clock.tick()
        world.update(delta)
        world.render()
        fps_display.draw()
        # swap the double buffer
        win.flip()

