"use client";

import { useState } from "react";

type Side = "home_yes" | "home_no";

type EVResponse = {
  p_model: number;
  fair_price: number;
  market_price: number;
  fee_cost: number;
  edge_raw: number;
  edge_after_fees: number;
  ev_per_contract: number;
};

function computeSecondsRemaining(quarter: number, clock: string): number {
  const parts = clock.split(":");
  if (parts.length !== 2) return 0;
  const mm = Number(parts[0]);
  const ss = Number(parts[1]);
  if (Number.isNaN(mm) || Number.isNaN(ss)) return 0;

  const remainingThisQuarter = mm * 60 + ss;
  const remainingFullQuarters = Math.max(0, 4 - quarter) * 15 * 60;
  return remainingThisQuarter + remainingFullQuarters;
}

export default function EVPage() {
  const [slug, setSlug] = useState("nfl-buf-hou-2025-11-20");
  const [side, setSide] = useState<Side>("home_yes");

  const [quarter, setQuarter] = useState(1);
  const [clock, setClock] = useState("15:00");

  const [homeScore, setHomeScore] = useState(0);
  const [awayScore, setAwayScore] = useState(0);
  const [homeHasBall, setHomeHasBall] = useState(true);

  const [yardline100, setYardline100] = useState(25);
  const [down, setDown] = useState(1);
  const [ydstogo, setYdstogo] = useState(10);

  const [feeCost, setFeeCost] = useState(0.01);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EVResponse | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setLoading(true);

    try {
      const seconds_remaining = computeSecondsRemaining(quarter, clock);
      const score_diff_home = homeScore - awayScore;

      const payload = {
        slug,
        side,
        fee_cost: feeCost,
        state: {
          quarter,
          seconds_remaining,
          home_score: homeScore,
          away_score: awayScore,
          score_diff_home,
          home_has_ball: homeHasBall,
          yardline_100: yardline100,
          down,
          ydstogo,
        },
      };

      const res = await fetch("http://127.0.0.1:8000/ev/game", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`Backend error ${res.status}: ${text || res.statusText}`);
      }

      const data: EVResponse = await res.json();
      setResult(data);
    } catch (err: any) {
      console.error(err);
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl rounded-2xl border border-slate-800 bg-slate-900/70 shadow-xl p-6 md:p-8">
        <h1 className="text-2xl md:text-3xl font-semibold mb-2">NFL Polymarket EV Tool</h1>
        <p className="text-sm text-slate-400 mb-6">
          Enter a Polymarket NFL game slug and current game state. The backend fetches the live moneyline, runs the in-game model, and returns EV.
        </p>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Slug + Side */}
          <div className="grid md:grid-cols-[2fr,1fr] gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Polymarket game slug</label>
              <input
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                value={slug}
                onChange={(e) => setSlug(e.target.value)}
                placeholder="nfl-buf-hou-2025-11-20"
              />
              <p className="text-[11px] text-slate-500 mt-1">Copy the part after <code>/event/</code>.</p>
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Side</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSide("home_yes")}
                  className={`rounded-md px-3 py-2 text-sm border ${
                    side === "home_yes" ? "border-sky-500 bg-sky-500/20" : "border-slate-700 bg-slate-900"
                  }`}
                >
                  Home (YES)
                </button>
                <button
                  type="button"
                  onClick={() => setSide("home_no")}
                  className={`rounded-md px-3 py-2 text-sm border ${
                    side === "home_no" ? "border-red-500 bg-red-500/20" : "border-slate-700 bg-slate-900"
                  }`}
                >
                  Away (NO)
                </button>
              </div>
            </div>
          </div>

          {/* Game State */}
          <div className="grid md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Quarter (1–4)</label>
                <input
                  type="number"
                  min={1}
                  max={4}
                  className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                  value={quarter}
                  onChange={(e) => setQuarter(Number(e.target.value) || 1)}
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Clock (MM:SS)</label>
                <input
                  className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                  value={clock}
                  onChange={(e) => setClock(e.target.value)}
                />
              </div>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Home score</label>
                  <input
                    type="number"
                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                    value={homeScore}
                    onChange={(e) => setHomeScore(Number(e.target.value) || 0)}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Away score</label>
                  <input
                    type="number"
                    className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                    value={awayScore}
                    onChange={(e) => setAwayScore(Number(e.target.value) || 0)}
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Possession</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setHomeHasBall(true)}
                    className={`rounded-md px-3 py-2 text-sm border ${
                      homeHasBall ? "border-sky-500 bg-sky-500/20" : "border-slate-700 bg-slate-900"
                    }`}
                  >
                    Home has ball
                  </button>

                  <button
                    type="button"
                    onClick={() => setHomeHasBall(false)}
                    className={`rounded-md px-3 py-2 text-sm border ${
                      !homeHasBall ? "border-sky-500 bg-sky-500/20" : "border-slate-700 bg-slate-900"
                    }`}
                  >
                    Away has ball
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Field */}
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Yardline (0–100)</label>
              <input
                type="number"
                min={0}
                max={100}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                value={yardline100}
                onChange={(e) => setYardline100(Number(e.target.value) || 0)}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Down (1–4)</label>
              <input
                type="number"
                min={1}
                max={4}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                value={down}
                onChange={(e) => setDown(Number(e.target.value) || 1)}
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Yards to go</label>
              <input
                type="number"
                min={1}
                className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
                value={ydstogo}
                onChange={(e) => setYdstogo(Number(e.target.value) || 1)}
              />
            </div>
          </div>

          {/* Fees */}
          <div className="max-w-xs">
            <label className="block text-xs font-medium text-slate-300 mb-1">Fee per contract</label>
            <input
              type="number"
              step="0.001"
              min={0}
              className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
              value={feeCost}
              onChange={(e) => setFeeCost(Number(e.target.value) || 0)}
            />
          </div>

          {/* Submit */}
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={loading}
              className="rounded-md bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 hover:bg-sky-400 disabled:opacity-60"
            >
              {loading ? "Computing EV..." : "Compute EV"}
            </button>

            {error && <span className="text-xs text-red-400">Error: {error}</span>}
          </div>
        </form>

        {/* Result */}
        {result && (
          <div className="mt-8 rounded-xl border border-slate-800 bg-slate-900/80 p-4 md:p-5">
            <h2 className="text-lg font-semibold mb-3">Result</h2>

            <div className="grid md:grid-cols-3 gap-4 text-sm">
              {/* Model */}
              <div>
                <div className="text-xs text-slate-400">Model win prob</div>
                <div className="text-base font-medium">
                  {(result.p_model * 100).toFixed(2)}%
                </div>
              </div>

              {/* Market */}
              <div>
                <div className="text-xs text-slate-400">Market price</div>
                <div className="text-base font-medium">
                  {(result.market_price * 100).toFixed(2)}¢
                </div>
                <div className="text-[11px] text-slate-500">
                  Fair price: {(result.fair_price * 100).toFixed(2)}¢
                </div>
              </div>

              {/* EV */}
              <div>
                <div className="text-xs text-slate-400">EV after fees</div>
                <div
                  className={`text-base font-semibold ${
                    result.ev_per_contract >= 0 ? "text-emerald-400" : "text-red-400"
                  }`}
                >
                  {(result.ev_per_contract * 100).toFixed(2)}¢ per contract
                </div>
                <div className="text-[11px] text-slate-500">
                  Edge (raw): {(result.edge_raw * 100).toFixed(2)}¢
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
