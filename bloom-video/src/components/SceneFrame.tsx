import { AbsoluteFill } from "remotion";
import { COLORS, DATA, FONT, LAYOUT, TEXT, VIDEO } from "../data";

/** 모든 장면 공통: 단색 배경 + 우하단 "기준" 표기(자막 영역 위). */
export const SceneFrame: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <AbsoluteFill
    style={{
      backgroundColor: COLORS.bg,
      color: COLORS.text,
      fontFamily: FONT.family,
      fontWeight: FONT.regular,
    }}
  >
    {children}
    <div
      style={{
        position: "absolute",
        right: LAYOUT.margin,
        bottom: VIDEO.height * LAYOUT.subtitleZoneRatio + LAYOUT.asOfGap,
        fontSize: FONT.sizeAsOf,
        color: COLORS.sub,
        fontVariantNumeric: "tabular-nums",
      }}
    >
      {TEXT.asOfPrefix}
      {DATA.asOf}
    </div>
  </AbsoluteFill>
);
