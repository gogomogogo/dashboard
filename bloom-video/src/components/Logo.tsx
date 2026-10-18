import { Img, staticFile } from "remotion";

/** 배경 제거된 로고를 흰색 단색으로 표시 (CSS filter). */
export const Logo: React.FC<{ name: "bloom" | "oracle"; height: number; style?: React.CSSProperties }> = ({
  name,
  height,
  style,
}) => (
  <Img
    src={staticFile(`logos/${name}.png`)}
    style={{ height, width: "auto", filter: "brightness(0) invert(0.96)", ...style }}
  />
);
