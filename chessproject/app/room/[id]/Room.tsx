"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Chessboard, PieceDropHandlerArgs, PieceHandlerArgs } from "react-chessboard";
import {
  BoardFrame, SiteHeader, ServerBoard, boardColors,
  focusRing, primaryButton, secondaryButton, toPosition, checkStyles
} from "../../components/board";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const WS = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000";

export default function Room() {
  const { id } = useParams<{ id: string }>();
  const socket = useRef<WebSocket | null>(null);
  const colorRef = useRef<"white" | "black" | null>(null);
  const [color, setColor] = useState<"white" | "black" | null>(null);
  const [board, setBoard] = useState<ServerBoard>({});
  const [whiteToMove, setWhiteToMove] = useState(true);
  const [players, setPlayers] = useState(1);
  const [opponentLeft, setOpponentLeft] = useState(false);
  const [notice, setNotice] = useState("");
  const [disconnected, setDisconnected] = useState(false);
  const [copied, setCopied] = useState(false);
  const [url, setUrl] = useState("");
  const [result, setResult] = useState("");
  const [inCheck, setInCheck] = useState(false);
  const squareStyles = checkStyles(board, whiteToMove, inCheck);


  const position = useMemo(() => toPosition(board), [board]);
  const waiting = players < 2 && !opponentLeft;
  const myTurn = color !== null && !waiting && (color === "white") === whiteToMove && !result;

  useEffect(() => {
    setUrl(window.location.href);
    const ws = new WebSocket(`${WS}/ws/${id}`);
    socket.current = ws;

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "color") {
        colorRef.current = data.color;
        setColor(data.color);
      }
        
      else if (data.type === "players") {
        setPlayers(data.count);
        if (data.count === 2) setOpponentLeft(false);
      } else if (data.type === "state") {
        setBoard(data.board);
        setWhiteToMove(data.whiteToMove);
        setInCheck(Boolean(data.inCheck));
      }
      else if (data.type === "resigned") {
        setResult(data.color === colorRef.current ? "You resigned. You lost." : "Your opponent resigned. You won!");}
      else if (data.type === "error") {
        setNotice(data.detail);
        setTimeout(() => setNotice(""), 2500);
      } else if (data.type === "opponent_left") setOpponentLeft(true);
      if (data.checkMate) {
        const loser= data.whiteToMove ? "white" : "black";
        setResult(loser === colorRef.current ? "Checkmate! You lost." : "Checkmate! You won.");
      }
      else if (data.staleMate) {
        setResult("Stalemate! It's a draw.");
      }
    };
    ws.onclose = () => setDisconnected(true);

      return () => {
        ws.onclose = null;
        ws.close();
    };
  }, [id]);

  function onPieceDrop({ sourceSquare, targetSquare }: PieceDropHandlerArgs) {
    if (!targetSquare || !myTurn) return false;
    socket.current?.send(sourceSquare + targetSquare);
    return false;
  }

  function canDragPiece({ piece }: PieceHandlerArgs) {
    return myTurn && piece.pieceType[0] === color?.[0];
  }

  async function copyLink() {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  const status = result || (disconnected && !color
    ? "Room unavailable"
    : !color
      ? "Joining room"
      : opponentLeft
        ? "Your friend left"
        : waiting
          ? "Waiting for a friend"
          : myTurn
            ? "Your move"
            : "Their move");

  return (
    <main className="min-h-screen bg-[#F2F3EF] text-[#1C2320]">
      <div className="mx-auto max-w-6xl px-6 pb-16 sm:px-10">
        <SiteHeader />

        <div className="grid gap-10 lg:grid-cols-[minmax(0,600px)_1fr] lg:gap-16">
          <BoardFrame>
            <Chessboard
              options={{
                id: "room-board",
                position,
                onPieceDrop,
                canDragPiece,
                squareStyles,
                boardOrientation: color === "black" ? "black" : "white",
                animationDurationInMs: 250,
                ...boardColors,
              }}
            />
          </BoardFrame>

          <aside className="flex flex-col">
            <p className="text-sm text-[#55605A]">
              {color ? `You play ${color}` : "Live game"}
            </p>
            <h1
              aria-live="polite"
              className="mt-2 flex items-center gap-3 font-[family-name:var(--font-display)] text-4xl leading-tight sm:text-5xl"
            >
              {status}
              {waiting && color && (
                <span className="h-2.5 w-2.5 rounded-full bg-[#5B7F5A] motion-safe:animate-pulse" />
              )}
            </h1>
            <p className="mt-3 h-6 text-[#55605A]">
              {notice ||
                (disconnected && !color ? "This room is full or no longer exists." : "")}
            </p>

            {waiting && color && (
              <section className="mt-6 border-t border-[#1C2320]/15 pt-5">
                <h2 className="text-sm font-semibold">Send this link to a friend</h2>
                <div className="mt-3 flex gap-2">
                  <input
                    readOnly
                    value={url}
                    onFocus={(e) => e.target.select()}
                    aria-label="Invite link"
                    className={`min-w-0 flex-1 rounded-md border border-[#1C2320]/20 bg-white/60 px-3 py-3 text-sm text-[#55605A] ${focusRing}`}
                  />
                  <button onClick={copyLink} className={primaryButton}>
                    {copied ? "Copied" : "Copy link"}
                  </button>
                </div>
                <p className="mt-3 text-sm text-[#55605A]">
                  The game starts when they open it. You move first as white.
                </p>
              </section>
            )}

            <div className="mt-8 flex flex-wrap gap-3">
              {!result && !waiting && color && (
                <button onClick={() => socket.current?.send("resign")} className={secondaryButton}>
                  Resign
                </button>
              )}
              <Link href="/" className={secondaryButton}>
                Leave room
              </Link>
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}