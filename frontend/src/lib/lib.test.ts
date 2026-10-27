import { describe, expect, it } from "vitest";
import { toCsv } from "./csv";
import { decisionTime, mw, pct, stamp } from "./format";
import { queryString } from "./api";

describe("format", () => {
  it("formats MW with sign and handles null", () => {
    expect(mw(1852.4, true)).toBe("+1,852");
    expect(mw(-3.2, true)).toBe("-3");
    expect(mw(null)).toBe("n/a");
  });
  it("formats percentages", () => {
    expect(pct(0.851)).toBe("85.1%");
    expect(pct(undefined)).toBe("n/a");
  });
  it("renders UTC stamps", () => {
    expect(stamp("2026-01-14T07:30:00+00:00")).toBe("14 Jan 07:30 UTC");
    expect(stamp(null)).toBe("n/a");
  });
  it("puts the decision on the day before delivery", () => {
    expect(decisionTime("2026-01-15", "09:00")).toBe("2026-01-14T09:00:00.000Z");
    expect(decisionTime("2026-01-01", "09:00")).toBe("2025-12-31T09:00:00.000Z");
  });
});

describe("csv", () => {
  it("writes a header, blanks for nulls, and one row per point", () => {
    const csv = toCsv([
      {
        startTime: "2026-01-02T00:00:00+00:00",
        actual: 100,
        forecast: null,
        publishTime: null,
        leadHours: null,
        error: null,
        persistence: 90,
      },
    ]);
    const [header, row] = csv.trim().split("\n");
    expect(header.split(",")).toHaveLength(7);
    expect(row).toBe("2026-01-02T00:00:00+00:00,100,,,,,90");
  });
});

describe("api", () => {
  it("builds the query string", () => {
    const q = queryString({
      from: "2026-01-01",
      to: "2026-01-31",
      mode: "day_ahead",
      gate: "09:00",
      h: 24,
    });
    expect(q).toContain("mode=day_ahead");
    expect(q).toContain("gate=09%3A00");
  });
});