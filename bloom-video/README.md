# 블룸에너지는 뭐하는 회사인가 — 모션 그래픽

Remotion(React + TypeScript), 1920×1080 · 30fps · 오디오 없음. 결과물은 `out/Scene1~7.mp4`, `out/Main.mp4`.

## 숫자 바꾸고 다시 렌더하기
1. `src/data.ts`의 `DATA`(시총·매출·장면 길이 등)를 고친다. 주가는 `python3 scripts/fetch_price.py` 또는 `python3 scripts/import_price.py <받은CSV>`로 `data/price.csv`를 갱신한다.
2. `npm i` 후 `npx remotion studio`로 미리 본다 (선택).
3. `npm run render:all` 로 장면별 MP4 7개와 Main MP4를 `out/`에 다시 만든다.

## 참고
- 로고 원본은 `assets/`, 배경 제거본은 `python3 scripts/make_logos.py`로 `public/logos/`에 생성.
- 브라우저 다운로드가 막힌 환경에서는 `REMOTION_BROWSER=<chrome-headless-shell 경로>`를 지정한다.
