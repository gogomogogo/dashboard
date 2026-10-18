import { useCurrentFrame } from "remotion";
import { enter, progress } from "../components/anim";
import { CountUp } from "../components/CountUp";
import { SceneFrame } from "../components/SceneFrame";
import { COLORS, FONT, LAYOUT, S3, TEXT } from "../data";
import { first, gainPct, last, weekly } from "../price";

const minC = Math.min(...weekly.map((d) => d.close));
const maxC = Math.max(...weekly.map((d) => d.close));
const pts = weekly.map((d, i) => ({
  x: S3.left + (i / (weekly.length - 1)) * (S3.right - S3.left),
  y: S3.bottom - ((d.close - minC) / (maxC - minC)) * (S3.bottom - S3.top),
}));
const cum = pts.map(() => 0);
for (let i = 1; i < pts.length; i++) {
  cum[i] = cum[i - 1] + Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
}
const total = cum[cum.length - 1];
const linePath = pts.map((p, i) => `${i ? "L" : "M"} ${p.x} ${p.y}`).join(" ");
const areaPath = `${linePath} L ${S3.right} ${S3.bottom} L ${S3.left} ${S3.bottom} Z`;

/** 선 길이 비율 p 에 해당하는 x 좌표 (채움 영역을 선 끝까지만 보이게) */
const xAt = (p: number) => {
  const target = p * total;
  const i = Math.max(1, cum.findIndex((c) => c >= target));
  const seg = cum[i] - cum[i - 1] || 1;
  return pts[i - 1].x + ((target - cum[i - 1]) / seg) * (pts[i].x - pts[i - 1].x);
};

const fmtDate = (d: string) => d.slice(0, 7).replace("-", ".");
const money = (v: number) => `$${v.toFixed(S3.priceDecimals)}`;

/** 3년 주가: 선이 왼→오로 그려지고 끝점에 3년 상승률 */
export const Scene3: React.FC = () => {
  const frame = useCurrentFrame();
  const p = progress(frame, S3.draw, S3.drawSec);
  const done = S3.draw + S3.drawSec;
  const end = pts[pts.length - 1];

  return (
    <SceneFrame index={2}>
      <div style={{ position: "absolute", top: S3.heroTop, left: S3.left, ...enter(frame, done) }}>
        <div style={{ fontSize: FONT.sizeHero, fontWeight: FONT.bold, lineHeight: 1, color: COLORS.accent }}>
          <CountUp value={gainPct} decimals={S3.gainDecimals} startSec={done} prefix="+" suffix="%" />
        </div>
        <div style={{ fontSize: FONT.sizeBody, color: COLORS.sub, marginTop: FONT.sizeAsOf }}>{TEXT.scene3.gainLabel}</div>
      </div>

      <svg width="100%" height="100%" style={{ position: "absolute", inset: 0 }}>
        <defs>
          <clipPath id="price-reveal">
            <rect x={0} y={0} width={xAt(p)} height={S3.bottom + LAYOUT.iconStroke} />
          </clipPath>
        </defs>
        <path d={areaPath} fill={COLORS.accent} opacity={S3.areaOpacity} clipPath="url(#price-reveal)" />
        <path
          d={linePath}
          fill="none"
          stroke={COLORS.accent}
          strokeWidth={LAYOUT.iconStroke}
          strokeLinecap="round"
          strokeLinejoin="round"
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1 - p}
        />
        <circle cx={end.x} cy={end.y} r={S3.dotRadius} fill={COLORS.accent} opacity={progress(frame, done)} />
      </svg>

      <div
        style={{
          position: "absolute",
          left: S3.left,
          top: S3.bottom + S3.startLabelGap,
          fontSize: FONT.sizeSmall,
          color: COLORS.sub,
          fontVariantNumeric: "tabular-nums",
          ...enter(frame, S3.draw),
        }}
      >
        {fmtDate(first.date)} · {money(first.close)}
      </div>
      <div
        style={{
          position: "absolute",
          left: end.x + S3.endLabelGap,
          top: end.y,
          translate: `0 -50%`,
          fontSize: FONT.sizeMedium,
          fontWeight: FONT.bold,
          fontVariantNumeric: "tabular-nums",
          opacity: progress(frame, done),
        }}
      >
        {money(last.close)}
      </div>
    </SceneFrame>
  );
};
