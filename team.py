TEAM_GOALS = [
    'defend',
    'attack',
    'patrol'
]

class Team(object):
    def __init__(self, color):
        self.color = color

        self.agents = []

        self.goal = None
        self.goal_mode = None
        self.def_target = None
        self.atk_target = None
        self.pos_target = None

    def update(self, delta):
        for agent in self.agents:
            agent.update(delta)

    def render(self):
        for agent in self.agents:
            agent.render()

    def spawn(self, agent):
        if self.goal is not None:
            agent.set_goal(self.goal)
        self.agents.append(agent)

    def set_goal(self, goal_args):
        self.goal = goal_args
        self.goal_mode = goal_args[0]

        if self.goal_mode == 'defend':
            self.def_target = goal_args[1]
        elif self.goal_mode == 'attack':
            self.atk_target = goal_args[1]
        else:
            self.pos_target = goal_args[1]

        for agent in self.agents:
            agent.set_goal(self.goal)