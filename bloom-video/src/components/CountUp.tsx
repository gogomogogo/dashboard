import { useCurrentFrame } from "remotion";
import { VIDEO } from "../data";
import { progress } from "./anim";

type Props = {
  value: number;
  startSec: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  from?: number;
};

/** 숫자 카운트업. 길이 VIDEO.countUpSec, easeOutCubic. */
export const CountUp: React.FC<Props> = ({
  value,
  startSec,
  decimals = 0,
  prefix = "",
  suffix = "",
  from = 0,
}) => {
  const frame = useCurrentFrame();
  const p = progress(frame, startSec, VIDEO.countUpSec);
  const v = from + (value - from) * p;
  return (
    <span style={{ fontVariantNumeric: "tabular-nums" }}>
      {prefix}
      {v.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}
      {suffix}
    </span>
  );
};
