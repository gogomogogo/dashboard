import { AbsoluteFill, Freeze } from "remotion";
import { COLORS, DATA, FONT, LAYOUT, TEXT, VIDEO, holdFrames, sceneFrames } from "../data";

/** 모든 장면 공통: 단색 배경 + 우하단 "기준" 표기(자막 영역 위).
 *  마지막 VIDEO.holdSec 동안은 최종 상태로 정지한다. */
export const SceneFrame: React.FC<{ index: number; children: React.ReactNode }> = ({ index, children }) => {
  const holdStart = sceneFrames[index] - holdFrames;
  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        color: COLORS.text,
        fontFamily: FONT.family,
        fontWeight: FONT.regular,
      }}
    >
      <Freeze frame={holdStart} active={(f) => f >= holdStart}>
        {children}
      </Freeze>
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
};
