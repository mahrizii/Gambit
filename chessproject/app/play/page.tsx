"use client";
import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Chessboard, PieceDropHandlerArgs } from "react-chessboard";
import type { CSSProperties } from "react";
import {
  BoardFrame, SiteHeader, ServerBoard, boardColors,
  primaryButton, secondaryButton, toPosition, checkStyles
} from "../components/board";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
type Candidate = { move: string; score: number; nodes: number };
type LogLine = { text: string; kind: "look" | "prune" | "cand" };

const ARROW_COLORS = ["rgba(31,77,41,0.9)", "rgba(190,70,50,0.8)", "rgba(31,77,41,0.5)"];

function heatStyles(cands: Candidate[]): Record<string, CSSProperties> {
  if (cands.length === 0) return {};
  const max = Math.max(...cands.map((c) => c.nodes), 1);
  const best = cands.reduce((a, b) => (b.score > a.score ? b : a));
  const styles: Record<string, CSSProperties> = {};
  for (const c of cands) {
    const a = (0.15 + 0.6 * (c.nodes / max)).toFixed(2);
    styles[c.move.slice(2, 4)] = {
      backgroundImage: `linear-gradient(rgba(47,107,58,${a}), rgba(47,107,58,${a}))`,
      boxShadow: c === best ? "inset 0 0 0 3px #1F4D29" : undefined,
    };
  }
  return styles;
}
export default function Play() {
  const [gameId, setGameId] = useState<string | null>(null);
  const [board, setBoard] = useState<ServerBoard>({});
  const [legalMoves, setLegalMoves] = useState<string[]>([]);
  const [thinking, setThinking] = useState(false);
  const [history, setHistory] = useState<string[]>([]);
  const [error, setError] = useState("");
  const [showThinking, setShowThinking] = useState(true);
  const [inCheck, setInCheck] = useState(false);
  const [line, setLine] = useState<string[]>([]);
  const [pruneSq, setPruneSq] = useState<string | null>(null);
  const [cands, setCands] = useState<Candidate[]>([]);
  const [log, setLog] = useState<LogLine[]>([]);
  const [counts, setCounts] = useState({ nodes: 0, pruned: 0, ms: 0 });
  const position = useMemo(() => toPosition(board), [board]);
  const gameOver = gameId !== null && !thinking && legalMoves.length === 0;

  async function loadLegalMoves(id: string) {
    const res = await fetch(`${API}/game/${id}/legal-moves`);
    const data = await res.json();
    setLegalMoves(data.moves ?? []);
  }
  function addLog(entry: LogLine) {
  setLog((l) => [...l.slice(-40), entry]);
}

function clearThinking() {
  setLine([]);
  setPruneSq(null);
  setCands([]);
  setLog([]);
  setCounts({ nodes: 0, pruned: 0, ms: 0 });
}

function handleEvent(ev: any) {
  if (ev.type === "look") {
    setLine(ev.line);
    setPruneSq(null);
    setCounts((c) => ({ ...c, nodes: ev.nodes, pruned: ev.pruned }));
    addLog({ text: ev.line.join(" → "), kind: "look" });
  } else if (ev.type === "prune") {
    setPruneSq(ev.line[ev.line.length - 1].slice(2, 4));
    addLog({ text: `cut  ${ev.line.join(" → ")}`, kind: "prune" });
  } else if (ev.type === "candidate") {
    setCands((c) => [...c, ev]);
    addLog({ text: `${ev.move}  scored ${ev.score.toFixed(2)}  (${ev.nodes} positions)`, kind: "cand" });
  } else if (ev.type === "done") {
    setLine([]);
    setPruneSq(null);
    setCounts({ nodes: ev.nodes, pruned: ev.pruned, ms: ev.ms });
    setBoard(ev.state.board);
    setInCheck(Boolean(ev.state.inCheck));
    setHistory((h) => [...h, ev.move]);
  }
}

async function aiMoveStreaming(id: string) {
  const res = await fetch(`${API}/game/${id}/ai-move-stream`, { method: "POST" });
  if (!res.ok || !res.body) return;
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      if (part.startsWith("data: ")) handleEvent(JSON.parse(part.slice(6)));
    }
  }
}

async function aiMovePlain(id: string) {
  const res = await fetch(`${API}/game/${id}/ai-move`, { method: "POST" });
  if (!res.ok) return;
  const data = await res.json();
  setBoard(data.state.board);
  setInCheck(Boolean(data.state.inCheck));
  setHistory((h) => [...h, data.move]);
}
  async function newGame() {
    setError("");
    setHistory([]);
    setGameId(null);
    setLegalMoves([]);
    setInCheck(false);
    clearThinking();
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

            setInCheck(Boolean(data.state.inCheck));
      setThinking(true);
      setLegalMoves([]);
      clearThinking();
      if (showThinking) await aiMoveStreaming(gameId);
      else await aiMovePlain(gameId);
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
  const check = checkStyles(board, !thinking, inCheck);
  const prune: Record<string, CSSProperties> = pruneSq
    ? { [pruneSq]: { backgroundImage: "linear-gradient(rgba(200,60,45,0.4), rgba(200,60,45,0.4))" } }
    : {};
  const squareStyles = showThinking ? { ...heatStyles(cands), ...prune, ...check } : check;
  const arrows = showThinking
    ? line.map((m, i) => ({ startSquare: m.slice(0, 2), endSquare: m.slice(2, 4), color: ARROW_COLORS[i] ?? ARROW_COLORS[2] }))
    : [];
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

          <div className="grid items-start gap-10 lg:grid-cols-[minmax(0,600px)_1fr] lg:gap-16">
          <BoardFrame>
            <Chessboard
              options={{
                id: "play-board",
                position,
                onPieceDrop,
                allowDragging: !thinking && !gameOver,
                animationDurationInMs: 250,
                ...boardColors,
                squareStyles,
                arrows,
                allowDrawingArrows: false,
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
            <label className="mt-4 flex items-center gap-2 text-sm text-[#55605A] cursor-pointer select-none">
            <input
            type="checkbox"
            checked={showThinking}
            onChange={(e) => setShowThinking(e.target.checked)}
            className="h-4 w-4 accent-[#5B7F5A]"
              />
              Show engine thinking
            </label>
          {showThinking && (counts.nodes > 0 || thinking) && (
            <section className="mt-6 border-t border-[#1C2320]/15 pt-5">
              <div className="grid grid-cols-3 gap-3">
                {[
                  ["Positions", counts.nodes.toLocaleString()],
                  ["Pruned", counts.pruned.toLocaleString()],
                  ["Time", counts.ms ? `${(counts.ms / 1000).toFixed(1)}s` : "…"],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-md bg-[#1C2320]/[0.05] px-3 py-2">
                    <p className="text-xs text-[#55605A]">{label}</p>
                    <p className="text-lg font-semibold tabular-nums">{value}</p>
                  </div>
                ))}
              </div>
              <h2 className="mt-5 text-sm font-semibold">Search log</h2>
              <ol className="mt-2 h-56 overflow-hidden font-mono text-xs leading-5">
                {log.slice(-11).map((entry, i) => (
                  <li
                    key={i}
                    className={`truncate ${
                      entry.kind === "prune" ? "text-[#55605A]/60" : entry.kind === "cand" ? "font-semibold text-[#2F6B3A]" : ""
                    }`}
                  >
                    {entry.text}
                  </li>
                ))}
              </ol>
            </section>
)}
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