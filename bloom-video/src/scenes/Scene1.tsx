import { interpolateColors, useCurrentFrame } from "remotion";
import { enter, progress } from "../components/anim";
import { Logo } from "../components/Logo";
import { SceneFrame } from "../components/SceneFrame";
import { COLORS, FONT, LAYOUT, S1, TEXT } from "../data";

/** 회사 정체: 로고 → SOFC → 설계·제조·판매·설치 전부 직접 */
export const Scene1: React.FC = () => {
  const frame = useCurrentFrame();
  const steps = TEXT.scene1.steps;
  const chipAt = (i: number) => S1.firstChip + i * S1.chipStagger;
  const hl = progress(frame, S1.highlight, S1.highlightSec);
  const chipLine = interpolateColors(hl, [0, 1], [COLORS.compareLine, COLORS.accent]);
  const row: React.CSSProperties = {
    position: "absolute",
    width: "100%",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  };

  return (
    <SceneFrame index={0}>
      <div style={{ ...row, top: S1.logoTop, opacity: progress(frame, S1.logo, S1.logoSec) }}>
        <Logo name="bloom" height={S1.logoHeight} />
      </div>

      <div style={{ ...row, top: S1.titleTop, gap: "0.4em", fontSize: FONT.sizeLarge, ...enter(frame, S1.title) }}>
        <span style={{ fontWeight: FONT.bold }}>{TEXT.scene1.title}</span>
        <span style={{ color: COLORS.sub }}>{TEXT.scene1.titleSub}</span>
      </div>

      <div style={{ ...row, top: S1.chipsTop }}>
        {steps.map((s, i) => (
          <div key={s} style={{ display: "flex", alignItems: "center" }}>
            {i > 0 ? (
              <svg
                width={S1.arrowLength}
                height={S1.arrowHead * 2 + LAYOUT.iconStroke * 2}
                style={{ opacity: progress(frame, chipAt(i)) }}
              >
                {(() => {
                  const y = S1.arrowHead + LAYOUT.iconStroke;
                  const x0 = S1.arrowHead;
                  const x1 = S1.arrowLength - S1.arrowHead;
                  return (
                    <path
                      d={`M ${x0} ${y} L ${x1} ${y} M ${x1 - S1.arrowHead} ${y - S1.arrowHead} L ${x1} ${y} L ${x1 - S1.arrowHead} ${y + S1.arrowHead}`}
                      fill="none"
                      stroke={COLORS.compareLine}
                      strokeWidth={LAYOUT.iconStroke}
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  );
                })()}
              </svg>
            ) : null}
            <div
              style={{
                padding: `${S1.chipPadY}px ${S1.chipPadX}px`,
                borderRadius: S1.chipRadius,
                border: `${LAYOUT.iconStroke}px solid ${chipLine}`,
                fontSize: FONT.sizeBody,
                fontWeight: FONT.bold,
                lineHeight: 1,
                ...enter(frame, chipAt(i)),
              }}
            >
              {s}
            </div>
          </div>
        ))}
      </div>
    </SceneFrame>
  );
};
