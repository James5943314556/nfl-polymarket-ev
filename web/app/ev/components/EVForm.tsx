// app/ev/components/EVForm.tsx

"use client";

import { useState } from "react";
import type { Side, EVResponse } from "../types";

type Props = {
  onResult: (result: EVResponse | null) => void;
  onError: (msg: string | null) => void;
};

export default function EVForm({ onResult, onError }: Props) {
  const [slug, setSlug] = useState("nfl-buf-hou-2025-11-20");
  const [side, setSide] = useState<Side>("home_yes");

  const [quarter, setQuarter] = useState(1);
  const [minutesRemaining, setMinutesRemaining] = useState(15);
  const [secondsRemaining, setSecondsRemaining] = useState(0);

  const [homeScore, setHomeScore] = useState(0);
  const [awayScore, setAwayScore] = useState(0);

  const [homeHasBall, setHomeHasBall] = useState(true);
  const [yardline100, setYardline100] = useState(75);
  const [down, setDown] = useState(1);
  const [ydstogo, setYdstogo] = useState(10);

  const [feeCost, setFeeCost] = useState(0.01);

  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    onError(null);
    onResult(null);
    setLoading(true);

    try {
      const totalSeconds =
        Number(minutesRemaining) * 60 + Number(secondsRemaining);
      const scoreDiffHome = Number(homeScore) - Number(awayScore);

      const body = {
        slug: slug.trim(),
        side,
        fee_cost: feeCost,
        state: {
          quarter,
          seconds_remaining: totalSeconds,
          score_diff_home: scoreDiffHome,
          home_has_ball: homeHasBall,
          yardline_100: yardline100,
          down,
          ydstogo,
        },
      };

      const res = await fetch("http://localhost:8000/ev/game", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => null);
        const detail = data?.detail || res.statusText;
        throw new Error(
          typeof detail === "string" ? detail : JSON.stringify(detail)
        );
      }

      const data: EVResponse = await res.json();
      onResult(data);
    } catch (err: any) {
      onError(err.message || "Failed to compute EV");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-6 rounded-2xl border border-gray-200 bg-white/70 p-6 shadow-sm"
    >
      {/* Slug + Side */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">
            Polymarket game slug
          </label>
          <input
            type="text"
            value={slug}
            onChange={(e) => setSlug(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="nfl-buf-hou-2025-11-20"
          />
          <p className="mt-1 text-xs text-gray-500">
            From the URL:{" "}
            <code className="bg-gray-100 px-1 rounded">
              https://polymarket.com/event/
              <strong>nfl-buf-hou-2025-11-20</strong>
            </code>
          </p>
        </div>

        <div>
          <span className="block text-sm font-medium mb-1">
            Side you&apos;re considering
          </span>
          <div className="flex gap-4 text-sm">
            <label className="inline-flex items-center gap-2">
              <input
                type="radio"
                name="side"
                value="home_yes"
                checked={side === "home_yes"}
                onChange={() => setSide("home_yes")}
              />
              <span>Home (YES)</span>
            </label>
            <label className="inline-flex items-center gap-2">
              <input
                type="radio"
                name="side"
                value="home_no"
                checked={side === "home_no"}
                onChange={() => setSide("home_no")}
              />
              <span>Home (NO / away)</span>
            </label>
          </div>
        </div>
      </div>

      {/* Game State */}
      <div className="space-y-4">
        <h2 className="text-sm font-medium text-gray-800">
          Game state (live inputs)
        </h2>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium mb-1">Quarter</label>
            <input
              type="number"
              min={1}
              max={5}
              value={quarter}
              onChange={(e) => setQuarter(Number(e.target.value) || 1)}
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-medium mb-1">
              Minutes left
            </label>
            <input
              type="number"
              min={0}
              max={15}
              value={minutesRemaining}
              onChange={(e) =>
                setMinutesRemaining(Number(e.target.value) || 0)
              }
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-medium mb-1">
              Seconds (0–59)
            </label>
            <input
              type="number"
              min={0}
              max={59}
              value={secondsRemaining}
              onChange={(e) =>
                setSecondsRemaining(Number(e.target.value) || 0)
              }
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-medium mb-1">
              Yardline (0–100)
            </label>
            <input
              type="number"
              min={0}
              max={100}
              value={yardline100}
              onChange={(e) => setYardline100(Number(e.target.value) || 0)}
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
            <p className="mt-1 text-[10px] text-gray-500">
              0 = own goal line, 100 = opponent goal line
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-medium mb-1">
              Home score
            </label>
            <input
              type="number"
              min={0}
              value={homeScore}
              onChange={(e) => setHomeScore(Number(e.target.value) || 0)}
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">
              Away score
            </label>
            <input
              type="number"
              min={0}
              value={awayScore}
              onChange={(e) => setAwayScore(Number(e.target.value) || 0)}
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">Down</label>
            <input
              type="number"
              min={1}
              max={4}
              value={down}
              onChange={(e) => setDown(Number(e.target.value) || 1)}
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium mb-1">
              Yards to go
            </label>
            <input
              type="number"
              min={1}
              value={ydstogo}
              onChange={(e) => setYdstogo(Number(e.target.value) || 1)}
              className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm"
            />
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <span className="text-xs font-medium">Possession</span>
          <label className="inline-flex items-center gap-1">
            <input
              type="radio"
              name="possession"
              checked={homeHasBall}
              onChange={() => setHomeHasBall(true)}
            />
            <span>Home has ball</span>
          </label>
          <label className="inline-flex items-center gap-1">
            <input
              type="radio"
              name="possession"
              checked={!homeHasBall}
              onChange={() => setHomeHasBall(false)}
            />
            <span>Away has ball</span>
          </label>
        </div>
      </div>

      {/* Fees */}
      <div className="space-y-2">
        <label className="block text-xs font-medium mb-1">
          Fee cost (per contract, price space)
        </label>
        <input
          type="number"
          step="0.001"
          min={0}
          value={feeCost}
          onChange={(e) => setFeeCost(Number(e.target.value) || 0)}
          className="w-full rounded-md border border-gray-300 px-2 py-1 text-sm max-w-xs"
        />
        <p className="text-[10px] text-gray-500">
          0.01 = 1 cent per contract. Adjust if Polymarket fee changes.
        </p>
      </div>

      <div>
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
        >
          {loading ? "Computing..." : "Compute EV"}
        </button>
      </div>
    </form>
  );
}
