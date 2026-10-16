import { loadFont } from "@remotion/fonts";
import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

const fontFamily = "Pretendard";
loadFont({
  family: fontFamily,
  url: staticFile("fonts/PretendardVariable.woff2"),
  weight: "45 920",
});

// ─── 타이밍 (초 단위) ─ 녹음한 대사/효과음에 맞춰 여기 숫자만 바꾸면 됨 ───
const T = {
  screenOn: 0.5, // 화면 켜짐 (카톡! 효과음 위치)
  msg1: 0.75, // 원숭이: 야야 오라클이...
  msg2: 3.2, // 나: 잉?? 포스메져?
  msg3: 6.0, // 원숭이: ㅇㅇBE 납품... (두번째 카톡!)
  msg4: 9.0, // 나: 오키 한번 조사해봄 (이후 16초까지 정지 화면)
};

const KAKAO_BG = "#B2C7DA";
const KAKAO_YELLOW = "#FEE500";

const clamp = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

export const KakaoOracle: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = (sec: number) => Math.round(sec * fps);

  // 화면 켜짐: 검정 → 밝게 (살짝 과노출 후 안정)
  const screenOff = interpolate(
    frame,
    [s(T.screenOn), s(T.screenOn) + 7],
    [1, 0],
    clamp,
  );
  const screenFlash = interpolate(
    frame,
    [s(T.screenOn), s(T.screenOn) + 4, s(T.screenOn) + 16],
    [0, 0.55, 0],
    clamp,
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", fontFamily }}>
      {/* ── 채팅 화면 레이어 ── */}
      <AbsoluteFill>
        {/* 화면 빛 번짐 */}
        <AbsoluteFill
          style={{
            background:
              "radial-gradient(ellipse 520px 620px at 50% 50%, rgba(178,199,218,0.22), rgba(0,0,0,0) 70%)",
            opacity: 1 - screenOff,
          }}
        />
        <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
          <div
            style={{
              width: 540,
              height: 1000,
              borderRadius: 72,
              padding: 14,
              background: "linear-gradient(145deg, #2a2a2e, #0c0c0e 60%, #1c1c20)",
              boxShadow:
                "0 0 0 2px #3a3a40, 0 40px 120px rgba(0,0,0,0.8), inset 0 0 0 2px #050505",
              position: "relative",
            }}
          >
            <div
              style={{
                width: "100%",
                height: "100%",
                borderRadius: 58,
                overflow: "hidden",
                position: "relative",
                backgroundColor: KAKAO_BG,
              }}
            >
              <ChatScreen s={s} frame={frame} fps={fps} />
              {/* 화면 꺼짐/켜짐 */}
              <AbsoluteFill style={{ backgroundColor: "#000", opacity: screenOff }} />
              <AbsoluteFill style={{ backgroundColor: "#fff", opacity: screenFlash }} />
              {/* 유리 반사 */}
              <AbsoluteFill
                style={{
                  background:
                    "linear-gradient(115deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0) 35%)",
                }}
              />
            </div>
            {/* 다이나믹 아일랜드 */}
            <div
              style={{
                position: "absolute",
                top: 30,
                left: "50%",
                marginLeft: -60,
                width: 120,
                height: 34,
                borderRadius: 20,
                backgroundColor: "#000",
              }}
            />
          </div>
        </AbsoluteFill>
      </AbsoluteFill>

    </AbsoluteFill>
  );
};

// ───────────────────────── 카톡 화면 ─────────────────────────

const ChatScreen: React.FC<{
  s: (sec: number) => number;
  frame: number;
  fps: number;
}> = ({ s, frame, fps }) => {
  return (
    <AbsoluteFill style={{ flexDirection: "column" }}>
      {/* 상태바 */}
      <div
        style={{
          height: 64,
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          padding: "0 40px 8px 48px",
          fontSize: 20,
          fontWeight: 700,
          color: "#111",
        }}
      >
        <span>1:55</span>
        <span style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <SignalIcon />
          <BatteryIcon />
        </span>
      </div>
      {/* 채팅방 헤더 */}
      <div
        style={{
          height: 64,
          display: "flex",
          alignItems: "center",
          padding: "0 22px",
          color: "#111",
        }}
      >
        <span style={{ fontSize: 40, fontWeight: 400, lineHeight: 1, marginTop: -6 }}>‹</span>
        <span style={{ fontSize: 26, fontWeight: 700, marginLeft: 14 }}>원숭이</span>
        <span style={{ flex: 1 }} />
        <SearchIcon />
        <span style={{ width: 22 }} />
        <MenuIcon />
      </div>

      {/* 메시지 영역 */}
      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          gap: 18,
          padding: "24px 20px 0 20px",
        }}
      >
        <Message
          side="left"
          name="원숭이"
          time="오후 1:54"
          appear={s(T.msg1)}
          frame={frame}
          fps={fps}
          showProfile
        >
          야야 오라클이 데센 포스메져 선언했다함.
        </Message>
        <Message
          side="right"
          time="오후 1:54"
          appear={s(T.msg2)}
          readAt={s(T.msg3) - 12}
          frame={frame}
          fps={fps}
        >
          잉?? 포스메져? 갑자기?
        </Message>
        <Message
          side="left"
          name="원숭이"
          time="오후 1:55"
          appear={s(T.msg3)}
          frame={frame}
          fps={fps}
          showProfile
        >
          ㅇㅇBE 납품 사이트라는 데 조진거 아님???
        </Message>
        <Message
          side="right"
          time="오후 1:55"
          appear={s(T.msg4)}
          frame={frame}
          fps={fps}
        >
          오키 한번 조사해봄
        </Message>
      </div>

      {/* 입력창 */}
      <div
        style={{
          height: 104,
          backgroundColor: "#fff",
          display: "flex",
          alignItems: "flex-start",
          padding: "16px 18px 0 18px",
          gap: 12,
        }}
      >
        <span style={{ fontSize: 40, lineHeight: "48px", color: "#222", width: 40, textAlign: "center" }}>+</span>
        <div
          style={{
            flex: 1,
            height: 48,
            borderRadius: 24,
            backgroundColor: "#F2F2F2",
            display: "flex",
            alignItems: "center",
            padding: "0 18px",
            fontSize: 20,
            color: "#999",
          }}
        >
          메시지 입력
        </div>
        <span style={{ fontSize: 30, lineHeight: "48px", color: "#222", width: 40, textAlign: "center" }}>#</span>
      </div>
    </AbsoluteFill>
  );
};

const Message: React.FC<{
  side: "left" | "right";
  name?: string;
  time: string;
  appear: number;
  readAt?: number;
  frame: number;
  fps: number;
  showProfile?: boolean;
  children: React.ReactNode;
}> = ({ side, name, time, appear, readAt, frame, fps, showProfile, children }) => {
  if (frame < appear) return null;

  const pop = spring({
    frame: frame - appear,
    fps,
    config: { damping: 13, stiffness: 220, mass: 0.7 },
  });
  const isLeft = side === "left";
  const unreadVisible = !isLeft && (readAt === undefined || frame < readAt);

  const meta = (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: isLeft ? "flex-start" : "flex-end",
        justifyContent: "flex-end",
        fontSize: 15,
        color: "#556677",
        margin: "0 7px",
        flexShrink: 0,
        lineHeight: 1.25,
      }}
    >
      {unreadVisible ? (
        <span style={{ color: "#E6B800", fontWeight: 700, fontSize: 15 }}>1</span>
      ) : null}
      <span>{time}</span>
    </div>
  );

  const bubble = (
    <div
      style={{
        position: "relative",
        backgroundColor: isLeft ? "#fff" : KAKAO_YELLOW,
        color: "#111",
        fontSize: 25,
        fontWeight: 500,
        lineHeight: 1.4,
        padding: "13px 18px",
        borderRadius: 18,
        maxWidth: isLeft ? 300 : 330,
        wordBreak: "keep-all",
      }}
    >
      {/* 꼬리 */}
      <div
        style={{
          position: "absolute",
          top: 10,
          [isLeft ? "left" : "right"]: -8,
          width: 0,
          height: 0,
          borderTop: "8px solid transparent",
          borderBottom: "8px solid transparent",
          [isLeft ? "borderRight" : "borderLeft"]: `11px solid ${isLeft ? "#fff" : KAKAO_YELLOW}`,
        }}
      />
      {children}
    </div>
  );

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isLeft ? "flex-start" : "flex-end",
        opacity: Math.min(1, pop * 1.5),
        transformOrigin: isLeft ? "left top" : "right top",
        transform: `translateY(${(1 - pop) * 24}px) scale(${0.85 + 0.15 * pop})`,
      }}
    >
      {isLeft && showProfile ? <MonkeyAvatar /> : null}
      <div style={{ display: "flex", flexDirection: "column", marginLeft: isLeft ? 12 : 0 }}>
        {isLeft && name ? (
          <span style={{ fontSize: 19, color: "#333", marginBottom: 7 }}>{name}</span>
        ) : null}
        <div style={{ display: "flex", alignItems: "flex-end" }}>
          {isLeft ? (
            <>
              {bubble}
              {meta}
            </>
          ) : (
            <>
              {meta}
              {bubble}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const MonkeyAvatar: React.FC = () => (
  <div
    style={{
      width: 56,
      height: 56,
      borderRadius: 21,
      backgroundColor: "#F3D9A4",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      fontSize: 36,
      flexShrink: 0,
      overflow: "hidden",
    }}
  >
    <svg width="46" height="46" viewBox="0 0 46 46">
      <circle cx="8" cy="22" r="6" fill="#8B5A2B" />
      <circle cx="38" cy="22" r="6" fill="#8B5A2B" />
      <circle cx="8" cy="22" r="3" fill="#E8B98A" />
      <circle cx="38" cy="22" r="3" fill="#E8B98A" />
      <circle cx="23" cy="22" r="15" fill="#8B5A2B" />
      <ellipse cx="23" cy="26" rx="11" ry="10" fill="#E8B98A" />
      <ellipse cx="18" cy="20" rx="4" ry="4.5" fill="#E8B98A" />
      <ellipse cx="28" cy="20" rx="4" ry="4.5" fill="#E8B98A" />
      <circle cx="18" cy="21" r="2" fill="#2B1A0E" />
      <circle cx="28" cy="21" r="2" fill="#2B1A0E" />
      <path d="M18 31 Q23 35 28 31" stroke="#2B1A0E" strokeWidth="1.8" fill="none" strokeLinecap="round" />
    </svg>
  </div>
);

const SignalIcon = () => (
  <svg width="26" height="16" viewBox="0 0 26 16">
    {[0, 1, 2, 3].map((i) => (
      <rect key={i} x={i * 6.5} y={12 - i * 4} width="4.5" height={4 + i * 4} rx="1" fill="#111" />
    ))}
  </svg>
);
const BatteryIcon = () => (
  <svg width="34" height="16" viewBox="0 0 34 16">
    <rect x="0.75" y="0.75" width="28" height="14.5" rx="4" stroke="#111" strokeOpacity="0.5" fill="none" strokeWidth="1.5" />
    <rect x="3" y="3" width="20" height="10" rx="2" fill="#111" />
    <rect x="30.5" y="5" width="2.5" height="6" rx="1" fill="#111" fillOpacity="0.5" />
  </svg>
);
const SearchIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#111" strokeWidth="2">
    <circle cx="10.5" cy="10.5" r="6.5" />
    <line x1="15.5" y1="15.5" x2="21" y2="21" strokeLinecap="round" />
  </svg>
);
const MenuIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" stroke="#111" strokeWidth="2" strokeLinecap="round">
    <line x1="4" y1="6" x2="20" y2="6" />
    <line x1="4" y1="12" x2="20" y2="12" />
    <line x1="4" y1="18" x2="20" y2="18" />
  </svg>
);
