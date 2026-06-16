"""
report_generator.py - 报告生成模块

职责：
  1. 生成情绪趋势折线图、类别分布柱状图、关键词云图
  2. 生成 Markdown 格式周报
  3. 生成公众号排版文章
  4. 生成 PDF 报告
  5. 生成封面图
  6. 打包公众号素材到 output/wechat/

用法：
    python report_generator.py                   # 生成最新周报的报告
    python report_generator.py --week 2026-W25   # 指定周
"""

import sys, os, json, re, shutil, glob
from datetime import datetime

from config import PROJECT_DIR, CHART_DIR, WECHAT_DIR, REPORT_DIR, FONT_PATH

# ============================================================
# 导入
# ============================================================
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from wordcloud import WordCloud
from PIL import Image, ImageDraw, ImageFont
from fpdf import FPDF

FP = FontProperties(fname=FONT_PATH)


# ============================================================
# 1. 情绪趋势折线图
# ============================================================

def generate_sentiment_chart(history, output_name="sentiment_trend.png"):
    """生成情绪趋势折线图（支持跨年）"""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#ffffff")

    # Build x-axis labels: "W25" or "2026-W25" when multiple years
    years = {h.get("year", 0) for h in history}
    multi_year = len(years) > 1
    labels = [
        f"{h['week']}" if not multi_year else f"{h['year']}-W{h['week']}"
        for h in history
    ]
    x_pos = list(range(len(history)))
    scores = [h["avg_score"] for h in history]

    if len(history) == 1:
        ax.scatter(x_pos, scores, color="#1f77b4", s=100, zorder=5)
        ax.axhline(y=scores[0], color="#1f77b4", linestyle="--", alpha=0.3)
    else:
        ax.plot(
            x_pos, scores, marker="o", color="#1f77b4", linewidth=2.5,
            markersize=8, markerfacecolor="#ff7f0e",
        )
        ax.fill_between(x_pos, scores, alpha=0.1, color="#1f77b4")

    ax.axhline(y=0, color="gray", linestyle="-", linewidth=0.5, alpha=0.5)
    ax.axhline(y=0.3, color="green", linestyle="--", linewidth=0.5, alpha=0.3)
    ax.axhline(y=-0.3, color="red", linestyle="--", linewidth=0.5, alpha=0.3)

    ax.set_xlabel("周次", fontproperties=FP, fontsize=12)
    ax.set_ylabel("平均情绪得分", fontproperties=FP, fontsize=12)
    ax.set_title("财政政策情绪变化趋势", fontproperties=FP, fontsize=14, fontweight="bold")
    ax.set_ylim(-1.05, 1.05)

    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontproperties=FP, fontsize=9, rotation=45 if multi_year else 0)
    for label in ax.get_yticklabels():
        label.set_fontproperties(FP)

    ax.legend(["情绪得分"], prop=FP, loc="best")
    ax.grid(True, alpha=0.3)

    path = os.path.join(CHART_DIR, output_name)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  [Chart] 情绪趋势 -> {output_name}")
    return path


# ============================================================
# 2. 类别分布柱状图
# ============================================================

def generate_category_chart(categories, output_name="category_dist.png"):
    """生成政策类别分布柱状图"""
    fig, ax = plt.subplots(figsize=(7, 4))
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#ffffff")

    items = sorted(categories.items(), key=lambda x: -x[1])
    names = [i[0] for i in items]
    counts = [i[1] for i in items]
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#7f7f7f"]

    bars = ax.bar(
        range(len(names)), counts, color=colors[: len(names)],
        width=0.6, edgecolor="white",
    )
    for bar, count in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
            str(count), ha="center", va="bottom",
            fontproperties=FP, fontsize=11,
        )

    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontproperties=FP, fontsize=10)
    ax.set_title("本周政策类别分布", fontproperties=FP, fontsize=14, fontweight="bold")
    ax.set_ylabel("文章数量", fontproperties=FP, fontsize=11)
    for label in ax.get_yticklabels():
        label.set_fontproperties(FP)
    ax.grid(axis="y", alpha=0.3)

    path = os.path.join(CHART_DIR, output_name)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  [Chart] 类别分布 -> {output_name}")
    return path


# ============================================================
# 3. 关键词云图
# ============================================================

def generate_wordcloud(keywords, output_name="keyword_cloud.png"):
    """生成关键词云图"""
    text = " ".join(keywords) if keywords else "财政政策"
    wc = WordCloud(
        font_path=FONT_PATH,
        width=600, height=350,
        background_color="white",
        max_words=40,
        colormap="coolwarm",
        prefer_horizontal=0.7,
    )
    wc.generate(text)
    path = os.path.join(CHART_DIR, output_name)
    wc.to_file(path)
    print(f"  [Chart] 关键词云 -> {output_name}")
    return path


# ============================================================
# 4. 封面图
# ============================================================

def generate_cover(week_tag, output_name="cover.png"):
    """用 Pillow 生成带渐变和几何装饰的封面图"""
    width, height = 900, 500
    img = Image.new("RGB", (width, height), color="#1a365d")
    draw = ImageDraw.Draw(img)

    # 渐变叠加：从上到下浅蓝渐变
    for y in range(height):
        ratio = y / height
        r = int(26 + (43 * ratio))
        g = int(54 + (107 * ratio))
        b = int(93 + (176 * ratio))
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # 几何装饰：右上角圆环
    for r in range(80, 200, 20):
        draw.ellipse(
            [width - 250 + r // 4, -80 + r // 4, width - 50 - r // 4, 120 - r // 4],
            outline=(99, 179, 237, 40 if r > 120 else 80),
            width=2,
        )

    # 几何装饰：底部横线
    for i in range(3):
        y_pos = 400 + i * 20
        draw.rectangle(
            [(50 + i * 20, y_pos), (350 - i * 20, y_pos + 2)],
            fill=(99, 179, 237, 60 - i * 15),
        )

    # 装饰点
    for i in range(6):
        x = width - 80 - i * 30
        y = height - 60
        draw.ellipse([(x, y), (x + 6, y + 6)], fill=(99, 179, 237, 100))

    try:
        font_title = ImageFont.truetype(FONT_PATH, 48)
        font_sub = ImageFont.truetype(FONT_PATH, 24)
        font_week = ImageFont.truetype(FONT_PATH, 18)
    except:
        font_title = ImageFont.load_default()
        font_sub = font_title
        font_week = font_title

    # 标题（带阴影效果）
    shadow_offset = 3
    draw.text(
        (width // 2 + shadow_offset, 160 + shadow_offset),
        "财政政策舆情监测",
        fill=(0, 0, 0, 60),
        font=font_title, anchor="mm",
    )
    draw.text(
        (width // 2, 160),
        "财政政策舆情监测",
        fill="#e2e8f0",
        font=font_title, anchor="mm",
    )

    # 副标题
    draw.text(
        (width // 2, 250),
        f"每周政策分析 · {week_tag}",
        fill="#90cdf4",
        font=font_sub, anchor="mm",
    )

    # 日期
    draw.text(
        (width // 2, 330),
        f"生成日期: {datetime.now().strftime('%Y-%m-%d')}",
        fill="#718096",
        font=font_week, anchor="mm",
    )

    path = os.path.join(CHART_DIR, output_name)
    img.save(path)
    print(f"  [Cover] 封面图 -> {output_name}")
    return path


# ============================================================
# 5. Markdown 报告
# ============================================================

def generate_markdown(report):
    """生成 Markdown 格式周报"""
    week_tag = report.get("report_id", "")
    lines = []
    lines.append(f"# 财政政策舆情周报 · {report['report_id']}")
    lines.append("")
    lines.append(f"> 生成时间：{report['generated_at'][:10]}")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 一、本周财政风向洞察")
    lines.append("")
    lines.append(f"{report['weekly_insight']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 情绪概览
    ss = report["sentiment_summary"]
    lines.append("## 二、情绪概览")
    lines.append("")
    lines.append(f"- 平均情绪得分：**{ss['average_score']:.2f}**")
    lines.append(
        f"- 积极文章：{ss['positive_count']} 篇 | 中性：{ss['neutral_count']} 篇 | 谨慎：{ss['cautious_count']} 篇"
    )
    lines.append(f"- 数据来源：{report['article_count']} 篇文章")
    lines.append("")

    # 图表嵌入（与 md 文件同目录）
    lines.append("![情绪趋势图](sentiment_trend.png)")
    lines.append(f"![类别分布图](category_dist_{week_tag}.png)")
    lines.append(f"![关键词云图](keyword_cloud_{week_tag}.png)")
    lines.append("")

    # 文章详情
    lines.append("---")
    lines.append("## 三、本周政策详情")
    lines.append("")
    for i, art in enumerate(report["articles"], 1):
        an = art.get("analysis", {})
        sentiment_icon = {"积极": "📈", "中性": "📊", "谨慎": "📉"}
        icon = sentiment_icon.get(an.get("sentiment_label", ""), "📋")
        lines.append(f"### {i}. {art['title']}")
        lines.append("")
        lines.append(f"- **来源**: {art['source']}（{art['source_type']}）")
        lines.append(
            f"- **分类**: {an.get('category', '其他')} | **情绪**: {icon} {an.get('sentiment_label', '中性')} ({an.get('sentiment_score', 0):+.2f})"
        )
        lines.append(f"- **关键词**: {'、'.join(an.get('keywords', []))}")
        lines.append(f"- **原文**: [{art['url'][:50]}...]({art['url']})")
        lines.append("")
        lines.append(f"> {art.get('summary', '')[:150]}...")
        lines.append("")

    lines.append("---")
    lines.append("*本报告由 AI 自动生成 · 数据来源可追溯 · 分析基于 DeepSeek API*")

    return "\n".join(lines)


# ============================================================
# 6. 公众号文章
# ============================================================

def generate_wechat_article(report):
    """生成公众号排版格式"""
    lines = []
    lines.append(f"# 财政政策舆情周报 | {report['report_id']}")
    lines.append("")
    lines.append("（本文由 AI 自动生成，数据来源可追溯）")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 本周财政风向洞察")
    lines.append("")
    lines.append(f"{report['weekly_insight']}")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("情绪趋势图（点击放大）")
    lines.append("")
    lines.append("[图片：sentiment_trend.png]")
    lines.append("")
    lines.append("关键词云图")
    lines.append("[图片：keyword_cloud.png]")
    lines.append("")
    lines.append("政策类别分布")
    lines.append("[图片：category_dist.png]")
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## 本周政策清单")
    lines.append("")
    sentiment_icons = {"积极": "📈", "中性": "📊", "谨慎": "📉"}
    for i, art in enumerate(report["articles"], 1):
        an = art.get("analysis", {})
        icon = sentiment_icons.get(an.get("sentiment_label", ""), "📋")
        cat = an.get("category", "其他")
        label = an.get("sentiment_label", "中性")
        lines.append(f"**{i}. [{cat}] {art['title']}**")
        lines.append(f"> {icon} 情绪：{label} | 来源：{art['source']}")
        lines.append("")

    lines.append("---")
    lines.append("扫描二维码关注我们 · 每周获取财政政策深度分析")
    lines.append("[封面图：cover.png]")

    return "\n".join(lines)


# ============================================================
# 7. PDF 报告
# ============================================================

def generate_pdf(report, charts):
    """生成 PDF 格式报告"""
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("msyh", "", FONT_PATH)
    pdf.add_font("msyh", "B", FONT_PATH)

    # 封面
    pdf.set_font("msyh", "B", 22)
    pdf.cell(0, 15, "财政政策舆情周报", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("msyh", "", 14)
    pdf.cell(0, 10, report["report_id"], new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(10)

    # 洞察
    pdf.set_font("msyh", "B", 14)
    pdf.cell(0, 10, "本周财政风向洞察", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("msyh", "", 10)
    pdf.multi_cell(0, 6, report["weekly_insight"])
    pdf.ln(5)

    # 情绪概览
    pdf.set_font("msyh", "B", 14)
    pdf.cell(0, 10, "情绪概览", new_x="LMARGIN", new_y="NEXT")
    ss = report["sentiment_summary"]
    pdf.set_font("msyh", "", 10)
    pdf.cell(0, 7, f"平均情绪得分：{ss['average_score']:.2f}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0, 7,
        f"积极 {ss['positive_count']} / 中性 {ss['neutral_count']} / 谨慎 {ss['cautious_count']}",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.ln(5)

    # 图表（如果存在）
    for key, path in charts.items():
        if os.path.exists(path):
            pdf.image(path, x=10, w=180)
            pdf.ln(3)

    # 文章详情
    pdf.set_font("msyh", "B", 14)
    pdf.cell(0, 10, "政策详情", new_x="LMARGIN", new_y="NEXT")
    for i, art in enumerate(report["articles"], 1):
        an = art.get("analysis", {})
        if pdf.get_y() > 240:
            pdf.add_page()
        pdf.set_font("msyh", "B", 10)
        pdf.cell(0, 7, f"{i}. {art['title'][:50]}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("msyh", "", 8)
        pdf.cell(
            0, 5,
            f"来源: {art['source']} | 分类: {an.get('category','?')} | 情绪: {an.get('sentiment_label','?')}",
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(2)

    path = os.path.join(CHART_DIR, f"{report['report_id']}.pdf")
    pdf.output(path)
    print(f"  [PDF] 报告 -> {path.split(os.sep)[-1]}")
    return path


# ============================================================
# 8. 打包公众号素材
# ============================================================

def package_wechat(week_tag, charts, wechat_text):
    """将公众号素材打包到 output/wechat/{week_tag}/"""
    out_dir = os.path.join(WECHAT_DIR, week_tag)
    os.makedirs(out_dir, exist_ok=True)

    # 复制图表
    for src_name, src_path in charts.items():
        if os.path.exists(src_path):
            base_name = os.path.basename(src_path)
            shutil.copy2(src_path, os.path.join(out_dir, base_name))

    # 写入公众号文章
    article_path = os.path.join(out_dir, "wechat_article.md")
    with open(article_path, "w", encoding="utf-8") as f:
        f.write(wechat_text)

    # 使用说明
    readme = """使用说明：
1. 打开微信公众号编辑器
2. 将 wechat_article.md 的内容复制粘贴到编辑器
3. 按 [图片：xxx.png] 标记的位置，插入对应图片文件
4. 封面图使用 cover.png
5. 调整格式后即可发布
"""
    with open(os.path.join(out_dir, "README.txt"), "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"  [WeChat] 素材已打包 -> {out_dir}")
    return out_dir


# ============================================================
# 主流程
# ============================================================

def load_report(week_tag):
    path = os.path.join(REPORT_DIR, f"{week_tag}.json")
    if not os.path.exists(path):
        print(f"[ERROR] 未找到报告: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_history(current_report):
    """Scan all history reports to build trend data"""
    history = []
    files = glob.glob(os.path.join(REPORT_DIR, "*.json"))
    for f in files:
        try:
            with open(f, "r", encoding="utf-8") as fh:
                r = json.load(fh)
            ss = r.get("sentiment_summary", {})
            year = r.get("year", 0)
            week_num = r.get("week", 0)
            history.append({
                "year": year,
                "week": week_num,
                "avg_score": ss.get("average_score", 0),
            })
        except Exception:
            continue
    # Sort by (year, week) to handle cross-year correctly
    history.sort(key=lambda x: (x["year"], x["week"]))
    return history


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--week", default=None)
    args = parser.parse_args()

    from config import current_week_tag

    week_tag = args.week or current_week_tag()

    print(f"\nReport Generator - {week_tag}\n")

    report = load_report(week_tag)
    if not report:
        return

    # Step 1: 图表
    print("生成图表...")
    history = build_history(report)
    chart_sentiment = generate_sentiment_chart(history)
    chart_category = generate_category_chart(
        report["category_distribution"],
        output_name=f"category_dist_{week_tag}.png",
    )
    chart_wordcloud = generate_wordcloud(
        report.get("all_keywords", []),
        output_name=f"keyword_cloud_{week_tag}.png",
    )
    chart_cover = generate_cover(week_tag, output_name=f"cover_{week_tag}.png")

    charts = {
        "sentiment_trend.png": chart_sentiment,
        f"category_dist_{week_tag}.png": chart_category,
        f"keyword_cloud_{week_tag}.png": chart_wordcloud,
        f"cover_{week_tag}.png": chart_cover,
    }

    # Step 2: Markdown
    print("\n生成报告...")
    md_text = generate_markdown(report)
    md_path = os.path.join(CHART_DIR, f"{week_tag}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_text)
    print(f"  [Markdown] -> {os.path.basename(md_path)}")

    # Step 3: 公众号
    wechat_text = generate_wechat_article(report)

    # Step 4: PDF
    pdf_path = generate_pdf(report, charts)

    # Step 5: 打包公众号素材
    wechat_dir = package_wechat(week_tag, charts, wechat_text)

    # Step 6: 复制报告 MD 到 output 目录
    shutil.copy2(md_path, os.path.join(WECHAT_DIR, week_tag, f"{week_tag}_report.md"))

    print(f"\n全部完成！输出文件：")
    print(f"  - 图表: {CHART_DIR}/")
    print(f"  - PDF: {pdf_path}")
    print(f"  - Markdown: {md_path}")
    print(f"  - 公众号素材: {wechat_dir}/")


if __name__ == "__main__":
    main()
