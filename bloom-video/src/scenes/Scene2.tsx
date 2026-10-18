import { interpolate, useCurrentFrame } from "remotion";
import { enter, progress } from "../components/anim";
import { SceneFrame } from "../components/SceneFrame";
import { COLORS, FONT, LAYOUT, S2, TEXT, VIDEO, holdFrames, sceneFrames, sec } from "../data";

/** SOFC 비유: 충전재를 갈아 끼우는 건전지 → 가스 넣으면 전기 */
export const Scene2: React.FC = () => {
  const frame = useCurrentFrame();
  const cx = VIDEO.width / 2;
  const left = cx - S2.bodyWidth / 2;
  const right = cx + S2.bodyWidth / 2;
  const top = S2.centerY - S2.bodyHeight / 2;
  const inner = {
    x: left + S2.inset,
    y: top + S2.inset,
    w: S2.bodyWidth - S2.inset * 2,
    h: S2.bodyHeight - S2.inset * 2,
  };
  const stroke = { fill: "none", strokeWidth: LAYOUT.iconStroke, strokeLinecap: "round", strokeLinejoin: "round" } as const;

  // 단계 2: 기존 충전재 비우기 → 새 카트리지가 왼쪽에서 밀려 들어옴
  const oldFill = 1 - progress(frame, S2.drain, S2.drainSec);
  const slide = progress(frame, S2.cartridge, S2.cartridgeSec);
  const text1 = enter(frame, S2.text1);
  const text1Opacity = text1.opacity * (1 - progress(frame, S2.text1Out));

  // 단계 3: 가스 입자 흐름 + 번개 깜빡임
  const flowStart = sec(S2.flow);
  const flowOn = progress(frame, S2.flow);
  const every = sec(S2.dotEverySec);
  const travel = sec(S2.dotTravelSec);
  const dots: { x: number; o: number }[] = [];
  if (frame >= flowStart) {
    const t = frame - flowStart;
    for (let k = Math.floor((t - travel) / every); k <= Math.floor(t / every); k++) {
      if (k < 0) continue;
      const p = (t - k * every) / travel;
      if (p < 0 || p > 1) continue;
      dots.push({
        x: interpolate(p, [0, 1], [S2.gasStartX, left]),
        o: interpolate(p, [0, 0.15, 0.8, 1], [0, 1, 1, 0]),
      });
    }
  }
  const blinkFrames = sec(S2.blinkSec);
  const blinkPhase = ((frame - flowStart) % blinkFrames) / blinkFrames;
  const held = frame >= sceneFrames[1] - holdFrames; // 정지 구간은 번개를 완전히 켠 상태로
  const blink = held ? 1 : frame < flowStart ? 0 : interpolate(Math.sin(blinkPhase * Math.PI * 2), [-1, 1], [S2.blinkMin, 1]);
  const boltX = right + S2.capWidth + S2.boltGap;
  const b = S2.boltSize / 2;
  const bolt = `M ${boltX + b * 0.15} ${S2.centerY - b} L ${boltX - b * 0.45} ${S2.centerY + b * 0.1} L ${boltX + b * 0.05} ${S2.centerY + b * 0.1} L ${boltX - b * 0.15} ${S2.centerY + b} L ${boltX + b * 0.45} ${S2.centerY - b * 0.1} L ${boltX - b * 0.05} ${S2.centerY - b * 0.1} Z`;

  const label: React.CSSProperties = {
    position: "absolute",
    top: S2.centerY + S2.labelGap,
    width: 0,
    display: "flex",
    justifyContent: "center",
    whiteSpace: "nowrap",
    fontSize: FONT.sizeBody,
    color: COLORS.sub,
    opacity: flowOn,
  };
  const headline: React.CSSProperties = {
    position: "absolute",
    top: S2.textTop,
    width: "100%",
    textAlign: "center",
    fontSize: FONT.sizeLarge,
    fontWeight: FONT.bold,
  };

  return (
    <SceneFrame index={1}>
      <div
        style={{
          position: "absolute",
          top: S2.noteTop,
          right: LAYOUT.margin,
          fontSize: FONT.sizeNote,
          color: COLORS.sub,
        }}
      >
        {TEXT.analogyNote}
      </div>

      <div style={{ ...headline, ...text1, opacity: text1Opacity }}>{TEXT.scene2.step1}</div>
      <div style={{ ...headline, ...enter(frame, S2.text2) }}>{TEXT.scene2.step2}</div>

      <svg width={VIDEO.width} height={VIDEO.height} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <clipPath id="battery-inner">
            <rect x={inner.x} y={inner.y} width={inner.w} height={inner.h} rx={S2.fillRadius} />
          </clipPath>
        </defs>
        <g style={enter(frame, S2.battery)}>
          <rect
            x={left}
            y={top}
            width={S2.bodyWidth}
            height={S2.bodyHeight}
            rx={S2.bodyRadius}
            stroke={COLORS.text}
            {...stroke}
          />
          <rect
            x={right}
            y={S2.centerY - S2.capHeight / 2}
            width={S2.capWidth}
            height={S2.capHeight}
            rx={S2.capWidth / 3}
            stroke={COLORS.text}
            {...stroke}
          />
          <g clipPath="url(#battery-inner)">
            <rect x={inner.x} y={inner.y} width={inner.w} height={inner.h} fill={COLORS.accent} opacity={oldFill} />
            <rect
              x={inner.x - inner.w * (1 - slide)}
              y={inner.y}
              width={inner.w}
              height={inner.h}
              fill={COLORS.accent}
              opacity={slide > 0 ? 1 : 0}
            />
          </g>
        </g>

        {dots.map((d, i) => (
          <circle key={i} cx={d.x} cy={S2.centerY} r={S2.dotRadius} fill={COLORS.sub} opacity={d.o} />
        ))}
        <path d={bolt} stroke={COLORS.accent} {...stroke} opacity={flowOn * blink} />
      </svg>

      <div style={{ ...label, left: (S2.gasStartX + left) / 2 }}>{TEXT.scene2.gas}</div>
      <div style={{ ...label, left: boltX }}>{TEXT.scene2.power}</div>
    </SceneFrame>
  );
};
