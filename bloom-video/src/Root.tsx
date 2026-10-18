import { Composition, Folder } from "remotion";
import { fontsReady } from "./components/fonts";
import { VIDEO, sceneFrames } from "./data";
import { Scene4 } from "./scenes/Scene4";
import { Scene5 } from "./scenes/Scene5";
import { Scene6 } from "./scenes/Scene6";

void fontsReady;

const SCENES = [
  { id: "Scene4", component: Scene4, index: 3 },
  { id: "Scene5", component: Scene5, index: 4 },
  { id: "Scene6", component: Scene6, index: 5 },
];

export const RemotionRoot: React.FC = () => (
  <Folder name="Scenes">
    {SCENES.map((s) => (
      <Composition
        key={s.id}
        id={s.id}
        component={s.component}
        width={VIDEO.width}
        height={VIDEO.height}
        fps={VIDEO.fps}
        durationInFrames={sceneFrames[s.index]}
      />
    ))}
  </Folder>
);
