import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";
import { FONT } from "../data";

export const fontsReady = Promise.all([
  loadFont({
    family: FONT.family,
    url: staticFile("fonts/Pretendard-Regular.woff2"),
    weight: String(FONT.regular),
  }),
  loadFont({
    family: FONT.family,
    url: staticFile("fonts/Pretendard-Bold.woff2"),
    weight: String(FONT.bold),
  }),
]);
