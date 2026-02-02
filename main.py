#!/usr/bin/env python3
"""
국내 로봇 섹터 투자 분석 리포트 생성기
펀드매니저 관점의 종합 분석 시스템

사용법:
    python main.py                    # 전체 리포트 생성
    python main.py --quick            # 빠른 리포트 (주요 종목만)
    python main.py --json             # JSON 데이터만 생성
    python main.py --output ./report  # 출력 경로 지정
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.config import (
    ROBOT_CORE_STOCKS, ROBOT_ETFS,
    get_all_target_stocks, get_all_etfs
)
from src.screener import RobotSectorScreener
from src.data_collector import DataAggregator
from src.analyzer import ComprehensiveAnalyzer
from src.flow_analyzer import SectorFlowAnalyzer
from src.report_generator import ReportGenerator


def print_banner():
    """배너 출력"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║     🤖 국내 로봇 섹터 투자 분석 리포트                        ║
║        Korea Robot Sector Investment Analysis                 ║
║                                                               ║
║     자산운용사 관점의 펀드매니저 리포트                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def run_analysis(
    quick_mode: bool = False,
    output_dir: str = "reports",
    generate_json: bool = False,
    lookback_days: int = 252
) -> dict:
    """
    전체 분석 파이프라인 실행

    Args:
        quick_mode: 주요 종목만 분석 (빠른 실행)
        output_dir: 출력 디렉토리
        generate_json: JSON 데이터 생성 여부
        lookback_days: 분석 기간 (일)

    Returns:
        분석 결과 딕셔너리
    """
    print_banner()
    start_time = datetime.now()

    # 1. 종목 스크리닝
    print("\n📋 [1/5] 종목 스크리닝 중...")
    screener = RobotSectorScreener()

    if quick_mode:
        # 주요 종목만 선택
        target_stocks = {
            k: v for k, v in ROBOT_CORE_STOCKS.items()
            if v.get('category') in ['휴머노이드', '협동로봇', '서비스로봇']
               or '로보틱스' in v.get('name', '')
        }
        # 최소 5개는 포함
        if len(target_stocks) < 5:
            target_stocks = dict(list(ROBOT_CORE_STOCKS.items())[:10])
    else:
        target_stocks = screener.get_final_universe(
            include_etfs=False,
            include_supply_chain=True,
            include_large_caps=True
        )

    target_etfs = screener.get_etf_universe()

    print(f"   ✓ 분석 대상: {len(target_stocks)}개 종목, {len(target_etfs)}개 ETF")
    print(screener.generate_screening_report())

    # 2. 데이터 수집
    print("\n📥 [2/5] 데이터 수집 중...")
    aggregator = DataAggregator()

    print("   종목 데이터 수집...")
    stock_data = aggregator.collect_sector_data(target_stocks, lookback_days)

    print("   ETF 데이터 수집...")
    etf_data = aggregator.collect_etf_data(target_etfs, lookback_days)

    print(f"   ✓ 수집 완료: {len(stock_data)}개 종목, {len(etf_data)}개 ETF")

    # 3. 종합 분석
    print("\n📊 [3/5] 종합 분석 중...")
    analyzer = ComprehensiveAnalyzer()
    sector_analysis = analyzer.analyze_sector(stock_data)

    summary = sector_analysis['summary']
    print(f"   ✓ 분석 완료")
    print(f"     - 평균 스코어: {summary['avg_score']:.1f}")
    print(f"     - 매수: {summary['buy_count']}개, 중립: {summary['hold_count']}개, 매도: {summary['sell_count']}개")

    # 4. 수급 분석
    print("\n💰 [4/5] 수급 분석 중...")
    flow_analyzer = SectorFlowAnalyzer()
    flow_analysis = flow_analyzer.analyze_sector_flow(stock_data)

    if flow_analysis:
        flow_summary = flow_analysis.get('summary', {})
        print(f"   ✓ 수급 분석 완료")
        print(f"     - 섹터 수급 신호: {flow_summary.get('sector_flow_signal', 'N/A')}")
        print(f"     - 매집 종목: {flow_summary.get('accumulation_count', 0)}개")
    else:
        flow_analysis = {'summary': {}, 'top_foreign_buy': [], 'top_institution_buy': [], 'flow_leaders': []}

    # 5. 리포트 생성
    print("\n📝 [5/5] 리포트 생성 중...")
    generator = ReportGenerator()

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    html_path = output_path / f"robot_sector_report_{date_str}.html"
    json_path = output_path / f"robot_sector_data_{date_str}.json"

    # HTML 리포트 생성
    html = generator.generate_html(
        sector_analysis,
        flow_analysis,
        etf_data,
        output_path=str(html_path)
    )

    # JSON 데이터 생성 (선택적)
    if generate_json:
        generator.generate_json_data(
            sector_analysis,
            flow_analysis,
            etf_data,
            output_path=str(json_path)
        )

    # 완료 메시지
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\n{'='*60}")
    print(f"✅ 리포트 생성 완료! (소요시간: {elapsed:.1f}초)")
    print(f"{'='*60}")
    print(f"\n📄 HTML 리포트: {html_path}")
    if generate_json:
        print(f"📊 JSON 데이터: {json_path}")

    # Top Picks 요약
    print("\n🏆 Top 5 추천 종목:")
    for i, stock in enumerate(sector_analysis.get('top_picks', [])[:5], 1):
        name = stock.name if hasattr(stock, 'name') else stock.get('name', '')
        score = stock.score if hasattr(stock, 'score') else stock.get('score', 0)
        rating = stock.rating if hasattr(stock, 'rating') else stock.get('rating', '')
        print(f"   {i}. {name} (점수: {score:.0f}, 의견: {rating})")

    return {
        'sector_analysis': sector_analysis,
        'flow_analysis': flow_analysis,
        'etf_data': etf_data,
        'output_html': str(html_path),
        'output_json': str(json_path) if generate_json else None,
    }


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='국내 로봇 섹터 투자 분석 리포트 생성기'
    )
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='빠른 분석 모드 (주요 종목만)'
    )
    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='JSON 데이터도 함께 생성'
    )
    parser.add_argument(
        '--output', '-o',
        default='reports',
        help='출력 디렉토리 (기본: reports)'
    )
    parser.add_argument(
        '--lookback',
        type=int,
        default=252,
        help='분석 기간 (일, 기본: 252)'
    )

    args = parser.parse_args()

    try:
        result = run_analysis(
            quick_mode=args.quick,
            output_dir=args.output,
            generate_json=args.json,
            lookback_days=args.lookback
        )
        return 0
    except KeyboardInterrupt:
        print("\n\n⚠️ 사용자에 의해 중단됨")
        return 1
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
