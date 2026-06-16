"""streamlit_app.py - 财政政策舆情监测可视化界面"""

import sys, os, json, glob
from datetime import datetime

from config import PROJECT_DIR, REPORT_DIR, CHART_DIR

import streamlit as st

st.set_page_config(
    page_title="财政政策舆情监测",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS 注入 — 政务蓝主题
# ============================================================
st.markdown("""
<style>
    /* ============================================================
       设计系统 - 财政政策舆情监测
       主题: 政务蓝 · refined
       配色:
         --primary:      #1a365d   深蓝（标题、导航）
         --accent:       #2b6cb0   中蓝（强调、按钮）
         --accent-light: #ebf4ff   浅蓝底（卡片、提示）
         --surface:      #ffffff   白色（卡片底色）
         --bg:           #f0f2f6   灰底（页面底色）
         --text:         #1a202c   深灰（正文）
         --text-muted:   #718096   灰色（辅助文字）
         --border:       #e2e8f0   边框色
         --positive:     #38a169   积极绿
         --neutral:      #d69e2e   中性橙
         --cautious:     #e53e3e   谨慎红
       ============================================================ */

    /* ---- 全局底色 ---- */
    .stApp { background-color: #f0f2f6; }
    .main > div { padding: 1.5rem 2.5rem; }

    /* ---- 排版层级 ---- */
    h1, h2, h3 { color: #1a365d !important; letter-spacing: -0.02em; }
    h1 { font-size: 1.75rem !important; font-weight: 700 !important; }
    h2 { font-size: 1.25rem !important; font-weight: 600 !important; }
    h3 { font-size: 1.05rem !important; font-weight: 600 !important; }
    .stSubheader { color: #1a365d; font-weight: 600; font-size: 1.1rem; }
    p, li { color: #1a202c; line-height: 1.7; }

    /* ---- 侧边栏（浅色） ---- */
    section[data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e2e8f0;
        color: #1a202c;
    }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stMarkdown p {
        color: #4a5568;
        font-size: 0.85rem;
        font-weight: 500;
    }
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
        background: #f7fafc;
        border: 1px solid #e2e8f0;
        color: #1a202c;
        border-radius: 8px;
        font-size: 0.9rem;
    }
    section[data-testid="stSidebar"] .stSelectbox svg { fill: #a0aec0; }
    section[data-testid="stSidebar"] hr { border-color: #e2e8f0; margin: 1rem 0; }
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        color: #1a365d !important;
    }

    /* ---- 指标卡片 ---- */
    .metric-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 18px 16px 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        border: 1px solid rgba(226,232,240,0.6);
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(26,54,93,0.10);
    }
    .metric-card .label {
        font-size: 0.8rem;
        color: #718096;
        margin-bottom: 4px;
        letter-spacing: 0.02em;
    }
    .metric-card .value {
        font-size: 1.75rem;
        font-weight: 700;
        color: #1a202c;
        line-height: 1.2;
    }
    .metric-card .value.positive { color: #38a169; }
    .metric-card .value.neutral  { color: #d69e2e; }
    .metric-card .value.cautious { color: #e53e3e; }

    /* ---- 洞察框（签名级卡片） ---- */
    .insight-card {
        background: #ffffff;
        border-left: 4px solid #2b6cb0;
        border-radius: 10px;
        padding: 18px 22px;
        margin: 8px 0 24px;
        box-shadow: 0 2px 6px rgba(26,54,93,0.08);
        line-height: 1.8;
        color: #2d3748;
        font-size: 0.9rem;
        position: relative;
    }
    .insight-card::before {
        content: "📌";
        position: absolute;
        top: -10px;
        left: -6px;
        font-size: 1.1rem;
        background: #f0f2f6;
        padding: 0 4px;
    }

    /* ---- 图表 ---- */
    .stImage img {
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border: 1px solid #edf2f7;
        transition: box-shadow 0.2s;
    }
    .stImage img:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.10); }

    /* ---- 分类标签 ---- */
    .category-badge {
        display: inline-block;
        padding: 2px 12px;
        border-radius: 14px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        letter-spacing: 0.02em;
    }

    /* ---- 下载按钮（outline 风格） ---- */
    .stDownloadButton button {
        background: #ffffff !important;
        color: #2b6cb0 !important;
        border: 1.5px solid #2b6cb0 !important;
        border-radius: 8px !important;
        padding: 4px 24px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
    }
    .stDownloadButton button:hover {
        background: #2b6cb0 !important;
        color: #ffffff !important;
        border-color: #2b6cb0 !important;
        box-shadow: 0 2px 8px rgba(43,108,176,0.2);
    }

    /* ---- expander 文章卡片 ---- */
    .streamlit-expanderHeader {
        background: #ffffff;
        border-radius: 10px 10px 0 0 !important;
        border: 1px solid #e2e8f0 !important;
        border-bottom: none !important;
        padding: 10px 16px !important;
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        transition: background 0.15s;
    }
    .streamlit-expanderHeader:hover { background: #f7fafc; }
    .streamlit-expanderHeader[aria-expanded="false"] {
        border-radius: 10px !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }
    .streamlit-expanderContent {
        border-left: 1px solid #e2e8f0 !important;
        border-right: 1px solid #e2e8f0 !important;
        border-bottom: 1px solid #e2e8f0 !important;
        border-radius: 0 0 10px 10px !important;
        background: #ffffff;
        padding: 14px 18px !important;
    }

    /* ---- 关键词标签 ---- */
    .keyword-tags {
        display: flex;
        flex-wrap: wrap;
        gap: 6px;
        padding: 4px 0 8px;
    }
    .keyword-tag {
        display: inline-block;
        padding: 3px 14px;
        border-radius: 20px;
        font-size: 0.82rem;
        font-weight: 500;
        background: #ebf4ff;
        color: #2b6cb0;
        border: 1px solid #d4e4fa;
        transition: all 0.15s ease;
        cursor: default;
    }
    .keyword-tag:hover {
        background: #2b6cb0;
        color: #ffffff;
        border-color: #2b6cb0;
        transform: translateY(-1px);
    }

    /* ---- 分隔线 ---- */
    hr {
        border-color: #e2e8f0 !important;
        margin: 1.5rem 0 !important;
        opacity: 0.7;
    }

    /* ---- 页脚 ---- */
    .footer-note {
        text-align: center;
        color: #a0aec0;
        font-size: 0.78rem;
        padding: 1.5rem 0 0.5rem;
        border-top: 1px solid #edf2f7;
        margin-top: 1.5rem;
    }

    /* ---- 代码风格的关键词（文章中） ---- */
    code {
        color: #2b6cb0 !important;
        background: #ebf4ff !important;
        padding: 1px 6px !important;
        border-radius: 4px !important;
        font-size: 0.82rem !important;
    }

    /* ---- 数据来源可追溯链接 ---- */
    a {
        color: #2b6cb0 !important;
        text-decoration: none !important;
        transition: color 0.15s;
    }
    a:hover { color: #1a365d !important; text-decoration: underline !important; }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 数据加载
# ============================================================

def list_reports():
    files = glob.glob(os.path.join(REPORT_DIR, "*.json"))
    tags = []
    for f in files:
        name = os.path.basename(f).replace(".json", "")
        try:
            parts = name.split("-W")
            year = parts[0]
            week = int(parts[1])
            tags.append((year, week, name))
        except:
            continue
    tags.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return tags


def load_report(week_tag):
    path = os.path.join(REPORT_DIR, f"{week_tag}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


reports = list_reports()
if not reports:
    st.error("暂无报告数据。请先运行:\n1. python data_collector.py\n2. python analyzer.py")
    st.stop()

# ============================================================
# 侧边栏
# ============================================================
st.sidebar.title("📊 舆情监测")
st.sidebar.markdown("---")

years = sorted(set(r[0] for r in reports), reverse=True)
sel_year = st.sidebar.selectbox("年份", years)
year_reports = [r for r in reports if r[0] == sel_year]

# 构建带日期范围的周次选项
from datetime import date
week_options = []
for yr, wk, tag in year_reports:
    monday = date.fromisocalendar(int(yr), wk, 1)
    sunday = date.fromisocalendar(int(yr), wk, 7)
    if monday.month == sunday.month:
        label = f"{monday.month}月{monday.day}日-{sunday.day}日"
    else:
        label = f"{monday.month}月{monday.day}日-{sunday.month}月{sunday.day}日"
    week_options.append((label, tag))

sel_idx = st.sidebar.selectbox(
    "周次", range(len(week_options)),
    format_func=lambda i: week_options[i][0],
)
week_tag = week_options[sel_idx][1]
report = load_report(week_tag)
if not report:
    st.error(f"无法加载周报: {week_tag}")
    st.stop()

# --- 异常检测：计算全部周的情绪均值和标准差 ---
all_scores = []
for _, _, tag in year_reports:
    rpt = load_report(tag)
    if rpt:
        all_scores.append(rpt["sentiment_summary"]["average_score"])
if len(all_scores) > 1:
    import statistics
    mean_score = statistics.mean(all_scores)
    std_score = statistics.stdev(all_scores)
    curr_score = report["sentiment_summary"]["average_score"]
    deviation = curr_score - mean_score
    if abs(deviation) > std_score:
        direction = "偏高" if deviation > 0 else "偏低"
        emoji = "📈" if deviation > 0 else "📉"
        st.warning(
            f"{emoji} **本周情绪异常{direction}** — "
            f"当前 {curr_score:.2f}，全部周均值 {mean_score:.2f}±{std_score:.2f}，"
            f"偏离 {abs(deviation):.2f}（超过 1 个标准差），建议关注。"
        )

# ============================================================
# 主内容区 — 标签页
# ============================================================
tab1, tab2 = st.tabs(["📋 周报", "📊 对比"])

with tab1:
    st.title(f"📋 财政政策舆情周报")
    st.caption(f"**{week_tag}** · 生成时间: {report.get('generated_at','未知')[:19]}")

    # --- 指标卡片 ---
    ss = report["sentiment_summary"]
    sentiment_class = (
        "positive" if ss["average_score"] > 0.1
        else "cautious" if ss["average_score"] < -0.1
        else "neutral"
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="label">📈 平均情绪</div>'
            f'<div class="value {sentiment_class}">{ss["average_score"]:.2f}</div>'
            f'</div>',
            unsafe_allow_html=True)
    with c2:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="label">😊 积极</div>'
            f'<div class="value positive">{ss["positive_count"]}</div>'
            f'</div>',
            unsafe_allow_html=True)
    with c3:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="label">😐 中性</div>'
            f'<div class="value neutral">{ss["neutral_count"]}</div>'
            f'</div>',
            unsafe_allow_html=True)
    with c4:
        st.markdown(
            f'<div class="metric-card">'
            f'<div class="label">😟 谨慎</div>'
            f'<div class="value cautious">{ss["cautious_count"]}</div>'
            f'</div>',
            unsafe_allow_html=True)

    # --- 洞察框 ---
    st.subheader("📌 本周财政风向洞察")
    st.markdown(
        f'<div class="insight-card">{report.get("weekly_insight", "暂无洞察")}</div>',
        unsafe_allow_html=True
    )

    # --- 可视化图表 ---
    st.subheader("📊 可视化分析")
    chart_cols = st.columns(2)
    with chart_cols[0]:
        cp = os.path.join(CHART_DIR, "sentiment_trend.png")
        if os.path.exists(cp):
            st.image(cp, use_container_width=True)
    with chart_cols[1]:
        cp = os.path.join(CHART_DIR, f"category_dist_{week_tag}.png")
        if os.path.exists(cp):
            st.image(cp, use_container_width=True)

    # --- 关键词标签 ---
    st.subheader("🏷️ 本周关键词")
    all_kws = report.get("all_keywords", [])
    if all_kws:
        tags_html = '<div class="keyword-tags">'
        for kw in sorted(all_kws):
            tags_html += f'<span class="keyword-tag">{kw}</span>'
        tags_html += "</div>"
        st.markdown(tags_html, unsafe_allow_html=True)

    # --- 本周政策详情 ---
    st.markdown("---")
    st.subheader("📑 本周政策详情")

    CATEGORY_COLORS = {
        "减税降费": "#38a169", "财政支出": "#2b6cb0",
        "债务管理": "#d69e2e", "产业扶持": "#805ad5",
        "民生保障": "#e53e3e", "财政改革": "#dd6b20",
        "其他": "#718096",
    }

    # 文章按来源优先级排序：官方 > 财经媒体 > 社交媒体
    SOURCE_PRIORITY = {"官方": 0, "财经媒体": 1, "社交媒体": 2}
    sorted_articles = sorted(
        report.get("articles", []),
        key=lambda a: SOURCE_PRIORITY.get(a.get("source_type", ""), 99)
    )

    for i, art in enumerate(sorted_articles, 1):
        an = art.get("analysis", {})
        cat = an.get("category", "其他")
        cat_color = CATEGORY_COLORS.get(cat, "#718096")
        s = an.get("sentiment_label", "中性")
        sentiment_icon = {"积极": "📈", "中性": "📊", "谨慎": "📉"}
        title_text = f"{i}. [{cat}] {art['title'][:60]}"
        with st.expander(title_text, expanded=(i <= 3)):
            badge = f'<span class="category-badge" style="background:{cat_color}20;color:{cat_color};">{cat}</span>'
            st.markdown(f"{badge} **{art['title']}**", unsafe_allow_html=True)
            st.markdown(
                f"**来源**: {art['source']} | "
                f"**情绪**: {sentiment_icon.get(s, '📋')} {s} ({an.get('sentiment_score', 0):+.2f})"
                + (f" | **发布**: {art['published_date']}" if art.get('published_date') else "")
            )
            if an.get("keywords"):
                st.markdown("**关键词**: " + " ".join([f"`{k}`" for k in an["keywords"]]))
                # entity display
                ent = an.get("entities", {})
                if isinstance(ent, dict):
                    ent_parts = []
                    for label, key in [("部门", "departments"), ("金额", "amounts"), ("工具", "tools"), ("人物", "people")]:
                        items = ent.get(key, [])
                        if items:
                            ent_parts.append(f"**{label}**: " + " ".join([f"`{i}`" for i in items]))
                    if ent_parts:
                        st.markdown(" | ".join(ent_parts))
            if art.get("url"):
                st.markdown(f"[🔗 查看原文]({art['url']})")
            st.caption(
                (art.get("summary", "") or art.get("content", "")[:200])[:200]
            )

    # --- 下载 ---
    st.markdown("---")
    st.subheader("📥 下载")
    md_path = os.path.join(CHART_DIR, f"{week_tag}.md")
    pdf_path = os.path.join(CHART_DIR, f"{week_tag}.pdf")
    d1, d2, _ = st.columns(3)
    with d1:
        if os.path.exists(md_path):
            with open(md_path, "r", encoding="utf-8") as f:
                st.download_button("📄 下载 Markdown", f.read(), file_name=f"{week_tag}.md")
    with d2:
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                st.download_button("📕 下载 PDF", f.read(), file_name=f"{week_tag}.pdf")

    st.markdown(
        '<div class="footer-note">数据来源可追溯 · 分析基于 DeepSeek AI</div>',
        unsafe_allow_html=True
    )

with tab2:
    st.title("📊 多周对比分析")
    st.caption("选择两周进行并排对比")

    col_a, col_b = st.columns(2)
    with col_a:
        wk_opts_a = [f"第{r[1]}周 ({r[2]})" for r in year_reports]
        sel_a = st.selectbox("对比周次 A", wk_opts_a, key="comp_a")
        tag_a = sel_a.split(" (")[1].split(")")[0]
    with col_b:
        wk_opts_b = [f"第{r[1]}周 ({r[2]})" for r in year_reports]
        sel_b = st.selectbox("对比周次 B", wk_opts_b, key="comp_b", index=1 if len(wk_opts_b) > 1 else 0)
        tag_b = sel_b.split(" (")[1].split(")")[0]

    rpt_a = load_report(tag_a)
    rpt_b = load_report(tag_b)

    if rpt_a and rpt_b:
        sa = rpt_a["sentiment_summary"]
        sb = rpt_b["sentiment_summary"]

        st.markdown("---")
        c1, c2 = st.columns(2)
        for col, rpt, tag in [(c1, rpt_a, tag_a), (c2, rpt_b, tag_b)]:
            with col:
                s = rpt["sentiment_summary"]
                st.subheader(f"📋 {tag}")
                m1, m2 = st.columns(2)
                with m1:
                    st.markdown(f'<div class="metric-card"><div class="label">📈 平均情绪</div><div class="value">{s["average_score"]:.2f}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-card"><div class="label">😊 积极</div><div class="value positive">{s["positive_count"]}</div></div>', unsafe_allow_html=True)
                with m2:
                    st.markdown(f'<div class="metric-card"><div class="label">😐 中性</div><div class="value neutral">{s["neutral_count"]}</div></div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="metric-card"><div class="label">😟 谨慎</div><div class="value cautious">{s["cautious_count"]}</div></div>', unsafe_allow_html=True)

        # 图表对比
        st.markdown("---")
        st.subheader("📊 类别分布对比")
        cc1, cc2 = st.columns(2)
        with cc1:
            cp = os.path.join(CHART_DIR, f"category_dist_{tag_a}.png")
            if os.path.exists(cp):
                st.image(cp, use_container_width=True)
        with cc2:
            cp = os.path.join(CHART_DIR, f"category_dist_{tag_b}.png")
            if os.path.exists(cp):
                st.image(cp, use_container_width=True)

        # 文章对比
        st.markdown("---")
        st.subheader("📑 文章对比")
        ac1, ac2 = st.columns(2)
        for col, rpt in [(ac1, rpt_a), (ac2, rpt_b)]:
            with col:
                for art in rpt.get("articles", [])[:4]:
                    an = art.get("analysis", {})
                    cat = an.get("category", "其他")
                    s = an.get("sentiment_label", "中性")
                    icon = {"积极": "📈", "中性": "📊", "谨慎": "📉"}
                    st.markdown(f"**[{cat}]** {icon.get(s,'')} {art['title'][:40]}")
                    st.caption(f"来源: {art['source']}" + (f" · {art['published_date']}" if art.get('published_date') else ""))
                    st.markdown("---")
