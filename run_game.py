# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function
from baseline_agent import BaselineAgent
from random_agent import RandomAgent
import sys
import argparse
import numpy as np

#import numpy as np
from hanabi_learning_environment import pyhanabi


def run_game(game_parameters, agents, verbose=0):
    """Play a game, selecting random actions."""

    def print_state(state):
        """Print some basic information about the state."""
        print("")
        print("Current player: {}".format(state.cur_player()))
        print(state)

        # Example of more queries to provide more about this state. For
        # example, bots could use these methods to to get information
        # about the state in order to act accordingly.
        print("### Information about the state retrieved separately ###")
        print("### Information tokens: {}".format(state.information_tokens()))
        print("### Life tokens: {}".format(state.life_tokens()))
        print("### Fireworks: {}".format(state.fireworks()))
        print("### Deck size: {}".format(state.deck_size()))
        print("### Discard pile: {}".format(str(state.discard_pile())))
        print("### Player hands: {}".format(str(state.player_hands())))
        print("")

    def print_observation(observation):
        """Print some basic information about an agent observation."""
        print("--- Observation ---")
        print(observation)

        print("### Information about the observation retrieved separately ###")
        print("### Current player, relative to self: {}".format(
            observation.cur_player_offset()))
        print("### Observed hands: {}".format(observation.observed_hands()))
        print("### Card knowledge: {}".format(observation.card_knowledge()))
        print("### Discard pile: {}".format(observation.discard_pile()))
        print("### Fireworks: {}".format(observation.fireworks()))
        print("### Deck size: {}".format(observation.deck_size()))
        move_string = "### Last moves:"
        for move_tuple in observation.last_moves():
            move_string += " {}".format(move_tuple)
        print(move_string)
        print("### Information tokens: {}".format(observation.information_tokens()))
        print("### Life tokens: {}".format(observation.life_tokens()))
        print("### Legal moves: {}".format(observation.legal_moves()))
        print("--- EndObservation ---")

    def print_encoded_observations(encoder, state, num_players):
        print("--- EncodedObservations ---")
        print("Observation encoding shape: {}".format(encoder.shape()))
        print("Current actual player: {}".format(state.cur_player()))
        for i in range(num_players):
            print("Encoded observation for player {}: {}".format(
                i, encoder.encode(state.observation(i))))
        print("--- EndEncodedObservations ---")

    game = pyhanabi.HanabiGame(game_parameters)
    if verbose > 2:
      print(game.parameter_string(), end="")
    obs_encoder = pyhanabi.ObservationEncoder(
        game, enc_type=pyhanabi.ObservationEncoderType.CANONICAL)

    state = game.new_initial_state()
    while not state.is_terminal():
        if state.cur_player() == pyhanabi.CHANCE_PLAYER_ID:
            state.deal_random_card()
            continue

        observation = state.observation(state.cur_player())
        legal_moves = state.legal_moves()
        move = agents[state.cur_player()].act(observation)
        state.apply_move(move)
        if verbose > 2:
            print_state(state)
            print_observation(observation)
            print_encoded_observations(obs_encoder, state, game.num_players())
            print("")
            print("Number of legal moves: {}".format(len(legal_moves)))
        if verbose > 1:
            print("Agent has chosen: {}".format(move))
    if verbose > 1:
        print("")
        print("Game done. Terminal state:")
        print("")
        print(state)
        print("")
    if verbose > 0:
        print("score: {}".format(state.score()))




p = argparse.ArgumentParser(prog='PROG')
p.add_argument('foo')
for i in [('-p', 'players', 2, int), ('-c', 'colors', 5, int), ('-r', 'rank', 5, int), ('-hs', 'hand_size', 5, int),
        ('-i', 'max_information_tokens', 8, int), ('-l', 'max_life_tokens', 3, int), ('-s', 'seed', -1, int),
        ('-v', 'verbose', 0, int), ('-n', 'num_rounds', 1, int)]:
    p.add_argument(i[0], dest=i[1], default=i[2], type=i[3])
p.add_argument('-a', dest='agents', default=['baseline', 'baseline'], nargs='*')
args = vars(p.parse_args(sys.argv))
agent_dict = {'baseline': BaselineAgent, 'random': RandomAgent}

for _ in range(args['num_rounds']):
    agents=[]
    for agent in args['agents']:
        agents.append(agent_dict[agent](args))
    run_game(args,agents,args['verbose'])
