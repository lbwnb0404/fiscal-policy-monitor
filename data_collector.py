# -*- coding: utf-8 -*-
"""data_collector.py - 数据采集模块"""

import sys, os, json, re, hashlib
from datetime import datetime

from config import PROJECT_DIR, RAW_DIR, HEADERS, NAV_TITLES, POLICY_KEYWORDS, SOURCES, BILIBILI_KEYWORDS
from config import FETCH_RETRIES, FETCH_TIMEOUT

import requests
import time


# ============================================================
# HTTP 工具
# ============================================================

def _request_with_retry(url, headers=None, timeout=FETCH_TIMEOUT, process=None):
    """带重试的 HTTP 请求（指数退避），process 参数为处理成功响应的函数"""
    if headers is None:
        headers = HEADERS
    for attempt in range(FETCH_RETRIES + 1):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            if r.status_code == 200:
                return process(r) if process else r.text
            if attempt < FETCH_RETRIES:
                print(f"  [RETRY] HTTP {r.status_code} ({attempt+1}/{FETCH_RETRIES})")
        except requests.Timeout:
            if attempt < FETCH_RETRIES:
                print(f"  [RETRY] timeout ({attempt+1}/{FETCH_RETRIES})")
        except requests.ConnectionError:
            if attempt < FETCH_RETRIES:
                print(f"  [RETRY] connection ({attempt+1}/{FETCH_RETRIES})")
        except Exception as e:
            if attempt < FETCH_RETRIES:
                print(f"  [RETRY] {str(e)[:30]} ({attempt+1}/{FETCH_RETRIES})")
        if attempt < FETCH_RETRIES:
            time.sleep(1.5 ** attempt)
    return None


def fetch(url, timeout=FETCH_TIMEOUT):
    """获取 HTML 页面（带重试，指数退避）"""
    def _process(r):
        r.encoding = r.apparent_encoding
        return r.text
    result = _request_with_retry(url, timeout=timeout, process=_process)
    return result or ""


def fetch_json(url, timeout=FETCH_TIMEOUT):
    """获取 JSON API 响应（带重试，指数退避）"""
    headers = {**HEADERS, "Referer": "https://search.bilibili.com/"}
    result = _request_with_retry(url, headers=headers, timeout=timeout, process=lambda r: r.json())
    return result


# ============================================================
# HTML 解析
# ============================================================

def find_article_links(html, base_url):
    raw = re.findall(r'href="([^"]*\.(?:htm|html)[^"]*)"', html, re.IGNORECASE)
    seen, links = set(), []
    for href in raw:
        if href.startswith("http"):
            full = href
        elif href.startswith("/"):
            full = re.match(r"(https?://[^/]+)", base_url).group(1) + href
        elif href.startswith("./"):
            full = base_url.rstrip("/") + href[1:]
        else:
            full = base_url.rstrip("/") + "/" + href
        full = full.split("?")[0]
        if full not in seen:
            seen.add(full)
            links.append(full)
    return links


def extract_title(html, url=""):
    m = re.search(r"<title>\s*([^<]+)\s*</title>", html, re.IGNORECASE)
    if m:
        title = m.group(1).strip()
        title = re.sub(r"[_\-—·].*$", "", title).strip()
        if title and title not in NAV_TITLES and not any(
            n in title for n in ["人民网", "网站首页", "登录", "注册", "经济·科技"]
        ):
            return title
    m = re.search(r"/([^/]+)\.(?:htm|html)$", url)
    if m:
        t = m.group(1).replace("_", " ")[:50]
        if t.lower() in ("index", "default", "gb", "main", "list"):
            return ""
        return t
    return ""


def extract_content(html):
    clean = re.sub(
        r"<(script|style)[^>]*>.*?</\1>", "", html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    clean = re.sub(r"<[^>]+>", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    for nav in [
        "网站首页", "登录人民网通行证", "注册", "退出",
        "返回上级", "-->", "EN -->",
    ]:
        clean = clean.replace(nav, "")
    return re.sub(r"\s+", " ", clean).strip()[:2000]


def is_relevant(title, content=""):
    text = title + content[:300]
    for kw in POLICY_KEYWORDS:
        if kw in text:
            return True
    return False


# ============================================================
# 日期提取
# ============================================================

def extract_publish_date(html, url=""):
    """从文章 HTML 中提取发布日期，返回 YYYY-MM-DD 或空字符串"""
    import re as _re
    from datetime import datetime as _dt

    # 1. 中文日期: 2026年5月28日 / 2026年05月28日
    m = _re.search(r"(20\d{2})\u5e74(\d{1,2})\u6708(\d{1,2})\u65e5", html)
    if m:
        try:
            return _dt(int(m.group(1)), int(m.group(2)), int(m.group(3))).strftime("%Y-%m-%d")
        except ValueError:
            pass

    # 2. ISO 日期: 2026-05-28
    m = _re.search(r"(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])", html)
    if m:
        return m.group(0)

    # 3. 斜杠日期: 2026/05/28
    m = _re.search(r"(20\d{2})/(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])", html)
    if m:
        return m.group(0).replace("/", "-")

    # 4. B站时间戳已由调用方处理
    return ""


# ============================================================
# B站采集
# ============================================================

def collect_bilibili(source, max_articles=3):
    """通过 B站 JSON API 搜索并提取视频信息（轮换多个关键词）"""
    arts = []
    per_keyword = max(1, max_articles // len(BILIBILI_KEYWORDS))
    for kw in BILIBILI_KEYWORDS:
        if len(arts) >= max_articles:
            break
        print(f"[{source['name']}] searching '{kw}'...", end=" ", flush=True)
        data = fetch_json(
            f"{source['url']}?search_type=video&keyword={requests.utils.quote(kw)}&page=1"
        )
        if not data or data.get("code") != 0:
            print("FAILED")
            continue
        results = data["data"].get("result", [])
        print(f"{len(results)} found")
        for v in results[:per_keyword]:
            title = (
                v.get("title", "")
                .replace('<em class="keyword">', "")
                .replace("</em>", "")
                .strip()
            )
            if not title:
                continue
            # 跳过课程/教程等非新闻类视频
            skip_kws = ["讲", "教程", "课程", "精品", "课件", "公开课", "课堂", "微课"]
            if any(kw in title for kw in skip_kws):
                continue
            url = f"https://www.bilibili.com/video/{v.get('bvid','')}" if v.get("bvid") else ""
            if any(a["url"] == url for a in arts):
                continue
            bvid = v.get("bvid", "")
            desc = v.get("description", "")[:200]
            tags = v.get("tag", "")
            play = v.get("play", 0)
            content = f"{title} {desc} 标签:{tags}"
            from datetime import datetime as _dt
            pubdate_ts = v.get("pubdate", 0)
            pubdate_str = _dt.fromtimestamp(pubdate_ts).strftime("%Y-%m-%d") if pubdate_ts else ""
            arts.append(
                {
                    "article_id": hashlib.md5(
                        f"B站-{title}".encode()
                    ).hexdigest()[:12],
                    "title": title[:80],
                    "source": "B站",
                    "source_type": "社交媒体",
                    "platform": "bilibili.com",
                    "url": url,
                    "content": content,
                    "summary": title[:200],
                    "published_date": pubdate_str,
                    "collected_at": datetime.now().isoformat(),
                    "play": v.get("play", 0),
                }
            )
            if len(arts) >= max_articles:
                break
    # B站结果按播放量降序排列，优先展示热门视频
    arts.sort(key=lambda a: a.get("play", 0), reverse=True)
    return arts


# ============================================================
# 通用采集
# ============================================================

def collect_from_source(source, max_articles=3):
    if source["name"] == "B站":
        return collect_bilibili(source, max_articles)
    arts = []
    print(f"[{source['name']}] fetching {source['url'][:50]}...", end=" ")
    html = fetch(source["url"])
    if not html:
        print("FAILED")
        return arts
    links = find_article_links(html, source["url"])
    print(f"{len(links)} links found")
    for link_url in links[:20]:
        if len(arts) >= max_articles:
            break
        try:
            page_html = fetch(link_url)
            if not page_html or len(page_html) < 500:
                continue
            title = extract_title(page_html, link_url)
            if not title or len(title) < 4:
                continue
            if not is_relevant(title, page_html[:500]):
                continue
            content = extract_content(page_html)
            if len(content) < 100:
                continue
            arts.append(
                {
                    "article_id": hashlib.md5(
                        f"{source['name']}-{title}".encode()
                    ).hexdigest()[:12],
                    "title": title[:80],
                    "source": source["name"],
                    "source_type": source["type"],
                    "platform": re.sub(
                        r"https?://([^/]+).*", r"\1", source["base"]
                    ),
                    "url": link_url,
                    "content": content,
                    "summary": content[:200],
                    "published_date": extract_publish_date(page_html, link_url),
                    "collected_at": datetime.now().isoformat(),
                }
            )
            print(f"  + [{source['name']}] {title[:35]}")
        except Exception:
            continue
    return arts


# ============================================================
# 去重 & 保存
# ============================================================

def deduplicate(articles):
    seen = set()
    result = []
    for a in articles:
        if a["url"] not in seen:
            seen.add(a["url"])
            result.append(a)
    return result


def save_articles(articles, week_tag):
    path = os.path.join(RAW_DIR, f"{week_tag}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] {len(articles)} articles -> {path}")
    return path


# ============================================================
# 入口
# ============================================================

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--week", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-per-source", type=int, default=2)
    args = parser.parse_args()

    from config import current_week_tag

    week_tag = args.week or current_week_tag()
    print(f"Data Collection - {week_tag}\n")

    all_arts = []
    for src in SOURCES:
        try:
            arts = collect_from_source(src, max_articles=args.max_per_source)
            all_arts.extend(arts)
        except Exception as e:
            print(f"[ERROR] {src['name']}: {e}")

    all_arts = deduplicate(all_arts)
    print(f"\nTotal: {len(all_arts)} articles")

    if args.dry_run:
        print("(dry-run, not saved)")
    else:
        save_articles(all_arts, week_tag)

    return all_arts


if __name__ == "__main__":
    main()
