import { interpolate, useCurrentFrame } from "remotion";
import { enter, progress } from "../components/anim";
import { CountUp } from "../components/CountUp";
import { SceneFrame } from "../components/SceneFrame";
import { BARS, COLORS, DATA, FONT, LAYOUT, TEXT, VIDEO } from "../data";

/** 매출 성장률: 연도별 막대 + "+37%" */
export const Scene6: React.FC = () => {
  const frame = useCurrentFrame();
  const hist = DATA.revenueHistory;
  const n = hist.length;
  const max = Math.max(...hist.map((d) => d.value));
  const cx = (i: number) => VIDEO.width / 2 + (i - (n - 1) / 2) * BARS.pitch;
  const heightOf = (v: number) => (v / max) * BARS.maxHeight;
  const barStart = (i: number) => BARS.firstBar + i * BARS.stagger;
  const barsDone = barStart(n - 1) + BARS.growSec;
  const arrowSec = barsDone + BARS.arrowDelay;
  const heroSec = barsDone + BARS.heroDelay;

  // 2024 → 2025 곡선 화살표
  const a = BARS.arrow;
  const top = (i: number) => BARS.baselineY - heightOf(hist[i].value);
  const sx = cx(n - 2);
  const sy = top(n - 2) - a.startLift;
  const ex = cx(n - 1) - a.endInset;
  const ey = top(n - 1) - a.endLift;
  const qx = (sx + ex) / 2;
  const qy = Math.min(sy, ey) - a.arc;
  const path = `M ${sx} ${sy} Q ${qx} ${qy} ${ex} ${ey}`;
  // 끝점 접선 방향으로 화살촉
  const ang = Math.atan2(ey - qy, ex - qx);
  const head = (d: number) =>
    `${ex - a.headSize * Math.cos(ang + d)} ${ey - a.headSize * Math.sin(ang + d)}`;
  const spread = Math.PI / 5;
  const arrowP = progress(frame, arrowSec, BARS.arrowSec);
  const headOpacity = interpolate(arrowP, [0.8, 1], [0, 1], { extrapolateLeft: "clamp" });

  return (
    <SceneFrame index={5}>
      {/* 상단: +37% (가장 큰 요소) + 보조 문구 */}
      <div
        style={{
          position: "absolute",
          top: BARS.heroTop,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div
          style={{
            fontSize: FONT.sizeHero,
            fontWeight: FONT.bold,
            lineHeight: 1,
            color: COLORS.accent,
            ...enter(frame, heroSec),
          }}
        >
          <CountUp value={DATA.revenueGrowth} startSec={heroSec} prefix="+" suffix="%" />
        </div>
        <div style={{ fontSize: FONT.sizeBody, color: COLORS.sub, marginTop: FONT.sizeNote, ...enter(frame, heroSec) }}>
          {TEXT.scene6.label}
        </div>
      </div>

      {/* 막대 */}
      {hist.map((d, i) => {
        const g = progress(frame, barStart(i), BARS.growSec);
        const h = heightOf(d.value) * g;
        const last = i === n - 1;
        const label: React.CSSProperties = {
          position: "absolute",
          left: cx(i) - BARS.pitch / 2,
          width: BARS.pitch,
          textAlign: "center",
          fontSize: FONT.sizeSmall,
          fontVariantNumeric: "tabular-nums",
          lineHeight: 1,
        };
        return (
          <div key={d.year}>
            <div
              style={{
                position: "absolute",
                left: cx(i) - BARS.barWidth / 2,
                top: BARS.baselineY - h,
                width: BARS.barWidth,
                height: h,
                backgroundColor: last ? COLORS.accent : COLORS.compareFill,
              }}
            />
            <div
              style={{
                ...label,
                top: BARS.baselineY - h - BARS.valueGap - FONT.sizeSmall,
                color: last ? COLORS.text : COLORS.sub,
                fontWeight: last ? FONT.bold : FONT.regular,
                opacity: g,
              }}
            >
              ${d.value.toFixed(BARS.valueDecimals)}
              {DATA.revenue.unit}
            </div>
            <div
              style={{
                ...label,
                top: BARS.baselineY + BARS.yearGap,
                color: last ? COLORS.text : COLORS.sub,
                fontWeight: last ? FONT.bold : FONT.regular,
                opacity: progress(frame, barStart(i)),
              }}
            >
              {d.year}
            </div>
          </div>
        );
      })}

      <svg width={VIDEO.width} height={VIDEO.height} style={{ position: "absolute", inset: 0 }}>
        <path
          d={path}
          fill="none"
          stroke={COLORS.accent}
          strokeWidth={LAYOUT.iconStroke}
          strokeLinecap="round"
          pathLength={1}
          strokeDasharray={1}
          strokeDashoffset={1 - arrowP}
        />
        <path
          d={`M ${head(-spread)} L ${ex} ${ey} L ${head(spread)}`}
          fill="none"
          stroke={COLORS.accent}
          strokeWidth={LAYOUT.iconStroke}
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={headOpacity}
        />
      </svg>
    </SceneFrame>
  );
};

