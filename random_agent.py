from hanabi_learning_environment.rl_env import Agent
from hanabi_learning_environment import pyhanabi
import numpy as np
class RandomAgent(Agent):
    def __init__(self, config):
        super(RandomAgent, self).__init__(config)
        # Initialize
        self.config = config
        # Extract max info tokens or set default to 8.
        self.max_information_tokens = config.get('information_tokens', 8)
    def act(self, observation: pyhanabi.HanabiObservation):
        return np.random.choice(observation.legal_moves())