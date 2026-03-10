#!/usr/bin/env python3

from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import http.client
import ipaddress
import json
import shutil
import socket
import ssl
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CHROME_BASE = Path.home() / "Library/Application Support/Google/Chrome"
DEFAULT_REPORT_PATH = Path("playground/chrome_bookmarks_report.json")
DEFAULT_BACKUP_DIR = Path("playground/chrome_bookmarks_backups")
GENERATED_FOLDER_PREFIX = "自动整理 - "
GENERATED_CATEGORY_SUFFIX = "（自动整理）"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0 Safari/537.36"
)
DEAD_HTTP_CODES = {404, 410, 451}
RESTRICTED_HTTP_CODES = {401, 403, 405, 407, 429}
TRANSIENT_HTTP_CODES = {408, 425, 500, 502, 503, 504}
SKIPPED_SCHEMES = {"chrome", "chrome-extension", "javascript", "data", "about"}


CATEGORY_RULES: list[tuple[str, set[str], tuple[str, ...]]] = [
    (
        "人工智能与大模型",
        {
            "openai.com",
            "chatgpt.com",
            "anthropic.com",
            "claude.ai",
            "huggingface.co",
            "replicate.com",
            "perplexity.ai",
            "poe.com",
            "midjourney.com",
            "deepseek.com",
        },
        ("ai", "llm", "gpt", "agent", "prompt", "anthropic", "huggingface", "模型"),
    ),
    (
        "开发工具",
        {
            "github.com",
            "gitlab.com",
            "bitbucket.org",
            "stackoverflow.com",
            "superuser.com",
            "serverfault.com",
            "npmjs.com",
            "pypi.org",
            "brew.sh",
            "docker.com",
            "kubernetes.io",
            "vercel.com",
            "netlify.com",
            "cloudflare.com",
            "postman.com",
        },
        (
            "github",
            "gitlab",
            "docker",
            "kubernetes",
            "terraform",
            "npm",
            "pypi",
            "brew",
            "cli",
            "terminal",
            "devops",
            "api",
            "sdk",
            "代码",
            "开发",
        ),
    ),
    (
        "技术文档",
        {
            "developer.mozilla.org",
            "docs.python.org",
            "docs.github.com",
            "readthedocs.io",
            "devdocs.io",
            "w3.org",
            "nodejs.org",
            "react.dev",
            "vuejs.org",
            "nextjs.org",
            "docs.aws.amazon.com",
            "cloud.google.com",
            "learn.microsoft.com",
        },
        (
            "docs",
            "documentation",
            "reference",
            "readthedocs",
            "mdn",
            "spec",
            "manual",
            "指南",
            "文档",
            "参考",
        ),
    ),
    (
        "学习课程",
        {
            "coursera.org",
            "udemy.com",
            "edx.org",
            "freecodecamp.org",
            "leetcode.com",
            "exercism.org",
            "codecademy.com",
            "khanacademy.org",
        },
        ("course", "tutorial", "lesson", "learn", "training", "练习", "课程", "教程", "学习"),
    ),
    (
        "论文研究",
        {
            "arxiv.org",
            "scholar.google.com",
            "semanticscholar.org",
            "nature.com",
            "science.org",
            "ieee.org",
            "acm.org",
        },
        ("paper", "arxiv", "research", "study", "journal", "论文", "研究"),
    ),
    (
        "社交社区",
        {
            "x.com",
            "twitter.com",
            "reddit.com",
            "news.ycombinator.com",
            "zhihu.com",
            "weibo.com",
            "v2ex.com",
            "discord.com",
            "facebook.com",
            "linkedin.com",
        },
        ("reddit", "forum", "community", "discussion", "blog", "社区", "论坛", "问答"),
    ),
    (
        "影音娱乐",
        {
            "youtube.com",
            "youtu.be",
            "bilibili.com",
            "vimeo.com",
            "spotify.com",
            "music.apple.com",
            "netflix.com",
            "iqiyi.com",
            "qq.com",
        },
        ("video", "watch", "music", "movie", "podcast", "视频", "音乐", "电影"),
    ),
    (
        "办公效率",
        {
            "docs.google.com",
            "notion.so",
            "notion.site",
            "trello.com",
            "slack.com",
            "figma.com",
            "miro.com",
            "feishu.cn",
            "larksuite.com",
            "airtable.com",
        },
        ("calendar", "spreadsheet", "doc", "notion", "project", "会议", "表格", "协作", "效率"),
    ),
    (
        "购物消费",
        {
            "amazon.com",
            "taobao.com",
            "tmall.com",
            "jd.com",
            "ebay.com",
            "aliexpress.com",
            "bestbuy.com",
            "ikea.com",
        },
        ("shop", "store", "product", "cart", "deal", "购买", "商品", "店铺", "优惠"),
    ),
    (
        "新闻资讯",
        {
            "nytimes.com",
            "wsj.com",
            "bbc.com",
            "cnn.com",
            "theguardian.com",
            "36kr.com",
            "jiqizhixin.com",
            "ifanr.com",
        },
        ("news", "article", "report", "analysis", "资讯", "新闻", "报道"),
    ),
    (
        "生活工具",
        {
            "maps.google.com",
            "google.com",
            "translate.google.com",
            "wikipedia.org",
            "weather.com",
            "timeanddate.com",
        },
        ("translate", "map", "weather", "wiki", "tool", "工具", "地图", "百科"),
    ),
]


@dataclass
class BookmarkRecord:
    title: str
    url: str
    root: str
    folder_path: tuple[str, ...]

    @property
    def path_display(self) -> str:
        parts = [self.root, *self.folder_path, self.title]
        return " / ".join(part for part in parts if part)


@dataclass
class UrlCheckResult:
    status: str
    http_status: int | None
    detail: str
    final_url: str | None = None


def chrome_timestamp_now() -> str:
    epoch = dt.datetime(1601, 1, 1, tzinfo=dt.timezone.utc)
    now = dt.datetime.now(dt.timezone.utc)
    micros = int((now - epoch).total_seconds() * 1_000_000)
    return str(micros)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def host_matches(host: str, domain: str) -> bool:
    return host == domain or host.endswith(f".{domain}")


def is_generated_folder(name: str) -> bool:
    return name.startswith(GENERATED_FOLDER_PREFIX) or name.endswith(GENERATED_CATEGORY_SUFFIX)


def generated_category_name(category: str) -> str:
    if category.endswith(GENERATED_CATEGORY_SUFFIX):
        return category
    return f"{category}{GENERATED_CATEGORY_SUFFIX}"


def classify_bookmark(title: str, url: str, context: str = "") -> str:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    haystack = f"{context} {title} {url}".lower()

    if parsed.scheme == "file":
        return "本地文件"
    if parsed.scheme in SKIPPED_SCHEMES:
        return "浏览器内部"
    if host:
        if host.startswith("docs.") or "/docs" in parsed.path.lower():
            return "技术文档"
        if any(token in host for token in ("git", "repo", "code")):
            return "开发工具"

    for category, domains, keywords in CATEGORY_RULES:
        if any(host_matches(host, domain) for domain in domains):
            return category
        if any(keyword in haystack for keyword in keywords):
            return category

    if any(host_matches(host, domain) for domain in {"medium.com", "substack.com", "dev.to", "hashnode.com"}):
        return "博客文章"
    if any(host_matches(host, domain) for domain in {"figma.com", "dribbble.com", "behance.net", "pinterest.com"}):
        return "设计灵感"
    if any(host_matches(host, domain) for domain in {"gmail.com", "outlook.com", "mail.google.com"}):
        return "邮箱通信"
    return "未分类"


def list_profiles(base_dir: Path = CHROME_BASE) -> list[tuple[str, str, Path]]:
    local_state = base_dir / "Local State"
    if not local_state.exists():
        return []
    state = load_json(local_state)
    info_cache = ((state.get("profile") or {}).get("info_cache") or {})
    profiles: list[tuple[str, str, Path]] = []
    for directory_name, profile_info in sorted(info_cache.items()):
        bookmarks_path = base_dir / directory_name / "Bookmarks"
        if bookmarks_path.exists():
            profiles.append((directory_name, profile_info.get("name", directory_name), bookmarks_path))
    return profiles


def resolve_bookmarks_path(profile_hint: str | None, bookmarks_file: Path | None) -> Path:
    if bookmarks_file:
        return bookmarks_file.expanduser().resolve()

    profiles = list_profiles()
    if not profiles:
        raise SystemExit("未找到 Chrome 书签文件。")

    if not profile_hint:
        if len(profiles) == 1:
            return profiles[0][2]
        profile_hint = "Profile 1"

    for directory_name, display_name, path in profiles:
        if profile_hint in {directory_name, display_name}:
            return path

    available = ", ".join(f"{display} ({directory})" for directory, display, _ in profiles)
    raise SystemExit(f"找不到 profile={profile_hint!r}。可用 profile: {available}")


def collect_bookmarks(data: dict[str, Any], source_roots: tuple[str, ...]) -> list[BookmarkRecord]:
    results: list[BookmarkRecord] = []

    def walk(node: dict[str, Any], root_name: str, parents: tuple[str, ...]) -> None:
        node_type = node.get("type")
        if node_type == "url":
            results.append(
                BookmarkRecord(
                    title=node.get("name", ""),
                    url=node.get("url", ""),
                    root=root_name,
                    folder_path=parents,
                )
            )
            return
        if node_type == "folder":
            folder_name = node.get("name", "")
            if folder_name and is_generated_folder(folder_name):
                return
            next_parents = parents if not folder_name else (*parents, folder_name)
            for child in node.get("children", []) or []:
                walk(child, root_name, next_parents)

    roots = data.get("roots") or {}
    root_labels = {
        "bookmark_bar": "书签栏",
        "other": "其他书签",
        "synced": "移动设备书签",
    }
    for root_key in source_roots:
        root_node = roots.get(root_key)
        if not root_node:
            continue
        display_name = root_labels.get(root_key, root_key)
        for child in root_node.get("children", []) or []:
            walk(child, display_name, ())
    return results


def is_private_hostname(hostname: str | None) -> bool:
    if not hostname:
        return True
    hostname = hostname.lower()
    if hostname in {"localhost", "127.0.0.1"}:
        return True
    if hostname.endswith(".local") or hostname.endswith(".lan"):
        return True
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return "." not in hostname
    return ip.is_private or ip.is_loopback or ip.is_link_local


def probe_once(url: str, timeout: float, method: str) -> tuple[int | None, str | None, str | None]:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.getcode(), response.url, None


def check_url(url: str, timeout: float) -> UrlCheckResult:
    parsed = urllib.parse.urlparse(url)
    scheme = parsed.scheme.lower()
    if not scheme:
        return UrlCheckResult("invalid", None, "缺少 URL scheme")
    if scheme in SKIPPED_SCHEMES:
        return UrlCheckResult("skipped", None, f"跳过 {scheme} 链接")
    if scheme == "file":
        path = Path(urllib.request.url2pathname(parsed.path))
        if path.exists():
            return UrlCheckResult("alive", None, "本地文件存在")
        return UrlCheckResult("dead", None, "本地文件不存在")
    if scheme not in {"http", "https"}:
        return UrlCheckResult("skipped", None, f"不检查 {scheme} 链接")

    hostname = parsed.hostname
    if is_private_hostname(hostname):
        return UrlCheckResult("skipped", None, "内网或本地地址，默认跳过")

    def classify_http(code: int, final_url: str | None) -> UrlCheckResult:
        if code in DEAD_HTTP_CODES:
            return UrlCheckResult("dead", code, f"HTTP {code}", final_url)
        if code in TRANSIENT_HTTP_CODES:
            return UrlCheckResult("unreachable", code, f"HTTP {code}", final_url)
        return UrlCheckResult("alive", code, f"HTTP {code}", final_url)

    try:
        code, final_url, _ = probe_once(url, timeout, "HEAD")
        if code is not None:
            return classify_http(code, final_url)
    except urllib.error.HTTPError as error:
        if error.code in {405, 501}:
            pass
        else:
            return classify_http(error.code, error.url)
    except urllib.error.URLError as error:
        reason = error.reason
        if isinstance(reason, socket.gaierror):
            return UrlCheckResult("unreachable", None, f"DNS 解析失败: {reason}")
        if isinstance(reason, TimeoutError):
            return UrlCheckResult("unreachable", None, f"连接超时: {reason}")
        if isinstance(reason, ssl.SSLError):
            return UrlCheckResult("unreachable", None, f"TLS 错误: {reason}")
        return UrlCheckResult("unreachable", None, f"连接失败: {reason}")
    except (TimeoutError, socket.timeout) as error:
        return UrlCheckResult("unreachable", None, f"连接超时: {error}")
    except ssl.SSLError as error:
        return UrlCheckResult("unreachable", None, f"TLS 错误: {error}")
    except http.client.RemoteDisconnected as error:
        return UrlCheckResult("unreachable", None, f"远端提前断开: {error}")
    except ValueError as error:
        return UrlCheckResult("invalid", None, f"URL 非法: {error}")

    try:
        code, final_url, _ = probe_once(url, timeout, "GET")
        if code is not None:
            return classify_http(code, final_url)
    except urllib.error.HTTPError as error:
        return classify_http(error.code, error.url)
    except urllib.error.URLError as error:
        reason = error.reason
        if isinstance(reason, socket.gaierror):
            return UrlCheckResult("unreachable", None, f"DNS 解析失败: {reason}")
        if isinstance(reason, TimeoutError):
            return UrlCheckResult("unreachable", None, f"连接超时: {reason}")
        if isinstance(reason, ssl.SSLError):
            return UrlCheckResult("unreachable", None, f"TLS 错误: {reason}")
        return UrlCheckResult("unreachable", None, f"连接失败: {reason}")
    except (TimeoutError, socket.timeout) as error:
        return UrlCheckResult("unreachable", None, f"连接超时: {error}")
    except ssl.SSLError as error:
        return UrlCheckResult("unreachable", None, f"TLS 错误: {error}")
    except http.client.RemoteDisconnected as error:
        return UrlCheckResult("unreachable", None, f"远端提前断开: {error}")
    except ValueError as error:
        return UrlCheckResult("invalid", None, f"URL 非法: {error}")

    return UrlCheckResult("unreachable", None, "未知网络错误")


def run_url_checks(urls: list[str], timeout: float, concurrency: int) -> dict[str, UrlCheckResult]:
    results: dict[str, UrlCheckResult] = {}
    if not urls:
        return results
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, concurrency)) as executor:
        future_map = {executor.submit(check_url, url, timeout): url for url in urls}
        for future in concurrent.futures.as_completed(future_map):
            url = future_map[future]
            try:
                results[url] = future.result()
            except Exception as error:
                results[url] = UrlCheckResult("unreachable", None, f"探测异常: {type(error).__name__}: {error}")
    return results


def max_numeric_id(data: dict[str, Any]) -> int:
    highest = 0

    def walk(node: Any) -> None:
        nonlocal highest
        if isinstance(node, dict):
            raw_id = node.get("id")
            if isinstance(raw_id, str) and raw_id.isdigit():
                highest = max(highest, int(raw_id))
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
    return highest


def chrome_running() -> bool:
    result = subprocess.run(
        ["pgrep", "-x", "Google Chrome"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def make_folder(name: str, next_id: int) -> tuple[dict[str, Any], int]:
    stamp = chrome_timestamp_now()
    folder = {
        "type": "folder",
        "name": name,
        "id": str(next_id),
        "guid": str(uuid.uuid4()),
        "date_added": stamp,
        "date_modified": stamp,
        "children": [],
    }
    return folder, next_id + 1


def make_url(title: str, url: str, next_id: int) -> tuple[dict[str, Any], int]:
    bookmark = {
        "type": "url",
        "name": title,
        "url": url,
        "id": str(next_id),
        "guid": str(uuid.uuid4()),
        "date_added": chrome_timestamp_now(),
    }
    return bookmark, next_id + 1


def organize_bookmarks(
    data: dict[str, Any],
    bookmarks: list[BookmarkRecord],
    checks: dict[str, UrlCheckResult],
    target_root: str,
    folder_name: str | None,
    top_level: bool,
) -> list[str]:
    root = (data.get("roots") or {}).get(target_root)
    if root is None:
        raise SystemExit(f"Chrome 书签里不存在 root={target_root!r}")

    next_id = max_numeric_id(data) + 1
    buckets: dict[str, dict[str, Any]] = {}
    created_names: list[str] = []

    aliveish = {"alive", "skipped", "unreachable"}
    chosen = [item for item in bookmarks if checks.get(item.url, UrlCheckResult("alive", None, "未检查")).status in aliveish]
    chosen.sort(key=lambda item: (classify_bookmark(item.title, item.url, " ".join(item.folder_path)), item.title.lower(), item.url.lower()))

    container: dict[str, Any] | None = None
    if not top_level:
        if not folder_name:
            folder_name = GENERATED_FOLDER_PREFIX + dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        container, next_id = make_folder(folder_name, next_id)
        created_names.append(folder_name)

    for bookmark in chosen:
        category = classify_bookmark(bookmark.title, bookmark.url, " ".join(bookmark.folder_path))
        bucket_key = category
        category_node = buckets.get(bucket_key)
        if category_node is None:
            display_name = generated_category_name(category) if top_level else category
            category_node, next_id = make_folder(display_name, next_id)
            buckets[bucket_key] = category_node
            created_names.append(display_name)
            if top_level:
                root.setdefault("children", []).append(category_node)
            else:
                assert container is not None
                container["children"].append(category_node)
        url_node, next_id = make_url(bookmark.title, bookmark.url, next_id)
        category_node["children"].append(url_node)
        category_node["date_modified"] = chrome_timestamp_now()

    if container is not None:
        container["date_modified"] = chrome_timestamp_now()
        root.setdefault("children", []).append(container)

    root["date_modified"] = chrome_timestamp_now()
    return created_names


def remove_dead_bookmarks(node: dict[str, Any], dead_urls: set[str]) -> int:
    removed = 0
    children = node.get("children")
    if not isinstance(children, list):
        return 0

    kept: list[dict[str, Any]] = []
    for child in children:
        if child.get("type") == "url" and child.get("url") in dead_urls:
            removed += 1
            continue
        removed += remove_dead_bookmarks(child, dead_urls)
        kept.append(child)
    if len(kept) != len(children):
        node["children"] = kept
        node["date_modified"] = chrome_timestamp_now()
    return removed


def clear_bookmarks_keep_folders(node: dict[str, Any]) -> int:
    removed = 0
    children = node.get("children")
    if not isinstance(children, list):
        return 0

    kept: list[dict[str, Any]] = []
    for child in children:
        child_type = child.get("type")
        if child_type == "url":
            removed += 1
            continue
        if child_type == "folder":
            removed += clear_bookmarks_keep_folders(child)
            kept.append(child)
            continue
        kept.append(child)

    if len(kept) != len(children):
        node["children"] = kept
        node["date_modified"] = chrome_timestamp_now()
    return removed


def remove_generated_top_level_folders(root: dict[str, Any]) -> int:
    children = root.get("children")
    if not isinstance(children, list):
        return 0

    removed = 0
    kept: list[dict[str, Any]] = []
    for child in children:
        if child.get("type") == "folder" and is_generated_folder(child.get("name", "")):
            removed += 1
            continue
        kept.append(child)

    if len(kept) != len(children):
        root["children"] = kept
        root["date_modified"] = chrome_timestamp_now()
    return removed


def backup_file(source: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    target = backup_dir / f"{source.name}.{timestamp}.bak"
    shutil.copy2(source, target)
    return target


def build_report(
    bookmarks_path: Path,
    bookmarks: list[BookmarkRecord],
    checks: dict[str, UrlCheckResult],
    duplicates: list[tuple[str, int]],
) -> dict[str, Any]:
    status_counter = Counter(result.status for result in checks.values())
    category_counter = Counter(classify_bookmark(item.title, item.url, " ".join(item.folder_path)) for item in bookmarks)
    dead_items = [
        {
            "title": item.title,
            "url": item.url,
            "path": item.path_display,
            "detail": checks[item.url].detail,
            "http_status": checks[item.url].http_status,
        }
        for item in bookmarks
        if item.url in checks and checks[item.url].status == "dead"
    ]

    return {
        "bookmarks_file": str(bookmarks_path),
        "scanned_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "bookmark_count": len(bookmarks),
        "unique_url_count": len(checks),
        "status_summary": dict(status_counter),
        "category_summary": dict(category_counter.most_common()),
        "duplicate_urls": [{"url": url, "count": count} for url, count in duplicates],
        "dead_bookmarks": dead_items,
    }


def print_summary(report: dict[str, Any]) -> None:
    print(f"书签文件: {report['bookmarks_file']}")
    print(f"书签总数: {report['bookmark_count']}")
    print(f"唯一链接: {report['unique_url_count']}")
    print("状态统计:")
    for status, count in sorted(report["status_summary"].items()):
        print(f"  - {status}: {count}")
    print("分类统计（前 10）:")
    for category, count in list(report["category_summary"].items())[:10]:
        print(f"  - {category}: {count}")
    dead_items = report["dead_bookmarks"]
    if dead_items:
        print("确认失效（前 15）:")
        for item in dead_items[:15]:
            print(f"  - {item['title']} -> {item['url']} [{item['detail']}]")
    else:
        print("确认失效: 0")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="扫描、分类并清理 Chrome 书签。")
    parser.add_argument("--profile", help="Chrome profile 目录名或显示名，例如 'Profile 1' 或 'Fint'")
    parser.add_argument("--bookmarks-file", type=Path, help="直接指定 Bookmarks JSON 文件")
    parser.add_argument("--list-profiles", action="store_true", help="列出本机可用的 Chrome profiles")
    parser.add_argument(
        "--source-roots",
        nargs="+",
        default=["bookmark_bar", "other", "synced"],
        choices=["bookmark_bar", "other", "synced"],
        help="从哪些 roots 收集书签",
    )
    parser.add_argument("--timeout", type=float, default=6.0, help="每个链接的超时时间（秒）")
    parser.add_argument("--concurrency", type=int, default=12, help="并发检查链接数")
    parser.add_argument("--max-checks", type=int, default=None, help="仅检查前 N 个唯一 URL，便于试跑")
    parser.add_argument("--report-file", type=Path, default=DEFAULT_REPORT_PATH, help="JSON 报告输出路径")
    parser.add_argument("--apply-organize", action="store_true", help="写回 Chrome 书签文件，并创建自动分类文件夹")
    parser.add_argument("--apply-delete-dead", action="store_true", help="写回 Chrome 书签文件，并删除确认失效的链接")
    parser.add_argument("--clear-original-bookmarks", action="store_true", help="清空原有文件夹中的书签，但保留文件夹结构")
    parser.add_argument("--top-level-categories", action="store_true", help="把分类结果直接生成为顶层文件夹")
    parser.add_argument("--target-root", choices=["bookmark_bar", "other", "synced"], default="other")
    parser.add_argument("--folder-name", default=None, help="当不使用顶层分类时，自动整理生成的新文件夹名称")
    parser.add_argument("--backup-dir", type=Path, default=DEFAULT_BACKUP_DIR, help="写回前的备份目录")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.list_profiles:
        profiles = list_profiles()
        if not profiles:
            print("未发现 Chrome profiles")
            return 0
        for directory, display, path in profiles:
            print(f"- {display} ({directory}) -> {path}")
        return 0

    bookmarks_path = resolve_bookmarks_path(args.profile, args.bookmarks_file)
    data = load_json(bookmarks_path)
    bookmarks = collect_bookmarks(data, tuple(args.source_roots))
    urls = [item.url for item in bookmarks if item.url]
    duplicate_counter = Counter(urls)
    duplicates = sorted(
        ((url, count) for url, count in duplicate_counter.items() if count > 1),
        key=lambda item: (-item[1], item[0]),
    )

    unique_urls = sorted(set(urls))
    if args.max_checks is not None:
        unique_urls = unique_urls[: max(0, args.max_checks)]
    checks = run_url_checks(unique_urls, args.timeout, args.concurrency)

    report = build_report(bookmarks_path, bookmarks, checks, duplicates[:100])
    args.report_file.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.report_file, report)
    print_summary(report)
    print(f"JSON 报告已写入: {args.report_file.resolve()}")

    should_write = args.apply_organize or args.apply_delete_dead
    if not should_write:
        return 0

    if chrome_running():
        raise SystemExit("检测到 Google Chrome 正在运行。请先退出 Chrome，再执行写回操作。")

    backup_path = backup_file(bookmarks_path, args.backup_dir)
    print(f"已备份原书签: {backup_path.resolve()}")

    if args.apply_delete_dead:
        dead_urls = {url for url, result in checks.items() if result.status == "dead"}
        removed = 0
        for root_name in ("bookmark_bar", "other", "synced"):
            root = (data.get("roots") or {}).get(root_name)
            if root:
                removed += remove_dead_bookmarks(root, dead_urls)
        print(f"已删除确认失效书签: {removed}")

    if args.clear_original_bookmarks:
        cleared = 0
        for root_name in ("bookmark_bar", "other", "synced"):
            root = (data.get("roots") or {}).get(root_name)
            if root:
                cleared += clear_bookmarks_keep_folders(root)
        print(f"已清空原有位置中的书签: {cleared}")

    if args.apply_organize:
        target_root = (data.get("roots") or {}).get(args.target_root)
        if target_root and args.top_level_categories:
            removed_generated = remove_generated_top_level_folders(target_root)
            if removed_generated:
                print(f"已移除旧的自动整理顶层文件夹: {removed_generated}")
        created_names = organize_bookmarks(data, bookmarks, checks, args.target_root, args.folder_name, args.top_level_categories)
        if args.top_level_categories:
            print(f"已在 {args.target_root} 顶层生成分类文件夹: {len(created_names)} 个")
        else:
            print(f"已在 {args.target_root} 下生成分类文件夹: {', '.join(created_names[:3])}{' ...' if len(created_names) > 3 else ''}")

    write_json(bookmarks_path, data)
    print(f"已写回 Chrome 书签文件: {bookmarks_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
