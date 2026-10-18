// 영상에 쓰이는 모든 숫자·텍스트·장면 길이·레이아웃 값을 이 파일 하나에 모은다.
// 다른 파일에는 숫자를 하드코딩하지 않는다. 수정 후 재렌더만 하면 반영된다.

export const DATA = {
  asOf: "2026.10", // 화면 우하단 작은 출처 표기용
  // 시가총액, $B. 녹화 직전 갱신 예정
  marketCap: { bloom: 77, oracle: 389, unit: "B" },
  // 매출, $B. 블룸 FY2025 (10-K) / 오라클 FY2026 (5월 결산)
  revenue: { bloom: 2.02, oracle: 67.4, unit: "B" },
  // 블룸 연간 매출 $B (각 연도 10-K)
  revenueHistory: [
    { year: 2021, value: 0.97 },
    { year: 2022, value: 1.2 },
    { year: 2023, value: 1.33 },
    { year: 2024, value: 1.47 },
    { year: 2025, value: 2.02 },
  ],
  revenueGrowth: 37, // %, FY2025 YoY
  operatingIncome: 0.073, // $B (= $73M), FY2025
  netIncome: -0.088, // $B (= -$88M), FY2025 보통주 귀속
  sceneDurationsSec: [8, 12, 7, 8, 7, 10, 8],
};

// ── 영상 공통 ────────────────────────────────────────────
export const VIDEO = {
  width: 1920,
  height: 1080,
  fps: 30,
  holdSec: 1, // 각 장면 마지막 1초는 최종 상태로 정지
  transitionSec: 0.3, // 장면 전환 크로스페이드
  countUpSec: 0.8, // <CountUp> 공통 길이
  enterMovePx: 24, // 등장 시 이동 거리 (24px 이내)
  enterScaleFrom: 0.96, // 등장 시 스케일 시작값
  enterSec: 0.5, // 기본 등장 애니메이션 길이
};

export const COLORS = {
  bg: "#0B0D10",
  text: "#F5F5F5",
  sub: "#8A8F98",
  accent: "#4ADE80", // 블룸에너지
  compareFill: "#3A3F47", // 오라클 (채움)
  compareLine: "#5A606A", // 오라클 (선)
};

export const FONT = {
  family: "Pretendard",
  bold: 700,
  regular: 400,
  sizeHero: 160, // 가장 큰 숫자
  sizeXL: 112, // Scene 7 숫자 3칸
  sizeLarge: 72,
  sizeMedium: 56,
  sizeBody: 44,
  sizeSmall: 36,
  sizeNote: 24,
  sizeAsOf: 20,
};

export const LAYOUT = {
  margin: 140, // 좌우·상하 최소 여백
  subtitleZoneRatio: 0.18, // 하단 자막 영역 비율
  asOfGap: 16, // 자막 영역과 "기준" 표기 사이 간격
  iconStroke: 3,
};

export const TEXT = {
  asOfPrefix: "기준: ",
  oracle: "오라클",
  oracleUnit: "1", // "1 오라클"
  analogyNote: "※ 이해를 돕기 위한 비유",
  scene1: {
    title: "고체산화물 연료전지",
    titleSub: "SOFC",
    steps: ["설계", "제조", "판매", "설치"],
  },
  scene2: {
    step1: "건전지인데,",
    step2: "충전재를 갈아 끼우는 건전지",
    gas: "가스",
    power: "전기",
  },
  scene3: { gainLabel: "3년 상승률" },
  scene4: { label: "시가총액" },
  scene5: { label: "매출", note: (pct: number) => `오라클의 약 ${pct}%` },
  scene6: { label: "매출 성장률 (2025, 전년 대비)" },
  scene7: {
    labels: ["매출", "영업이익", "순이익"],
    footnote: "2025년 연간 기준",
  },
};

// ── Scene 1: 회사 정체 ───────────────────────────────────
export const S1 = {
  logoHeight: 140,
  logoTop: 250,
  titleTop: 450,
  chipsTop: 610,
  chipPadY: 20,
  chipPadX: 48,
  chipRadius: 20,
  arrowLength: 64, // 칩 사이 화살표 길이
  arrowHead: 10,
  // 타이밍 (초)
  logo: 0,
  logoSec: 1,
  title: 1,
  firstChip: 1.8,
  chipStagger: 0.25,
  highlight: 3.4, // 마지막 칩 등장 후 전체 테두리 강조
  highlightSec: 0.4,
};

// ── Scene 2: SOFC 비유 (건전지) ──────────────────────────
export const S2 = {
  centerY: 540,
  bodyWidth: 600,
  bodyHeight: 260,
  bodyRadius: 36,
  capWidth: 28,
  capHeight: 110,
  inset: 22, // 외곽선 ~ 충전재 간격
  fillRadius: 18,
  textTop: 220,
  noteTop: 140,
  // 가스 입자
  gasStartX: 300, // 입자 출발 x
  dotRadius: 8,
  dotEverySec: 0.3,
  dotTravelSec: 1.2,
  // 번개
  boltGap: 90, // 단자 ~ 번개 중심
  boltSize: 90,
  blinkSec: 0.6, // 깜빡임 주기
  blinkMin: 0.25,
  labelGap: 70, // 중심선 ~ 라벨
  // 타이밍 (초)
  battery: 0,
  text1: 0.4,
  drain: 2.6, // 충전재 비우기
  drainSec: 0.5,
  text1Out: 2.8,
  text2: 3.2,
  cartridge: 3.4, // 새 카트리지 밀려 들어옴
  cartridgeSec: 0.9,
  flow: 6, // 가스 → 전기
};

// ── Scene 3: 주가 차트 ───────────────────────────────────
export const S3 = {
  left: 240,
  right: 1480,
  top: 380,
  bottom: 780,
  dotRadius: 10,
  areaOpacity: 0.08,
  endLabelGap: 28,
  startLabelGap: 20,
  heroTop: 140,
  // 타이밍 (초)
  draw: 0.3,
  drawSec: 1.8,
  gainDecimals: 0,
  priceDecimals: 2,
};

// ── Scene 7: 이익 ────────────────────────────────────────
export const S7 = {
  pitch: 520, // 칸 중심 간 거리
  valueTop: 380,
  footnoteTop: 700,
  dimOpacity: 0.45,
  // 타이밍 (초)
  first: 0.3,
  stagger: 0.3,
  dim: 2.6,
  dimSec: 0.6,
  footnote: 1.4,
  millionsBelow: 1, // $B 값이 이보다 작으면 $M 으로 표기
  billionDecimals: 2,
};

// ── Scene 4·5 공유: 원 비교 레이아웃 ─────────────────────
export const CIRCLES = {
  oracleRadius: 260, // 오라클 원 반지름 기준. 블룸 반지름 = 260 × √(블룸/오라클)
  oracleCenterX: 640,
  bloomCenterX: 1300,
  baselineY: 770, // 두 원의 바닥선
  labelTop: 150, // 상단 라벨 위치
  logoHeight: 40,
  logoGap: 28, // 원 바닥 ~ 로고
  valueGap: 28, // 블룸 원 위 숫자 블록과 원 사이
  ratioDecimals: 2, // "= 0.20 오라클"
  // 장면 내 타이밍 (초)
  s4: { label: 0, oracle: 0.2, bloomGrow: 1.5, bloomGrowSec: 1, value: 2.6, ratio: 3.6 },
  s5: { label: 0, bloomShrink: 0.3, bloomShrinkSec: 1.2, value: 1.6, ratio: 2.6, note: 3.4 },
  s4ValueDecimals: 0, // "$77B"
  s5ValueDecimals: 1, // "$2.0B"
};

// ── Scene 6: 매출 막대 ───────────────────────────────────
export const BARS = {
  barWidth: 120,
  pitch: 260, // 막대 중심 간 거리 (간격 140px)
  baselineY: 820,
  maxHeight: 330,
  valueGap: 14, // 막대 위 값 라벨 간격
  yearGap: 14, // 막대 아래 연도 간격
  valueDecimals: 2,
  heroTop: 140, // "+37%" 위치
  arrow: { startLift: 76, endLift: 18, endInset: 74, arc: 80, headSize: 16 },
  // 타이밍 (초)
  firstBar: 0.3,
  stagger: 0.2,
  growSec: 0.6,
  arrowDelay: 0.1, // 마지막 막대 완료 후
  arrowSec: 0.6,
  heroDelay: 0.3, // 마지막 막대 완료 후
};

// ── 계산값 ───────────────────────────────────────────────
export const sec = (s: number) => Math.round(s * VIDEO.fps);
export const sceneFrames = DATA.sceneDurationsSec.map(sec);
export const holdFrames = sec(VIDEO.holdSec);
export const transitionFrames = sec(VIDEO.transitionSec);
export const mainFrames =
  sceneFrames.reduce((a, b) => a + b, 0) - transitionFrames * (sceneFrames.length - 1);

export const ratios = {
  marketCap: DATA.marketCap.bloom / DATA.marketCap.oracle,
  revenue: DATA.revenue.bloom / DATA.revenue.oracle,
};
