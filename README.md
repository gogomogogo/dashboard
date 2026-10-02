# 미국 시장 대시보드 (Streamlit)

## 실행
```bash
pip install -r requirements.txt
streamlit run app.py
```
브라우저에서 http://localhost:8501 이 열립니다.

## 파일 구성
- `app.py` 화면 구성 (사이드바, 히트맵, 지표 패널)
- `data.py` 데이터 수집과 캐싱
- `charts.py` 히트맵(트리맵)과 스크롤 줌 선 차트

## 데이터 출처
- S&P 500 구성종목: 위키피디아 / 시세·시가총액: Yahoo Finance (yfinance)
- 10년물 국채금리: FRED DGS10 (실패 시 Yahoo ^TNX)
- 공포와 탐욕 지수: CNN 비공식 엔드포인트
- 원/달러 환율 KRW=X, VIX ^VIX: Yahoo Finance
