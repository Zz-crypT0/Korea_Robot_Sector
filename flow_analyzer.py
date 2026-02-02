"""
외국인/기관 수급 분석 모듈
자산운용사 관점의 투자자별 매매 동향 분석
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

from .config import DEFAULT_CONFIG, AnalysisConfig


@dataclass
class FlowAnalysisResult:
    """수급 분석 결과 데이터클래스"""
    ticker: str
    name: str

    # 외국인
    foreign_net_buy_1d: int  # 일간 순매수 (원)
    foreign_net_buy_5d: int  # 5일 순매수
    foreign_net_buy_20d: int  # 20일 순매수
    foreign_holding_ratio: Optional[float]  # 외국인 보유비율

    # 기관
    institution_net_buy_1d: int
    institution_net_buy_5d: int
    institution_net_buy_20d: int

    # 개인
    individual_net_buy_1d: int
    individual_net_buy_5d: int
    individual_net_buy_20d: int

    # 수급 신호
    flow_signal: str  # "매집", "차익실현", "이탈", "중립"
    flow_score: float  # -100 ~ 100


class InvestorFlowAnalyzer:
    """투자자별 수급 분석기"""

    def __init__(self, config: AnalysisConfig = None):
        self.config = config or DEFAULT_CONFIG

    def calculate_net_buy(
        self,
        investor_data: pd.DataFrame,
        investor_type: str,
        days: int
    ) -> int:
        """기간별 순매수 금액 계산"""
        if investor_data.empty or investor_type not in investor_data.columns:
            return 0

        recent_data = investor_data[investor_type].tail(days)
        return int(recent_data.sum())

    def analyze_flow(self, stock_data: Dict) -> FlowAnalysisResult:
        """
        종목 수급 분석

        Args:
            stock_data: DataAggregator에서 수집한 데이터

        Returns:
            FlowAnalysisResult
        """
        ticker = stock_data.get('ticker', '')
        name = stock_data.get('name', '')
        investor_df = stock_data.get('investor', pd.DataFrame())

        # 외국인 수급
        foreign_1d = self.calculate_net_buy(investor_df, 'foreign', 1)
        foreign_5d = self.calculate_net_buy(investor_df, 'foreign', 5)
        foreign_20d = self.calculate_net_buy(investor_df, 'foreign', 20)

        # 기관 수급
        inst_1d = self.calculate_net_buy(investor_df, 'institution', 1)
        inst_5d = self.calculate_net_buy(investor_df, 'institution', 5)
        inst_20d = self.calculate_net_buy(investor_df, 'institution', 20)

        # 개인 수급
        ind_1d = self.calculate_net_buy(investor_df, 'individual', 1)
        ind_5d = self.calculate_net_buy(investor_df, 'individual', 5)
        ind_20d = self.calculate_net_buy(investor_df, 'individual', 20)

        # 수급 신호 계산
        flow_signal, flow_score = self._calculate_flow_signal(
            foreign_5d, foreign_20d,
            inst_5d, inst_20d
        )

        return FlowAnalysisResult(
            ticker=ticker,
            name=name,
            foreign_net_buy_1d=foreign_1d,
            foreign_net_buy_5d=foreign_5d,
            foreign_net_buy_20d=foreign_20d,
            foreign_holding_ratio=None,  # 별도 API 필요
            institution_net_buy_1d=inst_1d,
            institution_net_buy_5d=inst_5d,
            institution_net_buy_20d=inst_20d,
            individual_net_buy_1d=ind_1d,
            individual_net_buy_5d=ind_5d,
            individual_net_buy_20d=ind_20d,
            flow_signal=flow_signal,
            flow_score=flow_score
        )

    def _calculate_flow_signal(
        self,
        foreign_5d: int,
        foreign_20d: int,
        inst_5d: int,
        inst_20d: int
    ) -> Tuple[str, float]:
        """
        수급 신호 계산

        신호 종류:
        - 매집: 외국인+기관 동시 순매수 지속
        - 차익실현: 외국인+기관 동시 순매도
        - 외국인주도: 외국인만 순매수
        - 기관주도: 기관만 순매수
        - 중립: 혼조세
        """
        threshold = self.config.institution_buy_threshold

        # 스코어 계산 (-100 ~ 100)
        score = 0

        # 외국인 기여
        if foreign_5d > threshold:
            score += 25
        elif foreign_5d > 0:
            score += 10
        elif foreign_5d < -threshold:
            score -= 25
        elif foreign_5d < 0:
            score -= 10

        if foreign_20d > threshold * 3:
            score += 25
        elif foreign_20d > 0:
            score += 10
        elif foreign_20d < -threshold * 3:
            score -= 25
        elif foreign_20d < 0:
            score -= 10

        # 기관 기여
        if inst_5d > threshold:
            score += 25
        elif inst_5d > 0:
            score += 10
        elif inst_5d < -threshold:
            score -= 25
        elif inst_5d < 0:
            score -= 10

        if inst_20d > threshold * 3:
            score += 25
        elif inst_20d > 0:
            score += 10
        elif inst_20d < -threshold * 3:
            score -= 25
        elif inst_20d < 0:
            score -= 10

        # 신호 결정
        if score >= 50:
            signal = '강한매집'
        elif score >= 20:
            signal = '매집'
        elif score <= -50:
            signal = '강한이탈'
        elif score <= -20:
            signal = '차익실현'
        elif foreign_5d > 0 and inst_5d < 0:
            signal = '외국인주도'
        elif foreign_5d < 0 and inst_5d > 0:
            signal = '기관주도'
        else:
            signal = '중립'

        return signal, score

    def get_flow_trend(
        self,
        investor_data: pd.DataFrame,
        investor_type: str,
        windows: List[int] = [5, 10, 20]
    ) -> pd.DataFrame:
        """
        수급 추세 계산 (이동 순매수)

        Args:
            investor_data: 투자자별 매매 데이터
            investor_type: 'foreign', 'institution', 'individual'
            windows: 이동평균 기간

        Returns:
            DataFrame with rolling net buy
        """
        if investor_data.empty or investor_type not in investor_data.columns:
            return pd.DataFrame()

        result = pd.DataFrame(index=investor_data.index)

        for window in windows:
            result[f'net_buy_{window}d'] = investor_data[investor_type].rolling(window).sum()

        return result

    def calculate_flow_momentum(
        self,
        investor_data: pd.DataFrame,
        investor_type: str
    ) -> Dict:
        """
        수급 모멘텀 계산

        Returns:
            {
                'acceleration': 가속/감속 여부,
                'turning_point': 전환점 여부,
                'streak': 연속 순매수/순매도 일수
            }
        """
        if investor_data.empty or investor_type not in investor_data.columns:
            return {'acceleration': None, 'turning_point': False, 'streak': 0}

        data = investor_data[investor_type]

        # 5일 vs 20일 비교로 가속도 판단
        recent_5d = data.tail(5).sum()
        prev_5d = data.iloc[-10:-5].sum() if len(data) >= 10 else 0

        if recent_5d > 0 and recent_5d > prev_5d:
            acceleration = '순매수가속'
        elif recent_5d > 0 and recent_5d < prev_5d:
            acceleration = '순매수둔화'
        elif recent_5d < 0 and recent_5d < prev_5d:
            acceleration = '순매도가속'
        elif recent_5d < 0 and recent_5d > prev_5d:
            acceleration = '순매도둔화'
        else:
            acceleration = '중립'

        # 전환점 (부호 변경)
        turning_point = (recent_5d * prev_5d < 0) if prev_5d != 0 else False

        # 연속 일수
        streak = 0
        for i in range(1, min(len(data) + 1, 30)):
            val = data.iloc[-i]
            if i == 1:
                sign = 1 if val > 0 else -1
            if (val > 0 and sign > 0) or (val < 0 and sign < 0):
                streak += 1
            else:
                break

        return {
            'acceleration': acceleration,
            'turning_point': turning_point,
            'streak': streak * sign if sign else 0
        }


class SectorFlowAnalyzer:
    """섹터 전체 수급 분석"""

    def __init__(self, config: AnalysisConfig = None):
        self.config = config or DEFAULT_CONFIG
        self.flow_analyzer = InvestorFlowAnalyzer(config)

    def analyze_sector_flow(
        self,
        sector_data: Dict[str, Dict]
    ) -> Dict:
        """
        섹터 전체 수급 분석

        Returns:
            {
                'summary': 섹터 수급 요약,
                'stocks': 종목별 수급 결과,
                'top_foreign_buy': 외국인 순매수 상위,
                'top_institution_buy': 기관 순매수 상위,
                'flow_leaders': 수급 선도 종목
            }
        """
        results = []
        total_foreign = 0
        total_inst = 0

        for ticker, data in sector_data.items():
            try:
                result = self.flow_analyzer.analyze_flow(data)
                result_dict = {
                    'ticker': result.ticker,
                    'name': result.name,
                    'foreign_5d': result.foreign_net_buy_5d,
                    'foreign_20d': result.foreign_net_buy_20d,
                    'institution_5d': result.institution_net_buy_5d,
                    'institution_20d': result.institution_net_buy_20d,
                    'flow_signal': result.flow_signal,
                    'flow_score': result.flow_score,
                    'result': result
                }
                results.append(result_dict)

                total_foreign += result.foreign_net_buy_20d
                total_inst += result.institution_net_buy_20d
            except Exception as e:
                print(f"Error analyzing flow for {ticker}: {e}")

        if not results:
            return {}

        # 정렬
        df = pd.DataFrame(results)

        # 섹터 수급 요약
        summary = {
            'total_foreign_net_buy_20d': total_foreign,
            'total_institution_net_buy_20d': total_inst,
            'avg_flow_score': df['flow_score'].mean(),
            'accumulation_count': len(df[df['flow_signal'].isin(['매집', '강한매집'])]),
            'distribution_count': len(df[df['flow_signal'].isin(['차익실현', '강한이탈'])]),
            'sector_flow_signal': self._get_sector_signal(total_foreign, total_inst)
        }

        # 외국인 순매수 상위
        top_foreign = df.nlargest(5, 'foreign_20d')[
            ['ticker', 'name', 'foreign_5d', 'foreign_20d']
        ].to_dict('records')

        # 기관 순매수 상위
        top_inst = df.nlargest(5, 'institution_20d')[
            ['ticker', 'name', 'institution_5d', 'institution_20d']
        ].to_dict('records')

        # 수급 선도 종목 (외국인+기관 동시 순매수)
        flow_leaders = df[
            (df['foreign_20d'] > 0) & (df['institution_20d'] > 0)
        ].nlargest(5, 'flow_score')[
            ['ticker', 'name', 'foreign_20d', 'institution_20d', 'flow_signal']
        ].to_dict('records')

        return {
            'summary': summary,
            'stocks': [r['result'] for r in results],
            'top_foreign_buy': top_foreign,
            'top_institution_buy': top_inst,
            'flow_leaders': flow_leaders
        }

    def _get_sector_signal(
        self,
        total_foreign: int,
        total_inst: int
    ) -> str:
        """섹터 전체 수급 신호"""
        threshold = self.config.institution_buy_threshold * 10  # 섹터는 10배 기준

        if total_foreign > threshold and total_inst > threshold:
            return '섹터매집'
        elif total_foreign < -threshold and total_inst < -threshold:
            return '섹터이탈'
        elif total_foreign > threshold:
            return '외국인유입'
        elif total_inst > threshold:
            return '기관유입'
        elif total_foreign < -threshold:
            return '외국인이탈'
        elif total_inst < -threshold:
            return '기관이탈'
        else:
            return '중립'


def format_money(value: int) -> str:
    """금액 포맷팅 (억원 단위)"""
    if abs(value) >= 100000000:  # 1억 이상
        return f"{value / 100000000:.1f}억"
    elif abs(value) >= 10000:  # 1만 이상
        return f"{value / 10000:.0f}만"
    else:
        return f"{value:,}"


# ============================================
# 실행 예시
# ============================================
if __name__ == "__main__":
    # 테스트용 더미 데이터 생성
    dates = pd.date_range(end=datetime.now(), periods=60)

    dummy_investor = pd.DataFrame({
        'foreign': np.random.randint(-10_000_000_000, 10_000_000_000, 60),
        'institution': np.random.randint(-5_000_000_000, 5_000_000_000, 60),
        'individual': np.random.randint(-10_000_000_000, 10_000_000_000, 60),
    }, index=dates)

    analyzer = InvestorFlowAnalyzer()

    # 수급 분석
    test_data = {
        'ticker': '277810',
        'name': '레인보우로보틱스',
        'investor': dummy_investor
    }

    result = analyzer.analyze_flow(test_data)

    print(f"종목: {result.name}")
    print(f"외국인 20일 순매수: {format_money(result.foreign_net_buy_20d)}")
    print(f"기관 20일 순매수: {format_money(result.institution_net_buy_20d)}")
    print(f"수급 신호: {result.flow_signal}")
    print(f"수급 스코어: {result.flow_score}")
