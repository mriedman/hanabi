from typing import List, Tuple, Dict, Any
from random import random


class HanabiMDP(object):
    def __init__(self, multiplicities: List, colors: int, blueTokens: int, redTokens: int, players: int, cardsPerHand: int):
        """
        :param multiplicities: number of each card (default: [3,2,2,2,1])
        :param colors: number of colors (default: 5)
        :param blueTokens: number of blue information tokens (default: 8)
        :param redTokens: number of red tokens (default: 3)
        :param players: number of players
        :param cardsPerHand: number of cards in a player's hand
        """
        self.multiplicities = multiplicities
        self.colors = colors
        self.blueTokens = blueTokens
        self.redTokens = redTokens
        self.players = players
        self.cardsPerHand = cardsPerHand
        #  [(1,2),3] means there are 3 instances of the card with number 1 and color 2
        #  Cards are 0-indexed (i.e. the lowest card number is 0)
        self.deck = []
        for num, count in enumerate(multiplicities):
            for color in range(colors):
                self.deck.append([(num + 1, color), count])

    def startState(self) -> Tuple:
        #  -- The zeroth element is a tuple of each player's hand
        #     Card are represented as two ints, where the first is number and the second is color
        #  -- The first element is the number of blue chips remaining
        #  -- The second element is the number of red chips on the board
        #  -- The third element is the next card that may be placed on each stack
        #     A 5 means that the stack is finished and no more cards can be played on it
        #  -- The fourth element is the index of the player whose turn it is
        #  -- The fifth element is the cards remaining in the deck (not played or in a player's hand)
        #  -- The sixth element is a hint if one was given on the previous turn and otherwise None
        #     A hint is of the form (playerIndex, number (0) or color (1), which number/color)
        #     For example, (1, 0, 2) means Player 1 was told which of their cards are 2's.

        def drawCard() -> int:
            # This will help us select players' initial hands by selecting a random card and removing it from the deck
            cardsRemaining = sum(i[1] for i in self.deck)
            cardLocation = int(random()*cardsRemaining)
            cardsSeen = 0
            for card in self.deck:
                cardsSeen += card[1]
                if cardsSeen > cardLocation:
                    card[1] -= 1
                    return card[0]
        playerHands = []
        for _ in range(self.players):
            nextHand = [drawCard() for __ in range(self.cardsPerHand)]
            playerHands.append(tuple(nextHand))
        return (tuple(playerHands), 8, 0, 0, (0,) * self.colors, tuple(tuple(i) for i in self.deck), None)

    def actions(self, state: Tuple) -> List[Tuple]:
        """
        :param state: state tuple
        :return: list of possible actions
        """
        #  Action Format:
        #  First element is:
        #  0:Play a card
        #    Second element is the index of the card in the player's hand
        #  1:Use a blue chip
        #    Second element is the player the hint is given to
        #    Third element is:
        #    0: A number hint is being given
        #    1: A color hint is being given
        #    Fourth element is which number/color
        #  2:Discard a card
        #    Second element is the index of the card the player discarded
        actionList = []
        cardsRemaining = sum(i[1] for i in state[5])
        if cardsRemaining == 0:
            return actionList
        if state[1] > 0:  # Blue chips are still in play
            for player in range(self.players):
                if not player == state[4]:  # Can't give a hint to yourself
                    for number in range(len(self.multiplicities)):
                        actionList.append((1, player, 0, number))
                    for color in range(self.colors):
                        actionList.append((1, player, 1, color))
        for i in range(self.cardsPerHand):
            actionList.append((0, i))
            actionList.append((2, i))
        return actionList

    def succAndProbReward(self, state: Tuple, action: Tuple) -> List[Tuple]:
        #  Given a |state| and |action|, return a list of (newState, prob, reward) tuples
        #  corresponding to the states reachable from |state| when taking |action|.
        #  * Indicate a terminal state (after quitting, busting, or running out of cards)
        #    by setting the deck to None.
        numCardsRemaining = sum(i[1] for i in state[5])
        if action[0] == 0 or 2:
            playerHand = state[0][state[4]]
            playerCard = playerHand[action[1]]
            reward = 0
            redChips = state[2]
            blueChips = state[1]
            newNextCards = list(state[3])
            if action[0] == 0 and state[3][playerCard[1]] == playerCard[0]:
                reward = 1
                newNextCards[playerCard[1]] += 1
            elif action[0] == 0:
                redChips += 1
            elif action[0] == 2:
                blueChips = min(self.blueTokens, blueChips + 1)
            newStateList = []
            for cardIndex, card in enumerate(state[5]):
                if card[1] > 0:
                    newPlayerHand = playerHand[:action[1]] + (card[0],) + playerHand[action[1] + 1:]
                    allPlayerHands = state[0][:state[4]] + newPlayerHand + state[0][state[4] + 1:]
                    newDeck = list(state[5])
                    newDeck[cardIndex] = (newDeck[cardIndex][0], newDeck[cardIndex][1] - 1)
                    newPlayer = (state[4] + 1) % self.players
                    newState = (allPlayerHands, blueChips, redChips, tuple(newNextCards), newPlayer, newDeck, None)
                    newStateList.append((newState, card[1] / numCardsRemaining, reward))
            return newStateList
        if action[0] == 1:
            blueChips = state[1] - 1
            if blueChips == -1:
                raise ValueError("Hint Not Allowed")
            newPlayer = (state[4] + 1) % self.players
            newState = (state[0], blueChips, state[2], state[3], newPlayer, state[5], action[1:])
            return [(newState, 1, 0)]
        raise ValueError("Invalid Action Given")
