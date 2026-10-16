# 카톡 모션그래픽 (16초, 1920x1080, 30fps)

`src/KakaoOracle.tsx` 상단의 `T` 객체(초 단위)만 수정하면 녹음/효과음 타이밍에 맞출 수 있음.

| 시간 | 내용 | 효과음/대사 |
|---|---|---|
| 0.0s | 검은 화면 | |
| 0.5s | 휴대폰 화면 켜짐 | 카톡! |
| 0.75s | 원숭이: 야야 오라클이 데센 포스메져 선언했다함. | |
| 3.2s | 나: 잉?? 포스메져? 갑자기? | |
| 6.0s | 원숭이: ㅇㅇBE 납품 사이트라는 데 조진거 아님??? (내 메시지 읽음 표시 '1' 사라짐) | 카톡! |
| 9.0s | 나: 오키 한번 조사해봄 | |
| 9.0s~16s | 대화 화면 그대로 정지 (줌/전환 없음) | "그래서 조사해봤습니다" 대사 |

## 실행

```bash
npm i
npm run dev                                   # Remotion Studio 미리보기
npx remotion render KakaoOracle out/KakaoOracle.mp4
```

폰트: Pretendard (SIL OFL), `public/fonts`에 포함.
