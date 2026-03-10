#!/usr/bin/env python3

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)
SHANGHAI = ZoneInfo("Asia/Shanghai")
DEFAULT_STATE_DIR = Path("/var/lib/openclaw-ai-news")
LOCAL_FALLBACK_STATE_DIR = Path(__file__).resolve().parent.parent / "playground" / "openclaw-ai-news"
DEFAULT_MAX_ITEMS = 10
LOW_SIGNAL_PATTERNS = [
    "how ",
    "tips",
    "guide",
    "podcast",
    "review",
    "why is",
    "what is",
    "opinion",
    "interview",
    "international women",
    "teachers",
    "classroom",
    "education",
    "university",
    "universities",
    "school",
    "schools",
    "pay package",
    "recruitment process",
]
IMPACT_RULES = {
    "model_release": {
        "weight": 320,
        "keywords": [
            "model",
            "gpt",
            "chatgpt",
            "claude",
            "gemini",
            "gemma",
            "llama",
            "deepseek",
            "grok",
            "sonnet",
            "reasoning",
            "veo",
            "imagen",
            "lyria",
            "sora",
        ],
    },
    "product_launch": {
        "weight": 260,
        "keywords": [
            "launch",
            "launches",
            "launched",
            "introducing",
            "introduce",
            "release",
            "released",
            "preview",
            "now available",
            "availability",
            "api",
            "agent",
            "assistant",
            "copilot",
        ],
    },
    "funding": {
        "weight": 220,
        "keywords": ["funding", "raises", "raised", "investment", "valuation", "backed", "financing"],
    },
    "policy": {
        "weight": 210,
        "keywords": [
            "policy",
            "government",
            "regulation",
            "regulatory",
            "white house",
            "defense",
            "department",
            "security",
            "compliance",
        ],
    },
    "chips_compute": {
        "weight": 240,
        "keywords": [
            "chip",
            "gpu",
            "blackwell",
            "data center",
            "training",
            "inference",
            "compute",
            "accelerator",
            "cluster",
        ],
    },
    "research": {
        "weight": 200,
        "keywords": [
            "research",
            "paper",
            "publication",
            "benchmark",
            "science",
            "technical",
            "report",
            "evaluation",
        ],
    },
}
TOKEN_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "into",
    "that",
    "this",
    "your",
    "their",
    "about",
    "what",
    "when",
    "why",
    "how",
    "has",
    "have",
    "new",
    "now",
    "its",
    "can",
    "will",
    "all",
    "you",
    "are",
    "artificial",
    "intelligence",
    "news",
    "launches",
    "launch",
    "introducing",
    "introduce",
    "released",
    "release",
    "models",
    "model",
    "product",
    "products",
    "google",
    "meta",
    "microsoft",
    "nvidia",
    "anthropic",
    "openai",
}
OFFICIAL_PATH_HINTS = [
    "/blog",
    "/news",
    "/research",
    "/press",
    "/announcement",
    "/announcements",
    "/newsroom",
    "/updates",
    "/product",
    "/products",
    "/models",
    "/releases",
]
RELAXED_FILL_KEYWORDS = [
    "openai",
    "anthropic",
    "chatgpt",
    "claude",
    "gemini",
    "deepmind",
    "llama",
    "meta ai",
    "copilot",
    "nvidia",
    "waymo",
    "xai",
    "grok",
    "deepseek",
    "mistral",
    "perplexity",
    "oracle",
    "softbank",
    "data center",
    "gpu",
    "chip",
    "robotics",
    "defense",
]
RELAXED_FILL_EXCLUDES = [
    "gift card",
    "luggage",
    "headphones",
    "earbuds",
    "laptop",
    "iphone",
    "android",
    "pixel",
    "macbook",
    "tablet",
    "antivirus",
    "gaming handheld",
    "yakuza",
]
IGNORED_DISCOVERY_DOMAINS = {
    "facebook.com",
    "fb.com",
    "instagram.com",
    "linkedin.com",
    "x.com",
    "twitter.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "wikipedia.org",
    "github.com",
    "arxiv.org",
    "podcasts.apple.com",
    "open.spotify.com",
    "threads.net",
    "reddit.com",
    "medium.com",
    "substack.com",
}


def http_get(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def http_post_json(url: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def resolve_state_dir() -> Path:
    configured = os.environ.get("AI_NEWS_STATE_DIR")
    target = Path(configured) if configured else DEFAULT_STATE_DIR
    try:
        target.mkdir(parents=True, exist_ok=True)
        probe = target / ".write_test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return target
    except Exception:
        if configured:
            raise
    LOCAL_FALLBACK_STATE_DIR.mkdir(parents=True, exist_ok=True)
    return LOCAL_FALLBACK_STATE_DIR


STATE_DIR = resolve_state_dir()
SOURCES_FILE = Path(__file__).with_name("ai_news_sources.json")


def html_to_text(raw: str) -> str:
    text = re.sub(r"<script.*?</script>", "", raw, flags=re.S | re.I)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_domain(netloc: str) -> str:
    domain = netloc.lower().strip()
    if "@" in domain:
        domain = domain.rsplit("@", 1)[-1]
    if ":" in domain:
        domain = domain.split(":", 1)[0]
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def canonical_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    scheme = parsed.scheme or "https"
    domain = normalize_domain(parsed.netloc)
    path = parsed.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]
    return urllib.parse.urlunsplit((scheme, domain, path, "", ""))


def resolve_target_datetime(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(SHANGHAI)
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=SHANGHAI)
    return parsed.astimezone(SHANGHAI)


def compute_window(target_dt: datetime) -> tuple[datetime, datetime]:
    local_dt = target_dt.astimezone(SHANGHAI)
    window_end = local_dt.replace(hour=8, minute=0, second=0, microsecond=0)
    if local_dt < window_end:
        window_end -= timedelta(days=1)
    return window_end - timedelta(days=1), window_end


def window_id(window_start: datetime, window_end: datetime) -> str:
    return f"{window_start.strftime('%Y%m%dT%H%M%S%z')}__{window_end.strftime('%Y%m%dT%H%M%S%z')}"


def parse_rfc2822_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        parsed = parsedate_to_datetime(raw)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
        return parsed.astimezone(ZoneInfo("UTC"))
    except Exception:
        return None


def parse_iso_datetime(raw: str | None) -> datetime | None:
    if not raw:
        return None
    value = raw.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo("UTC"))
        return parsed.astimezone(ZoneInfo("UTC"))
    except Exception:
        return None


def parse_human_date(raw: str | None) -> datetime | None:
    if not raw:
        return None
    for fmt in ["%b %d, %Y", "%B %d, %Y"]:
        try:
            parsed = datetime.strptime(raw.strip(), fmt)
            return parsed.replace(tzinfo=SHANGHAI).astimezone(ZoneInfo("UTC"))
        except Exception:
            continue
    return None


def load_sources(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources = payload.get("sources") or []
    if not sources:
        raise RuntimeError(f"No sources found in {path}")
    return sources


def collect_categories(item_node: ET.Element) -> list[str]:
    categories = []
    for node in item_node.findall("category"):
        text = (node.text or "").strip()
        if text:
            categories.append(text)
    return categories


def strip_source_suffix(title: str) -> str:
    cleaned = re.sub(r"\s+[\-|｜|]\s+[^\-|｜|]+$", "", title.strip())
    return re.sub(r"\s+", " ", cleaned).strip()


def title_tokens(title: str) -> set[str]:
    raw_tokens = re.findall(r"[a-z0-9]+", title.lower())
    tokens = {token for token in raw_tokens if len(token) >= 3 and token not in TOKEN_STOPWORDS}
    return tokens


def significant_overlap(left: dict[str, Any], right: dict[str, Any]) -> bool:
    left_tokens = set(left.get("title_tokens") or [])
    right_tokens = set(right.get("title_tokens") or [])
    if not left_tokens or not right_tokens:
        return False
    overlap = left_tokens & right_tokens
    min_size = min(len(left_tokens), len(right_tokens))
    return len(overlap) >= 3 and len(overlap) / max(1, min_size) >= 0.75


def normalize_title_key(title: str) -> str:
    normalized = strip_source_suffix(title).lower()
    normalized = re.sub(r"[^a-z0-9\s]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def item_story_key(source_id: str, url: str) -> str:
    return hashlib.sha1(f"{source_id}|{canonical_url(url)}".encode("utf-8")).hexdigest()[:12]


def build_item(
    *,
    source: dict[str, Any],
    title: str,
    url: str,
    published_at: datetime,
    description: str,
    categories: list[str] | None = None,
) -> dict[str, Any]:
    canonical = canonical_url(url)
    category_list = [item.strip() for item in (categories or []) if item and item.strip()]
    return {
        "story_key": item_story_key(source["id"], canonical),
        "source_id": source["id"],
        "source_name": source["name"],
        "tier": source["tier"],
        "priority": int(source.get("priority", 0)),
        "title": strip_source_suffix(title),
        "title_key": normalize_title_key(title),
        "title_tokens": sorted(title_tokens(title)),
        "url": canonical,
        "domain": normalize_domain(urllib.parse.urlsplit(canonical).netloc),
        "published_at": published_at.astimezone(ZoneInfo("UTC")).isoformat(),
        "published_local": published_at.astimezone(SHANGHAI).strftime("%Y-%m-%d %H:%M"),
        "description": description.strip(),
        "categories": category_list,
        "duplicates": [],
    }


def keyword_matches(text: str, keyword: str) -> bool:
    value = text.lower()
    probe = keyword.lower().strip()
    if not probe:
        return False
    pattern = re.escape(probe).replace(r"\ ", r"\s+")
    return re.search(rf"(?<![a-z0-9]){pattern}(?![a-z0-9])", value) is not None


def matches_any(text: str, keywords: list[str]) -> bool:
    return any(keyword_matches(text, keyword) for keyword in keywords)


def is_ai_relevant(item: dict[str, Any], source: dict[str, Any]) -> bool:
    filters = source.get("ai_filters") or {}
    keyword_text_parts = [
        item.get("title") or "",
        item.get("description") or "",
        item.get("url") or "",
    ]
    full_text = "\n".join(keyword_text_parts).lower()
    exclude_keywords = filters.get("exclude_keywords") or []
    if exclude_keywords and matches_any(full_text, exclude_keywords):
        return False
    if source.get("all_ai"):
        return True

    keyword_matches = False
    keywords_any = filters.get("keywords_any") or []
    categories_any = [item.lower() for item in (filters.get("categories_any") or [])]
    if keywords_any and matches_any(full_text, keywords_any):
        keyword_matches = True
    if categories_any:
        item_categories = [entry.lower() for entry in item.get("categories") or []]
        if any(any(category in value for category in categories_any) for value in item_categories):
            keyword_matches = True
    return keyword_matches


def fetch_rss_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    xml_text = http_get(source["feed_url"])
    root = ET.fromstring(xml_text)
    items: list[dict[str, Any]] = []
    for node in root.findall(".//item"):
        title = (node.findtext("title") or "").strip()
        link = (node.findtext("link") or "").strip()
        published_at = parse_rfc2822_datetime((node.findtext("pubDate") or "").strip())
        if not title or not link or not published_at:
            continue
        description = html_to_text(node.findtext("description") or "")
        item = build_item(
            source=source,
            title=title,
            url=link,
            published_at=published_at,
            description=description,
            categories=collect_categories(node),
        )
        items.append(item)
    return items


def fetch_anthropic_news_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    page = http_get(source["url"])
    hrefs_seen = set()
    items: list[dict[str, Any]] = []
    for match in re.finditer(r'<a href="(?P<href>/news/[^"]+)"[^>]*>(?P<body>.*?)</a>', page, flags=re.S | re.I):
        href = match.group("href")
        if href in hrefs_seen:
            continue
        hrefs_seen.add(href)
        block = match.group("body")
        title_match = re.search(r"<h[1-6][^>]*>(?P<title>.*?)</h[1-6]>", block, flags=re.S | re.I)
        date_match = re.search(r"<time[^>]*>(?P<date>[^<]+)</time>", block, flags=re.S | re.I)
        body_match = re.search(r"<p[^>]*>(?P<body>.*?)</p>", block, flags=re.S | re.I)
        if not title_match or not date_match:
            continue
        published_at = parse_human_date(html_to_text(date_match.group("date")))
        if not published_at:
            continue
        title = html_to_text(title_match.group("title"))
        description = html_to_text(body_match.group("body")) if body_match else ""
        item = build_item(
            source=source,
            title=title,
            url=urllib.parse.urljoin(source["url"], href),
            published_at=published_at,
            description=description,
            categories=[],
        )
        items.append(item)
    return items


def meta_content(page: str, names: list[str]) -> str | None:
    for name in names:
        patterns = [
            rf'<meta[^>]+property="{re.escape(name)}"[^>]+content="([^"]+)"',
            rf'<meta[^>]+name="{re.escape(name)}"[^>]+content="([^"]+)"',
            rf'<meta[^>]+content="([^"]+)"[^>]+property="{re.escape(name)}"',
            rf'<meta[^>]+content="([^"]+)"[^>]+name="{re.escape(name)}"',
        ]
        for pattern in patterns:
            match = re.search(pattern, page, flags=re.I)
            if match:
                return html.unescape(match.group(1)).strip()
    return None


def extract_json_ld_blocks(page: str) -> list[Any]:
    payloads = []
    for match in re.finditer(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', page, flags=re.S | re.I):
        raw = html.unescape(match.group(1)).strip()
        if not raw:
            continue
        try:
            payloads.append(json.loads(raw))
        except Exception:
            continue
    return payloads


def find_blogposting(data: Any) -> dict[str, Any] | None:
    if isinstance(data, dict):
        node_type = str(data.get("@type") or "")
        if node_type.lower() in {"blogposting", "newsarticle", "article"} and data.get("headline"):
            return data
        for value in data.values():
            found = find_blogposting(value)
            if found:
                return found
    elif isinstance(data, list):
        for value in data:
            found = find_blogposting(value)
            if found:
                return found
    return None


def fetch_deepmind_blog_items(source: dict[str, Any]) -> list[dict[str, Any]]:
    landing = http_get(source["url"])
    hrefs = []
    seen = set()
    for href in re.findall(r'href="(/blog/[^"?#]+/)"', landing, flags=re.I):
        if href == "/blog/":
            continue
        if href in seen:
            continue
        seen.add(href)
        hrefs.append(href)

    items: list[dict[str, Any]] = []
    for href in hrefs[: int(source.get("max_scan_items", 12))]:
        url = urllib.parse.urljoin(source["url"], href)
        try:
            page = http_get(url)
        except Exception:
            continue
        title = meta_content(page, ["og:title", "twitter:title"]) or ""
        description = meta_content(page, ["description", "og:description", "twitter:description"]) or ""
        published_raw = meta_content(page, ["article:published_time"])
        categories = []
        section = meta_content(page, ["article:section"])
        if section:
            categories.append(section)
        published_at = parse_iso_datetime(published_raw)
        if not published_at:
            for payload in extract_json_ld_blocks(page):
                article = find_blogposting(payload)
                if not article:
                    continue
                title = title or str(article.get("headline") or "")
                description = description or str(article.get("description") or "")
                categories = categories or ([str(article.get("articleSection"))] if article.get("articleSection") else [])
                published_at = parse_iso_datetime(str(article.get("datePublished") or article.get("dateModified") or ""))
                if published_at:
                    break
        if not title or not published_at:
            continue
        item = build_item(
            source=source,
            title=title,
            url=url,
            published_at=published_at,
            description=description,
            categories=categories,
        )
        items.append(item)
    return items


def fetch_items_for_source(source: dict[str, Any]) -> list[dict[str, Any]]:
    entry_type = source.get("entry_type")
    if entry_type == "rss":
        return fetch_rss_items(source)
    if entry_type == "anthropic_news_html":
        return fetch_anthropic_news_items(source)
    if entry_type == "deepmind_blog_html":
        return fetch_deepmind_blog_items(source)
    raise RuntimeError(f"Unsupported source entry_type: {entry_type}")


def within_window(item: dict[str, Any], window_start: datetime, window_end: datetime) -> bool:
    published_at = parse_iso_datetime(item.get("published_at"))
    if not published_at:
        return False
    local = published_at.astimezone(SHANGHAI)
    return window_start <= local < window_end


def item_age_minutes(item: dict[str, Any], window_end: datetime) -> int:
    published_at = parse_iso_datetime(item.get("published_at"))
    if not published_at:
        return 10**9
    delta = window_end.astimezone(ZoneInfo("UTC")) - published_at.astimezone(ZoneInfo("UTC"))
    return max(0, int(delta.total_seconds() // 60))


def item_impact(item: dict[str, Any]) -> tuple[int, list[str]]:
    text = "\n".join(
        [item.get("title") or "", item.get("description") or "", " ".join(item.get("categories") or [])]
    ).lower()
    score = 0
    labels = []
    for label, rule in IMPACT_RULES.items():
        if matches_any(text, rule["keywords"]):
            score += int(rule["weight"])
            labels.append(label)
    for pattern in LOW_SIGNAL_PATTERNS:
        if pattern in text:
            score -= 180
            labels.append(f"low_signal:{pattern}")
    return score, labels


def compute_selection_score(item: dict[str, Any], window_end: datetime) -> tuple[int, list[str]]:
    tier_bonus = 100000 if item.get("tier") == "official" else 0
    impact_score, labels = item_impact(item)
    recency_bonus = max(0, 200 - item_age_minutes(item, window_end) // 10)
    total = tier_bonus + int(item.get("priority", 0)) * 100 + impact_score + recency_bonus
    return total, labels


def is_relaxed_ai_related(item: dict[str, Any]) -> bool:
    text = "\n".join(
        [item.get("title") or "", item.get("description") or "", item.get("url") or "", " ".join(item.get("categories") or [])]
    ).lower()
    if matches_any(text, RELAXED_FILL_EXCLUDES):
        return False
    return matches_any(text, RELAXED_FILL_KEYWORDS)


def is_duplicate_item(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return left["url"] == right["url"] or left["title_key"] == right["title_key"] or significant_overlap(left, right)


def dedupe_items(items: list[dict[str, Any]], window_end: datetime) -> list[dict[str, Any]]:
    ordered = []
    for item in items:
        score, impact_labels = compute_selection_score(item, window_end)
        enriched = dict(item)
        enriched["selection_score"] = score
        enriched["impact_labels"] = impact_labels
        ordered.append(enriched)
    ordered.sort(
        key=lambda item: (
            1 if item.get("tier") == "official" else 0,
            item.get("selection_score", 0),
            item.get("published_at", ""),
        ),
        reverse=True,
    )

    kept: list[dict[str, Any]] = []
    for item in ordered:
        duplicate = None
        for existing in kept:
            same_url = item["url"] == existing["url"]
            same_title = item["title_key"] == existing["title_key"]
            near_title = significant_overlap(item, existing)
            if same_url or same_title or near_title:
                duplicate = existing
                break
        if duplicate:
            duplicate.setdefault("duplicates", []).append(
                {
                    "source_id": item["source_id"],
                    "source_name": item["source_name"],
                    "url": item["url"],
                    "title": item["title"],
                    "tier": item["tier"],
                }
            )
            continue
        kept.append(item)
    return kept


def select_items(items: list[dict[str, Any]], max_items: int) -> list[dict[str, Any]]:
    official = [item for item in items if item.get("tier") == "official"]
    media = [item for item in items if item.get("tier") != "official"]
    selected = official[:max_items]
    if len(selected) < max_items:
        selected.extend(media[: max_items - len(selected)])
    return selected


def load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json_artifact(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def discover_candidate_sources(
    media_items: list[dict[str, Any]],
    source_domains: set[str],
    window_end: datetime,
) -> dict[str, Any]:
    path = STATE_DIR / "candidate_sources.json"
    state = load_json_file(path, {"candidates": {}})
    candidates = state.setdefault("candidates", {})
    media_to_scan = media_items[:12]
    media_domains = {item["domain"] for item in media_items}

    for item in media_to_scan:
        try:
            page = http_get(item["url"], timeout=20)
        except Exception:
            continue
        for match in re.finditer(r'href=["\']([^"\']+)["\']', page, flags=re.I):
            href = match.group(1)
            full_url = urllib.parse.urljoin(item["url"], href)
            parsed = urllib.parse.urlsplit(full_url)
            if parsed.scheme not in {"http", "https"}:
                continue
            domain = normalize_domain(parsed.netloc)
            if not domain or domain in source_domains or domain in media_domains:
                continue
            if any(domain == ignored or domain.endswith(f".{ignored}") for ignored in IGNORED_DISCOVERY_DOMAINS):
                continue
            hint_in_domain = domain.startswith(("blog.", "news.", "press.", "research."))
            hint_in_path = any(hint in parsed.path.lower() for hint in OFFICIAL_PATH_HINTS)
            if not hint_in_domain and not hint_in_path:
                continue
            record = candidates.setdefault(
                domain,
                {
                    "domain": domain,
                    "first_seen": window_end.isoformat(),
                    "last_seen": window_end.isoformat(),
                    "hit_count": 0,
                    "example_url": full_url,
                    "seen_via_url": item["url"],
                    "seen_via_source": item["source_name"],
                    "seen_via_title": item["title"],
                },
            )
            record["last_seen"] = window_end.isoformat()
            record["hit_count"] = int(record.get("hit_count", 0)) + 1
            if not record.get("example_url"):
                record["example_url"] = full_url
            if not record.get("seen_via_url"):
                record["seen_via_url"] = item["url"]
            if not record.get("seen_via_title"):
                record["seen_via_title"] = item["title"]

    sorted_candidates = dict(sorted(candidates.items(), key=lambda entry: (-entry[1].get("hit_count", 0), entry[0])))
    state["updated_at"] = datetime.now(SHANGHAI).isoformat()
    state["candidates"] = sorted_candidates
    save_json_artifact(path, state)
    return state


def run_openclaw(prompt: str, agent: str) -> str:
    cmd = [
        "openclaw",
        "agent",
        "--agent",
        agent,
        "--message",
        prompt,
        "--thinking",
        "low",
        "--json",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise RuntimeError(f"openclaw failed: {result.stderr or result.stdout}")
    payload = json.loads(result.stdout)
    texts = []
    for item in payload.get("result", {}).get("payloads", []):
        text = item.get("text")
        if text:
            texts.append(text.strip())
    if not texts:
        raise RuntimeError("openclaw returned no text payload")
    return "\n\n".join(texts).strip()


def extract_json_array(source: str) -> list[Any]:
    start = source.find("[")
    if start == -1:
        raise RuntimeError("JSON array start not found")
    level = 0
    in_string = False
    escape = False
    end = None
    for index, char in enumerate(source[start:], start=start):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "[":
            level += 1
        elif char == "]":
            level -= 1
            if level == 0:
                end = index
                break
    if end is None:
        raise RuntimeError("JSON array end not found")
    return json.loads(source[start : end + 1])


def build_summary_prompt(selected_items: list[dict[str, Any]], window_start: datetime, window_end: datetime) -> str:
    items = []
    for item in selected_items:
        items.append(
            {
                "story_key": item["story_key"],
                "title": item["title"],
                "source_name": item["source_name"],
                "tier": item["tier"],
                "published_local": item["published_local"],
                "description": item["description"],
                "categories": item.get("categories") or [],
                "impact_labels": item.get("impact_labels") or [],
            }
        )
    return textwrap.dedent(
        f"""
        你是一个中文 AI 圈晨报编辑。请基于给定新闻数据，为每条新闻写 60 到 120 个中文字符的“核心内容”摘要。

        必须遵守：
        1. 只能使用我提供的标题、简介、来源、时间和分类信息，不得编造事实。
        2. 不得加入你的判断、预测、情绪化表述或营销措辞。
        3. 摘要不要重复标题本身，不要写序号，不要写“这条新闻说的是……”。
        4. 如果信息不足，就只压缩现有信息，不要脑补细节。
        5. 输出必须是 JSON 数组，数组里的每个对象必须是：{{"story_key":"...","summary":"..."}}。
        6. `story_key` 必须原样使用输入值，一个都不能漏。
        7. 不要输出 Markdown、代码块或任何额外解释。

        窗口：{window_start.strftime('%Y-%m-%d %H:%M %Z')} 到 {window_end.strftime('%Y-%m-%d %H:%M %Z')}

        新闻数据：
        {json.dumps(items, ensure_ascii=False, indent=2)}
        """
    ).strip()


def fallback_preview_summary(item: dict[str, Any]) -> str:
    description = item.get("description") or ""
    if description:
        text = description.strip()
    else:
        text = item.get("title") or ""
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= 180:
        return text
    return text[:177] + "..."


def generate_summaries(
    selected_items: list[dict[str, Any]],
    agent: str,
    window_start: datetime,
    window_end: datetime,
    *,
    strict: bool,
) -> tuple[list[dict[str, Any]], str]:
    if not selected_items:
        return [], "empty"

    if not shutil.which("openclaw"):
        if strict:
            raise RuntimeError("openclaw is required for --send")
        return [
            {
                "story_key": item["story_key"],
                "summary": fallback_preview_summary(item),
            }
            for item in selected_items
        ], "fallback_preview"

    prompt = build_summary_prompt(selected_items, window_start, window_end)
    response = run_openclaw(prompt, agent)
    try:
        items = extract_json_array(response)
    except Exception:
        if strict:
            raise
        return [
            {
                "story_key": item["story_key"],
                "summary": fallback_preview_summary(item),
            }
            for item in selected_items
        ], "fallback_preview"

    mapping = {}
    for item in items:
        story_key = str(item.get("story_key") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if story_key and summary:
            mapping[story_key] = summary
    if strict and any(item["story_key"] not in mapping for item in selected_items):
        missing = [item["story_key"] for item in selected_items if item["story_key"] not in mapping]
        raise RuntimeError(f"openclaw summaries missing story keys: {missing}")
    if not mapping and strict:
        raise RuntimeError("openclaw did not return usable summaries")

    result = []
    for item in selected_items:
        result.append(
            {
                "story_key": item["story_key"],
                "summary": mapping.get(item["story_key"], fallback_preview_summary(item)),
            }
        )
    return result, "openclaw"


def merge_selected_with_summaries(selected_items: list[dict[str, Any]], summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary_map = {item["story_key"]: item["summary"] for item in summaries}
    merged = []
    for item in selected_items:
        payload = dict(item)
        payload["summary"] = summary_map.get(item["story_key"], "")
        merged.append(payload)
    return merged


def escape_lark(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def truncate_text(value: str, limit: int = 60) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def build_card_payload(index: int, total: int, item: dict[str, Any], window_start: datetime, window_end: datetime) -> dict[str, Any]:
    subtitle = (
        f"AI圈晨报 {index:02d}/{total:02d}｜"
        f"{'官方' if item['tier'] == 'official' else '可靠媒体'}｜{item['source_name']}｜{item['published_local']}"
    )
    summary = escape_lark(item.get("summary") or fallback_preview_summary(item))
    title = escape_lark(item["title"])
    body = f"**{title}**\n\n{summary}"
    footer = (
        f"窗口 {window_start.strftime('%m-%d %H:%M')} → {window_end.strftime('%m-%d %H:%M')}"
    )
    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True, "enable_forward": True},
            "header": {
                "template": "blue" if item["tier"] == "official" else "purple",
                "title": {"tag": "plain_text", "content": truncate_text(item["title"], 58)},
            },
            "elements": [
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": subtitle}],
                },
                {
                    "tag": "div",
                    "text": {"tag": "lark_md", "content": body},
                },
                {"tag": "hr"},
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"tag": "plain_text", "content": "查看原文"},
                            "type": "default",
                            "url": item["url"],
                        }
                    ],
                },
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": footer}],
                },
            ],
        },
    }


def load_sent_windows() -> dict[str, Any]:
    return load_json_file(STATE_DIR / "sent_windows.json", {"sent": {}})


def save_sent_windows(payload: dict[str, Any]) -> None:
    save_json_artifact(STATE_DIR / "sent_windows.json", payload)


def send_cards(
    webhook: str,
    digest_items: list[dict[str, Any]],
    window_start: datetime,
    window_end: datetime,
) -> list[dict[str, Any]]:
    responses = []
    total = len(digest_items)
    for index, item in enumerate(digest_items, start=1):
        payload = build_card_payload(index, total, item, window_start, window_end)
        response = http_post_json(webhook, payload)
        responses.append({"story_key": item["story_key"], "title": item["title"], "response": response})
        if response.get("code") != 0:
            raise RuntimeError(f"Feishu AI news card failed for {item['title']}: {response}")
    return responses


def save_artifacts(
    *,
    target_dt: datetime,
    context: dict[str, Any],
    digest_items: list[dict[str, Any]],
    cards: list[dict[str, Any]],
    candidate_state: dict[str, Any],
) -> None:
    stamp = target_dt.astimezone(SHANGHAI).strftime("%Y%m%d-%H%M%S")
    save_json_artifact(STATE_DIR / f"context-{stamp}.json", context)
    save_json_artifact(STATE_DIR / "last_context.json", context)
    save_json_artifact(STATE_DIR / f"digest-{stamp}.json", digest_items)
    save_json_artifact(STATE_DIR / "last_digest.json", digest_items)
    save_json_artifact(STATE_DIR / f"cards-{stamp}.json", cards)
    save_json_artifact(STATE_DIR / "last_cards.json", cards)
    save_json_artifact(STATE_DIR / "candidate_sources.json", candidate_state)


def render_preview(context: dict[str, Any], digest_items: list[dict[str, Any]]) -> str:
    lines = [
        f"AI圈晨报预览｜窗口 {context['windowStartLocal']} -> {context['windowEndLocal']}",
        f"精选 {len(digest_items)} 条｜官方 {context['selectionBreakdown']['official']} 条｜媒体 {context['selectionBreakdown']['media']} 条",
        "",
    ]
    for index, item in enumerate(digest_items, start=1):
        lines.extend(
            [
                f"{index:02d}. {item['title']}",
                f"    来源：{'官方' if item['tier'] == 'official' else '可靠媒体'}｜{item['source_name']}｜{item['published_local']}",
                f"    摘要：{item.get('summary') or fallback_preview_summary(item)}",
                f"    链接：{item['url']}",
                "",
            ]
        )
    return "\n".join(lines).rstrip()


def collect_news(
    *,
    sources: list[dict[str, Any]],
    window_start: datetime,
    window_end: datetime,
    max_items: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    relaxed_candidates: list[dict[str, Any]] = []
    source_status: list[dict[str, Any]] = []
    official_domains = set()
    for source in sources:
        if not source.get("enabled", True):
            continue
        for domain in source.get("domains") or []:
            official_domains.add(normalize_domain(domain))
        try:
            raw_items = fetch_items_for_source(source)
            raw_items = [item for item in raw_items if within_window(item, window_start, window_end)]
            strict_items = []
            relaxed_items = []
            for item in raw_items:
                if is_ai_relevant(item, source):
                    item["selection_mode"] = "strict"
                    strict_items.append(item)
                elif source.get("tier") == "media" and is_relaxed_ai_related(item):
                    relaxed_item = dict(item)
                    relaxed_item["selection_mode"] = "relaxed_fill"
                    relaxed_items.append(relaxed_item)
            collected.extend(strict_items)
            relaxed_candidates.extend(relaxed_items)
            source_status.append(
                {
                    "source_id": source["id"],
                    "count": len(strict_items),
                    "relaxed_count": len(relaxed_items),
                    "status": "ok",
                }
            )
        except Exception as exc:
            source_status.append({"source_id": source["id"], "count": 0, "status": f"error: {exc}"})

    deduped = dedupe_items(collected, window_end)
    selected = select_items(deduped, max_items)
    if len(selected) < max_items and relaxed_candidates:
        relaxed_deduped = dedupe_items(relaxed_candidates, window_end)
        for candidate in relaxed_deduped:
            if any(is_duplicate_item(candidate, existing) for existing in selected):
                continue
            selected.append(candidate)
            if len(selected) >= max_items:
                break
    discovery = discover_candidate_sources([item for item in deduped if item["tier"] == "media"], official_domains, window_end)
    return deduped, selected, {"source_status": source_status, "candidate_state": discovery}


def build_context(
    *,
    target_dt: datetime,
    window_start: datetime,
    window_end: datetime,
    deduped_items: list[dict[str, Any]],
    selected_items: list[dict[str, Any]],
    summary_mode: str,
    source_status: list[dict[str, Any]],
    candidate_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "generatedAt": target_dt.astimezone(SHANGHAI).isoformat(),
        "timezone": "Asia/Shanghai",
        "windowStartLocal": window_start.strftime("%Y-%m-%d %H:%M"),
        "windowEndLocal": window_end.strftime("%Y-%m-%d %H:%M"),
        "windowId": window_id(window_start, window_end),
        "summaryMode": summary_mode,
        "rawItemCount": len(deduped_items),
        "selectedCount": len(selected_items),
        "selectionBreakdown": {
            "official": len([item for item in selected_items if item["tier"] == "official"]),
            "media": len([item for item in selected_items if item["tier"] == "media"]),
        },
        "sourceStatus": source_status,
        "candidateSourceCount": len((candidate_state.get("candidates") or {}).keys()),
        "selectedItems": [
            {
                "story_key": item["story_key"],
                "title": item["title"],
                "source_name": item["source_name"],
                "tier": item["tier"],
                "published_local": item["published_local"],
                "url": item["url"],
                "selection_score": item.get("selection_score"),
                "impact_labels": item.get("impact_labels"),
                "duplicates": item.get("duplicates") or [],
            }
            for item in selected_items
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send AI news digest cards to Feishu")
    parser.add_argument("--datetime", help="Override target datetime, ISO 8601")
    parser.add_argument("--max-items", type=int, default=DEFAULT_MAX_ITEMS, help="Maximum number of news cards")
    parser.add_argument("--agent", default=os.environ.get("AI_NEWS_OPENCLAW_AGENT") or os.environ.get("OPENCLAW_AGENT", "main"))
    parser.add_argument("--webhook", default=os.environ.get("AI_NEWS_FEISHU_WEBHOOK") or os.environ.get("FEISHU_WEBHOOK"))
    parser.add_argument("--force-send", action="store_true", help="Force re-send for the same time window")
    parser.add_argument("--sources-file", default=str(SOURCES_FILE), help="Source registry JSON path")
    args = parser.parse_args()

    target_dt = resolve_target_datetime(args.datetime)
    window_start, window_end = compute_window(target_dt)
    sources = load_sources(Path(args.sources_file))
    deduped_items, selected_items, runtime = collect_news(
        sources=sources,
        window_start=window_start,
        window_end=window_end,
        max_items=args.max_items,
    )

    summaries, summary_mode = generate_summaries(
        selected_items,
        args.agent,
        window_start,
        window_end,
        strict=args.send,
    )
    digest_items = merge_selected_with_summaries(selected_items, summaries)
    cards = [
        build_card_payload(index, len(digest_items), item, window_start, window_end)
        for index, item in enumerate(digest_items, start=1)
    ]
    context = build_context(
        target_dt=target_dt,
        window_start=window_start,
        window_end=window_end,
        deduped_items=deduped_items,
        selected_items=digest_items,
        summary_mode=summary_mode,
        source_status=runtime["source_status"],
        candidate_state=runtime["candidate_state"],
    )
    save_artifacts(
        target_dt=target_dt,
        context=context,
        digest_items=digest_items,
        cards=cards,
        candidate_state=runtime["candidate_state"],
    )

    if args.send:
        if not args.webhook:
            raise RuntimeError("AI_NEWS_FEISHU_WEBHOOK or FEISHU_WEBHOOK is required when --send is used")
        sent_state = load_sent_windows()
        sent = sent_state.setdefault("sent", {})
        current_window_id = context["windowId"]
        if current_window_id in sent and not args.force_send:
            print(
                json.dumps(
                    {
                        "skipped": True,
                        "reason": "already_sent",
                        "windowId": current_window_id,
                        "sentAt": sent[current_window_id].get("sentAt"),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0

        responses = send_cards(args.webhook, digest_items, window_start, window_end)
        sent[current_window_id] = {
            "sentAt": datetime.now(SHANGHAI).isoformat(),
            "itemCount": len(digest_items),
            "force": bool(args.force_send),
        }
        save_sent_windows(sent_state)
        print(json.dumps({"windowId": current_window_id, "responses": responses}, ensure_ascii=False, indent=2))
        return 0

    print(render_preview(context, digest_items))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
