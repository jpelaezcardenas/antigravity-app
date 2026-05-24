"use client";

import Link from "next/link";

export function FAB() {
  return (
    <Link
      href="/app/bunker"
      className="fixed bottom-28 right-4 md:bottom-8 w-14 h-14 rounded-full bg-primary text-on-primary shadow-lg flex items-center justify-center hover:shadow-xl hover:scale-110 transition-all font-bold text-xl"
      title="Admin Panel"
    >
      🔧
    </Link>
  );
}
