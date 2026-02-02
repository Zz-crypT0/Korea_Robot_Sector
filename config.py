"""
설정 파일 - 로봇 섹터 분석을 위한 핵심 설정
자산운용사 관점의 펀드매니저 리포트용
"""
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict

# ============================================
# 로봇 섹터 핵심 종목 리스트 (수동 정의)
# ============================================
ROBOT_CORE_STOCKS = {
    # 산업용 로봇
    "454910": {"name": "로보티즈", "category": "서비스로봇", "market": "KOSDAQ"},
    "090710": {"name": "휴림로봇", "category": "산업용로봇", "market": "KOSDAQ"},
    "090460": {"name": "비에이치", "category": "부품", "market": "KOSDAQ"},

    # 로봇 자동화
    "108860": {"name": "셀바스AI", "category": "AI로봇", "market": "KOSDAQ"},
    "039030": {"name": "이오테크닉스", "category": "레이저장비", "market": "KOSDAQ"},
    "950140": {"name": "잉글우드랩", "category": "로봇SW", "market": "KOSDAQ"},

    # 대기업 로봇 관련
    "005930": {"name": "삼성전자", "category": "종합반도체", "market": "KOSPI"},
    "000660": {"name": "SK하이닉스", "category": "메모리반도체", "market": "KOSPI"},
    "012450": {"name": "한화에어로스페이스", "category": "방산/로봇", "market": "KOSPI"},
    "042660": {"name": "한화오션", "category": "조선/로봇", "market": "KOSPI"},
    "272210": {"name": "한화시스템", "category": "방산IT", "market": "KOSPI"},

    # 협동로봇/서비스로봇
    "056190": {"name": "에스에프에이", "category": "물류자동화", "market": "KOSPI"},
    "138580": {"name": "비즈니스온", "category": "전자문서", "market": "KOSDAQ"},
    "039440": {"name": "에스티아이", "category": "반도체장비", "market": "KOSDAQ"},
    "317830": {"name": "에스피시스템스", "category": "디스플레이장비", "market": "KOSDAQ"},

    # 모터/감속기 (로봇 핵심부품)
    "060150": {"name": "인텍플러스", "category": "검사장비", "market": "KOSDAQ"},
    "214150": {"name": "클래시스", "category": "의료기기", "market": "KOSDAQ"},
    "140860": {"name": "파크시스템스", "category": "나노장비", "market": "KOSDAQ"},
    "352820": {"name": "하이브", "category": "엔터", "market": "KOSPI"},  # 로봇 투자 관련

    # 두산 그룹 로봇
    "336260": {"name": "두산로보틱스", "category": "협동로봇", "market": "KOSPI"},
    "042670": {"name": "두산인프라코어", "category": "건설기계", "market": "KOSPI"},

    # 현대 그룹 로봇
    "005380": {"name": "현대차", "category": "완성차/로봇", "market": "KOSPI"},
    "000270": {"name": "기아", "category": "완성차", "market": "KOSPI"},
    "267260": {"name": "현대일렉트릭", "category": "전력기기", "market": "KOSPI"},

    # 레인보우로보틱스 (보스턴다이나믹스 협력)
    "277810": {"name": "레인보우로보틱스", "category": "휴머노이드", "market": "KOSDAQ"},
}

# ============================================
# 로봇 관련 ETF
# ============================================
ROBOT_ETFS = {
    "364980": {"name": "KODEX 글로벌로봇(합성)", "type": "글로벌"},
    "385590": {"name": "KODEX K-로봇액티브", "type": "국내"},
    "456600": {"name": "TIGER 로봇", "type": "국내"},
    "466920": {"name": "HANARO 글로벌로봇", "type": "글로벌"},
}

# ============================================
# 자동 스크리닝을 위한 키워드
# ============================================
ROBOT_KEYWORDS = [
    "로봇", "로보틱스", "협동로봇", "휴머노이드",
    "자동화", "스마트팩토리", "물류자동화",
    "모션컨트롤", "감속기", "서보모터",
    "AI", "인공지능", "머신러닝",
    "드론", "무인", "자율주행",
]

# 업종 분류 (KRX 업종코드 기반)
ROBOT_RELATED_SECTORS = [
    "기계", "전기전자", "운수장비", "의료정밀",
    "IT하드웨어", "IT서비스", "반도체",
]

# ============================================
# 분석 설정
# ============================================
@dataclass
class AnalysisConfig:
    # 기간 설정
    lookback_days: int = 252  # 1년
    short_term_days: int = 20  # 1개월
    medium_term_days: int = 60  # 3개월

    # 기술적 분석 파라미터
    ma_periods: List[int] = None
    rsi_period: int = 14

    # 밸류에이션 기준
    per_threshold_low: float = 10.0
    per_threshold_high: float = 30.0
    pbr_threshold: float = 3.0

    # 수급 분석
    institution_buy_threshold: int = 1000000000  # 10억원
    foreign_buy_threshold: int = 1000000000

    def __post_init__(self):
        if self.ma_periods is None:
            self.ma_periods = [5, 20, 60, 120]

# 기본 설정 인스턴스
DEFAULT_CONFIG = AnalysisConfig()

# ============================================
# 리포트 설정
# ============================================
REPORT_CONFIG = {
    "title": "국내 로봇 섹터 투자 분석 리포트",
    "subtitle": "자산운용사 관점의 펀드매니저 리포트",
    "author": "AI Quant Research Team",
    "update_frequency": "Daily",
    "sections": [
        "executive_summary",      # 핵심 요약
        "market_overview",        # 시장 개요
        "sector_analysis",        # 섹터 분석
        "stock_analysis",         # 종목별 분석
        "flow_analysis",          # 수급 분석
        "technical_analysis",     # 기술적 분석
        "valuation",              # 밸류에이션
        "risk_factors",           # 리스크 요인
        "investment_opinion",     # 투자의견
    ],
}

# ============================================
# API 설정 (환경변수에서 가져오기)
# ============================================
import os

API_CONFIG = {
    "naver_client_id": os.getenv("NAVER_CLIENT_ID", ""),
    "naver_client_secret": os.getenv("NAVER_CLIENT_SECRET", ""),
    "kis_app_key": os.getenv("KIS_APP_KEY", ""),
    "kis_app_secret": os.getenv("KIS_APP_SECRET", ""),
}

# ============================================
# 유틸리티 함수
# ============================================
def get_analysis_period():
    """분석 기간 반환"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DEFAULT_CONFIG.lookback_days)
    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")

def get_all_target_stocks() -> Dict[str, dict]:
    """분석 대상 전체 종목 반환"""
    all_stocks = {}
    all_stocks.update(ROBOT_CORE_STOCKS)
    return all_stocks

def get_all_etfs() -> Dict[str, dict]:
    """분석 대상 ETF 반환"""
    return ROBOT_ETFS.copy()
