"""
config.py - 全局配置

所有模块共享的常量、路径和初始化逻辑集中在此。
导入此模块即完成环境变量加载、依赖路径设置和输出目录创建。

用法：
    from config import PROJECT_DIR, CHART_DIR, WEEK_TAG, HEADERS, ...
"""

import sys, os
from datetime import datetime

# ============================================================
# 项目根目录 & 环境初始化
# ============================================================

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(PROJECT_DIR, "py_deps_new"))
os.environ.setdefault("MPLCONFIGDIR", os.path.join(PROJECT_DIR, "output", "tmp"))
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_DIR, ".env"))

# ============================================================
# 输出目录
# ============================================================

RAW_DIR = os.path.join(PROJECT_DIR, "data", "raw")
REPORT_DIR = os.path.join(PROJECT_DIR, "data", "reports")
CHART_DIR = os.path.join(PROJECT_DIR, "output", "charts")
WECHAT_DIR = os.path.join(PROJECT_DIR, "output", "wechat")
LOG_DIR = os.path.join(PROJECT_DIR, "output", "logs")

for d in [RAW_DIR, REPORT_DIR, CHART_DIR, WECHAT_DIR, LOG_DIR]:
    os.makedirs(d, exist_ok=True)

# ============================================================
# 当前周标签
# ============================================================

def current_week_tag():
    iso = datetime.now().isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"

WEEK_TAG = current_week_tag()

# ============================================================
# HTTP 请求
# ============================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# ============================================================
# 数据采集 — 导航页标题黑名单
# ============================================================

NAV_TITLES = {
    "财经观察", "人民网", "人民会客厅", "网站首页", "首页",
    "人民网--", "经济·科技", "登录", "注册", "index",
    "人物", "记者", "访谈",
}

# ============================================================
# 数据采集 — 政策相关性关键词
# ============================================================

POLICY_KEYWORDS = [
    "财政", "税收", "减税", "降费", "税务", "税制", "税率",
    "支出", "预算", "国债", "地方债", "专项债", "债务",
    "产业", "扶持", "补贴", "转移支付",
    "民生", "社保", "养老", "医保", "就业",
    "改革", "宏观调控", "积极财政", "稳健",
    "经济", "GDP", "CPI", "PPI", "居民消费",
    "数据", "统计", "发布", "政策", "解读", "财经", "经济分析",
]

# ============================================================
# 数据采集 — 数据源配置
# ============================================================

SOURCES = [
    {"name": "财政部",       "type": "官方",      "base": "http://www.mof.gov.cn",
     "url": "http://www.mof.gov.cn/zhengwuxinxi/"},
    {"name": "国家统计局",   "type": "官方",      "base": "http://www.stats.gov.cn",
     "url": "http://www.stats.gov.cn/sj/zxfb/"},
    {"name": "第一财经",     "type": "财经媒体",  "base": "https://www.yicai.com",
     "url": "https://www.yicai.com/news/"},
    {"name": "B站",          "type": "社交媒体",  "base": "https://api.bilibili.com",
     "url": "https://api.bilibili.com/x/web-interface/search/type"},
]

BILIBILI_KEYWORDS = [
    "财政政策", "减税降费", "财政支出", "宏观经济",
    "经济形势", "政府预算", "中国经济", "财经新闻",
    "政策解读", "经济数据",
]

# ============================================================
# AI 分析 — DeepSeek 配置
# ============================================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

# 政策分类体系
CATEGORIES = ["减税降费", "财政支出", "债务管理", "产业扶持", "民生保障", "财政改革", "其他"]

# ============================================================
# 错误处理 — 重试 & 超时
# ============================================================

FETCH_RETRIES = 2          # HTTP 请求重试次数
FETCH_TIMEOUT = 10          # HTTP 请求超时秒数
API_RETRIES = 2             # DeepSeek API 重试次数
API_TIMEOUT = 30            # DeepSeek API 超时秒数
API_DEGRADE_THRESHOLD = 3   # 连续失败次数超过此值进入降级模式

# ============================================================
# 报告生成 — 字体路径
# ============================================================

# 字体路径（自动检测系统）
_DEFAULT_FONT = "C:/Windows/Fonts/msyh.ttc"
_LINUX_FONTS = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
]
if not os.path.exists(_DEFAULT_FONT):
    for fp in _LINUX_FONTS:
        if os.path.exists(fp):
            _DEFAULT_FONT = fp
            break
FONT_PATH = os.getenv("FONT_PATH", _DEFAULT_FONT)
