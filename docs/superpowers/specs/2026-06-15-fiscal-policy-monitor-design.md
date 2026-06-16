# 财政政策舆情监测系统 — 设计文档

**日期：** 2026-06-15
**状态：** 草案（待审核）

---

## 1. 项目概述

为双非财经院校财政学专业大三学生（无代码背景，备考中央民族大学应用经济学研究生）设计的复试展示项目。

**核心价值：** 体现 AI 能力、科研思维和主动性的全流程自动化财政政策监测工具。

**一句话定位：** 一条命令完成从政策采集到可视化周报全流程，附带公众号发布能力的财政政策舆情监测系统。

---

## 2. 架构总览

### 项目目录结构

```
财政政策舆情监测/
├── .env                        # DeepSeek API Key
├── requirements.txt            # Python 依赖清单
├── main.py                     # 一键运行入口（数据采集→分析→报告）
├── config.py                   # 全局配置（数据源、API地址、存储路径）
├── data_collector.py           # 模块1：数据采集
├── analyzer.py                 # 模块2：政策分析（调用 DeepSeek）
├── report_generator.py         # 模块3：报告生成（图表/排版/导出）
├── streamlit_app.py            # 模块4：交互式可视化
├── utils.py                    # 工具函数（JSON读写、日期处理、去重）
├── data/                       # 数据存储
│   ├── raw/                    # 原始采集数据（JSON）
│   └── reports/                # 已生成的周报（JSON + Markdown）
└── output/                     # 输出
    ├── charts/                 # 情绪趋势图、关键词云图（PNG）
    └── wechat/                 # 公众号素材包
```

### 数据流

```
Web（财政部/统计局/新华社/社交媒体）
    │
    ▼
data_collector.py   ← anysearch CLI（搜索 + 提取）
    │
    ▼
   raw/（原始文章 JSON）
    │
    ▼
analyzer.py         ← DeepSeek API（分类 + 情绪 + 关键词 + 洞察）
    │
    ▼
analyzed/（分析后 JSON）
    │
    ▼
report_generator.py ← matplotlib（图表）+ wordcloud（词云）+ fpdf2（PDF）
    │
    ├── output/charts/（PNG 图表）
    ├── output/wechat/（公众号素材包）
    ├── data/reports/（JSON + Markdown 报告）
    │
    ▼
streamlit_app.py    ← 用户通过浏览器查看历史报告
```

### 设计原则

| 原则 | 说明 |
|------|------|
| 文件存储 | 所有数据存 JSON 文件，不依赖数据库，零配置 |
| 模块解耦 | 4个模块通过文件系统通信，可独立运行 |
| 可追溯 | 每篇文章保留原始 URL，所有分析基于真实抓取文本 |
| 零幻觉 | DeepSeek 只分析真实文本，不编造政策内容 |
| 中文优先 | 全线中文，政策领域中文分词/字体/编码 |

---

## 3. 模块详细设计

### 模块1：data_collector.py

**职责：** 搜索和提取政策相关内容，保存为结构化 JSON。

**数据源矩阵：**

| 层级 | 数据源 | 搜索策略 | 用途 |
|------|--------|---------|------|
| 官方 | 财政部 (mof.gov.cn) | site:mof.gov.cn 财政政策 | 政策原文 |
| 官方 | 国家统计局 (stats.gov.cn) | site:stats.gov.cn 财政数据 | 经济数据 |
| 官方 | 中国人民银行 (pbc.gov.cn) | site:pbc.gov.cn 货币政策 | 货币政策 |
| 官方 | 新华社 (xinhuanet.com) | site:xinhuanet.com 财政政策 | 权威报道 |
| 财经媒体 | 第一财经 (yicai.com) | site:yicai.com 财政政策 | 专业分析 |
| 财经媒体 | 21世纪经济报道 | site:21jingji.com 财政 | 深度报道 |
| 社交媒体 | B站 | site:bilibili.com 财政政策 解读 | 公众讨论 |
| 社交媒体 | 小红书 | site:xiaohongshu.com 财政政策 | 公众讨论 |
| 社交媒体 | 抖音/头条 | site:toutiao.com 财政政策 | 公众讨论 |

### 模块2：analyzer.py

**职责：** 调用 DeepSeek API 对每篇文章进行分类、情绪评分、关键词提取，并生成周度洞察。

**分类体系：** 减税降费 / 财政支出 / 债务管理 / 产业扶持 / 民生保障 / 财政改革 / 其他

**情绪体系：** 积极（0.3~1.0）/ 中性（-0.3~0.3）/ 谨慎（-1.0~-0.3）

### 模块3：report_generator.py

**职责：** 图表生成 + 报告排版 + 公众号素材

**图表：** 情绪趋势折线图、类别分布柱状图、关键词云图（wordcloud + 微软雅黑）

**公众号素材包：**
```
output/wechat/2026-W25/
  +-- 01_封面图.png          # Pillow 文字封面
  +-- 02_情绪趋势图.png      # 图表
  +-- 03_关键词云图.png      # 图表
  +-- 04_类别分布图.png      # 图表
  +-- 周报正文.md             # 公众号排版
  +-- 使用说明.txt            # 粘贴指引
```

### 模块4：streamlit_app.py

**职责：** 交互式网页展示历史周报。
左侧年份/月份/周选择 | 中央政策详情 | 右侧图表 | 底部下载按钮

---

## 4. 周报数据模型

```python
{
    "report_id": "2026-W25",
    "year": 2026, "week": 25,
    "start_date": "2026-06-15", "end_date": "2026-06-21",
    "articles": [],
    "category_distribution": {
        "减税降费": 3, "财政支出": 2, "债务管理": 1,
        "产业扶持": 2, "民生保障": 2, "财政改革": 1
    },
    "sentiment_summary": {
        "average_score": 0.65,
        "positive_count": 7, "neutral_count": 4, "cautious_count": 1
    },
    "weekly_insight": "本周财政政策以积极扩张为主基调...",
    "all_keywords": ["减税", "小微企业", "专项债", "转移支付"],
    "generated_at": "2026-06-21T18:00:00"
}
```

---

## 5. 技术栈决策

| 组件 | 选择 | 理由 |
|------|------|------|
| 数据采集 | anysearch CLI | 已安装，无需额外申请API |
| LLM API | DeepSeek (deepseek-chat) | 性价比最高，中文能力强 |
| LLM SDK | openai Python包 | DeepSeek 兼容 OpenAI 格式 |
| 可视化前端 | Streamlit | 纯 Python，无需前端知识 |
| 图表 | matplotlib | 成熟稳定，中文支持好 |
| 词云 | wordcloud + numpy + pillow | 标准方案 |
| PDF | fpdf2 | 纯 Python，零系统依赖 |
| 公众号封面 | Pillow 文字图 | 零额外依赖 |
| 数据存储 | JSON 文件 | 零配置，易于理解 |

---

## 6. 实施计划

| 阶段 | 内容 | 涉及 Skill |
|------|------|-----------|
| 1. 环境搭建 | 安装依赖、配置API Key、创建项目结构 | - |
| 2. data_collector | anysearch 搜索+提取、去重、JSON存储 | anysearch |
| 3. analyzer | DeepSeek API 调用、分类+情绪+洞察 | - |
| 4. report_generator | 图表、Markdown、公众号排版、PDF | imagegen(封面) |
| 5. streamlit_app | 交互式可视化界面 | frontend-design |
| 6. main.py 整合 | 一键运行入口、定时任务支持 | - |
| 7. 文档与演示 | README、面试指南、代码注释 | nature-writing |

---

## 7. 环境需求清单

| 项目 | 状态 | 操作 |
|------|------|------|
| Python 3.14 | ✅ | - |
| pip | ✅ | - |
| requests | ❌ | pip install requests |
| openai | ❌ | pip install openai |
| streamlit | ❌ | pip install streamlit |
| matplotlib | ❌ | pip install matplotlib |
| wordcloud | ❌ | pip install wordcloud |
| numpy | ❌ | pip install numpy |
| pillow | ❌ | pip install pillow |
| fpdf2 | ❌ | pip install fpdf2 |
| DeepSeek API Key | ✅ | 写入 .env |
| 微软雅黑字体 | ✅ | C:/Windows/Fonts/msyh.ttc |

---

## 8. 面试亮点

| 面试官问题 | 回答要点 |
|-----------|---------|
| 为什么用 DeepSeek？ | 性价比最高、中文能力强；了解 API 兼容性 |
| 数据准确性？ | 基于真实抓取文本，每篇文章带 URL 可追溯 |
| 为什么加社交媒体？ | 全媒体视角：政策效果体现在公众感知 |
| 为什么不用数据库？ | 适合文件存储，零配置，可当场运行 |

---

## 9. 假设与决策记录

| 决策 | 理由 |
|------|------|
| PDF: fpdf2（非 weasyprint） | weasyprint 在 Windows 需额外 GTK 依赖 |
| 封面: Pillow 文字图 | 零额外 AI API 依赖 |
| 搜索: anysearch + site: | 无需专有爬虫 |
| 分词: DeepSeek 直接提取 | 无需 jieba，简化依赖 |
| 社交媒体：仅公开可搜内容 | 不使用非公开 API |

---

*设计文档结束*
