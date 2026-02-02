"""
재무 및 기술적 분석 모듈
펀드매니저 관점의 종합 분석
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
class StockAnalysisResult:
    """종목 분석 결과 데이터클래스"""
    ticker: str
    name: str

    # 가격 정보
    current_price: float
    price_change_1d: float
    price_change_1m: float
    price_change_3m: float
    price_change_ytd: float

    # 밸류에이션
    per: Optional[float]
    pbr: Optional[float]
    market_cap: Optional[int]

    # 기술적 지표
    rsi: Optional[float]
    ma_signal: str  # "상승추세", "하락추세", "중립"
    volume_trend: str  # "증가", "감소", "평균"

    # 투자의견
    score: float  # 0-100
    rating: str  # "매수", "중립", "매도"


class TechnicalAnalyzer:
    """기술적 분석기"""

    def __init__(self, config: AnalysisConfig = None):
        self.config = config or DEFAULT_CONFIG

    def calculate_returns(self, prices: pd.Series) -> Dict[str, float]:
        """수익률 계산"""
        if prices.empty or len(prices) < 2:
            return {}

        current = prices.iloc[-1]
        returns = {}

        # 1일 수익률
        if len(prices) >= 2:
            returns['1d'] = (current / prices.iloc[-2] - 1) * 100

        # 1주 수익률
        if len(prices) >= 5:
            returns['1w'] = (current / prices.iloc[-5] - 1) * 100

        # 1개월 수익률
        if len(prices) >= 20:
            returns['1m'] = (current / prices.iloc[-20] - 1) * 100

        # 3개월 수익률
        if len(prices) >= 60:
            returns['3m'] = (current / prices.iloc[-60] - 1) * 100

        # 6개월 수익률
        if len(prices) >= 120:
            returns['6m'] = (current / prices.iloc[-120] - 1) * 100

        # 1년 수익률
        if len(prices) >= 252:
            returns['1y'] = (current / prices.iloc[-252] - 1) * 100

        # YTD 수익률
        try:
            year_start = prices[prices.index.year == datetime.now().year].iloc[0]
            returns['ytd'] = (current / year_start - 1) * 100
        except:
            returns['ytd'] = None

        return returns

    def calculate_moving_averages(
        self,
        prices: pd.Series,
        periods: List[int] = None
    ) -> pd.DataFrame:
        """이동평균 계산"""
        if periods is None:
            periods = self.config.ma_periods

        mas = pd.DataFrame(index=prices.index)

        for period in periods:
            mas[f'MA{period}'] = prices.rolling(window=period).mean()

        return mas

    def calculate_rsi(
        self,
        prices: pd.Series,
        period: int = None
    ) -> pd.Series:
        """RSI 계산"""
        if period is None:
            period = self.config.rsi_period

        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_bollinger_bands(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.DataFrame:
        """볼린저 밴드 계산"""
        ma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        bb = pd.DataFrame(index=prices.index)
        bb['middle'] = ma
        bb['upper'] = ma + (std * std_dev)
        bb['lower'] = ma - (std * std_dev)
        bb['bandwidth'] = (bb['upper'] - bb['lower']) / bb['middle'] * 100

        return bb

    def calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> pd.DataFrame:
        """MACD 계산"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()

        macd = pd.DataFrame(index=prices.index)
        macd['macd'] = exp1 - exp2
        macd['signal'] = macd['macd'].ewm(span=signal, adjust=False).mean()
        macd['histogram'] = macd['macd'] - macd['signal']

        return macd

    def get_trend_signal(self, prices: pd.Series) -> Dict:
        """추세 신호 판단"""
        if len(prices) < 120:
            return {'signal': '데이터부족', 'strength': 0}

        current = prices.iloc[-1]
        ma20 = prices.rolling(20).mean().iloc[-1]
        ma60 = prices.rolling(60).mean().iloc[-1]
        ma120 = prices.rolling(120).mean().iloc[-1]

        # 정배열/역배열 판단
        if current > ma20 > ma60 > ma120:
            return {'signal': '강한상승추세', 'strength': 3}
        elif current > ma20 > ma60:
            return {'signal': '상승추세', 'strength': 2}
        elif current > ma20:
            return {'signal': '단기상승', 'strength': 1}
        elif current < ma20 < ma60 < ma120:
            return {'signal': '강한하락추세', 'strength': -3}
        elif current < ma20 < ma60:
            return {'signal': '하락추세', 'strength': -2}
        elif current < ma20:
            return {'signal': '단기하락', 'strength': -1}
        else:
            return {'signal': '중립', 'strength': 0}

    def get_volume_signal(
        self,
        volume: pd.Series,
        lookback: int = 20
    ) -> Dict:
        """거래량 신호 판단"""
        if len(volume) < lookback:
            return {'signal': '데이터부족', 'ratio': 1.0}

        recent_avg = volume.iloc[-5:].mean()
        historical_avg = volume.iloc[-lookback:-5].mean()

        ratio = recent_avg / historical_avg if historical_avg > 0 else 1.0

        if ratio > 2.0:
            signal = '급증'
        elif ratio > 1.5:
            signal = '증가'
        elif ratio > 0.7:
            signal = '평균'
        else:
            signal = '감소'

        return {'signal': signal, 'ratio': ratio}


class FundamentalAnalyzer:
    """기본적 분석기"""

    def __init__(self, config: AnalysisConfig = None):
        self.config = config or DEFAULT_CONFIG

    def analyze_valuation(
        self,
        per: Optional[float],
        pbr: Optional[float],
        eps_growth: Optional[float] = None
    ) -> Dict:
        """밸류에이션 분석"""
        result = {
            'per_grade': None,
            'pbr_grade': None,
            'overall_grade': None,
            'comment': ''
        }

        # PER 평가
        if per is not None and per > 0:
            if per < self.config.per_threshold_low:
                result['per_grade'] = '저평가'
            elif per > self.config.per_threshold_high:
                result['per_grade'] = '고평가'
            else:
                result['per_grade'] = '적정'

        # PBR 평가
        if pbr is not None and pbr > 0:
            if pbr < 1.0:
                result['pbr_grade'] = '저평가'
            elif pbr > self.config.pbr_threshold:
                result['pbr_grade'] = '고평가'
            else:
                result['pbr_grade'] = '적정'

        # 종합 평가
        grades = [result['per_grade'], result['pbr_grade']]
        grades = [g for g in grades if g is not None]

        if not grades:
            result['overall_grade'] = '판단불가'
        elif all(g == '저평가' for g in grades):
            result['overall_grade'] = '저평가'
        elif all(g == '고평가' for g in grades):
            result['overall_grade'] = '고평가'
        else:
            result['overall_grade'] = '적정'

        return result

    def calculate_growth_metrics(
        self,
        revenue: pd.Series,
        operating_profit: pd.Series
    ) -> Dict:
        """성장성 지표 계산"""
        result = {
            'revenue_growth_yoy': None,
            'op_growth_yoy': None,
            'revenue_cagr_3y': None
        }

        if len(revenue) >= 2:
            result['revenue_growth_yoy'] = (
                revenue.iloc[-1] / revenue.iloc[-2] - 1
            ) * 100 if revenue.iloc[-2] != 0 else None

        if len(operating_profit) >= 2:
            result['op_growth_yoy'] = (
                operating_profit.iloc[-1] / operating_profit.iloc[-2] - 1
            ) * 100 if operating_profit.iloc[-2] != 0 else None

        if len(revenue) >= 4:
            start = revenue.iloc[-4]
            end = revenue.iloc[-1]
            if start > 0 and end > 0:
                result['revenue_cagr_3y'] = (
                    (end / start) ** (1/3) - 1
                ) * 100

        return result


class ComprehensiveAnalyzer:
    """종합 분석기 (기술적 + 기본적)"""

    def __init__(self, config: AnalysisConfig = None):
        self.config = config or DEFAULT_CONFIG
        self.technical = TechnicalAnalyzer(config)
        self.fundamental = FundamentalAnalyzer(config)

    def analyze_stock(self, stock_data: Dict) -> StockAnalysisResult:
        """
        종목 종합 분석

        Args:
            stock_data: DataAggregator에서 수집한 데이터

        Returns:
            StockAnalysisResult
        """
        ticker = stock_data.get('ticker', '')
        name = stock_data.get('name', '')

        price_df = stock_data.get('price', pd.DataFrame())
        fundamental_df = stock_data.get('fundamental', pd.DataFrame())

        # 가격 정보
        current_price = 0
        returns = {}

        if not price_df.empty and 'close' in price_df.columns:
            prices = price_df['close']
            current_price = prices.iloc[-1]
            returns = self.technical.calculate_returns(prices)

        # 밸류에이션
        per = None
        pbr = None

        if not fundamental_df.empty:
            if 'per' in fundamental_df.columns:
                per = fundamental_df['per'].iloc[-1]
            if 'pbr' in fundamental_df.columns:
                pbr = fundamental_df['pbr'].iloc[-1]

        # 기술적 지표
        rsi = None
        ma_signal = '데이터부족'
        volume_trend = '데이터부족'

        if not price_df.empty and 'close' in price_df.columns:
            rsi_series = self.technical.calculate_rsi(prices)
            if not rsi_series.empty:
                rsi = rsi_series.iloc[-1]

            trend = self.technical.get_trend_signal(prices)
            ma_signal = trend['signal']

            if 'volume' in price_df.columns:
                vol_signal = self.technical.get_volume_signal(price_df['volume'])
                volume_trend = vol_signal['signal']

        # 투자 스코어 계산
        score, rating = self._calculate_investment_score(
            returns, per, pbr, rsi, ma_signal, volume_trend
        )

        return StockAnalysisResult(
            ticker=ticker,
            name=name,
            current_price=current_price,
            price_change_1d=returns.get('1d', 0),
            price_change_1m=returns.get('1m', 0),
            price_change_3m=returns.get('3m', 0),
            price_change_ytd=returns.get('ytd', 0),
            per=per,
            pbr=pbr,
            market_cap=stock_data.get('market_cap'),
            rsi=rsi,
            ma_signal=ma_signal,
            volume_trend=volume_trend,
            score=score,
            rating=rating
        )

    def _calculate_investment_score(
        self,
        returns: Dict,
        per: Optional[float],
        pbr: Optional[float],
        rsi: Optional[float],
        ma_signal: str,
        volume_trend: str
    ) -> Tuple[float, str]:
        """투자 스코어 계산 (0-100)"""
        score = 50  # 기본 점수

        # 수익률 기반 점수 (모멘텀)
        if returns.get('1m', 0) > 10:
            score += 10
        elif returns.get('1m', 0) > 5:
            score += 5
        elif returns.get('1m', 0) < -10:
            score -= 10
        elif returns.get('1m', 0) < -5:
            score -= 5

        # 밸류에이션 기반 점수
        if per is not None and 0 < per < 15:
            score += 10
        elif per is not None and per > 50:
            score -= 10

        if pbr is not None and 0 < pbr < 1:
            score += 5
        elif pbr is not None and pbr > 5:
            score -= 5

        # RSI 기반 점수
        if rsi is not None:
            if 30 <= rsi <= 70:
                score += 5
            elif rsi < 30:  # 과매도
                score += 10
            elif rsi > 70:  # 과매수
                score -= 5

        # 추세 기반 점수
        trend_scores = {
            '강한상승추세': 15,
            '상승추세': 10,
            '단기상승': 5,
            '중립': 0,
            '단기하락': -5,
            '하락추세': -10,
            '강한하락추세': -15,
        }
        score += trend_scores.get(ma_signal, 0)

        # 거래량 기반 점수
        if volume_trend == '급증':
            score += 5
        elif volume_trend == '증가':
            score += 2

        # 점수 범위 제한
        score = max(0, min(100, score))

        # 등급 결정
        if score >= 70:
            rating = '매수'
        elif score >= 40:
            rating = '중립'
        else:
            rating = '매도'

        return score, rating

    def analyze_sector(
        self,
        sector_data: Dict[str, Dict]
    ) -> Dict:
        """
        섹터 전체 분석

        Returns:
            {
                'summary': {...},
                'stocks': [StockAnalysisResult, ...],
                'top_picks': [...],
                'watchlist': [...]
            }
        """
        results = []
        total_market_cap = 0

        for ticker, data in sector_data.items():
            try:
                result = self.analyze_stock(data)
                results.append(result)

                if result.market_cap:
                    total_market_cap += result.market_cap
            except Exception as e:
                print(f"Error analyzing {ticker}: {e}")

        # 정렬
        results_sorted = sorted(results, key=lambda x: x.score, reverse=True)

        # 섹터 요약
        scores = [r.score for r in results]
        returns_1m = [r.price_change_1m for r in results if r.price_change_1m]

        summary = {
            'total_stocks': len(results),
            'total_market_cap': total_market_cap,
            'avg_score': np.mean(scores) if scores else 0,
            'avg_return_1m': np.mean(returns_1m) if returns_1m else 0,
            'buy_count': len([r for r in results if r.rating == '매수']),
            'hold_count': len([r for r in results if r.rating == '중립']),
            'sell_count': len([r for r in results if r.rating == '매도']),
        }

        # Top Picks (상위 5종목)
        top_picks = results_sorted[:5]

        # Watchlist (점수 향상 중인 종목)
        watchlist = [r for r in results_sorted if 40 <= r.score < 70][:5]

        return {
            'summary': summary,
            'stocks': results_sorted,
            'top_picks': top_picks,
            'watchlist': watchlist
        }


# ============================================
# 실행 예시
# ============================================
if __name__ == "__main__":
    analyzer = ComprehensiveAnalyzer()

    # 테스트용 더미 데이터
    test_prices = pd.Series(
        np.random.randn(252).cumsum() + 50000,
        index=pd.date_range(end=datetime.now(), periods=252)
    )

    # 수익률 계산
    returns = analyzer.technical.calculate_returns(test_prices)
    print("Returns:", returns)

    # RSI 계산
    rsi = analyzer.technical.calculate_rsi(test_prices)
    print(f"Current RSI: {rsi.iloc[-1]:.2f}")

    # 추세 신호
    trend = analyzer.technical.get_trend_signal(test_prices)
    print(f"Trend Signal: {trend}")
