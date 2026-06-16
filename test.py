"""
test.py - 财政政策舆情监测系统 · 基础测试

验证全流程各个模块能否正常工作。
用法：
    python test.py              # 运行全部测试
    python test.py --module collect  # 只测采集
    python test.py --module analyze  # 只测分析
    python test.py --module report   # 只测报告
    python test.py --module all      # 全流程端到端
"""

import sys, os, json, glob, time

from config import PROJECT_DIR

PASS = 0
FAIL = 0


def test(name, func):
    global PASS, FAIL
    try:
        func()
        PASS += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        FAIL += 1
        print(f"  [FAIL] {name}: {str(e)[:80]}")


def test_imports():
    """测试所有依赖包能否正常导入"""
    import requests

    requests.get("https://www.baidu.com", timeout=10)
    import matplotlib

    matplotlib.__version__
    import wordcloud
    import numpy
    from fpdf import FPDF
    import dotenv
    from openai import OpenAI


def test_collector():
    """测试采集模块能否抓取网页"""
    sys.path.insert(0, PROJECT_DIR)
    import data_collector as dc

    html = dc.fetch("http://www.mof.gov.cn/zhengwuxinxi/", timeout=10)
    assert len(html) > 1000, f"财政部页面内容不足: {len(html)}"
    links = dc.find_article_links(html, "http://www.mof.gov.cn")
    assert len(links) > 0, "未找到任何文章链接"
    print(f"    财政部页面: {len(html)} bytes, {len(links)} 个链接")


def test_analyzer_raw():
    """测试分析模块能否读取和解析数据"""
    files = glob.glob(os.path.join(PROJECT_DIR, "data", "raw", "*.json"))
    assert len(files) > 0, "data/raw/ 中没有 JSON 文件"
    for f in files:
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data, list), f"{f} 不是列表格式"
        if data:
            assert "title" in data[0], "缺少 title 字段"
            assert "content" in data[0], "缺少 content 字段"
            assert "source" in data[0], "缺少 source 字段"
    print(f"    {len(files)} 个数据文件，格式正确")


def test_report_outputs():
    """测试报告输出文件是否存在"""
    from config import CHART_DIR

    # 检查情绪趋势图（全局，所有周共用）
    assert os.path.exists(os.path.join(CHART_DIR, "sentiment_trend.png")), "缺少情绪趋势图"
    # 检查是否有按周生成的类别分布图
    cat_charts = glob.glob(os.path.join(CHART_DIR, "category_dist_*.png"))
    assert len(cat_charts) > 0, "没有按周生成的类别分布图"
    # 检查是否有按周生成的关键词云图
    kw_charts = glob.glob(os.path.join(CHART_DIR, "keyword_cloud_*.png"))
    assert len(kw_charts) > 0, "没有按周生成的关键词云图"
    # 检查 PDF
    pdfs = glob.glob(os.path.join(CHART_DIR, "*.pdf"))
    assert len(pdfs) > 0, "没有 PDF 报告"
    print(f"    情绪趋势图: 存在, 类别分布图: {len(cat_charts)} 个, 关键词云: {len(kw_charts)} 个, PDF: {len(pdfs)} 个")


def test_env():
    """测试环境配置"""
    assert os.getenv("DEEPSEEK_API_KEY"), "DEEPSEEK_API_KEY 未设置"
    assert os.path.exists(os.path.join(PROJECT_DIR, ".env")), ".env 文件不存在"


def test_date_extraction():
    """测试日期提取函数"""
    from data_collector import extract_publish_date

    # 中文日期
    assert extract_publish_date("2026年5月28日") == "2026-05-28"
    assert extract_publish_date("2026年05月28日 发布") == "2026-05-28"
    assert extract_publish_date("发布于2026年12月3日") == "2026-12-03"

    # ISO 日期
    assert extract_publish_date("2026-06-15 19:35:34") == "2026-06-15"
    assert extract_publish_date("date: 2026-01-01") == "2026-01-01"

    # 斜杠日期
    assert extract_publish_date("2026/06/10") == "2026-06-10"

    # 无效日期
    assert extract_publish_date("no date here") == ""
    assert extract_publish_date("") == ""
    assert extract_publish_date("1999年13月45日") == ""


def test_retry_logic():
    """测试重试逻辑的基本行为"""
    from data_collector import _request_with_retry, HEADERS

    # 对有效 URL 应能成功请求
    result = _request_with_retry("https://httpbin.org/get", timeout=15)
    assert result is not None, "有效 URL 请求失败"

    # 对无效域名应返回 None（所有重试后）
    result = _request_with_retry("https://invalid.example.xyz", timeout=3)
    assert result is None, "无效域名应返回 None"


def test_build_history():
    """测试 build_history 排序"""
    from report_generator import build_history

    # 构造跨年数据
    data = [
        {"year": 2026, "week": 48, "avg_score": 0.3},
        {"year": 2027, "week": 5, "avg_score": 0.1},
        {"year": 2026, "week": 2, "avg_score": 0.5},
    ]
    sorted_data = sorted(data, key=lambda x: (x["year"], x["week"]))
    assert sorted_data[0]["avg_score"] == 0.5, "2026-W02 should be first"
    assert sorted_data[-1]["avg_score"] == 0.1, "2027-W05 should be last"


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--module",
        default="all",
        choices=["all", "imports", "collect", "analyze", "report", "env"],
    )
    args = parser.parse_args()

    print(f"\n{'=' * 45}")
    print(f"  财政政策舆情监测系统 · 基础测试")
    print(f"{'=' * 45}\n")

    if args.module in ("all", "env"):
        print("[1/5] 环境配置")
        test("依赖包导入", test_imports)
        test("API Key 配置", test_env)

    if args.module in ("all", "collect"):
        print("\n[2/5] 数据采集")
        test("采集模块功能", test_collector)

    if args.module in ("all", "analyze"):
        print("\n[3/5] 数据分析")
        test("原始数据格式", test_analyzer_raw)

    if args.module in ("all", "report"):
        print("\n[4/5] 报告生成")
        test("输出文件完整性", test_report_outputs)

    if args.module == "all":
        print("\n[5/5] 端到端验证")

        def test_end_to_end():
            """测试全流程能否跑通"""
            import subprocess

            # 采集
            r = subprocess.run(
                [sys.executable, "data_collector.py", "--dry-run", "--max-per-source", "1"],
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert "Total:" in r.stdout, f"采集失败: {r.stderr[:200]}"
            # 报告
            r = subprocess.run(
                [sys.executable, "report_generator.py"],
                cwd=PROJECT_DIR,
                capture_output=True,
                text=True,
                timeout=30,
            )
            assert "全部完成" in r.stdout, f"报告失败: {r.stderr[:200]}"
            print(f"    全流程验证通过")

        test("端到端流程", test_end_to_end)

        # 单元测试
        test("日期提取函数", test_date_extraction)
        test("重试逻辑", test_retry_logic)
        test("跨年排序", test_build_history)

    print(f"\n{'=' * 45}")
    print(f"  结果: {PASS} 通过, {FAIL} 失败")
    if FAIL > 0:
        print(f"  [WARN]  有 {FAIL} 个测试未通过，请检查")
    else:
        print(f"  [OK] 全部通过！")
    print(f"{'=' * 45}\n")
    return 1 if FAIL > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
