"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Chessboard, PieceDropHandlerArgs } from "react-chessboard";
import {
  BoardFrame, SiteHeader, ServerBoard, boardColors,
  primaryButton, secondaryButton, toPosition,
} from "../components/board";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const WS = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export default function Play() {
  const [gameId, setGameId] = useState<string | null>(null);
  const [board, setBoard] = useState<ServerBoard>({});
  const [legalMoves, setLegalMoves] = useState<string[]>([]);
  const [thinking, setThinking] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [error, setError] = useState("");

  const position = useMemo(() => toPosition(board), [board]);
  const gameOver = gameId !== null && !thinking && legalMoves.length === 0;

  async function loadLegalMoves(id: string) {
    const res = await fetch(`${API}/game/${id}/legal-moves`);
    const data = await res.json();
    setLegalMoves(data.moves ?? []);
  }

  async function newGame() {
    setError("");
    setHistory([]);
    setGameId(null);
    setLegalMoves([]);
    try {
      const res = await fetch(`${API}/new-game`, { method: "POST" });
      const data = await res.json();
      setBoard(data.state.board);
      await loadLegalMoves(data.gameId);
      setGameId(data.gameId);
    } catch {
      setError("Couldn't reach the game server. Check that it's running, then start a new game.");
    }
  }

  useEffect(() => {
    newGame();
  }, []);

  async function playTurn(move: string) {
    if (!gameId) return;
    try {
      const res = await fetch(`${API}/game/${gameId}/move`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ move }),
      });
      if (!res.ok) {
        setBoard((prev) => ({ ...prev }));
        return;
      }
      const data = await res.json();
      setBoard(data.state.board);
      setHistory((h) => [...h, move]);

      setThinking(true);
      setLegalMoves([]);
      const aiRes = await fetch(`${API}/game/${gameId}/ai-move`, { method: "POST" });
      if (aiRes.ok) {
        const aiData = await aiRes.json();
        setBoard(aiData.state.board);
        setHistory((h) => [...h, aiData.move]);
      }
      await loadLegalMoves(gameId);
    } catch {
      setError("Lost the connection to the game server.");
    } finally {
      setThinking(false);
    }
  }

  function onPieceDrop({ sourceSquare, targetSquare }: PieceDropHandlerArgs) {
    if (!targetSquare || thinking) return false;
    const move = sourceSquare + targetSquare;
    if (!legalMoves.includes(move)) return false;
    playTurn(move);
    return true;
  }

  const status = error
    ? "Can't connect"
    : !gameId
      ? "Setting up"
      : thinking
        ? "Engine is thinking"
        : gameOver
          ? "Game over"
          : "Your move";

  const detail = error || (gameOver ? "No legal moves left in this position." : "");

  const rows: [string, string | undefined][] = [];
  for (let i = 0; i < history.length; i += 2) rows.push([history[i], history[i + 1]]);

  return (
    <main className="min-h-screen bg-[#F2F3EF] text-[#1C2320]">
      <div className="mx-auto max-w-6xl px-6 pb-16 sm:px-10">
        <SiteHeader />

        <div className="grid gap-10 lg:grid-cols-[minmax(0,600px)_1fr] lg:gap-16">
          <BoardFrame>
            <Chessboard
              options={{
                id: "play-board",
                position,
                onPieceDrop,
                allowDragging: !thinking && !gameOver,
                animationDurationInMs: 250,
                ...boardColors,
              }}
            />
          </BoardFrame>

          <aside className="flex flex-col">
            <p className="text-sm text-[#55605A]">You play white</p>
            <h1
              aria-live="polite"
              className="mt-2 flex items-center gap-3 font-[family-name:var(--font-display)] text-4xl leading-tight sm:text-5xl"
            >
              {status}
              {thinking && (
                <span className="h-2.5 w-2.5 rounded-full bg-[#5B7F5A] motion-safe:animate-pulse" />
              )}
            </h1>
            {detail && <p className="mt-3 text-[#55605A]">{detail}</p>}

            <section className="mt-8 border-t border-[#1C2320]/15 pt-5">
              <h2 className="text-sm font-semibold">Moves</h2>
              {rows.length === 0 ? (
                <p className="mt-2 text-sm text-[#55605A]">Drag a piece to start. You move first.</p>
              ) : (
                <ol className="mt-3 max-h-72 overflow-y-auto pr-2 text-sm tabular-nums">
                  {rows.map(([white, black], i) => (
                    <li key={i} className="grid grid-cols-[2.5rem_1fr_1fr] py-1">
                      <span className="text-[#55605A]">{i + 1}.</span>
                      <span>{white}</span>
                      <span>{black ?? ""}</span>
                    </li>
                  ))}
                </ol>
              )}
            </section>

            <div className="mt-8 flex flex-wrap gap-3">
              <button onClick={newGame} className={primaryButton}>
                New game
              </button>
              <Link href="/" className={secondaryButton}>
                Home
              </Link>
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}