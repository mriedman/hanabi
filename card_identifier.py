from hanabi_learning_environment.rl_env import Agent
from hanabi_learning_environment import pyhanabi
import numpy as np
from scipy.special import expit
import math
from typing import Tuple, Any, Callable, Dict, List
from collections import defaultdict
import random
from baseline_agent import BaselineAgent
from copy import deepcopy


class CardIdentifierAgent(Agent):

    def __init__(self, config):
        # Initialize
        self.config = config
        # Extract max info tokens or set default to 8.
        self.max_information_tokens = config.get('information_tokens', 8)
        # Set up card identifier
        self.card_identifier = HanabiCardIdentifier(.05, self.feature_extractor, config)
        # Set up encoder
        self.encoder = pyhanabi.ObservationEncoder(pyhanabi.HanabiGame(config))
        self.agent = BaselineAgent(config)
        if config['print']==1:
            self.card_identifier.printt=1

    def act(self, observation: pyhanabi.HanabiObservation):
        if observation.cur_player_offset() != 0:
            return None

        player = 0
        # Moves are sorted newest to oldest by default, but we want to update knowledg in chronological order
        prior_actions = observation.last_moves()[-1::-1]
        cards_remaining = self.cards_remaining(observation)
        for i in prior_actions:
            move = i.move()
            if move.type() == 5:
                # MOVE_TYPE = 5 is a dealing move
                continue
            if player == 0 and move.type() in [1, 2]:
                # Current player played or discarded on last turn

                self.card_identifier.incorporateCardProbFeedback(observation, move.card_index(), i.color(), i.rank())
                for j in range(move.card_index(), 4):
                    # Shift each card drawn more recently than the discarded card to the left
                    self.card_identifier.card_priors[j] = self.card_identifier.card_priors[j + 1]
                # Add a new card prior for the new card
                self.card_identifier.card_priors[4] = HanabiCardIdentifier.normalize(np.array(cards_remaining))
            if player == 0:
                # Re-weight card priors to account for any new cards we've seen (
                # e.g. if our cooperator discarded W5, we know our cards aren't W%
                for index, vals in enumerate(zip(cards_remaining, self.card_identifier.card_space)):
                    if vals[0] < vals[1]:
                        for card in self.card_identifier.card_priors:
                            card[index] *= vals[0] / vals[1]
                # Updated possible cards (based on what is known about opponents, fireworks, and discards)
                self.card_identifier.card_space = cards_remaining
                self.card_identifier.card_priors = [HanabiCardIdentifier.normalize(i) for i in
                                                    self.card_identifier.card_priors]
                # Debugging stuff
                if self.config['print'] > 10 or True:
                    #print(111)
                    if all(sum(i)>0 for i in self.card_identifier.card_priors):
                        card_probs = list(self.card_identifier.getCardProbs(observation))
                        if any(i > .07 for i in card_probs[0]):
                            print(card_probs)
                    #print(222)

            # If another player has hinted us...
            if move.type() in [3, 4] and player > 0:
                self.card_identifier.cardUpdate(observation, i, move)
            player += 1



        # print(self.card_identifier.card_priors)
        # Play card if we've been hinted number and color
        for card_index, hint in enumerate(observation.card_knowledge()[0]):
            if hint.color() is not None and hint.rank() is not None:
                if observation.card_playable_on_fireworks(hint.color(), hint.rank()):
                    move = pyhanabi.HanabiMove.get_play_move(card_index)
                    if self.legal_move(observation.legal_moves(), move):
                        return move
        # Play card if we've ruled out from our knowledge the possibility that the card can't be played even if we don't know what it is
        for card_index in range(5):
            playable = True
            for i, prob in enumerate(self.card_identifier.card_priors[card_index]):
                if prob > 0.01: # Arbitrary threshold- may need to raise or lower
                    if not observation.card_playable_on_fireworks(i//5, i % 5):
                        playable = False
                        break
            # Sometimes it doesn't work and this stops it from losing
            if playable and observation.life_tokens() < 2:
                #print('yayyyy')
                move = pyhanabi.HanabiMove.get_play_move(card_index)
                if self.legal_move(observation.legal_moves(), move):
                    return move

        # Check if it's possible to hint a card to your colleagues.
        fireworks = observation.fireworks()
        if observation.information_tokens() > 0:
            # Check if there are any playable cards in the hands of the opponents.
            for player_offset in range(1, observation.num_players()):
                player_hand = observation.observed_hands()[player_offset]
                player_hints = observation.card_knowledge()[player_offset]
                # Check if the card in the hand of the opponent is playable.
                for card, hint in zip(player_hand, player_hints):
                    if BaselineAgent.playable_card(card,
                                                   fireworks) and hint.color() is None:
                        move = pyhanabi.HanabiMove.get_reveal_color_move(player_offset, card.color())
                        if self.legal_move(observation.legal_moves(), move):
                            return move
                        # return move
                    if BaselineAgent.playable_card(card,
                                                   fireworks) and hint.rank() is None:
                        move = pyhanabi.HanabiMove.get_reveal_rank_move(player_offset, card.rank())
                        if self.legal_move(observation.legal_moves(), move):
                            return move
                        # return move.to_dict()

        # If no card is hintable then discard or play.
        for i in observation.legal_moves():
            if i.type() == pyhanabi.HanabiMoveType.DISCARD:
                return i
        return observation.legal_moves()[-1]

    @staticmethod
    def legal_move(legal_moves: List[pyhanabi.HanabiMove], move: pyhanabi.HanabiMove):
        for pos_move in legal_moves:
            if pos_move.type() == move.type():
                if move.type() == 1 or move.type() == 2:
                    if move.card_index() == pos_move.card_index():
                        return True
                if move.type() == 3:
                    if move.color() == pos_move.color() and move.target_offset() == pos_move.target_offset():
                        return True
                if move.type() == 4:
                    if move.rank() == pos_move.rank() and move.target_offset() == pos_move.target_offset():
                        return True
        return False

    def cards_remaining(self, observation: pyhanabi.HanabiObservation):
        # Determine unknown cards from observation
        card_list = [3,2,2,2,1] * 5
        known_cards = observation.discard_pile()
        hands = observation.observed_hands()
        for hand in hands:
            if str(hand[0]) == 'XX':
                continue
            known_cards += hand
        for card in known_cards:
            card_list[card.color() * 5 + card.rank()] -= 1
        offset = 0
        for firework in observation.fireworks():
            for i in range(firework):
                card_list[offset + i] -= 1
            offset += 5
        return card_list

    def feature_extractor1(self, observation: pyhanabi.HanabiObservation, card_index: int):
        num_cards = self.config['rank'] * self.config['colors']
        obs_vector = self.encoder.encode(observation)
        # Add prior card knowledge
        features = list(self.card_identifier.card_priors[card_index])
        offset = num_cards * self.config['hand_size'] + self.config['players'] + 2 * num_cards
        # Add fireworks info
        features += obs_vector[offset: offset + num_cards]
        offset += num_cards + 8 + 3 + 2 * num_cards - self.config['hand_size'] * self.config['players']
        # Add most recent hint info
        features += obs_vector[offset + 6:offset + 21]
        return features

    def feature_extractor(self, observation: pyhanabi.HanabiObservation, card_index: int):
        num_cards = self.config['rank'] * self.config['colors']
        # Add prior card knowledge
        features = list(self.card_identifier.card_priors[card_index])
        # Add fireworks info
        fireworks = observation.fireworks()
        for color in fireworks:
            for rank in range(5):
                if rank == color:
                    features.append(1)
                else:
                    features.append(0)
        # Add most recent hint info
        last_moves = observation.last_moves()
        opp_move = None
        for move in last_moves:
            if not move.move().type() == 5:
                opp_move = move
                break
        if opp_move is None or opp_move.move().type() < 3:
            features += [0] * 15
        elif opp_move.move().type() == 3:
            features += [1 if i == opp_move.move().color() else 0 for i in range(5)]
            features += [0]*5
            features += [1 if i in opp_move.card_info_revealed() else 0 for i in range(5)]
        elif opp_move.move().type() == 4:
            features += [0]*5
            features += [1 if i == opp_move.move().rank() else 0 for i in range(5)]
            features += [1 if i in opp_move.card_info_revealed() else 0 for i in range(5)]
        if card_index == 0:
            pass
        return features

    def reset(self, config):
        self.config = config
        if config['print']==1:
            self.card_identifier.printt=1
        self.card_identifier.reset(config)




class HanabiCardIdentifier:
    def __init__(self, discount: float, feature_extractor: Callable, config: Dict, exploration_prob=0):
        self.discount = discount
        self.featureExtractor = feature_extractor
        self.explorationProb = exploration_prob
        self.printt=0
        rng = np.random.default_rng()
        feature_length = config['rank'] * config['colors'] * 2 + config['rank'] + config['colors'] + config['hand_size']
        self.index_matrices = [[rng.random((30, feature_length)),
                                rng.random((20, 30)),
                                rng.random((20, 20)),
                                rng.random((config['rank'] * config['colors'], 20))]
                               for _ in range(config['hand_size'])]
        self.activator = expit
        #self.card_priors = np.array([1 for _ in range(config['rank'] * config['colors'])])
        self.card_priors = [np.array([3,2,2,2,1]*5) for _ in range(config['hand_size'])]
        self.card_priors = [self.normalize(i) for i in self.card_priors]
        self.card_space = [3,2,2,2,1]*5
        self.num_iters = 0

    @staticmethod
    def normalize(array):
        if sum(array)==0:
            print('hi')
            return HanabiCardIdentifier.normalize(np.ones(array.shape))
        return array / sum(array)

    def reset(self, config: Dict):
        self.activator = expit
        # self.card_priors = np.array([1 for _ in range(config['rank'] * config['colors'])])
        self.card_priors = [np.array([3, 2, 2, 2, 1] * 5) for _ in range(config['hand_size'])]
        self.card_priors = [self.normalize(i) for i in self.card_priors]
        self.card_space = [3, 2, 2, 2, 1] * 5
        self.num_iters = 0

    def cardUpdate(self, observation: pyhanabi.HanabiObservation, history: pyhanabi.HanabiHistoryItem, move: pyhanabi.HanabiMove):
        cp2=deepcopy(self.card_priors)
        if move.type() == 3: # Color
            pos_cards = [i for i in range(move.color() * 5, (move.color() + 1) * 5)]
        elif move.type() == 4: #Rank
            pos_cards = [i for i in range(move.rank(), 25, 5)]
        else:
            print('sadasdad')
            return
        for card in range(5):
            for i in range(25):
                if (card in history.card_info_revealed()) ^ (i in pos_cards):
                    self.card_priors[card][i] = 0
        for i,card in enumerate(self.card_priors):
            if sum(card) == 0:
                pass
                #print([i,cp2[i]])
        self.card_priors = [self.normalize(i) for i in self.card_priors]
        #print('sadksjbadskaksdj')



    # Return the __ associated with the weights and features
    def getCardProbs(self, state: pyhanabi.HanabiObservation) -> List:
        prob_list = []
        for index in range(5):
            scores = self.featureExtractor(state, index)
            for layer in self.index_matrices[index]:
                scores = layer.dot(scores)
                scores = self.activator(scores)
            prob_list.append(scores)
        return [self.normalize(probs) for probs in prob_list]

    def getCardProbLayers(self, state: pyhanabi.HanabiObservation, index: int):
        scores = self.featureExtractor(state, index)
        yield scores
        for layer in self.index_matrices[index]:
            scores = layer.dot(scores)
            scores = self.activator(scores)
            yield scores

    def getQ(self, state: pyhanabi.HanabiObservation, action: pyhanabi.HanabiMove) -> float:
        pass

    # This algorithm will produce an action given a state.
    # Here we use the epsilon-greedy algorithm: with probability
    # |explorationProb|, take a random action.
    '''def getAction(self, state: pyhanabi.HanabiObservation) -> Any:
        self.num_iters += 1
        if random.random() < self.explorationProb:
            return random.choice(self.actions(state))
        else:
            return max((self.getQ(state, action), action) for action in state.legal_moves())[1]'''

    # Call this function to get the step size to update the weights.
    def getStepSize(self) -> float:
        #return 0.5 / math.sqrt(self.num_iters)
        return 0.1

    def incorporateCardProbFeedback(self, observation, card, color, rank):
        self.num_iters += 1
        index = 5 * color + rank
        results = list(self.getCardProbLayers(observation, card))
        errors = [np.zeros((i.shape[0],)) for i in self.index_matrices[card]]
        matrices = self.index_matrices[card]
        for j, col in enumerate(errors[-1]):
            target = 1 if j == index else 0
            errors[-1][j] = (target - results[-1][j]) * results[-1][j] * (1 - results[-1][j])
        for l_num, layer in zip(range(len(errors)-2, -1, -1), errors[-2::-1]):
            for j, col in enumerate(errors[l_num]):
                layer[j] = sum(errors[l_num+1][k] * matrices[l_num+1][k][j] for k in range(len(errors[l_num+1]))) * \
                           results[l_num+1][j] * (1 - results[l_num+1][j])
        for l_num, layer in enumerate(matrices):
            for i, row in enumerate(layer):
                for j, col in enumerate(row):
                    row[j] *= (1 - self.getStepSize())
                    row[j] += self.getStepSize() * errors[l_num][i] * results[l_num][j]



    # We will call this function with (s, a, r, s'), which you should use to update |weights|.
    # Note that if s is a terminal state, then s' will be None.  Remember to check for this.
    # You should update the weights using self.getStepSize(); use
    # self.getQ() to compute the current estimate of the parameters.
    '''def incorporateFeedback(self, state: pyhanabi.HanabiObservation, action: Any, reward: int, newState: Tuple) -> None:
        # BEGIN_YOUR_CODE (our solution is 9 lines of code, but don't worry if you deviate from this)
        maxQ = 'NaN'
        for newAction in self.actions(newState):
            if maxQ == 'NaN' or self.getQ(newState, newAction) > maxQ:
                maxQ = self.getQ(newState, newAction)
        delta = self.getStepSize() * (reward + self.discount * maxQ)
        for f, v in self.featureExtractor(state, action):
            self.weights[f] *= (1 - self.getStepSize())
            self.weights[f] += delta
        # END_YOUR_CODE'''
