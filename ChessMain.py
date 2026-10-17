#handles user input and displaying the game


import pygame as p
import ChessEngine
import chessAi


p.init()
WIDTH = HEIGHT = 512 #size of board
DIMENSION = 8 #chess boards are 8x8
SQ_SIZE= HEIGHT // DIMENSION #the size of a square is the height divided by dimension
MAX_FPS = 15
IMAGES = {}

#loading images
def loadImages():
    pieces = ['bB', 'bK','bN','bp','bQ','bR','wB','wK','wN','wp','wQ','wR']
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load('images/' + piece + '.png'), (SQ_SIZE, SQ_SIZE))
#Now for example IMAGES['wp'] will load the white pawn image


'''
The main driver will handle user imput and updating the graphics
'''
def main():
    screen = p.display.set_mode((WIDTH, HEIGHT)) #sets width height
    clock = p.time.Clock() #sets clock
    screen.fill(p.Color('white')) #bg color
    gs = ChessEngine.GameState() #calls gs
    validMoves = gs.getValidMoves()
    moveMade = False #flag variable for when a move is made
    animate= False #flag variable for when we should animate a move
    loadImages() #loads images
    running = True
    sqSelected = ()
    playerClicks= []
    gameOver = False
    playerOne=True #true= human, false=ai
    PlayerTwo=False
    while running:
        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and PlayerTwo)
        for e in p.event.get():
            if e.type == p.QUIT: #makes it able to close
                running = False

            elif e.type == p.MOUSEBUTTONDOWN:
                if not gameOver and humanTurn:
                    location = p.mouse.get_pos()  #xy location of the mouse every frame
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if sqSelected == (row, col): #the user clicked the same square twice
                        sqSelected = ()
                        playerClicks=[]
                        break
                    else:
                        sqSelected = (row, col)
                        playerClicks.append((row, col))
                    if len(playerClicks) ==2:
                        move = ChessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                        print(move.getChessNotation())
                        for i in range(len(validMoves)):
                            if move ==validMoves[i]:
                                moveMade = True
                                animate=True
                                gs.makeMove(validMoves[i])
                                sqSelected = () #resets the clicks
                                playerClicks=[]
                        if not moveMade:
                            playerClicks = [sqSelected]
            #keyhandler
            elif e.type == p.KEYDOWN:
                if e.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    animate=False
                if e.key == p.K_r:
                    gs =ChessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks=[]
                    moveMade=False
                    animate=False
    #ai move finder
        if not gameOver and not humanTurn:
            AIMove= chessAi.findBestMoveNegaMax(gs,validMoves)
            if AIMove is None:
                AIMove= chessAi.findRandomMove(validMoves)
            gs.makeMove(AIMove)
            moveMade = True
            animate=True

        if moveMade:
            if animate:
                animateMove(gs.moveLog[-1],screen,gs.board,clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False



        drawGameState(screen, gs,validMoves,sqSelected)
        if gs.checkMate:
            gameOver = True
            if gs.whiteToMove:
                drawText(screen, 'Black wins by checkmate')
            else:
                drawText(screen, 'White wins by checkmate')
        if gs.staleMate:
            gameOver = True
            drawText(screen, 'Draw by stalemate')

        clock.tick(MAX_FPS) #sets max fps
        p.display.flip() #flips the render cause its upside down usually


#this will highlight squares
def highlightsquares(screen,gs,validMoves,sqSelected):
    if sqSelected!= ():
        r,c = sqSelected
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'): #check if sqselected is a moveable piece
            s=p.Surface((SQ_SIZE,SQ_SIZE))
            s.set_alpha(100) #transparency
            s.fill(p.Color('green'))
            screen.blit(s, (c*SQ_SIZE,r*SQ_SIZE))
            #highlight moves from that square
            s.fill(p.Color('yellow'))
            for move in validMoves:
                if move.startRow==r and move.startCol==c:
                    screen.blit(s, (SQ_SIZE*move.endCol,SQ_SIZE*move.endRow))

#responsible for graphics in current game state
def drawGameState(screen,gs,validMoves,sqSelected):
    drawBoard(screen) #draws the squares
    highlightsquares(screen,gs,validMoves,sqSelected)
    drawPieces(screen,gs.board) #draw pueces on top of those squares


#draws the square on the board
def drawBoard(screen):
    global colors
    colors = [p.Color("white"), p.Color("dark gray")]
    for r in range(DIMENSION): #loops through every square if (r+c % 2) is even then returns 0 else returns 1
        for c in range(DIMENSION):
           color = colors[((r+c) % 2)]
           p.draw.rect(screen, color, p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))


#draws the pieces on the board using the current GameState.board
def drawPieces(screen,board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--": #checks if the square is empty
                screen.blit(IMAGES[piece], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE)) #then proceed on drawing the piece
#animation
def animateMove(move,screen,board,clock):
    global colors
    coords = []
    dR= move.endRow - move.startRow
    dC= move.endCol - move.startCol
    FramesPerSquare= 8
    frameCount= (abs(dR)+ abs(dC))*FramesPerSquare
    for frame in range(frameCount+1):
        r,c=move.startRow+dR*frame/frameCount,move.startCol +dC*frame/frameCount
        drawBoard(screen)
        drawPieces(screen,board)
        #erase the piecemoved from ending square
        color = colors[(move.endRow+move.endCol)%2]
        endSquare = p.Rect(move.endCol*SQ_SIZE,move.endRow*SQ_SIZE,SQ_SIZE,SQ_SIZE)
        p.draw.rect(screen, color, endSquare)
        #draw captured piece onto rectangle
        if move.pieceCaptured != '--':
            screen.blit(IMAGES[move.pieceCaptured], endSquare)
        #draw moving piece
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)

def drawText(screen,text):
    font = p.font.SysFont('Impact', 32,False,False)
    textObject = font.render(text, 0, p.Color('dark red'))
    textLocation = p.Rect(0,0,WIDTH,HEIGHT).move(WIDTH/2-textObject.get_width()/2,HEIGHT/2-textObject.get_height()/2)
    screen.blit(textObject,textLocation)
    textObject = font.render(text, 0, p.Color('brown'))
    screen.blit(textObject,textLocation.move(2,2))
if __name__ == "__main__": #makes it so people can use it when downloading with wtv name
    main()