import { CircleCompare } from "../components/CircleCompare";
import { SceneFrame } from "../components/SceneFrame";
import { CIRCLES, DATA, TEXT, ratios } from "../data";

/** 시가총액 = 0.2 오라클 */
export const Scene4: React.FC = () => {
  const t = CIRCLES.s4;
  return (
    <SceneFrame>
      <CircleCompare
        label={TEXT.scene4.label}
        bloomValue={DATA.marketCap.bloom}
        unit={DATA.marketCap.unit}
        valueDecimals={CIRCLES.s4ValueDecimals}
        ratio={ratios.marketCap}
        ratioFrom={0}
        oracleSec={t.oracle}
        labelSec={t.label}
        bloomSec={t.bloomGrow}
        bloomDurSec={t.bloomGrowSec}
        valueSec={t.value}
        ratioSec={t.ratio}
      />
    </SceneFrame>
  );
};
