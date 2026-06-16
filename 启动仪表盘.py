"""
一键启动 Streamlit 并打开浏览器
双击运行即可：启动服务 → 自动打开 http://localhost:8501
"""
import subprocess, sys, time, webbrowser, os, socket

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
STREAMLIT_PORT = 8501


def is_port_open(port):
    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False


def main():
    print("=" * 50)
    print("  财政政策舆情监测系统")
    print("  正在启动 Streamlit 服务...")
    print("=" * 50)

    # 如果端口已被占用，先不启动新实例
    if is_port_open(STREAMLIT_PORT):
        print(f"\n[OK] 服务已在 http://localhost:{STREAMLIT_PORT} 运行")
    else:
        # 启动 Streamlit
        proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run",
             "streamlit_app.py",
             "--global.developmentMode", "false",
             "--server.port", str(STREAMLIT_PORT)],
            cwd=PROJECT_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        print(f"\n  正在初始化（约 5 秒）...", end="", flush=True)
        for i in range(10):
            time.sleep(1)
            if is_port_open(STREAMLIT_PORT):
                print(" 就绪！")
                break
            print(".", end="", flush=True)
        else:
            print("\n  启动超时，请检查日志")

    # 打开浏览器
    url = f"http://localhost:{STREAMLIT_PORT}"
    print(f"\n  正在打开浏览器...")
    webbrowser.open(url)
    print(f"\n  [OK] 服务已启动：{url}")
    print(f"  关闭此窗口不影响服务运行。")
    print(f"  如需停止，请关闭命令行的 Streamlit 进程。")
    print()

    # 保持窗口打开，让用户看到信息
    try:
        input("  按 Enter 键关闭本窗口...")
    except EOFError:
        pass  # 非交互终端下忽略


if __name__ == "__main__":
    main()
