import sys
import os

# 将 py_deps 添加到 Python 路径，避免全局安装依赖
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
PYDEPS_DIR = os.path.join(PROJECT_DIR, "py_deps_new")
if PYDEPS_DIR not in sys.path:
    sys.path.insert(0, PYDEPS_DIR)

# 设置 Matplotlib 缓存目录（避免权限问题）
os.environ.setdefault("MPLCONFIGDIR", os.path.join(PROJECT_DIR, "output", "tmp"))

# 加载 .env 文件
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_DIR, ".env"))
