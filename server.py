from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import json
import queue
import threading
from pydantic import BaseModel
from ChessEngine import GameState
import chessAi
import uuid
from fastapi.middleware.cors import CORSMiddleware
import os



games={}
rooms={}
app = FastAPI()
class MoveRequest(BaseModel):
    move: str
@app.post("/new-game")
def new_game():
    gameId = str(uuid.uuid4())
    game = GameState()
    games[gameId] = game

    return {"gameId": gameId, "state": game.TOJSON()}
@app.get("/game/{gameId}/legal-moves")
def legal_moves(gameId):
    game = games.get(gameId)
    moves=[]
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    else:
        for move in game.getValidMoves():
            moves.append(move.getChessNotation())
        return {"moves": moves}
@app.post("/game/{gameId}/move")
def move(gameId: str, moveRequest: MoveRequest):
    game = games.get(gameId)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    else:
        moveToMake=game.parseMove(moveRequest.move)
        if moveToMake is None:
            raise HTTPException(status_code=400, detail="Illegal move")
        else:
            game.makeMove(moveToMake)
            return {"state": game.TOJSON()}
@app.post("/game/{gameId}/ai-move")
def ai_move(gameId: str):
    game = games.get(gameId)

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    else:
        validMoves = game.getValidMoves()
        if len(validMoves) ==0:
            raise HTTPException(status_code=400, detail="Game is over!")
        else:
            moveAiMakes=chessAi.findBestMoveNegaMax(game, validMoves)
            game.makeMove(moveAiMakes)
            moveAiMakes=moveAiMakes.getChessNotation()
            return {"move": moveAiMakes, "state": game.TOJSON()}
@app.websocket("/ws/{gameId}")
async def websocket_endpoint(websocket: WebSocket, gameId: str):
    await websocket.accept()
    game = games.get(gameId)
    if game is None:
        await websocket.send_json({"type": "error", "detail": "Game not found"})
        await websocket.close()
        return
    players=rooms.setdefault(gameId, [])
    if len(players)>= 2:
        await websocket.send_json({"type": "error", "detail": "Game is full"})
        await websocket.close()
        return
    else:
        color="white" if len(players) == 0 else "black"
        players.append(websocket)
       
        await websocket.send_json({"type": "color", "color": color})
        await websocket.send_json({"type": "state", **game.TOJSON()})
        for p in players:
            await p.send_json({"type": "players", "count": len(players)})
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "resign":
                for p in players:
                    await p.send_json({"type": "resigned", "color": color})
                continue
            if color == "white" and game.whiteToMove == False or color == "black" and game.whiteToMove == True:
                await websocket.send_json({"type": "error", "detail": "It's not your turn"})
                continue
            else:
                moveToMake=game.parseMove(data)
                if moveToMake is None:
                    await websocket.send_json({"type": "error", "detail": "Illegal move"})
                else:
                    game.makeMove(moveToMake)
                    for p in players:
                        await p.send_json({"type": "state", **game.TOJSON()})
                        
    except WebSocketDisconnect:
        print(f"Client disconnected from game {gameId}")
        players.remove(websocket)
        for p in players:
            await p.send_json({"type": "opponent_left"})
            await p.send_json({"type": "players", "count": len(players)})
@app.post("/game/{gameId}/ai-move-stream")
def ai_move_stream(gameId: str):
    game = games.get(gameId)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    validMoves = game.getValidMoves()
    if len(validMoves) == 0:
        raise HTTPException(status_code=400, detail="Game is over!")
    def events():
        q = queue.Queue()
        result = {}
        def run():
            try:
                best, info = chessAi.searchStream(game, validMoves, q.put)
                result["best"] = best
                result["info"] = info
            finally:
                q.put(None)
        threading.Thread(target=run, daemon=True).start()
        while True:
            event = q.get()
            if event is None:
                break
            yield f"data: {json.dumps(event)}\n\n"
        best = result["best"]
        game.makeMove(best)
        done = {"type": "done", "move": best.getChessNotation(),
                "state": game.TOJSON(), **result["info"]}
        yield f"data: {json.dumps(done)}\n\n"
    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)