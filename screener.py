"""
로봇 섹터 종목 자동 스크리닝 모듈
업종, 키워드, 재무지표 기반 종목 필터링
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import re

try:
    from pykrx import stock
except ImportError:
    stock = None

from .config import (
    ROBOT_CORE_STOCKS, ROBOT_ETFS, ROBOT_KEYWORDS,
    ROBOT_RELATED_SECTORS, DEFAULT_CONFIG
)


class RobotSectorScreener:
    """로봇 섹터 종목 스크리닝"""

    def __init__(self):
        self.core_stocks = ROBOT_CORE_STOCKS
        self.etfs = ROBOT_ETFS
        self.keywords = ROBOT_KEYWORDS
        self.sectors = ROBOT_RELATED_SECTORS

    def screen_by_keyword(
        self,
        all_stocks: pd.DataFrame,
        keywords: List[str] = None
    ) -> pd.DataFrame:
        """
        종목명 기반 키워드 스크리닝

        Args:
            all_stocks: DataFrame with 'ticker', 'name' columns
            keywords: 검색 키워드 리스트 (기본: ROBOT_KEYWORDS)

        Returns:
            매칭된 종목 DataFrame
        """
        if keywords is None:
            keywords = self.keywords

        if all_stocks.empty:
            return pd.DataFrame()

        # 키워드 패턴 생성
        pattern = '|'.join(keywords)

        # 종목명 매칭
        mask = all_stocks['name'].str.contains(pattern, case=False, na=False)

        matched = all_stocks[mask].copy()
        matched['match_type'] = 'keyword'

        return matched

    def screen_by_theme(self, date: str = None) -> pd.DataFrame:
        """
        KRX 테마별 종목 조회 (로봇/AI 관련 테마)

        Note: pykrx의 테마 기능 활용
        """
        if stock is None:
            return pd.DataFrame()

        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        robot_themes = [
            '로봇', '인공지능', 'AI', '스마트팩토리',
            '자율주행', '드론', '협동로봇'
        ]

        try:
            # 테마별 종목 조회 (pykrx 버전에 따라 다를 수 있음)
            # 현재 pykrx에서 테마 조회 기능이 제한적이므로 대안 사용
            return pd.DataFrame()
        except:
            return pd.DataFrame()

    def get_supply_chain_stocks(self) -> Dict[str, dict]:
        """
        로봇 산업 공급망 종목 (부품, 소프트웨어 등)
        """
        supply_chain = {
            # 감속기/모터
            "214150": {"name": "클래시스", "role": "의료로봇", "market": "KOSDAQ"},
            "060150": {"name": "인텍플러스", "role": "검사장비", "market": "KOSDAQ"},

            # 센서
            "140860": {"name": "파크시스템스", "role": "나노측정", "market": "KOSDAQ"},
            "067310": {"name": "하나마이크론", "role": "반도체패키징", "market": "KOSDAQ"},

            # 로봇 비전/AI
            "039030": {"name": "이오테크닉스", "role": "레이저", "market": "KOSDAQ"},
            "108860": {"name": "셀바스AI", "role": "AI솔루션", "market": "KOSDAQ"},

            # 자동화 장비
            "056190": {"name": "에스에프에이", "role": "물류자동화", "market": "KOSPI"},
            "039440": {"name": "에스티아이", "role": "반도체장비", "market": "KOSDAQ"},
        }
        return supply_chain

    def get_large_cap_robot_exposure(self) -> Dict[str, dict]:
        """
        로봇 사업 노출도가 있는 대형주
        """
        large_caps = {
            "005930": {
                "name": "삼성전자",
                "robot_exposure": "로봇 부품(반도체), 스마트팩토리",
                "exposure_ratio": "low",
                "market": "KOSPI"
            },
            "000660": {
                "name": "SK하이닉스",
                "robot_exposure": "메모리반도체(로봇용)",
                "exposure_ratio": "low",
                "market": "KOSPI"
            },
            "005380": {
                "name": "현대차",
                "robot_exposure": "보스턴다이나믹스, 로봇사업부",
                "exposure_ratio": "medium",
                "market": "KOSPI"
            },
            "012450": {
                "name": "한화에어로스페이스",
                "robot_exposure": "한화로보틱스, 협동로봇",
                "exposure_ratio": "high",
                "market": "KOSPI"
            },
            "336260": {
                "name": "두산로보틱스",
                "robot_exposure": "협동로봇 전문",
                "exposure_ratio": "pure_play",
                "market": "KOSPI"
            },
            "277810": {
                "name": "레인보우로보틱스",
                "robot_exposure": "휴머노이드, 이족보행로봇",
                "exposure_ratio": "pure_play",
                "market": "KOSDAQ"
            },
        }
        return large_caps

    def classify_by_robot_category(
        self,
        stocks: Dict[str, dict]
    ) -> Dict[str, List[str]]:
        """
        로봇 카테고리별 분류

        Categories:
        - 휴머노이드/서비스로봇
        - 산업용/협동로봇
        - 물류/배송로봇
        - 의료로봇
        - 로봇부품(감속기, 모터, 센서)
        - 로봇SW/AI
        """
        categories = {
            'humanoid': [],      # 휴머노이드/서비스로봇
            'industrial': [],    # 산업용/협동로봇
            'logistics': [],     # 물류/배송로봇
            'medical': [],       # 의료로봇
            'components': [],    # 로봇부품
            'software': [],      # 로봇SW/AI
            'conglomerate': [],  # 대기업(로봇사업부)
            'other': [],         # 기타
        }

        category_keywords = {
            'humanoid': ['휴머노이드', '서비스로봇', '이족', '레인보우'],
            'industrial': ['협동로봇', '산업용', '두산로보틱스', '한화로보틱스'],
            'logistics': ['물류', '배송', 'AMR', 'AGV', '에스에프에이'],
            'medical': ['의료', '수술', '재활', '클래시스'],
            'components': ['감속기', '모터', '센서', '부품'],
            'software': ['AI', '비전', '소프트웨어', 'SW', '셀바스'],
            'conglomerate': ['삼성', '현대', 'SK', 'LG'],
        }

        for ticker, info in stocks.items():
            name = info.get('name', '')
            category_assigned = False

            for cat, keywords in category_keywords.items():
                for kw in keywords:
                    if kw.lower() in name.lower():
                        categories[cat].append(ticker)
                        category_assigned = True
                        break
                if category_assigned:
                    break

            if not category_assigned:
                categories['other'].append(ticker)

        return categories

    def get_final_universe(
        self,
        include_etfs: bool = True,
        include_supply_chain: bool = True,
        include_large_caps: bool = True
    ) -> Dict[str, dict]:
        """
        최종 분석 유니버스 생성

        Args:
            include_etfs: ETF 포함 여부
            include_supply_chain: 공급망 종목 포함 여부
            include_large_caps: 대형주 포함 여부

        Returns:
            통합된 종목 딕셔너리
        """
        universe = {}

        # 1. 핵심 로봇 종목
        universe.update(self.core_stocks)

        # 2. 공급망 종목
        if include_supply_chain:
            for ticker, info in self.get_supply_chain_stocks().items():
                if ticker not in universe:
                    universe[ticker] = {
                        'name': info['name'],
                        'category': info['role'],
                        'market': info['market'],
                        'type': 'supply_chain'
                    }

        # 3. 대형주
        if include_large_caps:
            for ticker, info in self.get_large_cap_robot_exposure().items():
                if ticker not in universe:
                    universe[ticker] = {
                        'name': info['name'],
                        'category': info['robot_exposure'],
                        'market': info['market'],
                        'type': 'large_cap',
                        'exposure': info['exposure_ratio']
                    }

        return universe

    def get_etf_universe(self) -> Dict[str, dict]:
        """ETF 유니버스 반환"""
        return self.etfs.copy()

    def generate_screening_report(self) -> str:
        """스크리닝 결과 리포트 생성"""
        universe = self.get_final_universe()
        categories = self.classify_by_robot_category(universe)

        report = []
        report.append("=" * 60)
        report.append("로봇 섹터 스크리닝 결과")
        report.append("=" * 60)
        report.append(f"\n총 종목 수: {len(universe)}개")
        report.append(f"ETF 수: {len(self.etfs)}개")

        report.append("\n[카테고리별 분류]")
        category_names = {
            'humanoid': '휴머노이드/서비스',
            'industrial': '산업용/협동로봇',
            'logistics': '물류/배송',
            'medical': '의료로봇',
            'components': '로봇부품',
            'software': '로봇SW/AI',
            'conglomerate': '대기업',
            'other': '기타'
        }

        for cat, tickers in categories.items():
            if tickers:
                names = [universe.get(t, {}).get('name', t) for t in tickers]
                report.append(f"  {category_names.get(cat, cat)}: {', '.join(names)}")

        report.append("\n[ETF]")
        for ticker, info in self.etfs.items():
            report.append(f"  {info['name']} ({ticker}) - {info['type']}")

        return '\n'.join(report)


# ============================================
# 실행 예시
# ============================================
if __name__ == "__main__":
    screener = RobotSectorScreener()

    # 스크리닝 리포트 출력
    print(screener.generate_screening_report())

    # 최종 유니버스
    universe = screener.get_final_universe()
    print(f"\n분석 대상 종목: {len(universe)}개")
