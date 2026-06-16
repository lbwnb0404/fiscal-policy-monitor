"""
analyzer.py - 政策分析模块

职责：
  1. 读取 data_collector 采集的原始文章
  2. 调用 DeepSeek API 对每篇文章分析：政策分类 + 情绪评分 + 关键词
  3. 综合生成"本周财政风向洞察"
  4. 输出完整周报到 data/reports/

用法：
    python analyzer.py                       # 分析最新一周
    python analyzer.py --week 2026-W25       # 分析指定周
    python analyzer.py --dry-run             # 试运行
"""

import sys, os, json, re
from datetime import datetime

from config import PROJECT_DIR, RAW_DIR, REPORT_DIR
from config import DEEPSEEK_API_KEY, DEEPSEEK_URL, DEEPSEEK_MODEL, CATEGORIES
from config import API_RETRIES, API_TIMEOUT, API_DEGRADE_THRESHOLD

import requests
import time


# ============================================================
# DeepSeek 调用（带重试 & 降级）
# ============================================================

_api_failure_count = 0  # 连续失败计数
_api_degraded = False    # 是否已进入降级模式


def call_deepseek(messages, max_tokens=500, temperature=0.1):
    """调用 DeepSeek API（带重试 + 指数退避 + 自动降级）"""
    global _api_failure_count, _api_degraded

    if _api_degraded:
        print("  [DEGRADED] API 降级中，跳过调用")
        return ""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": DEEPSEEK_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    for attempt in range(API_RETRIES + 1):
        try:
            resp = requests.post(
                f"{DEEPSEEK_URL}/chat/completions",
                headers=headers, json=data, timeout=API_TIMEOUT,
            )
            if resp.status_code == 200:
                _api_failure_count = 0
                return resp.json()["choices"][0]["message"]["content"].strip()
            elif resp.status_code == 401:
                print(f"  [API ERROR] API Key 无效")
                _api_failure_count += 1
                break  # 密钥错误无需重试
            elif resp.status_code == 429:
                print(f"  [API ERROR] 频率限制 ({resp.text[:50]})")
                _api_failure_count += 1
            else:
                print(f"  [API ERROR] {resp.status_code}: {resp.text[:80]}")
                _api_failure_count += 1
        except requests.Timeout:
            print(f"  [API RETRY] 超时 ({attempt+1}/{API_RETRIES})")
            _api_failure_count += 1
        except requests.ConnectionError:
            print(f"  [API RETRY] 连接失败 ({attempt+1}/{API_RETRIES})")
            _api_failure_count += 1
        except Exception as e:
            print(f"  [API RETRY] {str(e)[:40]} ({attempt+1}/{API_RETRIES})")
            _api_failure_count += 1

        # 判断是否进入降级模式
        if _api_failure_count >= API_DEGRADE_THRESHOLD:
            _api_degraded = True
            print(f"  [DEGRADE] 连续 {_api_failure_count} 次失败，进入降级模式")

        if attempt < API_RETRIES:
            time.sleep(2 ** attempt)

    return ""


def reset_api_degradation():
    """重置 API 降级状态（供外部调用）"""
    global _api_failure_count, _api_degraded
    _api_failure_count = 0
    _api_degraded = False


# ============================================================
# 分析单篇文章
# ============================================================

# Degraded mode: keyword-based local classification rules (Chinese)
_LOCAL_CATEGORY_RULES = [
    ("减税降费", ["减税", "降费", "税率", "税制", "税收优惠", "税务"]),
    ("财政支出", ["财政支出", "预算", "拨款", "专项", "支出", "投资"]),
    ("债务管理", ["债务", "国债", "地方债", "专项债", "赤字", "偿债"]),
    ("产业扶持", ["产业", "扶持", "补贴", "制造业", "创新", "科技", "AI", "人工智能"]),
    ("民生保障", ["民生", "社保", "养老", "医保", "就业", "教育", "医疗"]),
    ("财政改革", ["改革", "体制", "机制", "现代化", "数字化", "预算管理"]),
]

def _local_analyze(article):
    """Degraded mode: keyword-based local rule analysis for Chinese text"""
    text = article.get("title", "") + " " + article.get("content", "")[:600]
    best_cat = "其他"
    best_score = 0
    for cat, kws in _LOCAL_CATEGORY_RULES:
        score = sum(1 for kw in kws if kw in text)
        if score > best_score:
            best_score = score
            best_cat = cat
    pos_kws = ["增长", "扩张", "积极", "利好", "回升", "突破", "向好", "加大"]
    cau_kws = ["风险", "压力", "下滑", "放缓", "困难", "挑战", "债务", "紧缩"]
    pos = sum(1 for kw in pos_kws if kw in text)
    cau = sum(1 for kw in cau_kws if kw in text)
    if pos > cau:
        sentiment_label = "积极"
        sentiment_score = round(min(0.5, pos * 0.12), 2)
    elif cau > pos:
        sentiment_label = "谨慎"
        sentiment_score = round(max(-0.5, -cau * 0.12), 2)
    else:
        sentiment_label = "中性"
        sentiment_score = 0.0
    import re as _re
    words = _re.findall(r"[\u4e00-\u9fff]{2,4}", article.get("title", ""))
    keywords = list(dict.fromkeys(words))[:5]
    print(f"  [DEGRADED] \u672c\u5730\u89c4\u5219 -> {best_cat}/{sentiment_label}")
    return {
        "category": best_cat,
        "sentiment_score": sentiment_score,
        "sentiment_label": sentiment_label,
        "keywords": keywords,
        "brief_summary": article.get("title", "")[:20],
        "entities": {"departments": [], "amounts": [], "tools": [], "people": []},
    }

def analyze_article(article):
    """Classify+emotion+keywords for one article (API first, local rules when degraded)"""
    global _api_degraded
    if _api_degraded:
        return _local_analyze(article)
    content = article.get("content", "")[:1500]
    title = article.get("title", "")
    source = article.get("source", "")

    prompt = f"""你是一位财政政策分析专家。请分析以下政策文章，返回严格的 JSON 格式。

文章标题：{title}
文章来源：{source}
文章内容：{content}

请分析并返回 JSON：
{{
  "category": "从以下选择一项：{"、".join(CATEGORIES)}",
  "sentiment_score": "浮点数 -1.0 到 1.0，负数=谨慎/紧缩，正数=积极/扩张，接近0=中性",
  "sentiment_label": "积极/中性/谨慎",
  "keywords": ["关键词1", "关键词2", "关键词3", "关键词4", "关键词5"],
  "brief_summary": "一句话摘要（20字以内）",
  "entities": {{
    "departments": ["涉及的部门名称，如财政部、国务院等"],
    "amounts": ["涉及的金额数字，如5000亿元、1.5万亿等"],
    "tools": ["涉及的政策工具，如专项债、减税降费等"],
    "people": ["涉及的人物姓名，如廖岷、蓝佛安等"]
  }}
}}

只返回 JSON，不要包含其他文字。"""

    messages = [
        {
            "role": "system",
            "content": "你是国务院发展研究中心的财政政策分析专家。你只输出 JSON 格式的分析结果，语言精准、专业。",
        },
        {"role": "user", "content": prompt},
    ]

    result_text = call_deepseek(messages, max_tokens=500)
    if not result_text:
        return {
            "category": "其他",
            "sentiment_score": 0,
            "sentiment_label": "中性",
            "keywords": [],
            "brief_summary": "",
            "entities": {"departments": [], "amounts": [], "tools": [], "people": []},
        }

    # 尝试从返回文本中提取 JSON（支持嵌套对象）
    start = result_text.find("{")
    end = result_text.rfind("}")
    if start >= 0 and end > start:
        try:
            result = json.loads(result_text[start:end+1])
            # 验证字段
            if result.get("category") not in CATEGORIES:
                result["category"] = "其他"
            if not isinstance(result.get("sentiment_score"), (int, float)):
                result["sentiment_score"] = 0
            result["sentiment_score"] = max(
                -1.0, min(1.0, float(result["sentiment_score"]))
            )
            if result.get("sentiment_label") not in ["积极", "中性", "谨慎"]:
                result["sentiment_label"] = "中性"
            if not isinstance(result.get("keywords"), list):
                result["keywords"] = []
            # 确保 entities 字段存在且格式正确
            if not isinstance(result.get("entities"), dict):
                result["entities"] = {}
            for key in ["departments", "amounts", "tools", "people"]:
                if not isinstance(result["entities"].get(key), list):
                    result["entities"][key] = []
            return result
        except (json.JSONDecodeError, KeyError, ValueError, AttributeError):
            pass

    return {
        "category": "其他",
        "sentiment_score": 0,
        "sentiment_label": "中性",
        "keywords": [],
        "brief_summary": "",
    }


# ============================================================
# 生成周度洞察
# ============================================================

def generate_weekly_insight(analyzed_articles):
    """综合所有文章，生成洞察"""
    if not analyzed_articles:
        return "本周未采集到财政政策相关信息。"

    summaries = []
    for a in analyzed_articles:
        cat = a.get("analysis", {}).get("category", "其他")
        sentiment = a.get("analysis", {}).get("sentiment_label", "中性")
        title = a.get("title", "")
        summaries.append(f"- [{cat}/{sentiment}] {title}")

    prompt = f"""你是国务院发展研究中心的资深研究员，专攻财政政策分析。请基于以下本周采集到的政策信息，撰写一段高质量"本周财政风向洞察"（250-350字）。

要求：
1. 语言精炼专业，有政策研究深度，避免空泛描述
2. 具体引用信息来源（如"根据财政部XX文件/统计局最新数据"）
3. 采用三段式结构：
   - **总体判断**：本周政策基调（积极/中性/谨慎）、核心信号
   - **重点领域**：哪些政策方向最活跃，各自的关键信号
   - **趋势展望**：下周/近期的政策关注点
4. 关键判断用 **加粗** 强调，数据观点要具体
5. 使用政策分析术语，避免过于口语化

本周文章摘要：
{chr(10).join(summaries)}

只输出洞察文本本身，不要加标题。"""

    messages = [
        {
            "role": "system",
            "content": "你是国务院发展研究中心的资深研究员，专攻中国财政政策分析。你的语言精炼、专业、有深度，擅长从政策文本中提炼关键信号和趋势判断。",
        },
        {"role": "user", "content": prompt},
    ]

    return call_deepseek(messages, max_tokens=600, temperature=0.3)


# ============================================================
# 主流程
# ============================================================

def load_raw_articles(week_tag):
    """加载原始采集数据"""
    path = os.path.join(RAW_DIR, f"{week_tag}.json")
    if not os.path.exists(path):
        print(f"[ERROR] 未找到数据文件: {path}")
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def analyze_all(articles):
    """批量分析文章"""
    analyzed = []
    for i, art in enumerate(articles):
        print(f"  [{i+1}/{len(articles)}] 分析: {art.get('title', '')[:35]}...", end=" ")
        result = analyze_article(art)
        # 清理导航类文章（人民网导航页）
        content = art.get("content", "")
        if len(content) < 50:
            print("SKIP (内容过短)")
            continue
        art["analysis"] = result
        analyzed.append(art)
        print(f"{result.get('category', '?')}/{result.get('sentiment_label', '?')}")
    return analyzed


def save_report(week_tag, articles_analyzed, insight):
    """保存周报到 data/reports/"""
    # 计算汇总统计
    cats = {}
    sentiments = {"积极": 0, "中性": 0, "谨慎": 0}
    all_kws = []
    for a in articles_analyzed:
        an = a.get("analysis", {})
        c = an.get("category", "其他")
        cats[c] = cats.get(c, 0) + 1
        s = an.get("sentiment_label", "中性")
        sentiments[s] = sentiments.get(s, 0) + 1
        all_kws.extend(an.get("keywords", []))

    scores = [
        a.get("analysis", {}).get("sentiment_score", 0)
        for a in articles_analyzed
    ]
    avg_score = round(sum(scores) / len(scores), 2) if scores else 0

    report = {
        "report_id": week_tag,
        "year": int(week_tag[:4]),
        "week": int(week_tag.split("-W")[1]) if "-W" in week_tag else 0,
        "generated_at": datetime.now().isoformat(),
        "article_count": len(articles_analyzed),
        "articles": articles_analyzed,
        "category_distribution": cats,
        "sentiment_summary": {
            "average_score": avg_score,
            "positive_count": sentiments["积极"],
            "neutral_count": sentiments["中性"],
            "cautious_count": sentiments["谨慎"],
        },
        "all_keywords": list(set(all_kws)),
        "weekly_insight": insight,
    }

    path = os.path.join(REPORT_DIR, f"{week_tag}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] 报告 -> {path}")
    return report


def main():
    import argparse
    from config import current_week_tag

    parser = argparse.ArgumentParser()
    parser.add_argument("--week", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    week_tag = args.week or current_week_tag()
    print(f"\nAnalyzer - {week_tag}\n")

    articles = load_raw_articles(week_tag)
    if not articles:
        return

    print(f"Loaded {len(articles)} raw articles\nAnalyzing...\n")
    analyzed = analyze_all(articles)

    print(f"\nGenerating weekly insight...")
    insight = generate_weekly_insight(analyzed)
    print(f"\nInsight:\n{insight}\n")

    if args.dry_run:
        print("[Dry-Run] 未保存")
    else:
        save_report(week_tag, analyzed, insight)

    print(f"Done! {len(analyzed)} articles analyzed")


if __name__ == "__main__":
    main()
