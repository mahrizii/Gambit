import random
import time
pieceScore = {"K": 0, "Q": 10, "R": 5, "B": 3, "N": 3, "p": 1}
CHECKMATE = 1000
STALEMATE = 0
DEPTH=3
nodeCounter = 0
pawnTable = [
[0, 0, 0, 0, 0, 0, 0, 0],
[50, 50, 50, 50, 50, 50, 50, 50],
[10, 10, 20, 30, 30, 20, 10, 10],
[5, 5, 10, 25, 25, 10, 5, 5],
[0, 0, 0, 20, 20, 0, 0, 0],
[5, -5, -10, 0, 0, -10, -5, 5],
[5, 10, 10, -20, -20, 10, 10, 5],
[0, 0, 0, 0, 0, 0, 0, 0],
]
knightTable = [
[-50, -40, -30, -30, -30, -30, -40, -50],
[-40, -20, 0, 0, 0, 0, -20, -40],
[-30, 0, 10, 15, 15, 10, 0, -30],
[-30, 5, 15, 20, 20, 15, 5, -30],
[-30, 0, 15, 20, 20, 15, 0, -30],
[-30, 5, 10, 15, 15, 10, 5, -30],
[-40, -20, 0, 5, 5, 0, -20, -40],
[-50, -40, -30, -30, -30, -30, -40, -50],
]
bishopTable = [
[-20, -10, -10, -10, -10, -10, -10, -20],
[-10, 0, 0, 0, 0, 0, 0, -10],
[-10, 0, 5, 10, 10, 5, 0, -10],
[-10, 5, 5, 10, 10, 5, 5, -10],
[-10, 0, 10, 10, 10, 10, 0, -10],
[-10, 10, 10, 10, 10, 10, 10, -10],
[-10, 5, 0, 0, 0, 0, 5, -10],
[-20, -10, -10, -10, -10, -10, -10, -20],
]
rookTable = [
[0, 0, 0, 0, 0, 0, 0, 0],
[5, 10, 10, 10, 10, 10, 10, 5],
[-5, 0, 0, 0, 0, 0, 0, -5],
[-5, 0, 0, 0, 0, 0, 0, -5],
[-5, 0, 0, 0, 0, 0, 0, -5],
[-5, 0, 0, 0, 0, 0, 0, -5],
[-5, 0, 0, 0, 0, 0, 0, -5],
[0, 0, 0, 5, 5, 0, 0, 0],
]
queenTable = [
[-20, -10, -10, -5, -5, -10, -10, -20],
[-10, 0, 0, 0, 0, 0, 0, -10],
[-10, 0, 5, 5, 5, 5, 0, -10],
[-5, 0, 5, 5, 5, 5, 0, -5],
[0, 0, 5, 5, 5, 5, 0, -5],
[-10, 5, 5, 5, 5, 5, 0, -10],
[-10, 0, 5, 0, 0, 0, 0, -10],
[-20, -10, -10, -5, -5, -10, -10, -20],
]
kingTable = [
[-30, -40, -40, -50, -50, -40, -40, -30],
[-30, -40, -40, -50, -50, -40, -40, -30],
[-30, -40, -40, -50, -50, -40, -40, -30],
[-30, -40, -40, -50, -50, -40, -40, -30],
[-20, -30, -30, -40, -40, -30, -30, -20],
[-10, -20, -20, -20, -20, -20, -20, -10],
[20, 20, 0, 0, 0, 0, 20, 20],
[20, 30, 10, 0, 0, 10, 30, 20],
]
pieceSquareTables = {
"p": pawnTable,
"N": knightTable,
"B": bishopTable,
"R": rookTable,
"Q": queenTable,
"K": kingTable,
}
def findRandomMove(validMoves):
    return random.choice(validMoves)

def findBestMove(gs, validMoves,nodeCounter=0):
    turnMultiplier = 1 if gs.whiteToMove else -1
    opponentMinMaxScore = CHECKMATE  # Best score opponent can achieve (we want to minimize this)
    bestPlayerMove = None
    random.shuffle(validMoves)

    for playerMove in validMoves:
        gs.makeMove(playerMove)
        nodeCounter+=1
        print(nodeCounter)
        opponentsMoves = gs.getValidMoves()

        if gs.staleMate:
            opponentMaxScore = STALEMATE
        elif gs.checkMate:
            opponentMaxScore = -CHECKMATE  # Opponent loses after our move
        else:
            opponentMaxScore = -CHECKMATE
            for opponentMove in opponentsMoves:
                gs.makeMove(opponentMove)

                if gs.checkMate:
                    score = CHECKMATE  # Opponent wins
                elif gs.staleMate:
                    score = STALEMATE
                else:
                    score = -turnMultiplier * scoreMaterial(gs.board)

                if score > opponentMaxScore:  # Opponent tries to maximize
                    opponentMaxScore = score
                gs.undoMove()

        if opponentMaxScore < opponentMinMaxScore:  # We try to minimize opponent's best
            opponentMinMaxScore = opponentMaxScore
            bestPlayerMove = playerMove

        gs.undoMove()
    nodeCounter=0
    return bestPlayerMove

'''
helper method to make the first recursive call'''
def findBestMoveNegaMax(gs, validMoves):
    stats = {"nodes": 0, "pruned": 0}
    nextMove = None
    bestMove = None
    bestScore= -CHECKMATE
    alpha, beta = -CHECKMATE, CHECKMATE
    random.shuffle(validMoves)
    validMoves.sort(key=moveOrderScore, reverse=True)


    startTime = time.perf_counter()
    turnMultiplier = 1 if gs.whiteToMove else -1
    for move in validMoves:
        stats["nodes"] += 1
        gs.makeMove(move)
        nextMoves= gs.getValidMoves()
        score= -findMoveNegaMax(gs,nextMoves,DEPTH-1,-beta,-alpha,-turnMultiplier,stats)#goes to the next layer
        gs.undoMove()
        if score > bestScore:
            bestScore, bestMove = score, move
        alpha = max(alpha, score)
    endTime = time.perf_counter()
    print(f"Nodes: {stats['nodes']}, Time: {endTime - startTime}")
    return bestMove


    return nextMove
def findMoveNegaMax(gs, validMoves,depth,alpha,beta,turnMultiplier, stats):

    if depth==0:
        return turnMultiplier * scoreBoardPosition(gs)
    validMoves.sort(key=moveOrderScore, reverse=True)
    maxScore = -CHECKMATE
    cabdudates= []
    for move in validMoves:
        stats["nodes"] += 1
        gs.makeMove(move)
        score = -findMoveNegaMax(gs, gs.getValidMoves(), depth-1, -beta, -alpha, -turnMultiplier, stats)
        gs.undoMove()
        maxScore = max(maxScore, score)
        alpha = max(alpha, maxScore)
        if alpha >= beta:
            stats["pruned"] += 1
            break
    return maxScore
'''
Positive score= white winning, negative score = black winning
'''
def scoreBoard(gs):
    if gs.checkMate:
        if gs.whiteToMove:
            return -CHECKMATE
        else:
            return CHECKMATE
    elif gs.staleMate:
        return STALEMATE


    score = 0
    for row in gs.board:
        for square in row:
            if square[0] == 'w':
                score += pieceScore[square[1]]
            elif square[0] == 'b':
                score -= pieceScore[square[1]]
    return score

def scoreMaterial(board):
    score = 0
    for row in board:
        for square in row:
            if square[0] == 'w':
                score += pieceScore[square[1]]
            elif square[0] == 'b':
                score -= pieceScore[square[1]]
    return score
def moveOrderScore(move):
    if move.pieceCaptured == "--":
        return 0
    else:
        victim = move.pieceCaptured[1]
        capturer= move.pieceMoved[1]
        moveScore=(pieceScore[victim]*10-pieceScore[capturer])
        return moveScore
def scoreBoardPosition(gs):
    TotalScore=0

    for r, rows in enumerate(gs.board):
        for c, squares in enumerate(rows):
            if squares != "--":
                if squares[0]=="w":
                    TotalScore+=pieceScore[squares[1]]
                    TotalScore+=pieceSquareTables[squares[1]][r][c]/100
                else:
                    TotalScore -= pieceScore[squares[1]]
                    TotalScore -= pieceSquareTables[squares[1]][7-r][c]/100
    return TotalScore