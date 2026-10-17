import Link from "next/link";

export type ServerBoard = Record<string, string>;

export function toPosition(board: ServerBoard) {
  const pos: Record<string, { pieceType: string }> = {};
  for (const [square, piece] of Object.entries(board)) {
    pos[square] = { pieceType: piece[0] + piece[1].toUpperCase() };
  }
  return pos;
}

export const boardColors = {
  lightSquareStyle: { backgroundColor: "#EAE6D3" },
  darkSquareStyle: { backgroundColor: "#5B7F5A" },
};

export const focusRing =
  "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#5B7F5A]";

export const primaryButton = `rounded-md bg-[#1C2320] px-5 py-3 text-[15px] font-medium text-[#F2F3EF] transition duration-150 hover:bg-[#2C3631] active:scale-[0.98] disabled:opacity-60 ${focusRing}`;

export const secondaryButton = `rounded-md border border-[#1C2320]/25 px-5 py-3 text-[15px] font-medium transition duration-150 hover:bg-[#1C2320]/[0.05] active:scale-[0.98] ${focusRing}`;

export function BoardFrame({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-[6px] bg-[#3B2E25] p-2 shadow-[inset_0_1px_0_#5A4636,0_40px_80px_-40px_rgba(28,35,32,0.55)] sm:p-3">
      {children}
    </div>
  );
}
export function checkStyles(
  board: ServerBoard,
  whiteToMove: boolean,
  inCheck: boolean
): Record<string, React.CSSProperties> {
  if (!inCheck) return {};
  const king = whiteToMove ? "wK" : "bK";
  const square = Object.keys(board).find((sq) => board[sq] === king);
  if (!square) return {};
  return {
    [square]: {
      background:
        "radial-gradient(circle, rgba(196, 52, 40, 0.95) 0%, rgba(196, 52, 40, 0.55) 45%, rgba(196, 52, 40, 0) 75%)",
    },
  };
}
export function SiteHeader() {
  return (
    <header className="flex items-center justify-between py-6">
      <Link href="/" className={`font-[family-name:var(--font-display)] text-2xl ${focusRing}`}>
        Gambit
      </Link>
    </header>
  );
}