# 미국 시장 대시보드 (Streamlit)

## 실행
```bash
pip install -U -r requirements.txt
streamlit run app.py
```
브라우저에서 http://localhost:8501 이 열립니다. 상단 메뉴로 페이지를 전환합니다.

## 페이지
- 시장 개요: S&P 500 히트맵, 섹터 흐름, 국내 순매수 TOP10, 주요 매체 이슈(한국어 번역), 10년물 금리, 공포와 탐욕 지수, 원/달러 환율, VIX
- 종목 분석: 티커 검색, 캔들 차트(거래량, 이동평균선, 볼린저밴드, RSI, MACD), 기본 지표, 뉴스
- 캘린더: 주요국 경제지표 발표 일정, 미국 실적발표 일정 (주 단위)

## 파일 구성
- `app.py` 진입점과 페이지 메뉴
- `views/` 페이지별 화면 (market_overview, stock_analysis, event_calendar)
- `data.py` 데이터 수집과 캐싱
- `charts.py` 선 차트, 캔들 차트, 로고 히트맵
- `calendars.py` 캘린더 HTML
- `indicators.py` 기술적 지표 계산
- `news.py` 주요 매체 헤드라인 수집, 이슈 묶기, 중요도, 번역
- `common.py` 공통 도우미

## 데이터 출처
- S&P 500 구성종목: 위키피디아
- 시세, 시가총액, 기업 정보, 뉴스, 경제지표·실적 캘린더: Yahoo Finance (yfinance)
- 10년물 국채금리: FRED DGS10 (실패 시 Yahoo ^TNX)
- 공포와 탐욕 지수: 공개 과거 데이터(GitHub) + CNN
- 국내 순매수 TOP10: 한국예탁결제원 SEIBro (티커 연결: OpenFIGI)
- 주요 이슈: Reuters·Bloomberg(Google 뉴스 경유), WSJ, FT, CNBC, MarketWatch, Yahoo Finance RSS

## 번역 품질 높이기 (선택)
기본은 Google 번역입니다. Claude API 키를 넣으면 금융 용어에 맞춘 번역으로 바뀝니다.
- 로컬: `.streamlit/secrets.toml` 파일에 `ANTHROPIC_API_KEY = "sk-ant-..."`
- Streamlit Cloud: 앱 Settings → Secrets 에 같은 줄 추가

## 국내 순매수 TOP10 자동 갱신 (GitHub Actions)
Streamlit Cloud 서버에서 SEIBro 접속이 막힐 수 있어서, GitHub Actions가 평일 하루 두 번
SEIBro 데이터를 받아 `snapshots/net_buy.json`으로 커밋합니다. 앱은 실시간 조회가 실패하면 이 파일을 씁니다.
- 필요한 파일: `.github/workflows/net_buy.yml`, `scripts/fetch_net_buy.py`, `snapshots/net_buy.json`
- 처음 한 번: 저장소 Actions 탭 → "SEIBro 순매수 저장" → Run workflow
- 커밋이 실패하면: 저장소 Settings → Actions → General → Workflow permissions → Read and write permissions
