from hanabi_learning_environment.rl_env import Agent
from hanabi_learning_environment import pyhanabi
import numpy as np


class RandomAgent(Agent):
    def __init__(self, config):
        # Initialize
        self.config = config
        # Extract max info tokens or set default to 8.
        self.max_information_tokens = config.get('information_tokens', 8)

    def reset(self, config):
        self.config = config

    def act(self, observation: pyhanabi.HanabiObservation):
        if observation.cur_player_offset() == 0:
            return np.random.choice(observation.legal_moves())
        return None
