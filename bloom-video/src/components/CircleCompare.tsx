import { useCurrentFrame } from "remotion";
import { CIRCLES, COLORS, FONT, LAYOUT, TEXT, VIDEO } from "../data";
import { enter, progress } from "./anim";
import { CountUp } from "./CountUp";
import { Logo } from "./Logo";

type Props = {
  label: string;
  bloomValue: number;
  unit: string;
  valueDecimals: number;
  ratio: number; // 블룸 / 오라클
  /** 시작 시 블룸 원의 비율 (0 = 없음, 이전 장면 비율 = 모핑) */
  ratioFrom: number;
  /** 오라클 원 등장 시각. null 이면 처음부터 표시 (이전 장면에서 이어짐) */
  oracleSec: number | null;
  labelSec: number;
  bloomSec: number;
  bloomDurSec: number;
  valueSec: number;
  ratioSec: number;
  note?: string;
  noteSec?: number;
};

const radiusOf = (ratio: number) => CIRCLES.oracleRadius * Math.sqrt(ratio); // 면적 비례

/** 가로 중심 x 에 내용을 가운데 정렬로 놓는다. */
const CenterAt: React.FC<{ x: number; style: React.CSSProperties; children: React.ReactNode }> = ({
  x,
  style,
  children,
}) => (
  <div
    style={{
      position: "absolute",
      left: x,
      width: 0,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      whiteSpace: "nowrap",
      ...style,
    }}
  >
    {children}
  </div>
);

export const CircleCompare: React.FC<Props> = (p) => {
  const frame = useCurrentFrame();
  const R = CIRCLES.oracleRadius;
  const base = CIRCLES.baselineY;
  const oracleStyle = p.oracleSec === null ? {} : enter(frame, p.oracleSec);

  const grow = progress(frame, p.bloomSec, p.bloomDurSec);
  const rNow = radiusOf(p.ratioFrom + (p.ratio - p.ratioFrom) * grow);
  const rEnd = radiusOf(p.ratio);
  const bloomLogoStyle = p.ratioFrom > 0 ? {} : { opacity: progress(frame, p.bloomSec) };

  return (
    <>
      <CenterAt x={VIDEO.width / 2} style={{ top: CIRCLES.labelTop, ...enter(frame, p.labelSec) }}>
        <div style={{ fontSize: FONT.sizeBody, color: COLORS.sub }}>{p.label}</div>
      </CenterAt>

      {/* 오라클 */}
      <div style={{ position: "absolute", inset: 0, ...oracleStyle }}>
        <div
          style={{
            position: "absolute",
            left: CIRCLES.oracleCenterX - R,
            top: base - 2 * R,
            width: 2 * R,
            height: 2 * R,
            borderRadius: "50%",
            boxSizing: "border-box",
            backgroundColor: COLORS.compareFill,
            border: `${LAYOUT.iconStroke}px solid ${COLORS.compareLine}`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: FONT.sizeLarge,
            fontWeight: FONT.bold,
            gap: "0.3em",
          }}
        >
          <span style={{ fontVariantNumeric: "tabular-nums" }}>{TEXT.oracleUnit}</span>
          <span style={{ color: COLORS.sub, fontWeight: FONT.regular }}>{TEXT.oracle}</span>
        </div>
        <CenterAt x={CIRCLES.oracleCenterX} style={{ top: base + CIRCLES.logoGap }}>
          <Logo name="oracle" height={CIRCLES.logoHeight} />
        </CenterAt>
      </div>

      {/* 블룸에너지 */}
      <div
        style={{
          position: "absolute",
          left: CIRCLES.bloomCenterX - rNow,
          top: base - 2 * rNow,
          width: 2 * rNow,
          height: 2 * rNow,
          borderRadius: "50%",
          backgroundColor: COLORS.accent,
        }}
      />
      <CenterAt x={CIRCLES.bloomCenterX} style={{ top: base + CIRCLES.logoGap, ...bloomLogoStyle }}>
        <Logo name="bloom" height={CIRCLES.logoHeight} />
      </CenterAt>

      <CenterAt
        x={CIRCLES.bloomCenterX}
        style={{ bottom: VIDEO.height - (base - 2 * rEnd - CIRCLES.valueGap), justifyContent: "flex-end" }}
      >
        <div
          style={{
            fontSize: FONT.sizeHero,
            fontWeight: FONT.bold,
            lineHeight: 1,
            color: COLORS.accent,
            ...enter(frame, p.valueSec),
          }}
        >
          <CountUp value={p.bloomValue} decimals={p.valueDecimals} startSec={p.valueSec} prefix="$" suffix={p.unit} />
        </div>
        <div style={{ fontSize: FONT.sizeLarge, fontWeight: FONT.bold, marginTop: FONT.sizeNote, ...enter(frame, p.ratioSec) }}>
          <span style={{ fontVariantNumeric: "tabular-nums" }}>= {p.ratio.toFixed(CIRCLES.ratioDecimals)}</span>{" "}
          <span style={{ color: COLORS.sub, fontWeight: FONT.regular }}>{TEXT.oracle}</span>
        </div>
        {p.note && p.noteSec !== undefined ? (
          <div style={{ fontSize: FONT.sizeBody, color: COLORS.sub, marginTop: FONT.sizeAsOf, ...enter(frame, p.noteSec) }}>
            {p.note}
          </div>
        ) : null}
      </CenterAt>
    </>
  );
};
