"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Chessboard } from "react-chessboard";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const WS = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

type Position = Record<string, { pieceType: string }>;

const START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR";
const FRIED_LIVER = [
  "e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6", "f3g5", "d7d5",
  "e4d5", "f6d5", "g5f7", "e8f7", "d1f3", "f7e6", "b1c3",
];

function fenToPosition(fen: string): Position {
  const pos: Position = {};
  fen.split("/").forEach((row, r) => {
    let c = 0;
    for (const ch of row) {
      if (/\d/.test(ch)) {
        c += Number(ch);
        continue;
      }
      const color = ch === ch.toUpperCase() ? "w" : "b";
      pos["abcdefgh"[c] + (8 - r)] = { pieceType: color + ch.toUpperCase() };
      c++;
    }
  });
  return pos;
}

function buildFrames(): Position[] {
  const frames = [fenToPosition(START)];
  for (const move of FRIED_LIVER) {
    const next = { ...frames[frames.length - 1] };
    next[move.slice(2, 4)] = next[move.slice(0, 2)];
    delete next[move.slice(0, 2)];
    frames.push(next);
  }
  return frames;
}

const FRAMES = buildFrames();
const LAST = FRAMES.length - 1;


function HeroBoard() {
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setFrame(LAST);
      return;
    }
    const delay = frame === LAST ? 3200 : frame === 0 ? 1400 : 900;
    const timer = setTimeout(() => setFrame((f) => (f === LAST ? 0 : f + 1)), delay);
    return () => clearTimeout(timer);
  }, [frame]);

  return (
    <div className="rounded-[6px] bg-[#3B2E25] p-3 shadow-[inset_0_1px_0_#5A4636,0_40px_80px_-40px_rgba(28,35,32,0.55)]">
      <Chessboard
        options={{
          id: "hero-board",
          position: FRAMES[frame],
          allowDragging: false,
          allowDrawingArrows: false,
          showNotation: false,
          animationDurationInMs: 550,
          lightSquareStyle: { backgroundColor: "#EAE6D3" },
          darkSquareStyle: { backgroundColor: "#5B7F5A" },
        }}
      />
    </div>
  );
}

export default function Home() {
  const router = useRouter();
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  async function inviteFriend() {
    setCreating(true);
    setError("");
    try {
      const res = await fetch(`${API}/new-game`, { method: "POST" });
      const data = await res.json();
      router.push(`/room/${data.gameId}`);
    } catch {
      setError("Couldn't reach the game server. Check that it's running, then try again.");
      setCreating(false);
    }
  }

  const focus =
    "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5B7F5A]";

  return (
    <main className="min-h-screen bg-[#F2F3EF] text-[#1C2320]">
      <div className="mx-auto flex min-h-screen max-w-6xl flex-col px-6 sm:px-10">
        <header className="flex items-center justify-between py-6">
          <span className="font-[family-name:var(--font-display)] text-2xl">Gambit</span>
          <a
            href="https://github.com/YOUR_USERNAME/YOUR_REPO"
            className={`text-sm text-[#55605A] underline-offset-4 hover:text-[#1C2320] hover:underline ${focus}`}
          >
            Source on GitHub
          </a>
        </header>

        <section className="grid flex-1 items-center gap-12 py-10 lg:grid-cols-[1fr_minmax(0,520px)] lg:gap-20">
          <div className="max-w-xl">
            <h1 className="font-[family-name:var(--font-display)] text-[clamp(3.25rem,8vw,6rem)] font-medium leading-[0.92] tracking-[-0.02em]">
              Your move.
            </h1>
            <p className="mt-6 max-w-md text-lg leading-relaxed text-[#55605A]">
              A chess engine written in Python. It searches thousands of positions
              before every reply and weighs each one by material and piece placement.
            </p>

            <div className="mt-10 flex flex-wrap gap-3">
              <Link
                href="/play"
                className={`rounded-md bg-[#1C2320] px-6 py-3.5 text-[15px] font-medium text-[#F2F3EF] transition duration-150 hover:bg-[#2C3631] active:scale-[0.98] ${focus}`}
              >
                Play the engine
              </Link>
              <button
                onClick={inviteFriend}
                disabled={creating}
                className={`rounded-md border border-[#1C2320]/25 px-6 py-3.5 text-[15px] font-medium transition duration-150 hover:bg-[#1C2320]/[0.05] active:scale-[0.98] disabled:opacity-60 ${focus}`}
              >
                {creating ? "Creating room…" : "Invite a friend"}
              </button>
            </div>

            {error && (
              <p role="alert" className="mt-4 text-sm text-[#9B3B2E]">
                {error}
              </p>
            )}
          </div>

          <figure className="w-full">
            <HeroBoard />
            <figcaption className="mt-4 text-sm text-[#55605A]">
              The Fried Liver Attack, on a loop.
            </figcaption>
          </figure>
        </section>
      </div>
    </main>
  );
}