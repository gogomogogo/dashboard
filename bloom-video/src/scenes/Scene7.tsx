import { useCurrentFrame } from "remotion";
import { enter, progress } from "../components/anim";
import { SceneFrame } from "../components/SceneFrame";
import { COLORS, DATA, FONT, S7, TEXT, VIDEO } from "../data";

/** $B 값을 "$2.02B" / "$73M" / "-$88M" 형식으로 */
const money = (b: number) => {
  const sign = b < 0 ? "-" : "";
  const abs = Math.abs(b);
  return abs < S7.millionsBelow
    ? `${sign}$${Math.round(abs * 1000)}M`
    : `${sign}$${abs.toFixed(S7.billionDecimals)}${DATA.revenue.unit}`;
};

/** 이익은 미미: 매출 / 영업이익 / 순이익. 조용히 끝낸다. */
export const Scene7: React.FC = () => {
  const frame = useCurrentFrame();
  const values = [DATA.revenue.bloom, DATA.operatingIncome, DATA.netIncome];
  const dim = 1 - (1 - S7.dimOpacity) * progress(frame, S7.dim, S7.dimSec);

  return (
    <SceneFrame index={6}>
      {values.map((v, i) => {
        const main = i === 0;
        const e = enter(frame, S7.first + i * S7.stagger);
        return (
          <div
            key={TEXT.scene7.labels[i]}
            style={{
              position: "absolute",
              top: S7.valueTop,
              left: VIDEO.width / 2 + (i - 1) * S7.pitch,
              width: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              whiteSpace: "nowrap",
              ...e,
              opacity: e.opacity * (main ? 1 : dim),
            }}
          >
            <div style={{ fontSize: FONT.sizeBody, color: COLORS.sub }}>{TEXT.scene7.labels[i]}</div>
            <div
              style={{
                fontSize: FONT.sizeXL,
                fontWeight: FONT.bold,
                fontVariantNumeric: "tabular-nums",
                color: main ? COLORS.text : COLORS.sub,
                marginTop: FONT.sizeNote,
              }}
            >
              {money(v)}
            </div>
          </div>
        );
      })}
      <div
        style={{
          position: "absolute",
          top: S7.footnoteTop,
          width: "100%",
          textAlign: "center",
          fontSize: FONT.sizeSmall,
          color: COLORS.sub,
          ...enter(frame, S7.footnote),
        }}
      >
        {TEXT.scene7.footnote}
      </div>
    </SceneFrame>
  );
};
