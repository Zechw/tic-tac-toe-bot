import random
import numpy as np
import tensorflow as tf
from game import Game

class QNetworkBot:
    def __init__(self):
        self.minibatchSize = 1000
        self.discountFactor = 0.5
        self.maxMemorySize = 10000
        self.replayMemory = []
        self.buildNet()

    def buildNet(self):
        self.net = tf.keras.models.Sequential()
        self.net.add(tf.keras.layers.Dense(36, input_shape=(18,)))
        self.net.add(tf.keras.layers.Dense(36, activation='relu'))
        self.net.add(tf.keras.layers.Dense(36, activation='relu'))
        self.net.add(tf.keras.layers.Dense(36, activation='relu'))
        self.net.add(tf.keras.layers.Dense(36, activation='relu'))
        self.net.add(tf.keras.layers.Dense(18, activation='sigmoid'))
        # self.net.add(tf.keras.layers.GaussianNoise(1))
        self.net.add(tf.keras.layers.Dense(9))
        self.net.compile(optimizer=tf.keras.optimizers.SGD(0.5), loss='mse')

    def fire(self, board):
        return self.net.predict(np.array([self.boardToInputs(board)]))[0]

    @staticmethod
    def boardToInputs(board):
        inputList = []
        for space in board: #code even, odd inputs to each player
            inputList.append(1 if 0 is space else 0)
            inputList.append(1 if 1 is space else 0)
        return inputList

    def getMove(self, board, whichPlayerAmI):
        if random.random() > min(0.95, len(self.replayMemory)/self.maxMemorySize):
            while True:
                randomPosition = random.randint(0,8)
                if Game.isMoveValid(board, randomPosition):
                    return randomPosition
        q = self.fire(board)
        maxResult = max([x for i, x in enumerate(q) if board[i] is None])
        for move, r in enumerate(q):
            if r == maxResult and board[move] is None:
                return move
        raise Exception('NO MOVE!')

    def reportGame(self, game):
        winner = game.whoWon(game.board)
        if winner is None:
            self.reportDraw(game)
        else:
            self.reportWin(game, winner)
        self.trainMiniBatch()

    def reportWin(self, game, winner):
        self.reportReward(game, winner, 1)

    def reportDraw(self, game):
        self.reportReward(game, 0, 0) # player 0 always plays last move in a draw.

    def reportReward(self, game, whichPlayerAmI, reward):
        moves = game.moveHistory
        board = game.board[:]
        isTerminal = True
        for move in reversed(moves):
            board[move] = None
            self.storeReplay(board, move, whichPlayerAmI, reward, isTerminal)
            isTerminal = False
            reward = 0 # only reward for winning move
            whichPlayerAmI = 1 - whichPlayerAmI # alternate turns

    def trainMiniBatch(self):
        minibatch = random.sample(self.replayMemory, min(len(self.replayMemory), self.minibatchSize))
        inputs = []
        nextInputs = []
        actions = []
        rewards = []
        for replay in minibatch:
            inputs.append(self.boardToInputs(replay.state))
            nextInputs.append(self.boardToInputs(replay.nextState))
            actions.append(replay.action)
            rewards.append(replay.reward if replay.isTerminal else None)
        outputs = self.net.predict(np.array(inputs))
        nextOutputs = self.net.predict(np.array(nextInputs))
        for i, o in enumerate(outputs):
            r = rewards[i]
            if r is None:
                r = -1 * self.discountFactor * max(nextOutputs[i])
            o[actions[i]] = r
        inputs = np.array(inputs)
        if outputs.size != 0:
            self.net.train_on_batch(inputs, outputs)

    def storeReplay(self, board, move, whichPlayerAmI, reward, isTerminal):
        currentBoard = board[:]
        nextBoard = board[:]
        nextBoard[move] = whichPlayerAmI
        self.replayMemory.append(Replay(currentBoard, move, whichPlayerAmI, reward, nextBoard, isTerminal))
        if len(self.replayMemory) > self.maxMemorySize:
            self.replayMemory.pop(0)

class Replay:
    def __init__(self, state, action, playerIndicator, reward, nextState, isTerminal):
        self.state = state
        self.action = action
        self.playerIndicator = playerIndicator
        self.reward = reward
        self.nextState = nextState
        self.isTerminal = isTerminal

    def pr(self):
        print(self.state, self.action, self.reward, self.nextState, self.isTerminal)
