"""
main.py - 一键运行入口

一键完成：数据采集 → AI 分析 → 报告生成 → 启动可视化

用法：
    python main.py              # 全流程运行
    python main.py --step collect   # 仅采集
    python main.py --step analyze   # 仅分析
    python main.py --step report    # 仅生成报告
    python main.py --step streamlit # 启动可视化
    python main.py --auto       # 全自动（含 Streamlit）
"""

import sys, os, subprocess, time

from config import PROJECT_DIR


def run_step(script, label):
    print(f"\n{'=' * 50}")
    print(f"  步骤: {label}")
    print(f"{'=' * 50}")
    result = subprocess.run(
        [sys.executable, script],
        cwd=PROJECT_DIR,
        capture_output=False,
    )
    return result.returncode == 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="财政政策舆情监测 - 一键全流程")
    parser.add_argument(
        "--step",
        default="all",
        choices=["all", "collect", "analyze", "report", "streamlit"],
    )
    parser.add_argument("--auto", action="store_true", help="全自动运行（含Streamlit）")
    args = parser.parse_args()

    step = args.step
    if args.auto:
        step = "all"

    if step in ("all", "collect"):
        if not run_step("data_collector.py", "数据采集"):
            print("[ERROR] 数据采集失败")
            return

    if step in ("all", "analyze"):
        if not run_step("analyzer.py", "AI 政策分析"):
            print("[ERROR] 政策分析失败")
            return

    if step in ("all", "report"):
        if not run_step("report_generator.py", "报告生成"):
            print("[ERROR] 报告生成失败")
            return

    if step in ("all", "streamlit") or args.auto:
        print(f"\n启动 Streamlit 可视化界面...")
        print(f"访问地址: http://localhost:8501")
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
             "--server.port", "8501"],
            cwd=PROJECT_DIR,
        )

    if step == "all" and not args.auto:
        from config import WEEK_TAG

        print(f"\n{'=' * 50}")
        print(f"  全流程完成！")
        print(f"  Streamlit 可视化: http://localhost:8501")
        print(f"  PDF 报告: output/charts/{WEEK_TAG}.pdf")
        print(f"  公众号素材: output/wechat/{WEEK_TAG}/")
        print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
