"""
데이터 수집 모듈
KRX, 네이버 금융, pykrx를 활용한 국내 주식 데이터 수집
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
import json
import time
import warnings
warnings.filterwarnings('ignore')

try:
    from pykrx import stock
except ImportError:
    stock = None
    print("Warning: pykrx not installed. Some features may not work.")

from .config import (
    ROBOT_CORE_STOCKS, ROBOT_ETFS,
    DEFAULT_CONFIG, get_analysis_period
)


class KRXDataCollector:
    """KRX/pykrx 기반 데이터 수집기"""

    def __init__(self):
        self.cache = {}

    def get_stock_price(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        주가 데이터 조회 (pykrx 활용)

        Args:
            ticker: 종목코드 (6자리)
            start_date: 시작일 (YYYYMMDD)
            end_date: 종료일 (YYYYMMDD)

        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"price_{ticker}_{start_date}_{end_date}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if stock is None:
            return pd.DataFrame()

        try:
            df = stock.get_market_ohlcv(start_date, end_date, ticker)
            df = df.reset_index()
            df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'value', 'change']
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')

            self.cache[cache_key] = df
            time.sleep(0.1)  # API 제한 방지
            return df
        except Exception as e:
            print(f"Error fetching price for {ticker}: {e}")
            return pd.DataFrame()

    def get_fundamental_data(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        기본적 분석 데이터 조회 (PER, PBR, 배당수익률 등)
        """
        if stock is None:
            return pd.DataFrame()

        try:
            df = stock.get_market_fundamental(start_date, end_date, ticker)
            df = df.reset_index()
            df.columns = ['date', 'bps', 'per', 'pbr', 'eps', 'div', 'dps']
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            time.sleep(0.1)
            return df
        except Exception as e:
            print(f"Error fetching fundamental for {ticker}: {e}")
            return pd.DataFrame()

    def get_investor_trading(
        self,
        ticker: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        투자자별 매매동향 조회 (외국인, 기관)
        """
        if stock is None:
            return pd.DataFrame()

        try:
            df = stock.get_market_trading_value_by_date(
                start_date, end_date, ticker,
                detail=True
            )
            df = df.reset_index()
            df['date'] = pd.to_datetime(df['날짜'])
            df = df.set_index('date')

            # 컬럼 정리
            columns_map = {
                '기관합계': 'institution',
                '기타법인': 'corp',
                '개인': 'individual',
                '외국인합계': 'foreign',
            }

            result = pd.DataFrame(index=df.index)
            for old_col, new_col in columns_map.items():
                if old_col in df.columns:
                    result[new_col] = df[old_col]

            time.sleep(0.1)
            return result
        except Exception as e:
            print(f"Error fetching investor trading for {ticker}: {e}")
            return pd.DataFrame()

    def get_market_cap(self, ticker: str, date: str) -> Optional[int]:
        """시가총액 조회"""
        if stock is None:
            return None

        try:
            df = stock.get_market_cap(date, date, ticker)
            if not df.empty:
                return df['시가총액'].iloc[0]
        except:
            pass
        return None

    def get_all_stock_list(self, market: str = "ALL", date: str = None) -> pd.DataFrame:
        """
        전체 종목 리스트 조회

        Args:
            market: KOSPI, KOSDAQ, or ALL
            date: 조회 기준일
        """
        if stock is None:
            return pd.DataFrame()

        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        try:
            if market == "ALL":
                kospi = stock.get_market_ticker_list(date, market="KOSPI")
                kosdaq = stock.get_market_ticker_list(date, market="KOSDAQ")
                tickers = list(set(kospi + kosdaq))
            else:
                tickers = stock.get_market_ticker_list(date, market=market)

            # 종목명 가져오기
            data = []
            for ticker in tickers:
                try:
                    name = stock.get_market_ticker_name(ticker)
                    data.append({'ticker': ticker, 'name': name})
                except:
                    pass

            return pd.DataFrame(data)
        except Exception as e:
            print(f"Error fetching stock list: {e}")
            return pd.DataFrame()


class NaverFinanceCollector:
    """네이버 금융 데이터 수집기"""

    BASE_URL = "https://finance.naver.com"
    API_URL = "https://api.finance.naver.com"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_stock_info(self, ticker: str) -> Dict:
        """종목 기본 정보 조회"""
        try:
            url = f"{self.API_URL}/service/itemSummary.naver"
            params = {'itemcode': ticker}
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching stock info for {ticker}: {e}")
        return {}

    def get_consensus(self, ticker: str) -> Dict:
        """
        증권사 컨센서스 데이터 조회
        (목표주가, 투자의견 등)
        """
        try:
            url = f"{self.BASE_URL}/item/coinfo.naver"
            params = {'code': ticker, 'target': 'consensus'}
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                # HTML 파싱 로직 (간소화)
                return {
                    'target_price': None,
                    'opinion': None,
                    'analysts_count': 0
                }
        except Exception as e:
            print(f"Error fetching consensus for {ticker}: {e}")
        return {}

    def get_news_sentiment(self, keyword: str, days: int = 7) -> Dict:
        """
        뉴스 검색 및 간단한 센티먼트 분석

        Args:
            keyword: 검색 키워드
            days: 최근 N일
        """
        positive_words = ['상승', '호재', '성장', '기대', '매수', '확대', '개선', '수주']
        negative_words = ['하락', '악재', '감소', '우려', '매도', '축소', '악화', '손실']

        try:
            # 네이버 뉴스 검색 API 대신 간단한 집계
            return {
                'keyword': keyword,
                'period_days': days,
                'positive_ratio': 0.5,  # 실제 구현시 뉴스 분석 결과
                'negative_ratio': 0.3,
                'neutral_ratio': 0.2,
                'total_articles': 0
            }
        except:
            return {}


class DataAggregator:
    """데이터 통합 및 전처리"""

    def __init__(self):
        self.krx = KRXDataCollector()
        self.naver = NaverFinanceCollector()

    def collect_stock_data(
        self,
        ticker: str,
        lookback_days: int = 252
    ) -> Dict:
        """
        종목별 전체 데이터 수집

        Returns:
            {
                'price': DataFrame,
                'fundamental': DataFrame,
                'investor': DataFrame,
                'info': Dict,
                'market_cap': int
            }
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        result = {
            'ticker': ticker,
            'price': self.krx.get_stock_price(ticker, start_str, end_str),
            'fundamental': self.krx.get_fundamental_data(ticker, start_str, end_str),
            'investor': self.krx.get_investor_trading(ticker, start_str, end_str),
            'info': self.naver.get_stock_info(ticker),
            'market_cap': self.krx.get_market_cap(ticker, end_str),
        }

        return result

    def collect_sector_data(
        self,
        stocks: Dict[str, dict],
        lookback_days: int = 252
    ) -> Dict[str, Dict]:
        """
        섹터 전체 종목 데이터 수집

        Args:
            stocks: {ticker: info_dict} 형태의 종목 딕셔너리
        """
        all_data = {}
        total = len(stocks)

        for idx, (ticker, info) in enumerate(stocks.items(), 1):
            print(f"[{idx}/{total}] Collecting {info['name']} ({ticker})...")

            try:
                data = self.collect_stock_data(ticker, lookback_days)
                data['name'] = info['name']
                data['category'] = info.get('category', 'Unknown')
                data['market'] = info.get('market', 'Unknown')
                all_data[ticker] = data
            except Exception as e:
                print(f"  Error: {e}")
                continue

            time.sleep(0.2)  # API 제한 방지

        return all_data

    def collect_etf_data(
        self,
        etfs: Dict[str, dict],
        lookback_days: int = 252
    ) -> Dict[str, Dict]:
        """ETF 데이터 수집"""
        all_data = {}

        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)

        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")

        for ticker, info in etfs.items():
            print(f"Collecting ETF: {info['name']} ({ticker})...")

            try:
                data = {
                    'ticker': ticker,
                    'name': info['name'],
                    'type': info['type'],
                    'price': self.krx.get_stock_price(ticker, start_str, end_str),
                }
                all_data[ticker] = data
            except Exception as e:
                print(f"  Error: {e}")

            time.sleep(0.2)

        return all_data


# ============================================
# 실행 예시
# ============================================
if __name__ == "__main__":
    aggregator = DataAggregator()

    # 단일 종목 테스트
    test_data = aggregator.collect_stock_data("277810")  # 레인보우로보틱스

    print("\n=== Price Data ===")
    print(test_data['price'].tail())

    print("\n=== Fundamental Data ===")
    print(test_data['fundamental'].tail())

    print("\n=== Investor Trading ===")
    print(test_data['investor'].tail())
