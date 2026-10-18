import { Composition, Folder } from "remotion";
import { fontsReady } from "./components/fonts";
import { VIDEO, mainFrames, sceneFrames } from "./data";
import { Main } from "./Main";
import { SCENES } from "./scenes";

void fontsReady;

const size = { width: VIDEO.width, height: VIDEO.height, fps: VIDEO.fps };

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Main" component={Main} durationInFrames={mainFrames} {...size} />
    <Folder name="Scenes">
      {SCENES.map((s, i) => (
        <Composition key={s.id} id={s.id} component={s.component} durationInFrames={sceneFrames[i]} {...size} />
      ))}
    </Folder>
  </>
);
