from typing import Tuple, List, Any
import random

class MDP(object):
    # Return the start state.
    def startState(self) -> Tuple:
        raise NotImplementedError("Override me")

    # Return set of actions possible from |state|.
    def actions(self, state: Tuple) -> List[Any]:
        raise NotImplementedError("Override me")

    # Return a list of (newState, prob, reward) tuples corresponding to edges
    # coming out of |state|.
    # Mapping to notation from class:
    #   state = s, action = a, newState = s', prob = T(s, a, s'), reward = Reward(s, a, s')
    # If IsEnd(state), return the empty list.
    def succAndProbReward(self, state: Tuple, action: Any) -> List[Tuple]:
        raise NotImplementedError("Override me")

    def discount(self) -> float: return 1

class HanabiAgent(object):
    def __init__(self, playerIndex: int):
        self.playerIndex = playerIndex

    def getAction(self, state: Tuple) -> Any: raise NotImplementedError('Override Me')

    def update(self, state: Tuple) -> None: raise NotImplementedError('Override Me')

    def deriveDataFromGameState(self, state: Tuple) -> Tuple:
        playerHands = list(state[0])
        deck = list(state[5])
        for card in playerHands[self.playerIndex]:
            for i, j in enumerate(deck):
                if j[0] == card:
                    deck[i] = (card, j[1] + 1)
        newHint = None
        if state[6] is not None and state[6][0] == 1 and state[6][1] == self.playerIndex:
            #  A hint is being given to the player
            newHint = []
            for i, card in enumerate(playerHands[self.playerIndex]):
                if card[state[6][2]] == state[6][3]:
                    newHint.append(i)
            newHint = state[6][2:] + (tuple(newHint),)
        playerHands[self.playerIndex] = ()
        return (tuple(playerHands),) + state[1:5] + (deck,) + state[6:] + (newHint,)

def simulate(mdp: MDP, agents: List[HanabiAgent], numTrials = 10, verbose = False):
    def sample(probs):
        target = random.random()
        accum = 0
        for i, prob in enumerate(probs):
            accum += prob
            if accum >= target: return i
        raise Exception("Invalid probs: %s" % probs)

    totalRewards = []  # The rewards we get on each trial
    for trial in range(numTrials):
        state = mdp.startState()
        sequence = [state]
        totalDiscount = 1
        totalReward = 0
        for _ in range(100):
            for agent in agents:
                for otherAgent in agents:
                    otherAgent.update(otherAgent.deriveDataFromGameState(state))
                action = agent.getAction(agent.deriveDataFromGameState(state))
                transitions = mdp.succAndProbReward(state, action)
                if len(transitions) == 0:
                    break

                # Choose a random transition
                i = sample([prob for newState, prob, reward in transitions])
                newState, prob, reward = transitions[i]
                sequence.append(action)
                sequence.append(reward)
                sequence.append(newState)

                totalReward += totalDiscount * reward
                totalDiscount *= mdp.discount()
                state = newState
        if verbose:
            print(("Trial %d (totalReward = %s): %s" % (trial, totalReward, sequence)))
        totalRewards.append(totalReward)
    return totalRewards
