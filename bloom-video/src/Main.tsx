import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { Fragment } from "react";
import { sceneFrames, transitionFrames } from "./data";
import { SCENES } from "./scenes";

/** 전체 영상: 장면 사이 0.3초 크로스페이드 */
export const Main: React.FC = () => (
  <TransitionSeries>
    {SCENES.map((s, i) => (
      <Fragment key={s.id}>
        {i > 0 ? (
          <TransitionSeries.Transition
            presentation={fade()}
            timing={linearTiming({ durationInFrames: transitionFrames })}
          />
        ) : null}
        <TransitionSeries.Sequence name={s.id} durationInFrames={sceneFrames[i]}>
          <s.component />
        </TransitionSeries.Sequence>
      </Fragment>
    ))}
  </TransitionSeries>
);
