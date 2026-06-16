"""run_weekly.py - 每周定时任务脚本"""

import sys, os, subprocess
from datetime import datetime

from config import PROJECT_DIR, LOG_DIR


today = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_file = os.path.join(LOG_DIR, f"weekly_{today}.log")


def log(msg):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    print(msg)


def run_step(script, label):
    log(f"--- {label} ---")
    result = subprocess.run(
        [sys.executable, script],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode == 0:
        log(f"  OK: {label} 完成")
    else:
        log(f"  ERROR: {label} 失败")
        for line in result.stderr.split("\n")[-3:]:
            if line.strip():
                log(f"  {line.strip()}")
    return result.returncode == 0


def main():
    log(f"{'=' * 50}")
    log(f"  财政政策舆情周报 - 定时任务")
    log(f"  启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"{'=' * 50}\n")

    steps = [
        ("data_collector.py", "数据采集"),
        ("analyzer.py", "AI政策分析"),
        ("report_generator.py", "报告生成"),
    ]

    all_ok = True
    for script, label in steps:
        if not run_step(script, label):
            all_ok = False

    log(f"\n{'=' * 50}")
    if all_ok:
        log(f"  全流程完成！本周周报已生成")
    else:
        log(f"  部分步骤失败，请检查日志")
    log(f"{'=' * 50}")
    print(f"\nLog saved to: {log_file}")


if __name__ == "__main__":
    main()
