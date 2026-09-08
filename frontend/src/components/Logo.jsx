import React from 'react';

export default function Logo({ light = false }) {
  return (
    <div className="flex items-center gap-2 font-bold text-xl tracking-tight">
      <svg
        className="w-8 h-8"
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect width="100" height="100" rx="20" fill="#15803d" />
        <path
          d="M35 25V75M35 50L65 25M35 50L65 75"
          stroke="white"
          strokeWidth="10"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M60 25C60 25 75 35 60 45C48 45 48 35 60 25Z"
          fill="#4ade80"
        />
      </svg>
      <span className={light ? "text-amber-100" : "text-gray-900"}>
        KISAN<span className="text-emerald-400">Q</span>
      </span>
    </div>
  );
}