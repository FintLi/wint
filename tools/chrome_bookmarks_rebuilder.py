#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import urllib.parse
from collections import Counter
from pathlib import Path
from typing import Any

import chrome_bookmarks_organizer as base

AUTO_SUFFIX = "（自动整理）"
OLD_AUTO_PREFIX = "自动整理 - "
DEFAULT_REPORT_PATH = Path("playground/chrome_bookmarks_rebuild_report.json")

PATH_HINTS: dict[str, tuple[str, str]] = {
    "pythonlanguage": ("开发编程", "Python 开发与脚本"),
    "python": ("开发编程", "Python 开发与脚本"),
    "regularexprssion": ("开发编程", "文本处理与正则"),
    "re": ("开发编程", "文本处理与正则"),
    "programming": ("开发编程", "通用编程基础"),
    "webdevelop": ("网站开发", "通用网页开发"),
    "web": ("网站开发", "通用网页开发"),
    "webfrontend": ("网站开发", "前端与界面"),
    "typescript": ("网站开发", "前端与界面"),
    "webbackend": ("网站开发", "后端与接口"),
    "websitescrap": ("网站抓取与自动化", "网页抓取与采集"),
    "scrapy": ("网站抓取与自动化", "Scrapy 与抓取框架"),
    "database": ("数据与数据库", "数据库与存储"),
    "db": ("数据与数据库", "数据库与存储"),
    "da": ("数据分析与数据工程", "数据分析与可视化"),
    "bigdata": ("数据分析与数据工程", "大数据与计算框架"),
    "java spark ml impala": ("数据分析与数据工程", "大数据与计算框架"),
    "jupyter": ("数据分析与数据工程", "数据分析与可视化"),
    "ml": ("人工智能与机器学习", "机器学习"),
    "machinelearning": ("人工智能与机器学习", "机器学习"),
    "oline course": ("学习资料与课程", "在线课程与练习"),
    "learn": ("学习资料与课程", "在线课程与练习"),
    "books": ("学习资料与课程", "书籍与长文"),
    "linux": ("系统与运维", "Linux 与系统"),
    "operationsystem": ("系统与运维", "Linux 与系统"),
    "internetsecurity": ("系统与运维", "网络与安全"),
    "personalsite": ("个人站点与收藏", "个人站点与博客"),
    "smarthome": ("生活工具与设备", "智能家居"),
    "funny": ("杂项与灵感", "有趣与启发"),
    "temp": ("待整理", "待人工复核"),
    "49": ("待整理", "待人工复核"),
    "typhur": ("工作与项目", "Typhur 相关"),
    "parlant": ("工作与项目", "Parlant 相关"),
    "vc服务": ("工作与项目", "业务服务与接口"),
    "amazon reviews": ("工作与项目", "电商与评论数据"),
    "七出": ("服务与账号", "VPS 与主机"),
    "村圳": ("生活工具与设备", "城市与本地信息"),
    "usage": ("工作与项目", "工具使用与操作"),
}

THIRD_HINTS: dict[str, str] = {
    "pythonlanguage": "语言基础与常用库",
    "python": "语言基础与常用库",
    "regularexprssion": "正则表达式",
    "re": "正则表达式",
    "programming": "编程基础与通用技巧",
    "webdevelop": "通用网页开发",
    "web": "通用网页开发",
    "webfrontend": "前端页面与样式",
    "typescript": "TypeScript 与 JavaScript",
    "webbackend": "后端接口与服务",
    "websitescrap": "抓取案例与经验",
    "scrapy": "Scrapy 实战",
    "database": "关系型数据库",
    "db": "关系型数据库",
    "da": "数据分析实践",
    "bigdata": "大数据实践",
    "java spark ml impala": "Spark / Impala / Java",
    "jupyter": "Jupyter 与 Notebook",
    "ml": "机器学习方法",
    "machinelearning": "机器学习方法",
    "oline course": "课程与教程",
    "learn": "在线课程与练习",
    "books": "书单与电子书",
    "linux": "Linux 命令与系统原理",
    "operationsystem": "Linux 命令与系统原理",
    "internetsecurity": "安全与代理",
    "personalsite": "独立站点与博客",
    "smarthome": "智能家居设备",
    "funny": "灵感与杂读",
    "temp": "待后续细分",
    "49": "待后续细分",
    "typhur": "业务系统与协作",
    "parlant": "文档与接入",
    "vc服务": "接口与服务平台",
    "amazon reviews": "评论与运营数据",
    "七出": "云主机面板与购买",
    "村圳": "深圳房产与租住",
    "usage": "实操与使用说明",
}

COMMUNITY_HOSTS = {
    "zhihu.com": ("社区资讯与内容", "技术社区与问答", "知乎与问答讨论"),
    "reddit.com": ("社区资讯与内容", "技术社区与问答", "Reddit 讨论"),
    "news.ycombinator.com": ("社区资讯与内容", "技术社区与问答", "Hacker News"),
    "v2ex.com": ("社区资讯与内容", "技术社区与问答", "V2EX 讨论"),
    "cnblogs.com": ("社区资讯与内容", "博客文章与专栏", "博客园文章"),
    "csdn.net": ("社区资讯与内容", "博客文章与专栏", "CSDN 文章"),
    "jianshu.com": ("社区资讯与内容", "博客文章与专栏", "简书文章"),
    "medium.com": ("社区资讯与内容", "博客文章与专栏", "Medium 文章"),
    "substack.com": ("社区资讯与内容", "博客文章与专栏", "Newsletter 与专栏"),
    "36kr.com": ("社区资讯与内容", "新闻与资讯", "科技资讯"),
    "jiqizhixin.com": ("社区资讯与内容", "新闻与资讯", "人工智能资讯"),
    "bbc.com": ("社区资讯与内容", "新闻与资讯", "新闻报道"),
    "new.qq.com": ("社区资讯与内容", "新闻与资讯", "新闻报道"),
}

SHOPPING_HOSTS = {
    "amazon.com": ("生活工具与设备", "购物与消费", "电商购物"),
    "taobao.com": ("生活工具与设备", "购物与消费", "电商购物"),
    "jd.com": ("生活工具与设备", "购物与消费", "电商购物"),
    "store.google.com": ("生活工具与设备", "购物与消费", "设备购买"),
}

VIDEO_HOSTS = {
    "youtube.com": ("生活工具与设备", "影音娱乐", "视频与播放列表"),
    "youtu.be": ("生活工具与设备", "影音娱乐", "视频与播放列表"),
    "bilibili.com": ("生活工具与设备", "影音娱乐", "视频与课程"),
}

DOC_HOSTS = {
    "developer.mozilla.org": ("网站开发", "通用网页开发", "官方文档与规范"),
    "docs.python.org": ("开发编程", "Python 开发与脚本", "官方文档与规范"),
    "readthedocs.io": ("开发编程", "通用编程基础", "官方文档与规范"),
    "pandas.pydata.org": ("数据分析与数据工程", "数据分析与可视化", "Pandas 与数据处理"),
}

WORK_HOST_KEYWORDS = (
    "typhur",
    "feishu",
    "larksuite",
    "git.typhur",
    "open.feishu",
    "lingxing",
    "n8n",
    "fintli.com",
)


MAX_TOP_LEVELS = 8

TOP_LEVEL_COMPRESS: dict[str, tuple[str, str | None]] = {
    "工作与项目": ("工作与内网", None),
    "服务与账号": ("工具与生活", None),
    "开发编程": ("开发与网站", None),
    "网站开发": ("开发与网站", None),
    "系统与运维": ("开发与网站", None),
    "网站抓取与自动化": ("抓取与自动化", None),
    "数据分析与数据工程": ("数据与人工智能", None),
    "数据与数据库": ("数据与人工智能", None),
    "人工智能与机器学习": ("数据与人工智能", None),
    "学习资料与课程": ("学习与阅读", None),
    "个人站点与收藏": ("社区与资讯", None),
    "社区资讯与内容": ("社区与资讯", None),
    "生活工具与设备": ("工具与生活", None),
    "杂项与灵感": ("工具与生活", None),
    "待整理": ("待整理", None),
}


def compress_hierarchy(level1: str, level2: str, level3: str, bookmark: base.BookmarkRecord) -> tuple[str, str, str]:
    parsed = urllib.parse.urlparse(bookmark.url)
    host = (parsed.hostname or "").lower()
    text = normalize_token(" ".join([bookmark.title, bookmark.url, *bookmark.folder_path]))

    if base.is_private_hostname(host) or has_any(host, WORK_HOST_KEYWORDS) or has_any(
        text,
        [
            "飞书", "lark", "feishu", "typhur", "gitlab", "merge request", "confluence", "jira",
            "内网", "办公", "okr", "绩效", "审批", "报表", "运营", "listing", "review",
            "open.feishu", "lingxing", "panel", "quota", "management center", "分钟", "minutes",
        ],
    ):
        top = "工作与内网"
        if base.is_private_hostname(host):
            sub = "内网系统与办公"
            if has_any(text, ["dex", "login", "auth", "sso", "panel", "quota", "proxy", "management"]):
                third = "登录、网关与管理后台"
            else:
                third = "内网入口与业务系统"
        elif has_any(text, ["feishu", "飞书", "sheet", "doc", "minutes", "card", "表格", "文档"]):
            sub = "协作文档与办公"
            third = "飞书文档、表格与会议纪要"
        elif has_any(text, ["amazon", "listing", "review", "评论", "运营", "选品"]):
            sub = "业务运营与数据"
            third = "电商运营、评论与业务数据"
        elif has_any(text, ["git", "merge request", "api", "swagger", "接口", "deploy", "发布", "vc服务"]):
            sub = "研发平台与接口"
            third = "代码仓库、接口与发布平台"
        else:
            sub = "工作资料与项目"
            third = "项目资料与工作台"
        return top, sub, third

    top = TOP_LEVEL_COMPRESS.get(level1, (level1, None))[0]

    if top == "开发与网站":
        if level1 == "开发编程":
            return top, "编程语言与基础", level3
        if level1 == "网站开发":
            if level2 in {"前端与界面", "通用网页开发"}:
                return top, "前端与网页", level3
            return top, "后端与接口", level3
        return top, "系统运维与网络", level3

    if top == "抓取与自动化":
        if level2 == "Scrapy 与抓取框架":
            return top, "抓取框架", level3
        if level2 == "浏览器自动化":
            return top, "浏览器自动化", level3
        if level2 == "反爬与代理":
            return top, "反爬、代理与安全", level3
        return top, "抓取案例与流程", level3

    if top == "数据与人工智能":
        if level1 == "数据与数据库":
            return top, "数据库与存储", level3
        if level1 == "数据分析与数据工程":
            if level2 == "大数据与计算框架":
                return top, "数据工程与大数据", level3
            return top, "数据分析与可视化", level3
        return top, "机器学习与大模型", level3

    if top == "学习与阅读":
        if level2 == "在线课程与练习":
            return top, "课程、练习与教程", level3
        return top, "书籍、长文与资料", level3

    if top == "社区与资讯":
        if level1 == "个人站点与收藏":
            return top, "个人站点与博客", level3
        if level2 == "技术社区与问答":
            return top, "问答与讨论", level3
        if level2 == "新闻与资讯":
            return top, "新闻与资讯", level3
        return top, "博客与专栏", level3

    if top == "工具与生活":
        if level1 == "服务与账号":
            return top, "账号、主机与服务", level3
        if level1 == "生活工具与设备":
            if level2 == "购物与消费":
                return top, "购物、设备与消费", level3
            if level2 == "智能家居":
                return top, "设备与智能家居", level3
            if level2 == "城市与本地信息":
                return top, "本地信息与日常工具", level3
            return top, "影音与日常工具", level3
        return top, "杂项与灵感", level3

    return top, level2, level3


def normalize_token(value: str) -> str:
    value = value.lower().replace("_", " ").replace("-", " ").replace("/", " ")
    value = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", value)
    return " ".join(value.split())


def host_matches(host: str, domain: str) -> bool:
    return host == domain or host.endswith(f".{domain}")


def path_hint(folder_path: tuple[str, ...]) -> tuple[str, str] | None:
    normalized = [normalize_token(part) for part in folder_path if part]
    for token in reversed(normalized):
        if token in PATH_HINTS:
            return PATH_HINTS[token]
    return None


def third_hint(folder_path: tuple[str, ...]) -> str | None:
    normalized = [normalize_token(part) for part in folder_path if part]
    for token in reversed(normalized):
        if token in THIRD_HINTS:
            return THIRD_HINTS[token]
    return None


def has_any(text: str, keywords: tuple[str, ...] | list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def content_hierarchy(bookmark: base.BookmarkRecord) -> tuple[str, str, str]:
    parsed = urllib.parse.urlparse(bookmark.url)
    host = (parsed.hostname or "").lower()
    text = normalize_token(" ".join([bookmark.title, bookmark.url, *bookmark.folder_path]))

    for domain, hierarchy in DOC_HOSTS.items():
        if host_matches(host, domain):
            return hierarchy
    for domain, hierarchy in COMMUNITY_HOSTS.items():
        if host_matches(host, domain):
            return hierarchy
    for domain, hierarchy in SHOPPING_HOSTS.items():
        if host_matches(host, domain):
            return hierarchy
    for domain, hierarchy in VIDEO_HOSTS.items():
        if host_matches(host, domain):
            return hierarchy

    if base.is_private_hostname(host) or has_any(host, WORK_HOST_KEYWORDS) or has_any(text, [
        "飞书", "亚马逊", "listing", "review", "n8n", "merge request", "文档", "minute", "minutes", "卡片",
    ]):
        top = "工作与项目"
        sub = "业务系统与协作"
        if has_any(text, ["feishu", "飞书", "sheet", "doc", "document", "minutes", "card", "表格", "文档"]):
            third = "飞书文档与协作"
        elif has_any(text, ["api", "apidoc", "swagger", "git", "merge request", "接口", "文档"]):
            third = "接口文档与代码平台"
        elif has_any(text, ["amazon", "listing", "review", "评论", "运营"]):
            third = "电商运营与评论数据"
        elif has_any(text, ["n8n", "automation", "流程", "typeform"]):
            third = "自动化流程与表单"
        else:
            third = "项目工作台"
        return top, sub, third

    if has_any(text, [
        "openai", "chatgpt", "anthropic", "claude", "huggingface", "llm", "大模型", "agent", "prompt", "rag", "embedding", "transformer",
    ]):
        top = "人工智能与机器学习"
        sub = "大模型与智能体"
        if has_any(text, ["rag", "retrieval", "search", "embedding", "向量", "检索"]):
            third = "RAG 与检索增强"
        elif has_any(text, ["prompt", "agent", "workflow", "智能体"]):
            third = "Prompt 与 Agent"
        else:
            third = "模型平台与 API"
        return top, sub, third

    if has_any(text, ["machine learning", "深度学习", "nlp", "论文", "paper", "arxiv", "acl", "pytorch", "tensorflow", "scikit", "xgboost", "lgbm"]):
        top = "人工智能与机器学习"
        sub = "机器学习"
        if has_any(text, ["nlp", "语言", "acl", "anthology", "spacy"]):
            third = "自然语言处理"
        elif has_any(text, ["paper", "论文", "arxiv", "research", "研究"]):
            third = "论文与研究"
        elif has_any(text, ["tensorflow", "pytorch", "深度学习", "transformer"]):
            third = "深度学习与框架"
        else:
            third = "传统算法与方法"
        return top, sub, third

    if has_any(text, ["scrapy", "crawler", "crawl", "spider", "抓取", "爬虫", "selenium", "playwright", "beautifulsoup", "lxml", "cookie", "ajax", "proxy", "captcha"]):
        top = "网站抓取与自动化"
        if has_any(text, ["scrapy"]):
            sub = "Scrapy 与抓取框架"
            third = "Scrapy 实战"
        elif has_any(text, ["selenium", "playwright", "cookie", "login", "登录"]):
            sub = "浏览器自动化"
            third = "登录与浏览器控制"
        elif has_any(text, ["proxy", "captcha", "反爬", "ssl", "代理"]):
            sub = "反爬与代理"
            third = "代理与反爬处理"
        elif has_any(text, ["ajax", "json", "api", "xhr", "动态"]):
            sub = "动态页面与接口"
            third = "接口抓取与异步页面"
        else:
            sub = "网页抓取与采集"
            third = "抓取案例与经验"
        return top, sub, third

    if has_any(text, ["css", "javascript", "typescript", "react", "vue", "next", "layout", "frontend", "前端", "网页设计", "界面设计"]):
        top = "网站开发"
        sub = "前端与界面"
        if has_any(text, ["typescript", "javascript", "js", "ts"]):
            third = "TypeScript 与 JavaScript"
        elif has_any(text, ["css", "layout", "html", "样式", "布局"]):
            third = "HTML / CSS 布局"
        elif has_any(text, ["react", "vue", "next", "component", "组件"]):
            third = "前端框架与组件"
        else:
            third = "页面设计与实现"
        return top, sub, third

    if has_any(text, ["flask", "django", "fastapi", "api", "swagger", "graphql", "backend", "server", "rest", "node", "express", "后端"]):
        top = "网站开发"
        sub = "后端与接口"
        if has_any(text, ["flask", "django", "fastapi", "python"]):
            third = "Python Web 服务"
        elif has_any(text, ["swagger", "rest", "graphql", "api", "接口"]):
            third = "接口设计与调试"
        else:
            third = "服务端框架"
        return top, sub, third

    if has_any(text, ["mysql", "postgres", "sqlite", "sqlserver", "oracle", "sql", "database", "mongodb", "redis", "elasticsearch", "clickhouse", "数据库"]):
        top = "数据与数据库"
        sub = "数据库与存储"
        if has_any(text, ["mysql"]):
            third = "MySQL"
        elif has_any(text, ["postgres"]):
            third = "PostgreSQL"
        elif has_any(text, ["sqlite"]):
            third = "SQLite"
        elif has_any(text, ["mongodb"]):
            third = "MongoDB"
        elif has_any(text, ["redis"]):
            third = "Redis"
        elif has_any(text, ["elasticsearch", "clickhouse"]):
            third = "检索与分析型存储"
        else:
            third = "SQL 与关系型数据库"
        return top, sub, third

    if has_any(text, ["pandas", "numpy", "jupyter", "notebook", "matplotlib", "seaborn", "plotly", "数据分析", "可视化", "foursquare"]):
        top = "数据分析与数据工程"
        sub = "数据分析与可视化"
        if has_any(text, ["jupyter", "notebook", "ipython"]):
            third = "Jupyter 与 Notebook"
        elif has_any(text, ["pandas", "numpy"]):
            third = "Pandas 与数据处理"
        else:
            third = "图表与可视化"
        return top, sub, third

    if has_any(text, ["spark", "hadoop", "hive", "impala", "flink", "kafka", "大数据"]):
        top = "数据分析与数据工程"
        sub = "大数据与计算框架"
        if has_any(text, ["spark"]):
            third = "Spark"
        elif has_any(text, ["hive", "impala"]):
            third = "Hive / Impala"
        else:
            third = "大数据实践"
        return top, sub, third

    if has_any(text, ["linux", "bash", "shell", "htop", "docker", "kubernetes", "k8s", "server", "运维", "部署", "命令行"]):
        top = "系统与运维"
        if has_any(text, ["docker", "kubernetes", "k8s", "部署"]):
            sub = "容器与部署"
            third = "Docker / Kubernetes"
        else:
            sub = "Linux 与系统"
            third = "Linux 命令与系统原理"
        return top, sub, third

    if has_any(text, ["proxy", "ssl", "tls", "vpn", "security", "安全", "证书", "代理"]):
        return "系统与运维", "网络与安全", "代理与网络安全"

    if has_any(text, ["vps", "host", "hosting", "racknerd", "bandwagon", "bluehost", "client area", "mail.hostinger"]):
        return "服务与账号", "VPS 与主机", "云主机面板与购买"

    if has_any(text, ["course", "tutorial", "教程", "课程", "learn", "mooc", "洛谷", "leetcode", "uva", "oj", "题", "练习"]):
        top = "学习资料与课程"
        sub = "在线课程与练习"
        if has_any(text, ["leetcode", "luogu", "uva", "oj", "题", "竞赛"]):
            third = "刷题与练习"
        else:
            third = "课程与教程"
        return top, sub, third

    if has_any(text, ["book", "ebook", "书", "gutenberg", "书单", "douban", "history museum", "古籍"]):
        top = "学习资料与课程"
        sub = "书籍与长文"
        if has_any(text, ["douban", "书单", "review", "评论"]):
            third = "书单与读书评论"
        elif has_any(text, ["gutenberg", "ebook", "pdf", "电子书"]):
            third = "电子书与资料库"
        else:
            third = "长文与人文阅读"
        return top, sub, third

    if has_any(text, ["blog", "专栏", "article", "文章", "博客"]):
        return "社区资讯与内容", "博客文章与专栏", "技术博客"

    if has_any(text, ["news", "资讯", "报道"]):
        return "社区资讯与内容", "新闻与资讯", "新闻报道"

    if has_any(text, ["youtube", "bilibili", "电影", "视频", "playlist", "4k", "蓝光"]):
        return "生活工具与设备", "影音娱乐", "视频与下载资源"

    if has_any(text, ["地图", "百科", "translate", "weather", "深圳", "房产", "租赁"]):
        return "生活工具与设备", "城市与本地信息", "深圳房产与租住"

    if has_any(text, ["google assistant", "chromecast", "smart home", "智能家居"]):
        return "生活工具与设备", "智能家居", "家居设备与平台"

    if has_any(text, ["shop", "购物", "buy", "product", "deal"]):
        return "生活工具与设备", "购物与消费", "电商购物"

    return "待整理", "待人工复核", "待后续细分"


def classify_hierarchy(bookmark: base.BookmarkRecord) -> tuple[str, str, str]:
    inferred = content_hierarchy(bookmark)
    hinted = path_hint(bookmark.folder_path)
    hinted_third = third_hint(bookmark.folder_path)

    if hinted:
        top, sub = hinted
        third = hinted_third or inferred[2]
        if top == "网站开发" and sub == "通用网页开发" and inferred[0] == "网站开发":
            raw = inferred
        elif top == "工作与项目" and inferred[0] == "工作与项目":
            raw = (top, inferred[1], inferred[2])
        elif top == "待整理" and inferred[0] != "待整理":
            raw = inferred
        elif top == inferred[0]:
            raw = (top, sub, hinted_third or inferred[2])
        else:
            raw = (top, sub, third)
    else:
        raw = inferred

    return compress_hierarchy(*raw, bookmark)


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
        node["date_modified"] = base.chrome_timestamp_now()
    return removed


def remove_generated_top_level_folders(root: dict[str, Any]) -> int:
    removed = 0
    children = root.get("children")
    if not isinstance(children, list):
        return 0
    kept: list[dict[str, Any]] = []
    for child in children:
        name = child.get("name", "")
        if child.get("type") == "folder" and (name.endswith(AUTO_SUFFIX) or name.startswith(OLD_AUTO_PREFIX)):
            removed += 1
            continue
        kept.append(child)
    if len(kept) != len(children):
        root["children"] = kept
        root["date_modified"] = base.chrome_timestamp_now()
    return removed


def ensure_folder(parent: dict[str, Any], name: str, next_id: int) -> tuple[dict[str, Any], int]:
    for child in parent.get("children", []) or []:
        if child.get("type") == "folder" and child.get("name") == name:
            return child, next_id
    folder, next_id = base.make_folder(name, next_id)
    parent.setdefault("children", []).append(folder)
    parent["date_modified"] = base.chrome_timestamp_now()
    return folder, next_id


def build_hierarchical_folders(
    target_data: dict[str, Any],
    source_bookmarks: list[base.BookmarkRecord],
    checks: dict[str, base.UrlCheckResult],
    target_root: str,
) -> tuple[int, Counter[str]]:
    root = (target_data.get("roots") or {}).get(target_root)
    if root is None:
        raise SystemExit(f"Chrome 书签里不存在 root={target_root!r}")

    next_id = base.max_numeric_id(target_data) + 1
    added = 0
    top_counts: Counter[str] = Counter()

    aliveish = {"alive", "skipped", "unreachable"}
    chosen = [bookmark for bookmark in source_bookmarks if checks.get(bookmark.url, base.UrlCheckResult("alive", None, "未检查")).status in aliveish]
    chosen.sort(key=lambda item: (*classify_hierarchy(item), item.title.lower(), item.url.lower()))

    for bookmark in chosen:
        level1, level2, level3 = classify_hierarchy(bookmark)
        top_counts[level1] += 1
        parent = root
        parent, next_id = ensure_folder(parent, f"{level1}{AUTO_SUFFIX}", next_id)
        parent, next_id = ensure_folder(parent, level2, next_id)
        parent, next_id = ensure_folder(parent, level3, next_id)
        url_node, next_id = base.make_url(bookmark.title, bookmark.url, next_id)
        parent.setdefault("children", []).append(url_node)
        parent["date_modified"] = base.chrome_timestamp_now()
        added += 1

    root["date_modified"] = base.chrome_timestamp_now()
    return added, top_counts


def build_report(
    source_path: Path,
    target_path: Path,
    source_bookmarks: list[base.BookmarkRecord],
    checks: dict[str, base.UrlCheckResult],
) -> dict[str, Any]:
    status_counter = Counter(result.status for result in checks.values())
    top_counter = Counter()
    sub_counter = Counter()
    third_counter = Counter()
    dead_items: list[dict[str, Any]] = []

    for bookmark in source_bookmarks:
        hierarchy = classify_hierarchy(bookmark)
        top_counter[hierarchy[0]] += 1
        sub_counter[f"{hierarchy[0]} / {hierarchy[1]}"] += 1
        third_counter[f"{hierarchy[0]} / {hierarchy[1]} / {hierarchy[2]}"] += 1
        result = checks.get(bookmark.url)
        if result and result.status == "dead":
            dead_items.append(
                {
                    "title": bookmark.title,
                    "url": bookmark.url,
                    "path": bookmark.path_display,
                    "detail": result.detail,
                    "hierarchy": hierarchy,
                }
            )

    return {
        "source_bookmarks_file": str(source_path),
        "target_bookmarks_file": str(target_path),
        "bookmark_count": len(source_bookmarks),
        "unique_url_count": len(checks),
        "status_summary": dict(status_counter),
        "top_level_summary": dict(top_counter.most_common()),
        "second_level_summary": dict(sub_counter.most_common(40)),
        "third_level_summary": dict(third_counter.most_common(80)),
        "dead_bookmarks": dead_items,
    }


def print_summary(report: dict[str, Any]) -> None:
    print(f"来源书签: {report['source_bookmarks_file']}")
    print(f"目标书签: {report['target_bookmarks_file']}")
    print(f"书签总数: {report['bookmark_count']}")
    print(f"唯一链接: {report['unique_url_count']}")
    print("状态统计:")
    for status, count in sorted(report["status_summary"].items()):
        print(f"  - {status}: {count}")
    print("顶层分类统计:")
    for category, count in list(report["top_level_summary"].items())[:12]:
        print(f"  - {category}: {count}")
    dead_items = report["dead_bookmarks"]
    if dead_items:
        print("确认失效（前 12）:")
        for item in dead_items[:12]:
            print(f"  - {item['title']} -> {item['url']} [{item['detail']}] => {' / '.join(item['hierarchy'])}")
    else:
        print("确认失效: 0")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="根据原始备份重建 Chrome 书签分类。")
    parser.add_argument("--profile", default="Fint", help="目标 Chrome profile 名称或显示名")
    parser.add_argument("--target-bookmarks-file", type=Path, help="目标 Bookmarks 文件；默认按 profile 查找")
    parser.add_argument("--source-bookmarks-file", type=Path, required=True, help="原始备份 Bookmarks 文件，作为重建来源")
    parser.add_argument("--source-roots", nargs="+", default=["bookmark_bar", "other", "synced"], choices=["bookmark_bar", "other", "synced"])
    parser.add_argument("--target-root", default="other", choices=["bookmark_bar", "other", "synced"])
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--concurrency", type=int, default=16)
    parser.add_argument("--report-file", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--apply", action="store_true", help="真正写回目标书签")
    parser.add_argument("--backup-dir", type=Path, default=Path("playground/chrome_bookmarks_backups"))
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    source_path = args.source_bookmarks_file.expanduser().resolve()
    target_path = base.resolve_bookmarks_path(args.profile, args.target_bookmarks_file)

    source_data = base.load_json(source_path)
    target_data = base.load_json(target_path)
    source_bookmarks = base.collect_bookmarks(source_data, tuple(args.source_roots))
    unique_urls = sorted({bookmark.url for bookmark in source_bookmarks if bookmark.url})
    checks = base.run_url_checks(unique_urls, args.timeout, args.concurrency)

    report = build_report(source_path, target_path, source_bookmarks, checks)
    args.report_file.parent.mkdir(parents=True, exist_ok=True)
    base.write_json(args.report_file, report)
    print_summary(report)
    print(f"重建报告已写入: {args.report_file.resolve()}")

    if not args.apply:
        return 0

    is_live_target = str(target_path).startswith(str(base.CHROME_BASE))
    if is_live_target and base.chrome_running():
        raise SystemExit("检测到 Google Chrome 正在运行。请先退出 Chrome，再执行重建。")

    backup_path = base.backup_file(target_path, args.backup_dir)
    print(f"已备份当前目标书签: {backup_path.resolve()}")

    removed_generated = 0
    cleared_urls = 0
    for root_name in ("bookmark_bar", "other", "synced"):
        root = (target_data.get("roots") or {}).get(root_name)
        if not root:
            continue
        if root_name == args.target_root:
            removed_generated += remove_generated_top_level_folders(root)
        cleared_urls += clear_bookmarks_keep_folders(root)

    added, top_counts = build_hierarchical_folders(target_data, source_bookmarks, checks, args.target_root)
    base.write_json(target_path, target_data)

    print(f"已移除旧的自动整理顶层文件夹: {removed_generated}")
    print(f"已清空原结构中的书签: {cleared_urls}")
    print(f"已重建书签到新分类目录: {added}")
    print("新顶层分类:")
    for name, count in top_counts.most_common():
        print(f"  - {name}{AUTO_SUFFIX}: {count}")
    print(f"已写回目标书签: {target_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(__import__("sys").argv[1:]))
