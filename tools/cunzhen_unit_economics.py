#!/usr/bin/env python3

import argparse
import math
from copy import deepcopy


SCENARIOS = {
    "fast-cash": {
        "leads": 90,
        "valid_listings": 40,
        "contact_rate": 0.82,
        "match_rate": 0.55,
        "viewing_rate": 0.55,
        "close_rate": 0.32,
        "avg_fee": 700,
        "listing_capture_cost": 18,
        "viewing_cost": 55,
        "fixed_cost": 1800,
    },
    "lean": {
        "leads": 60,
        "valid_listings": 30,
        "contact_rate": 0.78,
        "match_rate": 0.52,
        "viewing_rate": 0.48,
        "close_rate": 0.24,
        "avg_fee": 480,
        "listing_capture_cost": 35,
        "viewing_cost": 80,
        "fixed_cost": 3200,
    },
    "target-60d": {
        "leads": 150,
        "valid_listings": 80,
        "contact_rate": 0.80,
        "match_rate": 0.50,
        "viewing_rate": 0.50,
        "close_rate": 0.27,
        "avg_fee": 520,
        "listing_capture_cost": 28,
        "viewing_cost": 90,
        "fixed_cost": 5200,
    },
    "aggressive": {
        "leads": 240,
        "valid_listings": 120,
        "contact_rate": 0.82,
        "match_rate": 0.54,
        "viewing_rate": 0.55,
        "close_rate": 0.30,
        "avg_fee": 560,
        "listing_capture_cost": 30,
        "viewing_cost": 95,
        "fixed_cost": 7600,
    },
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Estimate Cunzhen pipeline, revenue, and breakeven for a 14/30/60-day operating plan."
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS.keys()),
        default="target-60d",
        help="Preset scenario to start from.",
    )
    parser.add_argument("--leads", type=int, help="Effective renter leads in the period.")
    parser.add_argument("--valid-listings", type=int, help="Verified publishable listings in the period.")
    parser.add_argument("--contact-rate", type=float, help="Share of leads contacted successfully.")
    parser.add_argument("--match-rate", type=float, help="Share of contacted leads receiving viable matches.")
    parser.add_argument("--viewing-rate", type=float, help="Share of matched leads completing a viewing.")
    parser.add_argument("--close-rate", type=float, help="Share of completed viewings that close.")
    parser.add_argument("--avg-fee", type=float, help="Average service fee per deal in RMB.")
    parser.add_argument(
        "--listing-capture-cost",
        type=float,
        help="Average acquisition or shooting cost per valid listing in RMB.",
    )
    parser.add_argument(
        "--viewing-cost",
        type=float,
        help="Average per-viewing fulfillment cost in RMB.",
    )
    parser.add_argument(
        "--fixed-cost",
        type=float,
        help="Fixed operating cost for the period in RMB.",
    )
    return parser


def with_overrides(base: dict, args: argparse.Namespace) -> dict:
    config = deepcopy(base)
    for key in (
        "leads",
        "valid_listings",
        "contact_rate",
        "match_rate",
        "viewing_rate",
        "close_rate",
        "avg_fee",
        "listing_capture_cost",
        "viewing_cost",
        "fixed_cost",
    ):
        value = getattr(args, key)
        if value is not None:
            config[key] = value
    return config


def calc_pipeline(config: dict) -> dict:
    contacted = config["leads"] * config["contact_rate"]
    matched = contacted * config["match_rate"]
    viewings = matched * config["viewing_rate"]
    deals = viewings * config["close_rate"]

    listing_cost_total = config["valid_listings"] * config["listing_capture_cost"]
    viewing_cost_total = viewings * config["viewing_cost"]
    revenue = deals * config["avg_fee"]
    contribution = revenue - listing_cost_total - viewing_cost_total
    net_profit = contribution - config["fixed_cost"]
    gross_margin = 0.0 if revenue == 0 else contribution / revenue

    fee_after_viewing_cost = max(config["avg_fee"] - config["viewing_cost"], 1)
    breakeven_deals = math.ceil((config["fixed_cost"] + listing_cost_total) / fee_after_viewing_cost)

    return {
        **config,
        "contacted": contacted,
        "matched": matched,
        "viewings": viewings,
        "deals": deals,
        "listing_cost_total": listing_cost_total,
        "viewing_cost_total": viewing_cost_total,
        "revenue": revenue,
        "contribution": contribution,
        "net_profit": net_profit,
        "gross_margin": gross_margin,
        "breakeven_deals": breakeven_deals,
    }


def currency(value: float) -> str:
    return f"¥{value:,.0f}"


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def number(value: float) -> str:
    return f"{value:.1f}"


def print_report(report: dict, scenario: str) -> None:
    required_avg_fee = (
        (report["fixed_cost"] + report["listing_cost_total"] + report["viewing_cost_total"])
        / max(report["deals"], 1)
    )

    print(f"场景: {scenario}")
    print("=" * 44)
    print("漏斗")
    print(f"- 有效线索: {report['leads']}")
    print(f"- 成功联系: {number(report['contacted'])} ({pct(report['contact_rate'])})")
    print(f"- 完成匹配: {number(report['matched'])} ({pct(report['match_rate'])})")
    print(f"- 完成带看: {number(report['viewings'])} ({pct(report['viewing_rate'])})")
    print(f"- 成交单数: {number(report['deals'])} ({pct(report['close_rate'])})")
    print()
    print("收入与成本")
    print(f"- 平均服务费: {currency(report['avg_fee'])}")
    print(f"- 预计收入: {currency(report['revenue'])}")
    print(f"- 房源采集成本: {currency(report['listing_cost_total'])}")
    print(f"- 带看履约成本: {currency(report['viewing_cost_total'])}")
    print(f"- 固定成本: {currency(report['fixed_cost'])}")
    print(f"- 贡献毛利: {currency(report['contribution'])} ({pct(report['gross_margin'])})")
    print(f"- 净利润: {currency(report['net_profit'])}")
    print()
    print("关键判断")
    print(f"- 有效房源: {report['valid_listings']}")
    print(f"- 单个有效房源成本: {currency(report['listing_capture_cost'])}")
    print(f"- 单次带看成本: {currency(report['viewing_cost'])}")
    print(f"- 保本需要成交: {report['breakeven_deals']} 单")
    print(f"- 当前成交量下的保本客单价: {currency(required_avg_fee)}")

    if report["net_profit"] < 0:
        print()
        print("结论")
        print("- 当前参数更像验证模型，还不够快赚钱。")
        print("- 优先动作：提客单价、压固定成本、压带看成本、减少无效房源。")
    else:
        print()
        print("结论")
        print("- 当前参数具备正利润空间，可以继续复制。")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    config = with_overrides(SCENARIOS[args.scenario], args)
    report = calc_pipeline(config)
    print_report(report, args.scenario)


if __name__ == "__main__":
    main()
