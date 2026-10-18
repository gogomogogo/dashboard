import raw from "../data/price.csv";

export type PricePoint = { date: string; close: number };

const daily: PricePoint[] = raw
  .trim()
  .split(/\r?\n/)
  .slice(1)
  .map((line) => {
    const [date, close] = line.split(",");
    return { date, close: Number(close) };
  })
  .filter((d) => Number.isFinite(d.close))
  .sort((a, b) => a.date.localeCompare(b.date));

/** 주(월요일 시작) 단위로 묶어 각 주의 마지막 종가만 남긴다. */
const weekKey = (date: string) => {
  const d = new Date(`${date}T00:00:00Z`);
  const monday = new Date(d);
  monday.setUTCDate(d.getUTCDate() - ((d.getUTCDay() + 6) % 7));
  return monday.toISOString().slice(0, 10);
};

const byWeek = new Map<string, PricePoint>();
for (const p of daily) byWeek.set(weekKey(p.date), p);

export const weekly: PricePoint[] = [...byWeek.values()];
export const first = weekly[0];
export const last = weekly[weekly.length - 1];
export const gainPct = (last.close / first.close - 1) * 100;
