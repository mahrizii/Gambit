# This stores all the info for the current state of the game and responsible for determining the valid moves
#keeps a move log


class GameState():
    def __init__(self):
        #board is an 8x8 2d list, each element of the list has 2 characters. The first character represents the color, the second character represents the type of piece
       # "--" represents empty space with no piece
        self.board = [
            ["bR" , "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]]
        self.moveFunctions = {'p' :self.getPawnMoves, 'R' :self.getRookMoves, 'N' :self.getKnightMoves, 'B' :self.getBishopMoves, 'Q':self.getQueenMoves, 'K': self.getKingMoves}
        self.whiteToMove = True
        self.moveLog = []
        self.whiteKingLocation = (7,4)
        self.blackKingLocation = (0,4)
        self.checkMate = False
        self.staleMate = False
        self.enpassantPossible = ()
        self.currentCastleRight= CastleRights(True,True,True,True)
        self.castleRightLog = [self.currentCastleRight]

    def makeMove(self, move):
        # move the piece
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)
        self.whiteToMove = not self.whiteToMove

        # update king's location
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.endRow, move.endCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.endRow, move.endCol)

        # pawn promotion
        if move.isPawnPromotion:
            self.board[move.endRow][move.endCol] = move.pieceMoved[0] + 'Q'

        # en passant
        if move.isEnpassantMove:
            self.board[move.startRow][move.endCol] = '--'  # capture the pawn

        # update en passant possibility
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ((move.startRow + move.endRow) // 2, move.startCol)
        else:
            self.enpassantPossible = ()

        # handle castling move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # kingside
                self.board[move.endRow][move.endCol - 1] = self.board[move.endRow][move.endCol + 1]
                self.board[move.endRow][move.endCol + 1] = '--'
            else:  # queenside
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 2]
                self.board[move.endRow][move.endCol - 2] = '--'

        # update castle rights and log a copy
        self.updateCastleRight(move)
        self.castleRightLog.append(CastleRights(
            self.currentCastleRight.wks,
            self.currentCastleRight.bks,
            self.currentCastleRight.wqs,
            self.currentCastleRight.bqs
        ))

    def undoMove(self):
        if len(self.moveLog) == 0:
            return

        move = self.moveLog.pop()
        self.board[move.startRow][move.startCol] = move.pieceMoved
        self.board[move.endRow][move.endCol] = move.pieceCaptured
        self.whiteToMove = not self.whiteToMove

        # update king's location
        if move.pieceMoved == 'wK':
            self.whiteKingLocation = (move.startRow, move.startCol)
        elif move.pieceMoved == 'bK':
            self.blackKingLocation = (move.startRow, move.startCol)

        # undo en passant
        if move.isEnpassantMove:
            self.board[move.endRow][move.endCol] = '--'
            self.board[move.startRow][move.endCol] = move.pieceCaptured

        # undo 2-square pawn move
        if move.pieceMoved[1] == 'p' and abs(move.startRow - move.endRow) == 2:
            self.enpassantPossible = ()

        # undo castling move
        if move.isCastleMove:
            if move.endCol - move.startCol == 2:  # kingside
                self.board[move.endRow][move.endCol + 1] = self.board[move.endRow][move.endCol - 1]
                self.board[move.endRow][move.endCol - 1] = '--'
            else:  # queenside
                self.board[move.endRow][move.endCol - 2] = self.board[move.endRow][move.endCol + 1]
                self.board[move.endRow][move.endCol + 1] = '--'

        # restore previous castling rights
        self.castleRightLog.pop()
        lastRights = self.castleRightLog[-1]
        self.currentCastleRight = CastleRights(
            lastRights.wks,
            lastRights.bks,
            lastRights.wqs,
            lastRights.bqs
        )
        self.checkMate= False
        self.staleMate=False

    #update castling rights - whenver its a rook or king move
    def updateCastleRight(self, move):
        if move.pieceMoved == 'wK':
            self.currentCastleRight.wks = False
            self.currentCastleRight.wqs = False
        elif move.pieceMoved == 'bK':
            self.currentCastleRight.bks = False
            self.currentCastleRight.bqs = False

        # White rooks moved
        if move.pieceMoved == 'wR':
            if move.startRow == 7:
                if move.startCol == 0:  # left rook
                    self.currentCastleRight.wqs = False
                elif move.startCol == 7:  # right rook
                    self.currentCastleRight.wks = False

        # Black rooks moved
        elif move.pieceMoved == 'bR':
            if move.startRow == 0:
                if move.startCol == 0:  # left rook
                    self.currentCastleRight.bqs = False
                elif move.startCol == 7:  # right rook
                    self.currentCastleRight.bks = False

        # White rooks captured
        if move.pieceCaptured == 'wR':
            if move.endRow == 7:
                if move.endCol == 0:
                    self.currentCastleRight.wqs = False
                elif move.endCol == 7:
                    self.currentCastleRight.wks = False

        # Black rooks captured
        elif move.pieceCaptured == 'bR':
            if move.endRow == 0:
                if move.endCol == 0:
                    self.currentCastleRight.bqs = False
                elif move.endCol == 7:
                    self.currentCastleRight.bks = False
    '''
    The way the check algorithm works is:
    1) generate all possible moves
    2) for each move, make the move
    3) generate all opponent moves
    4) for each opponent moves, see if they attack your king
    5) if they do attack your king, not a valid move
    
    '''
    def getValidMoves(self):
        tempEnpassantPossible = self.enpassantPossible
        tempCastleRights = CastleRights(self.currentCastleRight.wks,self.currentCastleRight.bks,self.currentCastleRight.wqs,self.currentCastleRight.bqs)
        #1) generate all possible moves
        moves = self.getAllPossibleMoves()
        if self.whiteToMove:
            self.getCastleMoves(self.whiteKingLocation[0],self.whiteKingLocation[1],moves)
        else:
            self.getCastleMoves(self.blackKingLocation[0],self.blackKingLocation[1],moves)
        #2) for each move, make the move
        for i in range(len(moves)-1,-1,-1): #backward for loop to avoid bugs
            self.makeMove(moves[i])
            #3) generate all opponent moves
            #done in incheck function
            #4) for each opponent moves, see if they attack your king
            # dont in squareunderattack function
            #5) if they do attack your king, not a valid move
            self.whiteToMove = not self.whiteToMove
            if self.inCheck():
                moves.remove(moves[i])
            self.whiteToMove = not self.whiteToMove
            self.undoMove()
        if len(moves) == 0: #either checkmate or stalemate
            if self.inCheck():
                self.checkMate = True
            else:
                self.staleMate = True
        else:
            self.checkMate = False
            self.staleMate = False
        self.enpassantPossible = tempEnpassantPossible
        self.currentCastleRight = tempCastleRights
        return moves

    '''
    determine if the current player is in check
    '''
    def inCheck(self):
        if self.whiteToMove:
            return self.squareUnderAttack(self.whiteKingLocation[0], self.whiteKingLocation[1])
        else:
            return self.squareUnderAttack(self.blackKingLocation[0], self.blackKingLocation[1])



    '''
    determine if the enemy can attack the square r,c
    '''
    def squareUnderAttack(self,r,c):
        self.whiteToMove= not self.whiteToMove #switch to opponent view
        oppMoves = self.getAllPossibleMoves()
        self.whiteToMove = not self.whiteToMove
        for move in oppMoves:
            if move.endRow == r and move.endCol == c:
                return True
        return False


    def getAllPossibleMoves(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn =='b'and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r,c, moves)

        return moves

    '''
    get all the pawn moves for the pawn located at row, col and add these moves to the list
    '''
    def getPawnMoves(self, r, c, moves):
        if self.whiteToMove:
            if self.board[r-1][c] == "--":
               moves.append(Move((r,c), (r-1,c), self.board))
               if r==6 and self.board[r-2][c] == "--":
                    moves.append(Move((r,c), (r-2,c), self.board))
            if c-1>=0:
                if self.board[r-1][c-1][0] == "b":
                    moves.append(Move((r,c), (r-1,c-1), self.board))
                elif (r-1, c-1) == self.enpassantPossible:
                    moves.append(Move((r,c), (r-1,c-1), self.board, isEnpassantMove=True))
            if c+1 <=7:
                if self.board[r-1][c+1][0] == "b":
                    moves.append(Move((r,c), (r-1,c+1), self.board))
                elif (r-1, c+1) == self.enpassantPossible:
                    moves.append(Move((r,c), (r-1,c+1), self.board, isEnpassantMove=True))
        if self.whiteToMove == False:
            if self.board[r+1][c] == "--":
               moves.append(Move((r,c), (r+1,c), self.board))
               if r==1 and self.board[r+2][c] == "--":
                    moves.append(Move((r,c), (r+2,c), self.board))
            if c-1>=0:
                if self.board[r+1][c-1][0] == "w":
                    moves.append(Move((r,c), (r+1,c-1), self.board))
                elif (r+1, c-1) == self.enpassantPossible:
                    moves.append(Move((r,c), (r+1,c-1), self.board, isEnpassantMove=True))
            if c+1 <=7:
                if self.board[r+1][c+1][0] == "w":
                    moves.append(Move((r,c), (r+1,c+1), self.board))
                elif (r+1, c+1) == self.enpassantPossible:
                    moves.append(Move((r,c), (r+1,c+1), self.board, isEnpassantMove=True))



    def getRookMoves(self, r, c, moves):
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1))
        enemyColor = "b" if self.whiteToMove else "w"
        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i
                if 0 <= endRow < 8 and 0 <= endCol < 8:  # on board
                    endPiece = self.board[endRow][endCol]
                    if endPiece == "--":  # empty space valid
                        moves.append(Move((r, c), (endRow, endCol), self.board))

                    elif endPiece[0] == enemyColor:  # enemy piece valid
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break
                    else:  # friendly piece invalid
                        break
                else:  # off board
                    break

    def getKnightMoves(self, r, c, moves):
        knightMoves = ((-2, -1), (-2, 1), (-1, -2), (-1, 2),
                       (1, -2), (1, 2), (2, -1), (2, 1))
        allyColor = "w" if self.whiteToMove else "b"

        for m in knightMoves:
            endRow = r + m[0]
            endCol = c + m[1]

            if 0 <= endRow < 8 and 0 <= endCol < 8:  # on board
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:  # not an ally piece (empty or enemy)
                    moves.append(Move((r, c), (endRow, endCol), self.board))

    def getBishopMoves(self, r, c, moves):
        directions = ((-1, -1), (-1, 1), (1, -1), (1, 1))
        enemyColor = "b" if self.whiteToMove else "w"

        for d in directions:
            for i in range(1, 8):
                endRow = r + d[0] * i
                endCol = c + d[1] * i

                if 0 <= endRow < 8 and 0 <= endCol < 8:  # on board
                    endPiece = self.board[endRow][endCol]

                    if endPiece == "--":  # empty space valid
                        moves.append(Move((r, c), (endRow, endCol), self.board))

                    elif endPiece[0] == enemyColor:  # enemy piece valid
                        moves.append(Move((r, c), (endRow, endCol), self.board))
                        break

                    else:  # friendly piece invalid
                        break
                else:  # off board
                    break
    def getQueenMoves(self, r, c, moves):
        self.getRookMoves(r, c, moves)
        self.getBishopMoves(r, c, moves)
    def getKingMoves(self, r, c, moves):
        kingMoves = ((-1, -1),(-1,0), (-1, 1), (1, -1), (1, 1),(0,-1),(0,1),(1,0))
        allyColor="w" if self.whiteToMove else "b"
        for i in range(8):
            endRow = r + kingMoves[i][0]
            endCol = c + kingMoves[i][1]
            if 0 <= endRow < 8 and 0 <= endCol < 8:
                endPiece = self.board[endRow][endCol]
                if endPiece[0] != allyColor:
                    moves.append(Move((r, c), (endRow, endCol), self.board))

    '''
    Generate all valid castle moves for the king at (r,c) and add
    '''
    def getCastleMoves(self, r, c, moves):
        if self.squareUnderAttack(r,c):
            return
        if (self.whiteToMove and self.currentCastleRight.wks) or (not self.whiteToMove and self.currentCastleRight.bks):
            self.getKingsideCastleMoves(r, c, moves)
        if (self.whiteToMove and self.currentCastleRight.wqs) or (not self.whiteToMove and self.currentCastleRight.bqs):
            self.getQueensideCastleMoves(r,c,moves)

    def getKingsideCastleMoves(self, r, c, moves):
        if self.board[r][c+1] == '--' and self.board[r][c+2] == '--':
            if not self.squareUnderAttack(r,c+1) and not self.squareUnderAttack(r,c+2):
                moves.append(Move((r,c), (r,c+2), self.board,castle=True))

    def getQueensideCastleMoves(self, r, c, moves):
        if self.board[r][c-1] == '--' and self.board[r][c-2] == '--'and self.board[r][c-3] == '--':
            if not self.squareUnderAttack(r,c-1) and not self.squareUnderAttack(r,c-2):
                moves.append(Move((r,c), (r,c-2), self.board,castle=True))
    def parseMove(self, move):
        pieceMoved= move[0:2]
        pieceMovedTo= move[2:4]
        try:
            startRow = Move.ranksToRows[pieceMoved[1]]
            startCol = Move.filesToRanks[pieceMoved[0]]
            endRow = Move.ranksToRows[pieceMovedTo[1]]
            endCol = Move.filesToRanks[pieceMovedTo[0]]
        except KeyError:
            return None
        for move in self.getValidMoves():
            if (move.startRow == startRow and move.startCol == startCol and
                    move.endRow == endRow and move.endCol == endCol):
                return move
        return None
    def TOJSON(self):
        self.getValidMoves()
        jsonBoard={}
        for r, rows in enumerate(self.board):
            for c, piece in enumerate(rows):
                if piece != "--":
                    jsonBoard[Move.colsToFiles[c]+Move.rowsToRanks[r]]= piece
        return {"board": jsonBoard, "whiteToMove": self.whiteToMove, "checkMate": self.checkMate, "staleMate": self.staleMate, "inCheck": self.inCheck()}
class CastleRights():
    def __init__(self, wks,bks,wqs,bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs



class Move():
    ranksToRows = {"1":7, "2":6, "3":5, "4":4, "5":3, "6":2, "7":1, "8":0}
    rowsToRanks = {v: k for k, v in ranksToRows.items()}
    filesToRanks = { "a":0, "b":1, "c":2, "d":3, "e":4, "f":5, "g":6, "h":7}
    colsToFiles = {v: k for k,v in filesToRanks.items()}
    def __init__(self,startSq,endSq, board, isEnpassantMove = False, castle=False):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        #pawn promotion
        self.isPawnPromotion = False
        if (self.pieceMoved == 'wp' and self.endRow == 0) or (self.pieceMoved == 'bp' and self.endRow == 7):
            self.isPawnPromotion = True
        #en passant
        self.isEnpassantMove = isEnpassantMove
        if self.isEnpassantMove:
            self.pieceCaptured = 'wp' if self.pieceMoved == 'bp' else 'bp'
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol
        #castle move
        self.isCastleMove= castle
    '''
    overriding the equals method
    '''
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False
    def getChessNotation(self):
        return self.getRankFile(self.startRow, self.startCol) + self.getRankFile(self.endRow, self.endCol)
    def getRankFile(self,r,c):
        return self.colsToFiles[c] + self.rowsToRanks[r]