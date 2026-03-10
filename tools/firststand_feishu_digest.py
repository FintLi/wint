#!/usr/bin/env python3

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


SCHEDULE_URL = "https://lolesports.com/en-GB/leagues/first_stand"
PRIMER_URL = "https://lolesports.com/en-GB/news/first-stand-2026-primer"
HOTSPAWN_GROUP_DRAW_URL = "https://www.hotspawn.com/league-of-legends/news/first-stand-2026-group-draw"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
SHANGHAI = ZoneInfo("Asia/Shanghai")
DEFAULT_FOCUS_TEAMS = ["BLG", "JDG"]
TEAM_SEARCH_TERMS = {
    "BLG": ["BLG", "Bilibili Gaming", "Bilibili"],
    "JDG": ["JDG", "JD Gaming"],
    "WBG": ["WBG", "Weibo Gaming"],
    "TES": ["TES", "Top Esports"],
    "GEN": ["GEN", "Gen.G"],
    "G2": ["G2", "G2 Esports"],
    "BFX": ["BFX", "BNK FearX", "FearX"],
    "LOUD": ["LOUD"],
    "LYON": ["LYON", "LYON Gaming"],
    "TSW": ["TSW", "Team Secret Whales"],
}
TEAM_DISPLAY_NAMES = {
    "BLG": "Bilibili Gaming",
    "JDG": "JD Gaming",
    "WBG": "Weibo Gaming",
    "TES": "Top Esports",
    "GEN": "Gen.G",
    "G2": "G2 Esports",
    "BFX": "BNK FearX",
    "LOUD": "LOUD",
    "LYON": "LYON",
    "TSW": "Team Secret Whales",
}
GROUP_STAGE_SLOT_BLUEPRINTS = [
    {"group": "A", "round": "opening", "opening_index": 0},
    {"group": "A", "round": "opening", "opening_index": 1},
    {"group": "B", "round": "opening", "opening_index": 0},
    {"group": "B", "round": "opening", "opening_index": 1},
    {"group": "A", "round": "winners", "opening_index": None},
    {"group": "A", "round": "elimination", "opening_index": None},
    {"group": "B", "round": "winners", "opening_index": None},
    {"group": "B", "round": "elimination", "opening_index": None},
    {"group": "A", "round": "qualification", "opening_index": None},
    {"group": "B", "round": "qualification", "opening_index": None},
]
STATE_DIR = Path("/var/lib/openclaw-firststand")
SECTION_TITLES = [
    "每日赛事总览",
    "每日看点汇聚",
    "每日花边新闻",
    "每日下饭操作集锦",
    "每日高光操作集锦",
    "每日晋级的形式分析",
    "第二日的预测",
]
SECTION_TEMPLATES = {
    "每日赛事总览": "blue",
    "每日看点汇聚": "turquoise",
    "每日花边新闻": "purple",
    "每日下饭操作集锦": "yellow",
    "每日高光操作集锦": "green",
    "每日晋级的形式分析": "orange",
    "第二日的预测": "red",
}
PREMATCH_SECTION_TITLES = [
    "今日对阵",
    "当日新闻速看",
    "队伍与队员状态",
    "关键胜负手",
    "观赛提醒",
]


def http_get(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def http_post_json(url: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": USER_AGENT},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8", errors="replace")
    return json.loads(raw)


def extract_json_array(source: str, needle: str) -> list[dict[str, Any]]:
    start = source.find(needle)
    if start == -1:
        raise RuntimeError(f"needle not found: {needle}")

    index = start + len(needle) - 1
    level = 0
    in_string = False
    escape = False
    end = None

    for cursor, char in enumerate(source[index:], start=index):
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
                end = cursor
                break

    if end is None:
        raise RuntimeError("unterminated JSON array")

    return json.loads(source[index : end + 1])


def iso_to_shanghai(iso_value: str) -> datetime:
    if iso_value.endswith("Z"):
        iso_value = iso_value[:-1] + "+00:00"
    return datetime.fromisoformat(iso_value).astimezone(SHANGHAI)


def fetch_firststand_schedule() -> list[dict[str, Any]]:
    html = http_get(SCHEDULE_URL)
    events = extract_json_array(html, '"events":[')
    filtered = []
    for event in events:
        if event.get("league", {}).get("slug") != "first_stand":
            continue
        if event.get("tournament", {}).get("name") != "2026":
            continue

        teams = []
        for team in event.get("matchTeams", []):
            result = team.get("result") or {}
            teams.append(
                {
                    "name": team.get("name") or "TBD",
                    "code": team.get("code") or "TBD",
                    "gameWins": result.get("gameWins"),
                    "outcome": result.get("outcome"),
                }
            )

        filtered.append(
            {
                "id": event.get("id"),
                "block": event.get("blockName") or "Unknown",
                "startTime": event.get("startTime"),
                "localTime": iso_to_shanghai(event.get("startTime")).strftime("%Y-%m-%d %H:%M"),
                "state": event.get("state"),
                "strategy": (event.get("match") or {}).get("strategy", {}).get("count"),
                "teams": teams,
            }
        )

    filtered.sort(key=lambda item: item["startTime"])
    return filtered


def html_to_text(raw: str) -> str:
    text = re.sub(r"<script.*?</script>", "", raw, flags=re.S)
    text = re.sub(r"<style.*?</style>", "", text, flags=re.S)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = text.replace("&nbsp;", " ")
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = re.sub(r"\n+", "\n", text)
    return text


def team_display_name(team_code: str) -> str:
    return TEAM_DISPLAY_NAMES.get(team_code.upper(), team_code.upper())


def match_team_codes(event: dict[str, Any]) -> list[str]:
    return [team.get("code") or "TBD" for team in event.get("teams", [])]


def team_entry(team_code: str) -> dict[str, Any]:
    return {
        "name": team_display_name(team_code),
        "code": team_code,
        "gameWins": None,
        "outcome": None,
    }


def locked_match_codes(event: dict[str, Any]) -> list[str] | None:
    codes = match_team_codes(event)
    if len(codes) != 2 or "TBD" in codes:
        return None
    return codes


def outcome_code(event: dict[str, Any], outcome: str) -> str | None:
    for team in event.get("teams", []):
        if team.get("outcome") == outcome and team.get("code") not in {None, "TBD"}:
            return team["code"]
    return None


def fetch_hotspawn_group_draw_openers() -> dict[str, list[list[str]]]:
    raw = http_get(HOTSPAWN_GROUP_DRAW_URL)
    text = html_to_text(raw)
    matches = {}
    for group in ["A", "B"]:
        pattern = rf"Group {group}:\s*([A-Z0-9]+)\s+vs\s+([A-Z0-9]+),\s*([A-Z0-9]+)\s+vs\s+([A-Z0-9]+)"
        found = re.search(pattern, text)
        if not found:
            raise RuntimeError(f"could not parse Group {group} opener list")
        matches[group] = [
            [found.group(1), found.group(2)],
            [found.group(3), found.group(4)],
        ]
    return matches


def build_inferred_group_slots(group_events: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    if len(group_events) < 10:
        return {}

    openers = fetch_hotspawn_group_draw_openers()
    inferred: dict[int, dict[str, Any]] = {}

    for index, blueprint in enumerate(GROUP_STAGE_SLOT_BLUEPRINTS[:4]):
        codes = openers[blueprint["group"]][blueprint["opening_index"]]
        inferred[index] = {
            "codes": codes,
            "teamSource": "fallback_group_draw",
            "teamSourceUrl": HOTSPAWN_GROUP_DRAW_URL,
            "teamSourceNote": "官方赛程页尚未锁定首轮对阵时，按公开分组抽签结果补齐。",
        }

    group_pairs = {
        "A": (0, 1, 4, 5, 8),
        "B": (2, 3, 6, 7, 9),
    }
    for group, (open_one, open_two, winners_idx, elimination_idx, qualification_idx) in group_pairs.items():
        winner_one = outcome_code(group_events[open_one], "win")
        loser_one = outcome_code(group_events[open_one], "loss")
        winner_two = outcome_code(group_events[open_two], "win")
        loser_two = outcome_code(group_events[open_two], "loss")
        if winner_one and winner_two:
            inferred[winners_idx] = {
                "codes": [winner_one, winner_two],
                "teamSource": "fallback_bracket_inference",
                "teamSourceUrl": HOTSPAWN_GROUP_DRAW_URL,
                "teamSourceNote": f"{group} 组胜者战按已完成首轮赛果推导。",
            }
        if loser_one and loser_two:
            inferred[elimination_idx] = {
                "codes": [loser_one, loser_two],
                "teamSource": "fallback_bracket_inference",
                "teamSourceUrl": HOTSPAWN_GROUP_DRAW_URL,
                "teamSourceNote": f"{group} 组败者战按已完成首轮赛果推导。",
            }

        winners_loser = outcome_code(group_events[winners_idx], "loss") if winners_idx < len(group_events) else None
        elimination_winner = outcome_code(group_events[elimination_idx], "win") if elimination_idx < len(group_events) else None
        if winners_loser and elimination_winner:
            inferred[qualification_idx] = {
                "codes": [winners_loser, elimination_winner],
                "teamSource": "fallback_bracket_inference",
                "teamSourceUrl": HOTSPAWN_GROUP_DRAW_URL,
                "teamSourceNote": f"{group} 组出线战按同组已完成赛果推导。",
            }

    return inferred


def enrich_schedule_with_fallback(schedule: list[dict[str, Any]]) -> list[dict[str, Any]]:
    enriched = copy.deepcopy(schedule)
    group_events = [event for event in enriched if event.get("block") == "Groups"]

    inferred_slots: dict[int, dict[str, Any]] = {}
    try:
        inferred_slots = build_inferred_group_slots(group_events)
    except Exception:
        inferred_slots = {}

    for event in enriched:
        if "teamSource" not in event:
            event["teamSource"] = "official" if locked_match_codes(event) else "official_tbd"
            event["teamSourceUrl"] = SCHEDULE_URL
            event["teamSourceNote"] = None
            event["needsOfficialConfirmation"] = event["teamSource"] != "official"

    for index, event in enumerate(group_events):
        if locked_match_codes(event):
            continue
        payload = inferred_slots.get(index)
        if not payload:
            continue
        event["teams"] = [team_entry(code) for code in payload["codes"]]
        event["teamSource"] = payload["teamSource"]
        event["teamSourceUrl"] = payload["teamSourceUrl"]
        event["teamSourceNote"] = payload["teamSourceNote"]
        event["needsOfficialConfirmation"] = True

    return enriched


def fetch_news_items(query: str, limit: int = 8) -> list[dict[str, str | None]]:
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(query)
        + "&hl=en-US&gl=US&ceid=US:en"
    )
    xml_text = http_get(url)
    root = ET.fromstring(xml_text)
    items: list[dict[str, str | None]] = []
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        source = None
        source_node = item.find("source")
        if source_node is not None and source_node.text:
            source = source_node.text.strip()
        items.append(
            {
                "title": title,
                "link": link,
                "published": pub_date,
                "source": source,
            }
        )
        if len(items) >= limit:
            break
    return items


def normalize_news(items: list[dict[str, str | None]], focus_terms: list[str], max_age_days: int = 60) -> list[dict[str, str | None]]:
    seen = set()
    normalized: list[dict[str, str | None]] = []
    terms = [term.lower() for term in focus_terms]
    cutoff = datetime.now(ZoneInfo("UTC")) - timedelta(days=max_age_days)
    for item in items:
        title = (item.get("title") or "").strip()
        title_key = re.sub(r"\s+", " ", title.lower()).strip()
        if not title_key or title_key in seen:
            continue
        if any(year in title_key for year in ["2023", "2024"]):
            continue
        published = (item.get("published") or "").strip()
        if published:
            try:
                published_at = parsedate_to_datetime(published)
                if published_at.tzinfo is None:
                    published_at = published_at.replace(tzinfo=ZoneInfo("UTC"))
                if published_at.astimezone(ZoneInfo("UTC")) < cutoff:
                    continue
            except Exception:
                pass
        if "first stand" not in title_key and not any(term in title_key for term in terms):
            continue
        seen.add(title_key)
        normalized.append(item)
    return normalized


def collect_news(focus_teams: list[str]) -> list[dict[str, str | None]]:
    queries = [
        "2026 League of Legends First Stand",
        f"LPL First Stand 2026 {' '.join(focus_teams)}",
        f"First Stand 2026 {' '.join(focus_teams)}",
        "First Stand 2026 Group Stage matchups",
        "First Stand 2026 venue criticism",
        "First Stand 2026 highlights",
    ]
    merged: list[dict[str, str | None]] = []
    for query in queries:
        merged.extend(fetch_news_items(query))
    return normalize_news(merged, focus_teams)[:12]


def team_search_terms(team_code: str) -> list[str]:
    aliases = TEAM_SEARCH_TERMS.get(team_code.upper(), [team_code.upper()])
    deduped = []
    seen = set()
    for item in aliases:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def collect_team_news(team_codes: list[str]) -> list[dict[str, str | None]]:
    queries = []
    focus_terms: list[str] = []
    alias_sets: list[list[str]] = []
    for team in team_codes:
        aliases = team_search_terms(team)
        alias_sets.append(aliases)
        focus_terms.extend(aliases)
        primary = aliases[0]
        alternate = aliases[1] if len(aliases) > 1 else aliases[0]
        queries.extend(
            [
                f"{primary} First Stand 2026 League of Legends",
                f"{alternate} First Stand 2026",
                f"{alternate} LPL 2026 playoffs",
                f"{alternate} League of Legends 2026 form",
            ]
        )
    if len(alias_sets) == 2:
        left = alias_sets[0][1] if len(alias_sets[0]) > 1 else alias_sets[0][0]
        right = alias_sets[1][1] if len(alias_sets[1]) > 1 else alias_sets[1][0]
        queries.extend(
            [
                f"{left} {right} LPL 2026",
                f"{left} {right} First Stand 2026",
            ]
        )
    merged: list[dict[str, str | None]] = []
    for query in queries:
        merged.extend(fetch_news_items(query, limit=5))
    return normalize_news(merged, focus_terms + team_codes + ["First Stand"])[:8]


def summarize_day(events: list[dict[str, Any]], day: date) -> list[dict[str, Any]]:
    results = []
    for event in events:
        local_dt = iso_to_shanghai(event["startTime"])
        if local_dt.date() != day:
            continue
        teams = []
        for team in event["teams"]:
            team_text = team["code"]
            if team.get("gameWins") is not None:
                team_text += f"({team['gameWins']})"
            teams.append(team_text)
        results.append(
            {
                "id": event["id"],
                "time": local_dt.strftime("%m-%d %H:%M"),
                "block": event["block"],
                "state": event["state"],
                "bo": event["strategy"],
                "match": " vs ".join(teams),
                "teams": [team["code"] for team in event["teams"]],
                "teamSource": event.get("teamSource", "official"),
                "needsOfficialConfirmation": event.get("needsOfficialConfirmation", False),
                "teamSourceNote": event.get("teamSourceNote"),
            }
        )
    return results


def latest_completed_match_day(events: list[dict[str, Any]]) -> date | None:
    completed_days = []
    for event in events:
        if event.get("state") != "completed":
            continue
        completed_days.append(iso_to_shanghai(event["startTime"]).date())
    return max(completed_days) if completed_days else None


def build_context(target_date: datetime, focus_teams: list[str]) -> dict[str, Any]:
    schedule = enrich_schedule_with_fallback(fetch_firststand_schedule())
    current_day = target_date.date()
    event_start = iso_to_shanghai(schedule[0]["startTime"]).date() if schedule else None
    latest_completed_day = latest_completed_match_day(schedule)
    report_day = latest_completed_day or current_day
    prediction_day = report_day + timedelta(days=1)

    return {
        "generatedAt": target_date.isoformat(),
        "timezone": "Asia/Shanghai",
        "focusTeams": focus_teams,
        "eventStartDate": event_start.isoformat() if event_start else None,
        "daysUntilStart": (event_start - current_day).days if event_start and current_day <= event_start else 0,
        "currentDate": current_day.isoformat(),
        "reportDate": report_day.isoformat(),
        "predictionDate": prediction_day.isoformat(),
        "latestCompletedMatchDay": latest_completed_day.isoformat() if latest_completed_day else None,
        "todayMatches": summarize_day(schedule, report_day),
        "tomorrowMatches": summarize_day(schedule, prediction_day),
        "upcomingMatches": [
            item for item in schedule if iso_to_shanghai(item["startTime"]).date() >= current_day
        ][:8],
        "recentNews": collect_news(focus_teams),
        "sourceNotes": {
            "official_schedule_url": SCHEDULE_URL,
            "official_primer_url": PRIMER_URL,
            "fallback_group_draw_url": HOTSPAWN_GROUP_DRAW_URL,
            "known_official_facts": [
                "官方 First Stand 2026 赛程页当前可抓到 13 场事件，时间覆盖 2026-03-16 到 2026-03-22。",
                "官方 Primer 页面与官方赛程页均表明赛事包含 Groups 与 Knockout 两个阶段。",
                "官方赛程页在部分对阵未最终锁定前会显示 TBD，因此若队伍未锁定必须明确标注待官方确认。",
            ],
            "fallback_notes": [
                "当官方赛程页在组赛阶段仍显示 TBD 时，会参考 2026-03-08 的公开分组抽签结果补齐首轮对阵。",
                "首轮赛果产生后，同组后续胜者战、败者战、出线战会按已完成公开赛果推导；这类对阵仍需写明待官方最终确认。",
            ],
            "image_note": "当前接入的是飞书自定义群机器人 Webhook；若没有 img_key，卡片里不能稳定内嵌新闻配图。",
        },
    }


def build_digest_prompt(context: dict[str, Any]) -> str:
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    return textwrap.dedent(
        f"""
        你是一个英雄联盟国际赛中文日报编辑，现在要写发给个人飞书群的《先锋赛日报》。

        必须遵守：
        1. 只能基于我给你的上下文事实输出，不能编造赛果、选手发言、BP、单局细节或具体操作过程。
        2. 如果今天还没开赛，必须明确写“赛前阶段/暂无正式比赛”。
        3. 必须严格按下面 7 个一级标题输出，标题文字一个字都不要改：
           每日赛事总览
           每日看点汇聚
           每日花边新闻
           每日下饭操作集锦
           每日高光操作集锦
           每日晋级的形式分析
           第二日的预测
        4. 必须优先关注 LPL 队伍，尤其是：{', '.join(context['focusTeams'])}。
           如果官方对阵页还没最终锁定队伍，必须明确标注“待官方最终确认”。
        5. “每日下饭操作集锦”和“每日高光操作集锦”在没有正式比赛或没有足够事实依据时，必须老实写“暂无正式比赛集锦/待官方高光更新”，不要硬编。
        6. “每日晋级的形式分析”在赛前阶段要写成赛制门槛、LPL 机会点、风险点；开赛后再结合已知赛果写。
        7. “第二日的预测”若明天没有比赛，要写明“明日暂无正赛，重点关注……”；若明天有比赛，就给每场一个简短胜负倾向和一句理由。
        8. 每个章节控制在 120 到 260 字，适合拆成独立飞书卡片阅读。
        9. 风格要像真正懂比赛的人写的，但要克制、务实、信息密度高。
        10. 只输出这 7 个标题和对应内容，不要加前言后记。

        上下文如下：
        {context_json}
        """
    ).strip()


def build_prematch_context(target_date: datetime, focus_teams: list[str], alert_window_hours: int) -> dict[str, Any] | None:
    schedule = enrich_schedule_with_fallback(fetch_firststand_schedule())
    candidates = []
    for event in schedule:
        if event.get("state") != "unstarted":
            continue
        team_codes = match_team_codes(event)
        if "TBD" in team_codes:
            continue
        if not any(team in focus_teams for team in team_codes):
            continue
        event_time = iso_to_shanghai(event["startTime"])
        delta_hours = (event_time - target_date).total_seconds() / 3600
        if 0 < delta_hours <= alert_window_hours:
            candidates.append((delta_hours, event, team_codes))

    if not candidates:
        return None

    candidates.sort(key=lambda item: item[0])
    delta_hours, event, team_codes = candidates[0]
    focus_in_match = [team for team in team_codes if team in focus_teams]
    team_news = collect_team_news(team_codes)
    return {
        "generatedAt": target_date.isoformat(),
        "focusTeams": focus_teams,
        "focusInMatch": focus_in_match,
        "hoursUntilMatch": round(delta_hours, 1),
        "match": {
            "id": event["id"],
            "startTime": event["startTime"],
            "localTime": iso_to_shanghai(event["startTime"]).strftime("%Y-%m-%d %H:%M"),
            "block": event["block"],
            "bo": event["strategy"],
            "teams": event["teams"],
            "teamSource": event.get("teamSource", "official"),
            "teamSourceUrl": event.get("teamSourceUrl", SCHEDULE_URL),
            "teamSourceNote": event.get("teamSourceNote"),
            "needsOfficialConfirmation": event.get("needsOfficialConfirmation", False),
        },
        "recentTeamNews": team_news,
        "officialScheduleUrl": SCHEDULE_URL,
        "officialPrimerUrl": PRIMER_URL,
        "fallbackGroupDrawUrl": HOTSPAWN_GROUP_DRAW_URL,
        "imageNote": "当前为自定义群机器人 webhook 模式；如未接入 img_key 上传，新闻配图更适合作为原文链接而非卡片内嵌图。",
    }


def build_prematch_prompt(context: dict[str, Any]) -> str:
    context_json = json.dumps(context, ensure_ascii=False, indent=2)
    return textwrap.dedent(
        f"""
        你是一个英雄联盟赛前提醒编辑。请基于给定上下文，写一条发给飞书群的《LPL赛前提醒》。

        必须遵守：
        1. 只能基于上下文输出，不能编造选手状态、伤病、训练赛、BP、内幕。
        2. 重点聚焦 LPL 队伍：{', '.join(context['focusTeams'])}。
        3. 输出必须用下面 5 个二级小标题，且标题不要改：
           今日对阵
           当日新闻速看
           队伍与队员状态
           关键胜负手
           观赛提醒
        4. 如果 match.needsOfficialConfirmation 为 true，必须在“今日对阵”里明确写出“当前官方赛程页未最终锁定对阵，以下按公开分组/已知赛果推导，仍待官方最终确认”。
        5. “队伍与队员状态”如果没有足够公开信息，必须明确写“暂无更具体公开状态信息，更多仍是赛前舆情判断”。
        6. 风格要像真正看比赛的人写的，简洁、密度高、可读性强。
        7. 总长度控制在 350 到 700 个中文字符。
        8. 不要输出任何额外前言、落款或免责声明。

        上下文如下：
        {context_json}
        """
    ).strip()


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
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
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


def save_artifacts(target_date: datetime, context: dict[str, Any], content: str, prefix: str) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = target_date.strftime("%Y%m%d-%H%M%S")
    (STATE_DIR / f"{prefix}-context-{stamp}.json").write_text(
        json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (STATE_DIR / f"{prefix}-{stamp}.txt").write_text(content, encoding="utf-8")
    (STATE_DIR / f"last_{prefix}_context.json").write_text(
        json.dumps(context, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (STATE_DIR / f"last_{prefix}.txt").write_text(content, encoding="utf-8")


def resolve_target_datetime(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(SHANGHAI)
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=SHANGHAI)
    return parsed.astimezone(SHANGHAI)


def truncate_text(value: str, limit: int = 22) -> str:
    text = value.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def escape_lark(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def normalize_heading(line: str) -> str:
    return re.sub(r"^[#>\-*\s]+", "", line).strip()


def parse_named_sections(text: str, titles: list[str]) -> dict[str, str]:
    sections: dict[str, list[str]] = {title: [] for title in titles}
    current = None
    title_set = set(titles)
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading = normalize_heading(line)
        if heading in title_set:
            current = heading
            continue
        if current:
            sections[current].append(line)

    return {title: "\n".join(lines).strip() for title, lines in sections.items() if lines}


def parse_sections(briefing: str) -> dict[str, str]:
    return parse_named_sections(briefing, SECTION_TITLES)


def links_for_section(title: str, context: dict[str, Any]) -> list[dict[str, str]]:
    links: list[dict[str, str]] = [
        {"text": "官方赛程", "url": SCHEDULE_URL},
        {"text": "官方 Primer", "url": PRIMER_URL},
    ]

    if title == "每日花边新闻":
        for item in context.get("recentNews", [])[:2]:
            links.append({"text": truncate_text(item.get("title") or "原文"), "url": item.get("link") or SCHEDULE_URL})
    elif title in {"每日看点汇聚", "第二日的预测", "每日晋级的形式分析"}:
        for item in context.get("recentNews", [])[:1]:
            links.append({"text": truncate_text(item.get("title") or "原文"), "url": item.get("link") or SCHEDULE_URL})

    dedup = []
    seen = set()
    for link in links:
        key = (link["text"], link["url"])
        if key in seen:
            continue
        seen.add(key)
        dedup.append(link)
    return dedup[:3]


def build_card_payload(title: str, subtitle: str, body: str, template: str, links: list[dict[str, str]], footer_note: str) -> dict[str, Any]:
    body_md = escape_lark(body)
    elements: list[dict[str, Any]] = [
        {
            "tag": "note",
            "elements": [
                {"tag": "plain_text", "content": subtitle},
            ],
        },
        {
            "tag": "div",
            "text": {"tag": "lark_md", "content": body_md},
        },
    ]

    if links:
        elements.append({"tag": "hr"})
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": link["text"]},
                        "type": "default",
                        "url": link["url"],
                    }
                    for link in links
                ],
            }
        )

    if footer_note:
        elements.append(
            {
                "tag": "note",
                "elements": [{"tag": "plain_text", "content": footer_note}],
            }
        )

    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True, "enable_forward": True},
            "header": {
                "template": template,
                "title": {"tag": "plain_text", "content": title},
            },
            "elements": elements,
        },
    }


def build_prematch_card_payload(
    title: str,
    subtitle: str,
    sections: dict[str, str],
    template: str,
    links: list[dict[str, str]],
    footer_note: str,
    fallback_body: str,
) -> dict[str, Any]:
    elements: list[dict[str, Any]] = [
        {
            "tag": "note",
            "elements": [
                {"tag": "plain_text", "content": subtitle},
            ],
        }
    ]

    rendered = False
    for section_title in PREMATCH_SECTION_TITLES:
        body = sections.get(section_title)
        if not body:
            continue
        if rendered:
            elements.append({"tag": "hr"})
        elements.append(
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{escape_lark(section_title)}**\n{escape_lark(body)}",
                },
            }
        )
        rendered = True

    if not rendered:
        elements.append(
            {
                "tag": "div",
                "text": {"tag": "lark_md", "content": escape_lark(fallback_body)},
            }
        )

    if links:
        elements.append({"tag": "hr"})
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": link["text"]},
                        "type": "default",
                        "url": link["url"],
                    }
                    for link in links
                ],
            }
        )

    if footer_note:
        elements.append(
            {
                "tag": "note",
                "elements": [{"tag": "plain_text", "content": footer_note}],
            }
        )

    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True, "enable_forward": True},
            "header": {
                "template": template,
                "title": {"tag": "plain_text", "content": title},
            },
            "elements": elements,
        },
    }


def send_digest_cards(webhook: str, target_dt: datetime, context: dict[str, Any], briefing: str) -> list[dict[str, Any]]:
    sections = parse_sections(briefing)
    if not sections:
        raise RuntimeError("digest sections could not be parsed")

    responses = []
    subtitle = f"日报日期 {context.get('reportDate')}｜LPL重点 {'/'.join(context.get('focusTeams', []))}"
    footer_note = "卡片版已拆分发送。当前 webhook 模式下，新闻原文可点开，但要做卡片内嵌图片还需要 img_key 上传能力。"

    for title in SECTION_TITLES:
        if title not in sections:
            continue
        payload = build_card_payload(
            title=f"先锋赛日报｜{title}",
            subtitle=subtitle,
            body=sections[title],
            template=SECTION_TEMPLATES.get(title, "blue"),
            links=links_for_section(title, context),
            footer_note=footer_note if title == "每日花边新闻" else "",
        )
        response = http_post_json(webhook, payload)
        responses.append({"title": title, "response": response})
        if response.get("code") != 0:
            raise RuntimeError(f"Feishu digest card failed for {title}: {response}")
    return responses


def load_sent_alerts() -> dict[str, Any]:
    path = STATE_DIR / "prematch_sent.json"
    if not path.exists():
        return {"sent": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"sent": {}}


def save_sent_alerts(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "prematch_sent.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def send_prematch_alert(webhook: str, target_dt: datetime, context: dict[str, Any], content: str) -> dict[str, Any]:
    match = context["match"]
    teams = [team["code"] for team in match["teams"]]
    hours_until = context.get("hoursUntilMatch")
    hours_text = f"赛前约 {hours_until} 小时｜" if hours_until is not None else ""
    subtitle = f"{match['localTime']} 开赛｜{hours_text}BO{match.get('bo') or '?'}｜{' vs '.join(teams)}"
    links = [{"text": "官方赛程", "url": SCHEDULE_URL}]
    if match.get("needsOfficialConfirmation") and match.get("teamSourceUrl"):
        links.append({"text": "公开抽签/对阵源", "url": match["teamSourceUrl"]})
    recent_news = context.get("recentTeamNews", [])
    if recent_news:
        for item in recent_news[:2]:
            links.append({"text": truncate_text(item.get("title") or "相关新闻"), "url": item.get("link") or SCHEDULE_URL})
    elif not match.get("needsOfficialConfirmation"):
        links.append({"text": "官方 Primer", "url": PRIMER_URL})

    footer_note = "已基于公开赛程与公开新闻生成；当前 webhook 模式下更适合点开原文，不适合稳定内嵌新闻配图。"
    if match.get("needsOfficialConfirmation"):
        footer_note = "官方赛程页当前仍可能显示 TBD；本卡片已按公开分组抽签与已知赛果推导，仍以官方最终更新为准。"

    sections = parse_named_sections(content, PREMATCH_SECTION_TITLES)
    payload = build_prematch_card_payload(
        title=f"LPL 赛前提醒｜{' vs '.join(teams)}",
        subtitle=subtitle,
        sections=sections,
        template="red",
        links=links[:3],
        footer_note=footer_note,
        fallback_body=content,
    )
    response = http_post_json(webhook, payload)
    if response.get("code") != 0:
        raise RuntimeError(f"Feishu prematch card failed: {response}")
    return response


def maybe_send_prematch(webhook: str, target_dt: datetime, focus_teams: list[str], agent: str, alert_window_hours: int) -> dict[str, Any] | None:
    context = build_prematch_context(target_dt, focus_teams, alert_window_hours)
    if not context:
        return None

    state = load_sent_alerts()
    sent = state.setdefault("sent", {})
    match_id = context["match"]["id"]
    if match_id in sent:
        return {"skipped": True, "reason": "already_sent", "matchId": match_id}

    prompt = build_prematch_prompt(context)
    content = run_openclaw(prompt, agent)
    save_artifacts(target_dt, context, content, prefix="prematch")
    response = send_prematch_alert(webhook, target_dt, context, content)
    sent[match_id] = {
        "sentAt": target_dt.isoformat(),
        "localTime": context["match"]["localTime"],
        "teams": [team["code"] for team in context["match"]["teams"]],
    }
    save_sent_alerts(state)
    return {"skipped": False, "matchId": match_id, "response": response}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--send", action="store_true", help="Send daily digest cards to Feishu")
    parser.add_argument("--send-prematch", action="store_true", help="Send prematch alert card if a focus-team match is within the alert window")
    parser.add_argument("--datetime", help="Override target datetime, ISO 8601")
    parser.add_argument("--agent", default=os.environ.get("OPENCLAW_AGENT", "main"))
    parser.add_argument("--webhook", default=os.environ.get("FEISHU_WEBHOOK"))
    parser.add_argument(
        "--focus-teams",
        default=os.environ.get("LPL_FOCUS_TEAMS", ",".join(DEFAULT_FOCUS_TEAMS)),
        help="Comma-separated focus teams",
    )
    parser.add_argument(
        "--alert-window-hours",
        type=int,
        default=int(os.environ.get("PREMATCH_ALERT_WINDOW_HOURS", "12")),
        help="How many hours before a focus-team match to allow sending the prematch reminder",
    )
    args = parser.parse_args()

    target_dt = resolve_target_datetime(args.datetime)
    focus_teams = [item.strip() for item in args.focus_teams.split(",") if item.strip()]
    if not focus_teams:
        focus_teams = DEFAULT_FOCUS_TEAMS[:]

    if args.send:
        if not args.webhook:
            raise RuntimeError("FEISHU_WEBHOOK is required when --send is used")
        context = build_context(target_dt, focus_teams)
        prompt = build_digest_prompt(context)
        briefing = run_openclaw(prompt, args.agent)
        save_artifacts(target_dt, context, briefing, prefix="digest")
        print(f"OpenClaw 先锋赛日报｜{target_dt.strftime('%Y-%m-%d')}")
        print("=" * 25)
        print(briefing)
        responses = send_digest_cards(args.webhook, target_dt, context, briefing)
        print("\nFeishu digest responses:")
        print(json.dumps(responses, ensure_ascii=False, indent=2))

    if args.send_prematch:
        if not args.webhook:
            raise RuntimeError("FEISHU_WEBHOOK is required when --send-prematch is used")
        result = maybe_send_prematch(
            webhook=args.webhook,
            target_dt=target_dt,
            focus_teams=focus_teams,
            agent=args.agent,
            alert_window_hours=args.alert_window_hours,
        )
        print("\nPrematch result:")
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if not args.send and not args.send_prematch:
        context = build_context(target_dt, focus_teams)
        prompt = build_digest_prompt(context)
        briefing = run_openclaw(prompt, args.agent)
        print(briefing)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
