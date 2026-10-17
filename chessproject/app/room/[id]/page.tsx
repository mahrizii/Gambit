import { Suspense } from "react";
import Room from "./Room";

export default function Page() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-[#F2F3EF]" />}>
      <Room />
    </Suspense>
  );
}