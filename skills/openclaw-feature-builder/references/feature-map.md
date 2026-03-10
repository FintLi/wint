# Feature Map

Use this map to decide where a requested feature belongs before editing code.

## 1. Main file

Primary implementation target:

- `/Users/fint/Public/projects/wint/tools/firststand_feishu_digest.py`

Primary touchpoints in that file:

- `SECTION_TITLES`
- `PREMATCH_SECTION_TITLES`
- `build_context()`
- `build_prematch_context()`
- `build_digest_prompt()`
- `build_prematch_prompt()`
- `run_openclaw()`
- `send_digest_cards()`
- `send_prematch_alert()`
- `maybe_send_prematch()`
- `main()`

## 2. Request routing

### A. “日报加一个栏目”

Likely touchpoints:

- `SECTION_TITLES`
- `SECTION_TEMPLATES`
- `build_context()` if new data is needed
- `build_digest_prompt()`
- `links_for_section()` if section-specific links help
- `send_digest_cards()` only if send order or footer behavior changes

### B. “赛前提醒多加一个模块 / 多发一种提醒”

Likely touchpoints:

- `PREMATCH_SECTION_TITLES`
- `build_prematch_context()`
- `build_prematch_prompt()`
- `send_prematch_alert()`
- `maybe_send_prematch()` if send timing or dedupe changes

### C. “多抓一种数据 / 新闻 / 来源”

Likely touchpoints:

- `http_get()` callers and parsing helpers
- `build_context()` or `build_prematch_context()`
- prompt builders only after the new field exists in context
- artifact inspection after generation to confirm the field really flowed through

### D. “换卡片样式 / 多按钮 / 更好看”

Likely touchpoints:

- `build_card_payload()`
- `build_prematch_card_payload()`
- `send_digest_cards()` or `send_prematch_alert()`

Constraint:

- current webhook mode supports interactive cards and links well
- current webhook mode does not provide a stable inline `img_key` upload path

### E. “加去重 / 记忆 / 避免重复发”

Likely touchpoints:

- `load_sent_alerts()`
- `save_sent_alerts()`
- `maybe_send_prematch()`
- files under `/var/lib/openclaw-firststand`

### F. “加一个命令 / 参数 / 运行模式”

Likely touchpoints:

- `main()` argument parsing
- env var defaults in `main()`
- any caller that needs a new branch for preview/send/send-prematch behavior

## 3. Remote surfaces to remember

When the feature changes deployment behavior, also check these live files:

- `/opt/openclaw-firststand/firststand_feishu_digest.py`
- `/usr/local/bin/openclaw-firststand-feishu`
- `/usr/local/bin/openclaw-firststand-prematch`
- `/etc/openclaw-firststand.env`
- `/etc/cron.d/openclaw-firststand-feishu`

If the issue becomes OpenClaw-core or host-level while implementing the feature, hand off to the existing incident skills instead of mixing workflows.
