import { Composition } from "remotion";
import { KakaoOracle } from "./KakaoOracle";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="KakaoOracle"
      component={KakaoOracle}
      durationInFrames={16 * 30}
      fps={30}
      width={1920}
      height={1080}
    />
  );
};
