#!/usr/bin/env python3
"""
데모 리포트 생성 스크립트
실제 API 호출 없이 더미 데이터로 리포트 생성
"""
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import ROBOT_CORE_STOCKS, ROBOT_ETFS
from src.analyzer import StockAnalysisResult, ComprehensiveAnalyzer
from src.flow_analyzer import FlowAnalysisResult
from src.report_generator import ReportGenerator


def generate_demo_price_data(days: int = 252) -> pd.DataFrame:
    """더미 주가 데이터 생성"""
    dates = pd.date_range(end=datetime.now(), periods=days)
    base_price = random.uniform(10000, 100000)

    # 랜덤 워크로 가격 생성
    returns = np.random.normal(0.0005, 0.02, days)
    prices = base_price * np.cumprod(1 + returns)

    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.uniform(-0.01, 0.01, days)),
        'high': prices * (1 + np.random.uniform(0, 0.03, days)),
        'low': prices * (1 - np.random.uniform(0, 0.03, days)),
        'close': prices,
        'volume': np.random.randint(100000, 10000000, days),
    })
    df = df.set_index('date')
    return df


def generate_demo_stock_data():
    """더미 종목 데이터 생성"""
    stock_data = {}

    for ticker, info in ROBOT_CORE_STOCKS.items():
        price_df = generate_demo_price_data()
        current_price = price_df['close'].iloc[-1]

        # 수익률 계산
        returns = {}
        if len(price_df) >= 2:
            returns['1d'] = (current_price / price_df['close'].iloc[-2] - 1) * 100
        if len(price_df) >= 20:
            returns['1m'] = (current_price / price_df['close'].iloc[-20] - 1) * 100
        if len(price_df) >= 60:
            returns['3m'] = (current_price / price_df['close'].iloc[-60] - 1) * 100

        # RSI 계산
        delta = price_df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # 이동평균 신호
        ma20 = price_df['close'].rolling(20).mean().iloc[-1]
        ma60 = price_df['close'].rolling(60).mean().iloc[-1]
        ma120 = price_df['close'].rolling(120).mean().iloc[-1]

        if current_price > ma20 > ma60 > ma120:
            ma_signal = '강한상승추세'
        elif current_price > ma20 > ma60:
            ma_signal = '상승추세'
        elif current_price > ma20:
            ma_signal = '단기상승'
        elif current_price < ma20 < ma60 < ma120:
            ma_signal = '강한하락추세'
        elif current_price < ma20 < ma60:
            ma_signal = '하락추세'
        elif current_price < ma20:
            ma_signal = '단기하락'
        else:
            ma_signal = '중립'

        # 투자 스코어
        score = 50 + random.uniform(-30, 30)
        if score >= 70:
            rating = '매수'
        elif score >= 40:
            rating = '중립'
        else:
            rating = '매도'

        stock_data[ticker] = {
            'ticker': ticker,
            'name': info['name'],
            'category': info.get('category', 'Unknown'),
            'market': info.get('market', 'Unknown'),
            'price': price_df,
            'current_price': current_price,
            'price_change_1d': returns.get('1d', 0),
            'price_change_1m': returns.get('1m', 0),
            'price_change_3m': returns.get('3m', 0),
            'per': random.uniform(10, 50),
            'pbr': random.uniform(0.5, 8),
            'rsi': rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50,
            'ma_signal': ma_signal,
            'volume_trend': random.choice(['증가', '감소', '평균']),
            'score': score,
            'rating': rating,
            'market_cap': random.randint(100000000000, 50000000000000),
            # 수급 데이터
            'foreign_5d': random.randint(-10000000000, 10000000000),
            'foreign_20d': random.randint(-30000000000, 30000000000),
            'institution_5d': random.randint(-5000000000, 5000000000),
            'institution_20d': random.randint(-15000000000, 15000000000),
        }

    return stock_data


def generate_demo_sector_analysis(stock_data: dict) -> dict:
    """더미 섹터 분석 결과 생성"""
    stocks = []

    for ticker, data in stock_data.items():
        stock = StockAnalysisResult(
            ticker=data['ticker'],
            name=data['name'],
            current_price=data['current_price'],
            price_change_1d=data['price_change_1d'],
            price_change_1m=data['price_change_1m'],
            price_change_3m=data['price_change_3m'],
            price_change_ytd=random.uniform(-20, 30),
            per=data['per'],
            pbr=data['pbr'],
            market_cap=data['market_cap'],
            rsi=data['rsi'],
            ma_signal=data['ma_signal'],
            volume_trend=data['volume_trend'],
            score=data['score'],
            rating=data['rating']
        )
        stocks.append(stock)

    # 스코어 기준 정렬
    stocks_sorted = sorted(stocks, key=lambda x: x.score, reverse=True)

    # 요약 통계
    scores = [s.score for s in stocks]
    returns_1m = [s.price_change_1m for s in stocks]
    total_market_cap = sum([s.market_cap for s in stocks if s.market_cap])

    summary = {
        'total_stocks': len(stocks),
        'total_market_cap': total_market_cap,
        'avg_score': np.mean(scores),
        'avg_return_1m': np.mean(returns_1m),
        'buy_count': len([s for s in stocks if s.rating == '매수']),
        'hold_count': len([s for s in stocks if s.rating == '중립']),
        'sell_count': len([s for s in stocks if s.rating == '매도']),
    }

    return {
        'summary': summary,
        'stocks': stocks_sorted,
        'top_picks': stocks_sorted[:5],
        'watchlist': stocks_sorted[5:10],
    }


def generate_demo_flow_analysis(stock_data: dict) -> dict:
    """더미 수급 분석 결과 생성"""
    stocks_list = []

    for ticker, data in stock_data.items():
        stocks_list.append({
            'ticker': ticker,
            'name': data['name'],
            'foreign_5d': data['foreign_5d'],
            'foreign_20d': data['foreign_20d'],
            'institution_5d': data['institution_5d'],
            'institution_20d': data['institution_20d'],
            'flow_signal': random.choice(['매집', '차익실현', '외국인주도', '기관주도', '중립']),
        })

    df = pd.DataFrame(stocks_list)

    # 외국인 순매수 상위
    top_foreign = df.nlargest(5, 'foreign_20d')[
        ['ticker', 'name', 'foreign_5d', 'foreign_20d']
    ].to_dict('records')

    # 기관 순매수 상위
    top_inst = df.nlargest(5, 'institution_20d')[
        ['ticker', 'name', 'institution_5d', 'institution_20d']
    ].to_dict('records')

    # 수급 선도 종목
    flow_leaders = df[
        (df['foreign_20d'] > 0) & (df['institution_20d'] > 0)
    ].head(5)[
        ['ticker', 'name', 'foreign_20d', 'institution_20d', 'flow_signal']
    ].to_dict('records')

    return {
        'summary': {
            'total_foreign_net_buy_20d': df['foreign_20d'].sum(),
            'total_institution_net_buy_20d': df['institution_20d'].sum(),
            'sector_flow_signal': random.choice(['섹터매집', '외국인유입', '기관유입', '중립']),
            'accumulation_count': len(df[df['flow_signal'] == '매집']),
        },
        'stocks': [],
        'top_foreign_buy': top_foreign,
        'top_institution_buy': top_inst,
        'flow_leaders': flow_leaders,
    }


def generate_demo_etf_data() -> dict:
    """더미 ETF 데이터 생성"""
    etf_data = {}

    for ticker, info in ROBOT_ETFS.items():
        price_df = generate_demo_price_data(120)

        etf_data[ticker] = {
            'ticker': ticker,
            'name': info['name'],
            'type': info['type'],
            'price': price_df,
        }

    return etf_data


def main():
    """데모 리포트 생성"""
    print("=" * 60)
    print("🤖 데모 리포트 생성 시작")
    print("=" * 60)

    # 1. 더미 데이터 생성
    print("\n📊 더미 데이터 생성 중...")
    stock_data = generate_demo_stock_data()
    print(f"   ✓ {len(stock_data)}개 종목 데이터 생성 완료")

    # 2. 분석 결과 생성
    print("\n📈 분석 결과 생성 중...")
    sector_analysis = generate_demo_sector_analysis(stock_data)
    flow_analysis = generate_demo_flow_analysis(stock_data)
    etf_data = generate_demo_etf_data()
    print("   ✓ 분석 완료")

    # 3. 리포트 생성
    print("\n📝 HTML 리포트 생성 중...")
    generator = ReportGenerator()

    output_dir = Path("reports")
    output_dir.mkdir(exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    output_path = output_dir / f"robot_sector_report_DEMO_{date_str}.html"

    html = generator.generate_html(
        sector_analysis,
        flow_analysis,
        etf_data,
        output_path=str(output_path)
    )

    print(f"   ✓ 리포트 저장: {output_path}")

    # 4. 완료 요약
    print("\n" + "=" * 60)
    print("✅ 데모 리포트 생성 완료!")
    print("=" * 60)
    print(f"\n📄 리포트 위치: {output_path.absolute()}")

    summary = sector_analysis['summary']
    print(f"\n📊 분석 요약:")
    print(f"   - 분석 종목: {summary['total_stocks']}개")
    print(f"   - 평균 스코어: {summary['avg_score']:.1f}")
    print(f"   - 매수 의견: {summary['buy_count']}개")
    print(f"   - 중립 의견: {summary['hold_count']}개")
    print(f"   - 매도 의견: {summary['sell_count']}개")

    print(f"\n🏆 Top 5 추천 종목:")
    for i, stock in enumerate(sector_analysis['top_picks'][:5], 1):
        print(f"   {i}. {stock.name} (점수: {stock.score:.0f}, 의견: {stock.rating})")

    return str(output_path)


if __name__ == "__main__":
    main()
