import { CircleCompare } from "../components/CircleCompare";
import { SceneFrame } from "../components/SceneFrame";
import { CIRCLES, DATA, TEXT, ratios } from "../data";

/** 매출 = 0.03 오라클. Scene4 레이아웃을 공유하고, 블룸 원이 시총 크기에서 매출 크기로 줄어든다. */
export const Scene5: React.FC = () => {
  const t = CIRCLES.s5;
  return (
    <SceneFrame>
      <CircleCompare
        label={TEXT.scene5.label}
        bloomValue={DATA.revenue.bloom}
        unit={DATA.revenue.unit}
        valueDecimals={CIRCLES.s5ValueDecimals}
        ratio={ratios.revenue}
        ratioFrom={ratios.marketCap}
        oracleSec={null}
        labelSec={t.label}
        bloomSec={t.bloomShrink}
        bloomDurSec={t.bloomShrinkSec}
        valueSec={t.value}
        ratioSec={t.ratio}
        note={TEXT.scene5.note(Math.round(ratios.revenue * 100))}
        noteSec={t.note}
      />
    </SceneFrame>
  );
};
