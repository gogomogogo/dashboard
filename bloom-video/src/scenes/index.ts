import { Scene1 } from "./Scene1";
import { Scene2 } from "./Scene2";
import { Scene3 } from "./Scene3";
import { Scene4 } from "./Scene4";
import { Scene5 } from "./Scene5";
import { Scene6 } from "./Scene6";
import { Scene7 } from "./Scene7";

/** 순서 = DATA.sceneDurationsSec 순서 */
export const SCENES = [Scene1, Scene2, Scene3, Scene4, Scene5, Scene6, Scene7].map((component, i) => ({
  id: `Scene${i + 1}`,
  component,
}));
