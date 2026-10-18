import { Easing, interpolate } from "remotion";
import { VIDEO, sec } from "../data";

export const ease = Easing.out(Easing.cubic);

/** 0→1 진행률. start/duration 은 초 단위. */
export const progress = (frame: number, startSec: number, durSec = VIDEO.enterSec) =>
  interpolate(frame, [sec(startSec), sec(startSec) + Math.max(1, sec(durSec))], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });

/** 공통 등장: 페이드 + 짧은 이동 + 스케일(0.96→1). */
export const enter = (frame: number, startSec: number, durSec = VIDEO.enterSec) => {
  const p = progress(frame, startSec, durSec);
  return {
    opacity: p,
    translate: `0px ${(1 - p) * VIDEO.enterMovePx}px`,
    scale: String(VIDEO.enterScaleFrom + (1 - VIDEO.enterScaleFrom) * p),
  };
};
