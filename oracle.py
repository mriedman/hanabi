from hanabi import HanabiMDP
from util import *


class OracleAgent(HanabiAgent):
    def __init__(self, playerIndex: int):
        super().__init__(playerIndex)
        self.cardsPerHand = 5
        self.cardInfo = [[-1, -1] for _ in range(self.cardsPerHand)]

    def getAction(self, state: Tuple) -> Any:
        #  If there is a playable card, play it
        for i, j in enumerate(state[0][self.playerIndex]):
            if state[3][j[1]] == j[0]:
                return (0, i)
        #  If there is a discard-able card, discard it
        for i, j in enumerate(state[0][self.playerIndex]):
            if state[3][j[1]] > j[0]:
                return (2, i)
        #  If another player has a playable card and there is a blue token, give them a hint
        #  If there are multiple, pick one at random
        if state[1] > 0:
            possibleHints = []
            for i, j in enumerate(state[0]):
                if j == ():
                    continue
                for k, card in enumerate(j):
                    if state[3][card[1]] == card[0]:
                        l = random.randint(0, 1)
                        possibleHints.append((1, i, l, card[l]))
            if len(possibleHints) > 0:
                return random.choice(possibleHints)
            #  If there are no playable cards, give a random hint
            for i, j in enumerate(state[0]):
                if j == ():
                    continue
                for k, card in enumerate(j):
                    l = random.randint(0, 1)
                    possibleHints.append((1, i, l, card[l]))
            return random.choice(possibleHints)
        #  If another player has a duplicate of your card, discard it
        for i, i1 in enumerate(state[0][self.playerIndex]):
            for j in state[0]:
                if j == ():
                    continue
                for card in j:
                    if card == i1:
                        return (2, i)
        #  Discard at random
        return (2, random.randint(0, 4))

    def deriveDataFromGameState(self, state: Tuple) -> Tuple:
        return state

    def update(self, state: Tuple) -> None:
        pass


mdp = HanabiMDP([3, 2, 2, 2, 1], 5, 8, 3, 2, 5)
agentList = [OracleAgent(i) for i in range(2)]
results = simulate(mdp, agentList, 1000)
print(sum(results)/1000)
print(max(results))
print(min(results))
