"""
리포트 생성 모듈
Jinja2 기반 HTML 리포트 생성
"""
import os
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
except ImportError:
    print("Warning: jinja2 not installed. Run: pip install jinja2")
    Environment = None
    FileSystemLoader = None

from .config import REPORT_CONFIG
from .analyzer import StockAnalysisResult


def format_price(value: float) -> str:
    """가격 포맷팅"""
    if value is None:
        return '-'
    return f"{value:,.0f}"


def format_money(value: int) -> str:
    """금액 포맷팅 (억원 단위)"""
    if value is None:
        return '-'
    if abs(value) >= 100000000000:  # 1000억 이상
        return f"{value / 100000000000:.1f}천억"
    elif abs(value) >= 100000000:  # 1억 이상
        return f"{value / 100000000:.1f}억"
    elif abs(value) >= 10000:  # 1만 이상
        return f"{value / 10000:.0f}만"
    else:
        return f"{value:,}"


class ReportGenerator:
    """HTML 리포트 생성기"""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = Path(__file__).parent.parent / "templates"

        self.template_dir = template_dir

        if Environment and FileSystemLoader:
            self.env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=True
            )
            # 커스텀 필터 등록
            self.env.filters['format_price'] = format_price
            self.env.filters['format_money'] = format_money
            self.env.filters['round'] = lambda x, n: round(x, n) if x is not None else None
        else:
            self.env = None

    def prepare_report_data(
        self,
        sector_analysis: Dict,
        flow_analysis: Dict,
        etf_data: Dict = None
    ) -> Dict[str, Any]:
        """
        리포트 템플릿용 데이터 준비

        Args:
            sector_analysis: ComprehensiveAnalyzer의 analyze_sector 결과
            flow_analysis: SectorFlowAnalyzer의 analyze_sector_flow 결과
            etf_data: ETF 분석 데이터

        Returns:
            템플릿 렌더링용 딕셔너리
        """
        now = datetime.now()
        summary = sector_analysis.get('summary', {})
        flow_summary = flow_analysis.get('summary', {})

        # 주식 분석 결과를 딕셔너리로 변환
        all_stocks = []
        for stock in sector_analysis.get('stocks', []):
            if isinstance(stock, StockAnalysisResult):
                all_stocks.append({
                    'ticker': stock.ticker,
                    'name': stock.name,
                    'current_price': stock.current_price,
                    'price_change_1d': stock.price_change_1d or 0,
                    'price_change_1m': stock.price_change_1m or 0,
                    'price_change_3m': stock.price_change_3m or 0,
                    'per': stock.per,
                    'pbr': stock.pbr,
                    'rsi': stock.rsi,
                    'ma_signal': stock.ma_signal,
                    'volume_trend': stock.volume_trend,
                    'score': stock.score,
                    'rating': stock.rating,
                })
            else:
                all_stocks.append(stock)

        # Top Picks
        top_picks = all_stocks[:5]

        # 섹터 수익률 계산
        returns_1m = [s['price_change_1m'] for s in all_stocks if s.get('price_change_1m')]
        avg_return_1m = sum(returns_1m) / len(returns_1m) if returns_1m else 0

        # 섹터 심리 판단
        if avg_return_1m > 5:
            sector_sentiment = "강세"
            sentiment_color = "#38a169"
        elif avg_return_1m > 0:
            sector_sentiment = "약세 강세"
            sentiment_color = "#68d391"
        elif avg_return_1m > -5:
            sector_sentiment = "약세"
            sentiment_color = "#ed8936"
        else:
            sector_sentiment = "강한 약세"
            sentiment_color = "#e53e3e"

        # RSI 기반 과매수/과매도 종목
        oversold = [s for s in all_stocks if s.get('rsi') and s['rsi'] < 30]
        overbought = [s for s in all_stocks if s.get('rsi') and s['rsi'] > 70]

        # 정배열 종목
        golden_cross = [s for s in all_stocks if '상승' in s.get('ma_signal', '')]

        # 추세 분포 계산
        trend_counts = {
            '강한상승추세': 0, '상승추세': 0, '단기상승': 0,
            '중립': 0, '데이터부족': 0,
            '단기하락': 0, '하락추세': 0, '강한하락추세': 0
        }
        for s in all_stocks:
            signal = s.get('ma_signal', '데이터부족')
            if signal in trend_counts:
                trend_counts[signal] += 1

        trend_distribution = [
            trend_counts.get('강한상승추세', 0),
            trend_counts.get('상승추세', 0),
            trend_counts.get('단기상승', 0),
            trend_counts.get('중립', 0) + trend_counts.get('데이터부족', 0),
            trend_counts.get('단기하락', 0),
            trend_counts.get('하락추세', 0),
            trend_counts.get('강한하락추세', 0),
        ]

        # 카테고리 분포 (더미 데이터 - 실제 구현시 수정 필요)
        category_labels = ['휴머노이드', '협동로봇', '물류자동화', '로봇부품', '대기업', '기타']
        category_values = [3, 5, 4, 6, 5, 2]

        # 성과 추이 (더미 데이터)
        import random
        performance_dates = [
            (now.replace(day=1) - __import__('datetime').timedelta(days=30*i)).strftime('%Y-%m')
            for i in range(6)
        ][::-1]
        performance_values = [100]
        for _ in range(5):
            performance_values.append(performance_values[-1] * (1 + random.uniform(-0.05, 0.08)))

        # 수급 데이터
        flow_dates = [
            (now - __import__('datetime').timedelta(days=i*5)).strftime('%m/%d')
            for i in range(4)
        ][::-1]
        foreign_flow_values = [random.randint(-500, 500) for _ in range(4)]
        institution_flow_values = [random.randint(-300, 300) for _ in range(4)]

        # ETF 데이터 준비
        etf_list = []
        if etf_data:
            for ticker, data in etf_data.items():
                price_df = data.get('price')
                if price_df is not None and not price_df.empty and 'close' in price_df.columns:
                    current = price_df['close'].iloc[-1]
                    return_1m = ((current / price_df['close'].iloc[-20]) - 1) * 100 if len(price_df) >= 20 else 0
                    return_3m = ((current / price_df['close'].iloc[-60]) - 1) * 100 if len(price_df) >= 60 else 0
                else:
                    current = 0
                    return_1m = 0
                    return_3m = 0

                etf_list.append({
                    'ticker': ticker,
                    'name': data.get('name', ''),
                    'type': data.get('type', ''),
                    'current_price': current,
                    'return_1m': return_1m,
                    'return_3m': return_3m,
                })

        # 수급 선도 종목
        flow_leaders = flow_analysis.get('flow_leaders', [])

        # 시가총액 (조 단위)
        total_market_cap = summary.get('total_market_cap', 0)
        market_cap_trillion = total_market_cap / 1000000000000 if total_market_cap else 0

        return {
            # 리포트 메타
            'report_title': REPORT_CONFIG['title'],
            'report_subtitle': REPORT_CONFIG['subtitle'],
            'author': REPORT_CONFIG['author'],
            'update_frequency': REPORT_CONFIG['update_frequency'],
            'report_date': now.strftime('%Y년 %m월 %d일'),
            'report_datetime': now.strftime('%Y-%m-%d %H:%M:%S'),

            # Executive Summary
            'total_stocks': summary.get('total_stocks', len(all_stocks)),
            'sector_return_1m': round(avg_return_1m, 2),
            'avg_score': round(summary.get('avg_score', 50), 1),
            'sector_flow': flow_summary.get('sector_flow_signal', '중립'),
            'buy_rating_count': summary.get('buy_count', 0),
            'total_market_cap_trillion': round(market_cap_trillion, 1),
            'sector_sentiment': sector_sentiment,
            'sector_sentiment_color': sentiment_color,

            # 종목 데이터
            'all_stocks': all_stocks,
            'top_picks': top_picks,
            'oversold_stocks': oversold[:5],
            'overbought_stocks': overbought[:5],
            'golden_cross_stocks': golden_cross[:5],

            # 수급 데이터
            'top_foreign_buy': flow_analysis.get('top_foreign_buy', []),
            'top_institution_buy': flow_analysis.get('top_institution_buy', []),
            'flow_leaders': flow_leaders,

            # ETF 데이터
            'etf_list': etf_list,

            # 차트 데이터 (JSON)
            'performance_dates': json.dumps(performance_dates),
            'performance_values': json.dumps([round(v, 2) for v in performance_values]),
            'category_labels': json.dumps(category_labels),
            'category_values': json.dumps(category_values),
            'trend_distribution': json.dumps(trend_distribution),
            'flow_dates': json.dumps(flow_dates),
            'foreign_flow_values': json.dumps(foreign_flow_values),
            'institution_flow_values': json.dumps(institution_flow_values),
        }

    def generate_html(
        self,
        sector_analysis: Dict,
        flow_analysis: Dict,
        etf_data: Dict = None,
        output_path: str = None
    ) -> str:
        """
        HTML 리포트 생성

        Args:
            sector_analysis: 섹터 분석 결과
            flow_analysis: 수급 분석 결과
            etf_data: ETF 데이터
            output_path: 출력 파일 경로

        Returns:
            생성된 HTML 문자열
        """
        if self.env is None:
            return "<html><body><h1>Error: jinja2 not installed</h1></body></html>"

        # 템플릿 데이터 준비
        data = self.prepare_report_data(sector_analysis, flow_analysis, etf_data)

        # 템플릿 렌더링
        template = self.env.get_template('report_template.html')
        html = template.render(**data)

        # 파일 저장
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html)

            print(f"Report saved to: {output_path}")

        return html

    def generate_json_data(
        self,
        sector_analysis: Dict,
        flow_analysis: Dict,
        etf_data: Dict = None,
        output_path: str = None
    ) -> Dict:
        """
        JSON 데이터 생성 (API용)
        """
        data = self.prepare_report_data(sector_analysis, flow_analysis, etf_data)

        # JSON 직렬화 불가능한 항목 제거
        json_data = {
            'meta': {
                'title': data['report_title'],
                'date': data['report_date'],
                'datetime': data['report_datetime'],
            },
            'summary': {
                'total_stocks': data['total_stocks'],
                'sector_return_1m': data['sector_return_1m'],
                'avg_score': data['avg_score'],
                'sector_flow': data['sector_flow'],
                'sentiment': data['sector_sentiment'],
            },
            'stocks': data['all_stocks'],
            'top_picks': data['top_picks'],
            'flow': {
                'top_foreign': data['top_foreign_buy'],
                'top_institution': data['top_institution_buy'],
                'leaders': data['flow_leaders'],
            },
            'etf': data['etf_list'],
        }

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)

            print(f"JSON data saved to: {output_path}")

        return json_data


# ============================================
# 실행 예시
# ============================================
if __name__ == "__main__":
    generator = ReportGenerator()

    # 더미 데이터로 테스트
    dummy_sector = {
        'summary': {
            'total_stocks': 20,
            'avg_score': 55,
            'buy_count': 8,
            'hold_count': 10,
            'sell_count': 2,
            'total_market_cap': 50000000000000,
        },
        'stocks': [
            {
                'ticker': '277810',
                'name': '레인보우로보틱스',
                'current_price': 50000,
                'price_change_1d': 2.5,
                'price_change_1m': 15.3,
                'price_change_3m': -5.2,
                'per': 45.2,
                'pbr': 8.5,
                'rsi': 65,
                'ma_signal': '상승추세',
                'volume_trend': '증가',
                'score': 72,
                'rating': '매수',
            }
        ] * 5,
        'top_picks': [],
    }

    dummy_flow = {
        'summary': {
            'sector_flow_signal': '매집',
        },
        'top_foreign_buy': [
            {'name': '레인보우로보틱스', 'foreign_5d': 5000000000, 'foreign_20d': 15000000000}
        ],
        'top_institution_buy': [
            {'name': '두산로보틱스', 'institution_5d': 3000000000, 'institution_20d': 10000000000}
        ],
        'flow_leaders': [],
    }

    # HTML 생성
    html = generator.generate_html(dummy_sector, dummy_flow)
    print(f"Generated HTML length: {len(html)} chars")
