# 🤖 국내 로봇 섹터 투자 분석 리포트

**자산운용사 관점의 펀드매니저 스타일 투자 분석 시스템**

[![Daily Report](https://github.com/YOUR_USERNAME/korea-robot-sector-report/actions/workflows/daily_report.yml/badge.svg)](https://github.com/YOUR_USERNAME/korea-robot-sector-report/actions/workflows/daily_report.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## 📋 개요

KRX, 네이버 금융, pykrx 등 국내 데이터 소스를 활용하여 로봇 섹터 종목을 자동 스크리닝하고, 펀드매니저 스타일의 투자 분석 리포트를 생성하는 시스템입니다.

### 주요 기능

- 🔍 **자동 종목 스크리닝**: 로봇 섹터 관련 종목 자동 필터링
- 📊 **종합 분석**: 기술적 분석 + 기본적 분석 + 밸류에이션
- 💰 **수급 분석**: 외국인/기관 투자자 매매 동향 추적
- 📦 **ETF 분석**: 로봇 섹터 ETF 성과 비교
- 📈 **HTML 대시보드**: 인터랙티브한 펀드매니저 스타일 리포트
- ⚡ **GitHub Actions**: 매일 자동 리포트 생성 및 배포

## 🗂️ 프로젝트 구조

```
korea-robot-sector-report/
├── src/
│   ├── __init__.py
│   ├── config.py           # 설정 및 종목 리스트
│   ├── data_collector.py   # 데이터 수집 (pykrx, 네이버)
│   ├── screener.py         # 로봇 섹터 종목 스크리닝
│   ├── analyzer.py         # 재무/기술적 분석
│   ├── flow_analyzer.py    # 외국인/기관 수급 분석
│   └── report_generator.py # HTML 리포트 생성
├── templates/
│   └── report_template.html # Jinja2 HTML 템플릿
├── reports/                 # 생성된 리포트
├── .github/
│   └── workflows/
│       └── daily_report.yml # GitHub Actions 워크플로우
├── main.py                  # 메인 실행 스크립트
├── requirements.txt
└── README.md
```

## 🚀 빠른 시작

### 1. 저장소 클론

```bash
git clone https://github.com/YOUR_USERNAME/korea-robot-sector-report.git
cd korea-robot-sector-report
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 리포트 생성

```bash
# 전체 분석 리포트 생성
python main.py

# 빠른 분석 모드 (주요 종목만)
python main.py --quick

# JSON 데이터도 함께 생성
python main.py --json

# 출력 경로 지정
python main.py --output ./my-reports
```

### 4. 리포트 확인

생성된 `reports/robot_sector_report_YYYYMMDD.html` 파일을 브라우저에서 열면 됩니다.

## 📊 분석 대상 종목

### 핵심 로봇 종목

| 종목명 | 코드 | 카테고리 |
|--------|------|----------|
| 레인보우로보틱스 | 277810 | 휴머노이드 |
| 두산로보틱스 | 336260 | 협동로봇 |
| 한화에어로스페이스 | 012450 | 방산/로봇 |
| 에스에프에이 | 056190 | 물류자동화 |
| 셀바스AI | 108860 | AI로봇 |

### ETF

| ETF명 | 코드 | 유형 |
|-------|------|------|
| KODEX K-로봇액티브 | 385590 | 국내 |
| TIGER 로봇 | 456600 | 국내 |
| KODEX 글로벌로봇 | 364980 | 글로벌 |

## ⚙️ GitHub Actions 설정

### 자동 리포트 생성 스케줄

매일 평일 오후 6시(한국시간)에 자동으로 리포트가 생성됩니다.

### 설정 방법

1. **GitHub Pages 활성화**
   - Settings > Pages > Source: `gh-pages` branch

2. **환경 변수 설정** (선택사항)
   - Settings > Secrets and variables > Actions
   ```
   NAVER_CLIENT_ID=your_client_id
   NAVER_CLIENT_SECRET=your_client_secret
   ```

3. **수동 실행**
   - Actions 탭 > "Daily Robot Sector Report" > "Run workflow"

## 📈 리포트 구성

### 1. Executive Summary
- 섹터 전체 성과 요약
- 평균 투자 스코어
- 매수/중립/매도 종목 수
- 섹터 수급 신호

### 2. Top Picks
- 투자 스코어 상위 5개 종목
- 가격, 수익률, 밸류에이션 지표

### 3. 종목별 분석
- 전체 종목 현황 테이블
- 기술적 지표 (RSI, 이동평균 신호)
- 투자의견 및 스코어

### 4. 수급 분석
- 외국인/기관 순매수 Top 5
- 수급 선도 종목 (동시 매수)
- 수급 추이 차트

### 5. ETF 분석
- 로봇 섹터 ETF 성과 비교
- 수익률 추이

### 6. 기술적 분석
- 추세 분포 (정배열/역배열)
- RSI 과매수/과매도 종목

## 🔧 커스터마이징

### 분석 대상 종목 수정

`src/config.py`에서 `ROBOT_CORE_STOCKS` 딕셔너리를 수정:

```python
ROBOT_CORE_STOCKS = {
    "277810": {"name": "레인보우로보틱스", "category": "휴머노이드", "market": "KOSDAQ"},
    # 종목 추가/수정
}
```

### 분석 파라미터 조정

`src/config.py`의 `AnalysisConfig` 클래스 수정:

```python
@dataclass
class AnalysisConfig:
    lookback_days: int = 252  # 분석 기간
    rsi_period: int = 14      # RSI 기간
    per_threshold_low: float = 10.0  # PER 저평가 기준
    # ...
```

### HTML 템플릿 수정

`templates/report_template.html`에서 리포트 디자인 커스터마이징 가능

## 📌 주의사항

- **투자 참고용**: 본 리포트는 투자 참고 자료로만 활용하세요
- **API 제한**: pykrx는 무료 API로 요청 빈도 제한이 있을 수 있습니다
- **장 마감 후 실행**: 정확한 데이터를 위해 장 마감 후 실행 권장
- **데이터 지연**: 일부 데이터는 실시간이 아닐 수 있습니다

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일 참조

## 🔗 데이터 소스

- [KRX 한국거래소](http://www.krx.co.kr/)
- [네이버 금융](https://finance.naver.com/)
- [pykrx](https://github.com/sharebook-kr/pykrx)

## ⚠️ 면책 조항

> 본 프로젝트에서 제공하는 정보는 투자 권유를 목적으로 하지 않습니다.
> 투자 결정은 본인의 판단과 책임 하에 이루어져야 하며,
> 본 프로젝트의 정보를 기반으로 한 투자 손실에 대해 책임을 지지 않습니다.
> 과거 성과가 미래 수익을 보장하지 않습니다.
