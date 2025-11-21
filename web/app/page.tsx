"use client";

import { useState, useEffect, FormEvent } from "react";

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

// Compute total game seconds remaining, given quarter + MM:SS in that quarter.
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

// Parse a slug like "nfl-buf-hou-2025-11-20" into two team codes
// (BUF, HOU). This is just for labeling; the backend still only uses the slug string.
function parseTeamsFromSlug(slug: string): { team1: string; team2: string } {
  const parts = slug.split("-");
  let team1 = "TEAM1";
  let team2 = "TEAM2";

  const nflIdx = parts.findIndex((p) => p.toLowerCase() === "nfl");
  if (nflIdx !== -1 && parts.length >= nflIdx + 3) {
    team1 = parts[nflIdx + 1]?.toUpperCase() ?? team1;
    team2 = parts[nflIdx + 2]?.toUpperCase() ?? team2;
  } else if (parts.length >= 3) {
    team1 = parts[1]?.toUpperCase() ?? team1;
    team2 = parts[2]?.toUpperCase() ?? team2;
  }

  return { team1, team2 };
}

// Parse a label like "HOU 36" or "BUF 12" into yardline_100 from the HOME endzone.
// Convention: HOME endzone = 0, AWAY endzone = 100.
// If label is "<HOME> Y", then yardline_100 = Y.
// If label is "<AWAY> Y", then yardline_100 = 100 - Y.
//
// Example: home=HOU, away=BUF
//  - "HOU 36" => 36
//  - "BUF 12" => 88
function parseYardlineLabel(
  label: string,
  homeTeam: string,
  awayTeam: string
): number | null {
  const trimmed = label.trim();
  if (!trimmed) return null;

  const parts = trimmed.split(/\s+/);
  if (parts.length !== 2) return null;

  const team = parts[0].toUpperCase();
  const y = Number(parts[1]);
  if (Number.isNaN(y)) return null;

  if (team === homeTeam.toUpperCase()) {
    // Clamp to realistic range, but still allow weird values
    return Math.min(100, Math.max(0, y));
  }
  if (team === awayTeam.toUpperCase()) {
    return Math.min(100, Math.max(0, 100 - y));
  }
  // Team code doesn't match either side
  return null;
}

export default function EVPage() {
  // Core inputs
  const [slug, setSlug] = useState("nfl-buf-hou-2025-11-20");
  const [side, setSide] = useState<Side>("home_yes");

  // Allow clearing numeric inputs: 'number | ""'
  const [quarter, setQuarter] = useState<number | "">(1);
  const [clock, setClock] = useState("15:00");

  const [homeScore, setHomeScore] = useState<number | "">(0);
  const [awayScore, setAwayScore] = useState<number | "">(0);
  const [homeHasBall, setHomeHasBall] = useState(true);

  // Yardline entered as "HOU 36" / "BUF 12"
  const [yardlineLabel, setYardlineLabel] = useState("HOU 25");

  const [down, setDown] = useState<number | "">(1);
  const [ydstogo, setYdstogo] = useState<number | "">(10);

  const [feeCost, setFeeCost] = useState<number | "">(0.01);

  // Network + result state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<EVResponse | null>(null);

  // Teams derived from slug, used only for labeling
  const [{ team1, team2 }, setSlugTeams] = useState<{
    team1: string;
    team2: string;
  }>({
    team1: "TEAM1",
    team2: "TEAM2",
  });

  // User-selected "true" home/away (in case slug order is not home-away)
  const [homeTeam, setHomeTeam] = useState("TEAM1");
  const [awayTeam, setAwayTeam] = useState("TEAM2");

  // Yardline parsing error specifically
  const [yardlineError, setYardlineError] = useState<string | null>(null);

  // Re-parse teams whenever slug changes, and reset selection
  useEffect(() => {
    const parsed = parseTeamsFromSlug(slug);
    setSlugTeams(parsed);
    setHomeTeam(parsed.team1);
    setAwayTeam(parsed.team2);

    // Also reset yardline label to something consistent
    setYardlineLabel(`${parsed.team1} 25`);
  }, [slug]);

  function parseOrDefault(value: number | "", fallback: number): number {
    return typeof value === "number" && !Number.isNaN(value) ? value : fallback;
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setResult(null);
    setYardlineError(null);
    setLoading(true);

    try {
      const q = Math.min(4, Math.max(1, parseOrDefault(quarter, 1)));
      const hs = parseOrDefault(homeScore, 0);
      const as = parseOrDefault(awayScore, 0);
      const d = Math.min(4, Math.max(1, parseOrDefault(down, 1)));
      const ytg = Math.max(1, parseOrDefault(ydstogo, 10));
      const fee = Math.max(0, parseOrDefault(feeCost, 0));

      const seconds_remaining = computeSecondsRemaining(q, clock);
      const score_diff_home = hs - as;

      // Convert "HOU 36" / "BUF 12" into yardline_100
      const ylParsed = parseYardlineLabel(yardlineLabel, homeTeam, awayTeam);
      if (ylParsed === null) {
        setYardlineError(
          `Yardline must look like "${homeTeam} 36" or "${awayTeam} 12" and use one of the two team codes.`
        );
        throw new Error("Invalid yardline format");
      }

      const payload = {
        slug,
        side,
        fee_cost: fee,
        state: {
          quarter: q,
          seconds_remaining,
          home_score: hs,
          away_score: as,
          score_diff_home,
          home_has_ball: homeHasBall ? 1 : 0,
          yardline_100: ylParsed,
          down: d,
          ydstogo: ytg,
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
      // If yardlineError is already set, keep that, otherwise show generic
      if (!yardlineError) {
        setError(err.message || "Unknown error");
      }
    } finally {
      setLoading(false);
    }
  }

  const isHomeYes = side === "home_yes";

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-3xl rounded-2xl border border-slate-800 bg-slate-900/70 shadow-xl p-6 md:p-8 space-y-6">
        {/* Header */}
        <header className="space-y-1">
          <h1 className="text-2xl md:text-3xl font-semibold">
            NFL Polymarket EV Tool
          </h1>
          <p className="text-sm text-slate-400">
            The model always predicts the probability that the{" "}
            <span className="font-semibold">home team</span> (
            <span className="font-semibold">{homeTeam}</span>) wins. Your bet
            can be either YES or NO on that home team.
          </p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Slug + Side + Home team selection */}
          <section className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-3">
            <div className="grid md:grid-cols-[2fr,1.4fr] gap-4 items-start">
              {/* Slug */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Polymarket game slug
                </label>
                <input
                  className="w-full rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-500"
                  value={slug}
                  onChange={(e) => setSlug(e.target.value)}
                  placeholder="nfl-buf-hou-2025-11-20"
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  Paste the part after <code>/event/</code>, for example:{" "}
                  <code>nfl-buf-hou-2025-11-20</code>.
                </p>
              </div>

              {/* Side selector */}
              <div className="space-y-2">
                <span className="block text-xs font-medium text-slate-300">
                  Bet side (relative to the home team)
                </span>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setSide("home_yes")}
                    className={`rounded-md px-3 py-2 text-xs md:text-sm border text-left ${
                      side === "home_yes"
                        ? "border-sky-500 bg-sky-500/20"
                        : "border-slate-700 bg-slate-950/80"
                    }`}
                  >
                    YES – {homeTeam} wins the game
                  </button>
                  <button
                    type="button"
                    onClick={() => setSide("home_no")}
                    className={`rounded-md px-3 py-2 text-xs md:text-sm border text-left ${
                      side === "home_no"
                        ? "border-red-500 bg-red-500/20"
                        : "border-slate-700 bg-slate-950/80"
                    }`}
                  >
                    NO – {homeTeam} does not win ({awayTeam} or tie)
                  </button>
                </div>
                <p className="text-[11px] text-slate-500">
                  This is purely about the home team result. The backend still
                  fetches the Polymarket moneyline for this game slug.
                </p>
              </div>
            </div>

            {/* Home team selection based on slug */}
            <div className="mt-3 rounded-lg border border-slate-800 bg-slate-950/70 p-3 space-y-2 text-xs">
              <div className="text-slate-400 mb-1">Who is actually home?</div>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setHomeTeam(team1);
                    setAwayTeam(team2);
                    setYardlineLabel(`${team1} 25`);
                  }}
                  className={`rounded-md px-3 py-2 border text-left ${
                    homeTeam === team1
                      ? "border-sky-500 bg-sky-500/20"
                      : "border-slate-700 bg-slate-950/80"
                  }`}
                >
                  {team1} is home, {team2} is away
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setHomeTeam(team2);
                    setAwayTeam(team1);
                    setYardlineLabel(`${team2} 25`);
                  }}
                  className={`rounded-md px-3 py-2 border text-left ${
                    homeTeam === team2
                      ? "border-sky-500 bg-sky-500/20"
                      : "border-slate-700 bg-slate-950/80"
                  }`}
                >
                  {team2} is home, {team1} is away
                </button>
              </div>
              <p className="text-[11px] text-slate-500 mt-1">
                Double-check this against Polymarket / ESPN. The model’s “home
                win probability” is for the team you mark as home here.
              </p>
            </div>

            <div className="flex items-center justify-between text-xs text-slate-400 border-t border-slate-800 pt-3">
              <span>
                Game:{" "}
                <span className="font-semibold text-slate-100">
                  {awayTeam} (away) @ {homeTeam} (home)
                </span>
              </span>
              <span className="hidden sm:inline">
                Model target: P({homeTeam} wins).
              </span>
            </div>
          </section>

          {/* Game state + scoreboard */}
          <section className="grid md:grid-cols-2 gap-4">
            {/* Left: time + scores */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-4">
              <h2 className="text-sm font-semibold text-slate-200">
                Game state
              </h2>

              {/* Quarter + clock */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Quarter (1–4)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={4}
                    className="w-full rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-500"
                    value={quarter}
                    onChange={(e) => {
                      const v = e.target.value;
                      if (v === "") return setQuarter("");
                      const n = Number(v);
                      if (!Number.isNaN(n)) setQuarter(n);
                    }}
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Clock (MM:SS remaining in quarter)
                  </label>
                  <input
                    className="w-full rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-500"
                    value={clock}
                    onChange={(e) => setClock(e.target.value)}
                    placeholder="15:00"
                  />
                </div>
              </div>

              {/* Scoreboard */}
              <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-3 space-y-2 text-xs">
                <div className="flex justify-between items-center">
                  <span className="text-slate-400">Scoreboard</span>
                  <span className="text-slate-500">
                    Away: {awayTeam} — Home: {homeTeam}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-3 mt-1">
                  <div>
                    <label className="block text-[11px] font-medium text-slate-300 mb-1">
                      Away score ({awayTeam})
                    </label>
                    <input
                      type="number"
                      className="w-full rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-500"
                      value={awayScore}
                      onChange={(e) => {
                        const v = e.target.value;
                        if (v === "") return setAwayScore("");
                        const n = Number(v);
                        if (!Number.isNaN(n)) setAwayScore(n);
                      }}
                    />
                  </div>

                  <div>
                    <label className="block text-[11px] font-medium text-slate-300 mb-1">
                      Home score ({homeTeam})
                    </label>
                    <input
                      type="number"
                      className="w-full rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-500"
                      value={homeScore}
                      onChange={(e) => {
                        const v = e.target.value;
                        if (v === "") return setHomeScore("");
                        const n = Number(v);
                        if (!Number.isNaN(n)) setHomeScore(n);
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Right: possession + field + fees */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-4 space-y-4">
              <h2 className="text-sm font-semibold text-slate-200">
                Field position & fees
              </h2>

              {/* Possession */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Possession
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setHomeHasBall(true)}
                    className={`rounded-md px-3 py-2 text-xs md:text-sm border ${
                      homeHasBall
                        ? "border-sky-500 bg-sky-500/20"
                        : "border-slate-700 bg-slate-950/80"
                    }`}
                  >
                    Home has ball ({homeTeam})
                  </button>

                  <button
                    type="button"
                    onClick={() => setHomeHasBall(false)}
                    className={`rounded-md px-3 py-2 text-xs md:text-sm border ${
                      !homeHasBall
                        ? "border-sky-500 bg-sky-500/20"
                        : "border-slate-700 bg-slate-950/80"
                    }`}
                  >
                    Away has ball ({awayTeam})
                  </button>
                </div>
              </div>

              {/* Yardline + down + distance */}
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">
                    Yardline (e.g. "{homeTeam} 36" or "{awayTeam} 12")
                  </label>
                  <input
                    className="w-full rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-500"
                    value={yardlineLabel}
                    onChange={(e) => setYardlineLabel(e.target.value)}
                    placeholder={`${homeTeam} 25`}
                  />
                  <p className="text-[11px] text-slate-500 mt-1">
                    Use the team whose name is on the yardline marker. The tool
                    converts this into distance from the{" "}
                    <span className="font-semibold">home</span> endzone.
                  </p>
                  {yardlineError && (
                    <p className="text-[11px] text-red-400 mt-1">
                      {yardlineError}
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Down (1–4)
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={4}
                      className="w-full rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-500"
                      value={down}
                      onChange={(e) => {
                        const v = e.target.value;
                        if (v === "") return setDown("");
                        const n = Number(v);
                        if (!Number.isNaN(n)) setDown(n);
                      }}
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Yards to go
                    </label>
                    <input
                      type="number"
                      min={1}
                      className="w-full rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-500"
                      value={ydstogo}
                      onChange={(e) => {
                        const v = e.target.value;
                        if (v === "") return setYdstogo("");
                        const n = Number(v);
                        if (!Number.isNaN(n)) setYdstogo(n);
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Fees */}
              <div className="max-w-xs">
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Fee per contract (in $)
                </label>
                <input
                  type="number"
                  step="0.001"
                  min={0}
                  className="w-full rounded-md border border-slate-700 bg-slate-950/80 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-sky-500"
                  value={feeCost}
                  onChange={(e) => {
                    const v = e.target.value;
                    if (v === "") return setFeeCost("");
                    const n = Number(v);
                    if (!Number.isNaN(n)) setFeeCost(n);
                  }}
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  Rough total fee per contract (exchange fees + gas, etc.).
                </p>
              </div>
            </div>
          </section>

          {/* Submit + error */}
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={loading}
              className="rounded-md bg-sky-500 px-4 py-2 text-sm font-medium text-slate-950 hover:bg-sky-400 disabled:opacity-60"
            >
              {loading ? "Computing EV..." : "Compute EV"}
            </button>

            {error && (
              <span className="text-xs text-red-400 max-w-sm truncate">
                Error: {error}
              </span>
            )}
          </div>
        </form>

        {/* Result card */}
        {result && (
          <section className="mt-2 rounded-xl border border-slate-800 bg-slate-900/80 p-4 md:p-5 space-y-3">
            <h2 className="text-lg font-semibold mb-1">Result</h2>

            <p className="text-xs text-slate-400">
              You are looking at EV for:{" "}
              <span className="font-semibold text-slate-100">
                {isHomeYes
                  ? `YES – ${homeTeam} wins`
                  : `NO – ${homeTeam} does not win (${awayTeam})`}
              </span>
              .
            </p>

            <div className="grid md:grid-cols-3 gap-4 text-sm mt-2">
              <div>
                <div className="text-xs text-slate-400">
                  Model win prob (home: {homeTeam})
                </div>
                <div className="text-base font-medium">
                  {(result.p_model * 100).toFixed(2)}%
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-400">Market price</div>
                <div className="text-base font-medium">
                  {(result.market_price * 100).toFixed(2)}¢
                </div>
                <div className="text-[11px] text-slate-500">
                  Fair price (model):{" "}
                  {(result.fair_price * 100).toFixed(2)}¢
                </div>
              </div>

              <div>
                <div className="text-xs text-slate-400">EV after fees</div>
                <div
                  className={`text-base font-semibold ${
                    result.ev_per_contract >= 0
                      ? "text-emerald-400"
                      : "text-red-400"
                  }`}
                >
                  {(result.ev_per_contract * 100).toFixed(2)}¢ per contract
                </div>
                <div className="text-[11px] text-slate-500">
                  Edge (raw, pre-fees):{" "}
                  {(result.edge_raw * 100).toFixed(2)}¢
                </div>
              </div>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}
