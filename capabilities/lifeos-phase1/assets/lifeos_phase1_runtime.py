from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

try:
    from gateway.platforms.record_feedback_contract import build_record_feedback_contract
except ImportError:
    current_dir = Path(__file__).resolve().parent
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    try:
        from record_feedback_contract import build_record_feedback_contract
    except ImportError:
        def build_record_feedback_contract(event: Dict[str, Any]) -> Dict[str, Any]:
            raw_text = normalize_text(event.get("raw_text"))
            summary = normalize_text(event.get("instant_feedback")) or raw_text[:60]
            return {
                "header_template": "blue",
                "title": "📝 已记录",
                "subtitle": "这条内容已经进入 Phase 1 影子写入。",
                "summary": summary,
                "sections": [
                    {"title": "🧾 内容", "items": [raw_text]},
                    {"title": "🎯 关键信号", "items": [summary]},
                ],
                "tags": [],
                "note_text": "",
            }


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS lifeos_events (
    event_id TEXT PRIMARY KEY,
    event_schema_version TEXT NOT NULL,
    captured_at INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT '',
    source_meta_json TEXT NOT NULL DEFAULT '{}',
    raw_text TEXT NOT NULL,
    raw_links_json TEXT NOT NULL DEFAULT '[]',
    raw_context_json TEXT NOT NULL DEFAULT '{}',
    event_type TEXT NOT NULL DEFAULT 'self_expression',
    input_type TEXT NOT NULL DEFAULT '',
    expression_form TEXT NOT NULL DEFAULT '',
    scene_type TEXT NOT NULL DEFAULT '',
    signal_type TEXT NOT NULL DEFAULT '',
    emotion_tags_json TEXT NOT NULL DEFAULT '[]',
    energy_state TEXT NOT NULL DEFAULT '',
    role_signals_json TEXT NOT NULL DEFAULT '[]',
    need_signals_json TEXT NOT NULL DEFAULT '[]',
    intention_signals_json TEXT NOT NULL DEFAULT '[]',
    assumption_signals_json TEXT NOT NULL DEFAULT '[]',
    meaning_functions_json TEXT NOT NULL DEFAULT '[]',
    idea_systems_json TEXT NOT NULL DEFAULT '[]',
    lifeos_routes_json TEXT NOT NULL DEFAULT '[]',
    handling_mode TEXT NOT NULL DEFAULT '',
    importance_level TEXT NOT NULL DEFAULT '',
    importance_reason TEXT NOT NULL DEFAULT '',
    should_feedback INTEGER NOT NULL DEFAULT 1,
    feedback_mode TEXT NOT NULL DEFAULT 'light_feedback',
    should_continue_dialogue INTEGER NOT NULL DEFAULT 0,
    related_module_ids_json TEXT NOT NULL DEFAULT '[]',
    archive_markdown_path TEXT NOT NULL DEFAULT '',
    bitable_record_id TEXT NOT NULL DEFAULT '',
    payload_json TEXT NOT NULL DEFAULT '{}',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lifeos_feedback_cards (
    feedback_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    feedback_mode TEXT NOT NULL,
    card_title TEXT NOT NULL DEFAULT '',
    card_subtitle TEXT NOT NULL DEFAULT '',
    heard_summary TEXT NOT NULL DEFAULT '',
    core_signal TEXT NOT NULL DEFAULT '',
    emotion_tags_json TEXT NOT NULL DEFAULT '[]',
    energy_state TEXT NOT NULL DEFAULT '',
    role_signals_json TEXT NOT NULL DEFAULT '[]',
    structure_snapshot_json TEXT NOT NULL DEFAULT '{}',
    insight_note TEXT NOT NULL DEFAULT '',
    importance_reason TEXT NOT NULL DEFAULT '',
    next_step_suggestion TEXT NOT NULL DEFAULT '',
    followup_question TEXT NOT NULL DEFAULT '',
    closing_quote TEXT NOT NULL DEFAULT '',
    card_payload_json TEXT NOT NULL DEFAULT '{}',
    channel TEXT NOT NULL DEFAULT 'feishu_card',
    channel_message_id TEXT NOT NULL DEFAULT '',
    generated_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (event_id) REFERENCES lifeos_events(event_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lifeos_modules (
    module_id TEXT PRIMARY KEY,
    module_name TEXT NOT NULL,
    module_type TEXT NOT NULL,
    current_status TEXT NOT NULL,
    module_goal TEXT NOT NULL DEFAULT '',
    problem_to_solve TEXT NOT NULL DEFAULT '',
    why_it_matters TEXT NOT NULL DEFAULT '',
    input_sources_json TEXT NOT NULL DEFAULT '[]',
    output_artifacts_json TEXT NOT NULL DEFAULT '[]',
    core_rules_json TEXT NOT NULL DEFAULT '[]',
    working_mechanism TEXT NOT NULL DEFAULT '',
    related_idea_systems_json TEXT NOT NULL DEFAULT '[]',
    related_lifeos_routes_json TEXT NOT NULL DEFAULT '[]',
    upstream_dependencies_json TEXT NOT NULL DEFAULT '[]',
    downstream_effects_json TEXT NOT NULL DEFAULT '[]',
    owner TEXT NOT NULL DEFAULT '',
    current_blockers TEXT NOT NULL DEFAULT '',
    next_action TEXT NOT NULL DEFAULT '',
    acceptance_criteria TEXT NOT NULL DEFAULT '',
    review_cycle TEXT NOT NULL DEFAULT '',
    last_reviewed_at INTEGER,
    source_event_ids_json TEXT NOT NULL DEFAULT '[]',
    source_feedback_ids_json TEXT NOT NULL DEFAULT '[]',
    notes_md_path TEXT NOT NULL DEFAULT '',
    bitable_record_id TEXT NOT NULL DEFAULT '',
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS lifeos_routes (
    route_id TEXT PRIMARY KEY,
    event_id TEXT NOT NULL,
    primary_route TEXT NOT NULL,
    secondary_routes_json TEXT NOT NULL DEFAULT '[]',
    target_module_ids_json TEXT NOT NULL DEFAULT '[]',
    target_systems_json TEXT NOT NULL DEFAULT '[]',
    route_reason TEXT NOT NULL DEFAULT '',
    execution_status TEXT NOT NULL DEFAULT 'queued',
    followup_needed INTEGER NOT NULL DEFAULT 0,
    routed_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (event_id) REFERENCES lifeos_events(event_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS lifeos_supervisions (
    supervision_id TEXT PRIMARY KEY,
    module_id TEXT NOT NULL,
    supervision_status TEXT NOT NULL DEFAULT 'on_track',
    current_focus TEXT NOT NULL DEFAULT '',
    blocker_summary TEXT NOT NULL DEFAULT '',
    progress_note TEXT NOT NULL DEFAULT '',
    next_checkpoint TEXT NOT NULL DEFAULT '',
    supervision_action TEXT NOT NULL DEFAULT '',
    reviewed_at INTEGER NOT NULL,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    FOREIGN KEY (module_id) REFERENCES lifeos_modules(module_id) ON DELETE CASCADE
);
"""


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = "，".join(str(item).strip() for item in value if str(item).strip())
    return re.sub(r"\s+", " ", str(value)).strip()


def unique_list(values: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        item = normalize_text(value)
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def split_tags(value: Any) -> List[str]:
    text = normalize_text(value)
    if not text:
        return []
    return unique_list(re.split(r"\s*[,，/]\s*", text))


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return False


def _hermes_home() -> Path:
    raw = os.getenv("HERMES_HOME", "").strip()
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".hermes"


def _phase1_root() -> Path:
    override = os.getenv("LIFEOS_PHASE1_ROOT", "").strip()
    if override:
        return Path(override).expanduser()
    return _hermes_home() / "data" / "lifeos-phase1"


def _db_path() -> Path:
    override = os.getenv("LIFEOS_PHASE1_DB_PATH", "").strip()
    if override:
        return Path(override).expanduser()
    return _phase1_root() / "lifeos_phase1.sqlite"


def _markdown_root() -> Path:
    return _phase1_root() / "markdown"


def ensure_storage_ready() -> None:
    root = _phase1_root()
    root.mkdir(parents=True, exist_ok=True)
    _markdown_root().mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(_db_path(), timeout=1) as conn:
        conn.executescript(SCHEMA_SQL)


def _upsert(conn: sqlite3.Connection, table: str, row: Dict[str, Any], key_field: str) -> None:
    columns = list(row.keys())
    placeholders = ", ".join("?" for _ in columns)
    updates = ", ".join(f"{col}=excluded.{col}" for col in columns if col != key_field)
    sql = (
        f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders}) "
        f"ON CONFLICT({key_field}) DO UPDATE SET {updates}"
    )
    conn.execute(sql, [row[column] for column in columns])


def _row_to_dict(cursor: sqlite3.Cursor, row: tuple) -> Dict[str, Any]:
    return {description[0]: row[index] for index, description in enumerate(cursor.description or [])}


def _merge_json_lists(existing_value: Any, incoming_value: Any) -> str:
    existing = []
    incoming = []
    try:
        if existing_value:
            existing = json.loads(existing_value)
    except Exception:
        existing = []
    try:
        if incoming_value:
            incoming = json.loads(incoming_value)
    except Exception:
        incoming = []
    return dumps(unique_list([*(existing or []), *(incoming or [])]))


def _upsert_module_candidate(conn: sqlite3.Connection, row: Dict[str, Any]) -> None:
    cursor = conn.execute("SELECT * FROM lifeos_modules WHERE module_id = ?", (row["module_id"],))
    existing_row = cursor.fetchone()
    if not existing_row:
        _upsert(conn, "lifeos_modules", row, "module_id")
        return

    existing = _row_to_dict(cursor, existing_row)
    merged = dict(existing)
    merged["module_name"] = row["module_name"] or existing.get("module_name", "")
    merged["module_type"] = row["module_type"] or existing.get("module_type", "")
    merged["current_status"] = existing.get("current_status") or row["current_status"]
    if merged["current_status"] == "idea" and row.get("current_status"):
        merged["current_status"] = row["current_status"]
    for field in (
        "module_goal",
        "problem_to_solve",
        "why_it_matters",
        "working_mechanism",
        "owner",
        "current_blockers",
        "next_action",
        "acceptance_criteria",
        "review_cycle",
        "notes_md_path",
        "bitable_record_id",
    ):
        merged[field] = existing.get(field) or row.get(field) or ""
    for field in (
        "input_sources_json",
        "output_artifacts_json",
        "core_rules_json",
        "related_idea_systems_json",
        "related_lifeos_routes_json",
        "upstream_dependencies_json",
        "downstream_effects_json",
        "source_event_ids_json",
        "source_feedback_ids_json",
    ):
        merged[field] = _merge_json_lists(existing.get(field), row.get(field))
    merged["last_reviewed_at"] = row.get("last_reviewed_at") or existing.get("last_reviewed_at")
    merged["updated_at"] = row.get("updated_at") or existing.get("updated_at") or int(time.time() * 1000)
    _upsert(conn, "lifeos_modules", merged, "module_id")


def infer_input_type(event: Dict[str, Any]) -> str:
    raw_text = normalize_text(event.get("raw_text"))
    scene_type = normalize_text(event.get("scene_type"))
    topic_tags = split_tags(event.get("topic_tags"))
    if re.search(r"Hermes|OpenClaw|Codex|agent|bot|架构|源码|代码层|路由|schema", raw_text, re.IGNORECASE):
        return "行动过程"
    if any(tag in topic_tags for tag in ("家庭", "孩子", "关系", "人物观察")):
        return "人际触动"
    if any(tag in topic_tags for tag in ("读书", "学习")) or re.search(r"读书|阅读|这本书|作者", raw_text):
        return "读书"
    if re.search(r"https?://|网页|文章|看到.*信息|网上|链接", raw_text):
        return "网络信息"
    if scene_type == "情绪":
        return "内心感受/念头"
    if scene_type in {"复盘", "记录"} or re.search(r"做完|推进|刚处理完|事前|事后|复盘", raw_text):
        return "行动过程"
    if re.search(r"冥想|静下来|觉察|感受充分表达", raw_text):
        return "冥想表达"
    if scene_type in {"触动", "启发", "灵感"}:
        return "内心感受/念头"
    return "客观事件记录"


def infer_expression_form(event: Dict[str, Any]) -> str:
    scene_type = normalize_text(event.get("scene_type"))
    output_mode = normalize_text(event.get("output_mode"))
    event_type = normalize_text(event.get("event_type"))
    parts: List[str] = []
    if scene_type:
        parts.append(scene_type)
    if scene_type == "灵感":
        parts.append("灵感表达")
    elif scene_type == "情绪":
        parts.append("情绪表达")
    elif scene_type == "启发":
        parts.append("认知澄清")
    elif scene_type == "复盘":
        parts.append("复盘表达")
    if event_type == "request":
        parts.append("带请求")
    if output_mode == "深洞察":
        parts.append("深挖意图")
    elif output_mode == "轻反馈":
        parts.append("轻反馈")
    return " + ".join(unique_list(parts)) or "自然表达"


def infer_signal_type(event: Dict[str, Any]) -> str:
    raw_text = normalize_text(event.get("raw_text"))
    scene_type = normalize_text(event.get("scene_type"))
    if re.search(r"怎么办|为什么|能不能|是不是|该怎么", raw_text):
        return "问题"
    if scene_type == "灵感":
        return "灵感"
    if scene_type == "情绪":
        return "感受"
    if scene_type == "复盘":
        return "判断"
    if scene_type == "记录":
        return "纪实"
    if re.search(r"后续|下一步|准备|推进", raw_text):
        return "计划"
    return "判断"


def infer_energy_state(event: Dict[str, Any]) -> str:
    raw_text = normalize_text(event.get("raw_text"))
    intensity = normalize_text(event.get("intensity"))
    special_flags = split_tags(event.get("special_flags") or event.get("special_flag"))
    if re.search(r"爱|温暖|幸福|孩子", raw_text):
        return "爱（500）"
    if re.search(r"调试|测试|验收|判断|分析|字段|schema|流程|试试看|不会那么理想|不可能那么清楚", raw_text):
        return "理性（400）"
    if intensity == "high" or re.search(r"兴奋|特别有劲|特别想|超级|飞起来|wow|太好了", raw_text, re.IGNORECASE):
        return "意愿（310）"
    if "low_energy" in special_flags or re.search(r"累|疲惫|透支|没劲|困|担心|焦虑|不安", raw_text):
        return "勇气（200）"
    if re.search(r"一方面|另一方面|拉扯|矛盾", raw_text):
        return "中性（250）"
    return "中性（250）"


def infer_role_signals(event: Dict[str, Any]) -> List[str]:
    raw_text = normalize_text(event.get("raw_text"))
    topic_tags = split_tags(event.get("topic_tags"))
    roles: List[str] = []
    if re.search(r"觉知澄|觉察|观察自己", raw_text):
        roles.append("觉知澄")
    if re.search(r"系统|架构|模块|schema|路由|Hermes|Codex|OpenClaw", raw_text, re.IGNORECASE):
        roles.append("系统架构师")
    if any(tag in topic_tags for tag in ("家庭", "孩子")) or re.search(r"孩子|儿子|女儿|爸爸|父亲", raw_text):
        roles.append("父亲角色")
    if any(tag in topic_tags for tag in ("学习", "读书")):
        roles.append("学习者")
    if re.search(r"带大家|管理|推进|负责人|团队", raw_text):
        roles.append("推进者")
    return unique_list(roles)


def infer_meaning_functions(event: Dict[str, Any]) -> List[str]:
    output_mode = normalize_text(event.get("output_mode"))
    routes_to = split_tags(event.get("routes_to"))
    needs = split_tags(event.get("needs"))
    result: List[str] = []
    if output_mode in {"轻反馈", "深洞察"} or any(item in needs for item in ("clarity", "feedback", "decision")):
        result.append("需消化")
    if any(item in needs for item in ("decision", "guidance")):
        result.append("需决策")
    if any(item in needs for item in ("capture", "expression", "organization")):
        result.append("需沉淀")
    if any(item in needs for item in ("action",)) or re.search(r"下一步|去做|推进", normalize_text(event.get("raw_text"))):
        result.append("需行动")
    if any(route in routes_to for route in ("weekly_review_pool", "research_queue")):
        result.append("需分发")
    if re.search(r"观察|持续看|留意", normalize_text(event.get("raw_text"))):
        result.append("需观察追踪")
    return unique_list(result or ["需沉淀"])


def infer_idea_systems(event: Dict[str, Any]) -> List[str]:
    raw_text = normalize_text(event.get("raw_text"))
    topic_tags = split_tags(event.get("topic_tags"))
    systems: List[str] = []
    if re.search(r"系统|架构|模块|schema|路由|稳定运行", raw_text):
        systems.append("系统建设")
    if re.search(r"生产力|效率|流程|推进", raw_text):
        systems.append("生产力")
    if re.search(r"领导|带团队|稳定自己", raw_text):
        systems.append("领导力")
    if re.search(r"投资|价值投资|股票", raw_text):
        systems.append("价值投资")
    if any(tag in topic_tags for tag in ("关系", "家庭")):
        systems.append("关系经营")
    if any(tag in topic_tags for tag in ("学习", "读书")):
        systems.append("自我成长")
    return unique_list(systems)


def infer_lifeos_routes(event: Dict[str, Any]) -> List[str]:
    raw_text = normalize_text(event.get("raw_text"))
    topic_tags = split_tags(event.get("topic_tags"))
    routes: List[str] = []
    if re.search(r"系统|架构|schema|路由|思考", raw_text):
        routes.append("思考系统")
    if re.search(r"目标|项目|推进|计划|方案", raw_text):
        routes.append("目标/项目管理")
    if any(tag in topic_tags for tag in ("家庭", "孩子")) or ("关系" in topic_tags and "Agent协作" not in topic_tags):
        routes.append("关系系统")
    if any(tag in topic_tags for tag in ("学习", "读书")):
        routes.append("学习系统")
    if re.search(r"业务|客户|创业|产品", raw_text):
        routes.append("业务系统")
    if re.search(r"自我增强|稳定自己|冥想|成长", raw_text):
        routes.append("自我增强系统")
    if re.search(r"孩子|教育", raw_text):
        routes.append("孩子教育系统")
    if re.search(r"内容|传播|自媒体", raw_text):
        routes.append("内容传播系统")
    return unique_list(routes or ["思考系统"])


def infer_handling_mode(event: Dict[str, Any]) -> str:
    output_mode = normalize_text(event.get("output_mode"))
    raw_text = normalize_text(event.get("raw_text"))
    if re.search(r"立刻|马上|现在就", raw_text):
        return "action"
    if re.search(r"项目|阶段|里程碑", raw_text):
        return "project"
    if output_mode in {"轻反馈", "深洞察"}:
        return "process"
    if re.search(r"观察|留意|看看后面", raw_text):
        return "watch"
    return "record"


def infer_importance_level(event: Dict[str, Any]) -> str:
    raw_text = normalize_text(event.get("raw_text"))
    scene_type = normalize_text(event.get("scene_type"))
    if _is_truthy(event.get("deep_review_candidate")):
        return "high"
    if re.search(r"Hermes|OpenClaw|Codex|架构|源码|代码层|稳定", raw_text, re.IGNORECASE):
        return "high"
    if re.search(r"特别|非常|超级|关键|很重要|太好了", raw_text):
        return "high"
    if scene_type in {"启发", "触动"}:
        return "high"
    if normalize_text(event.get("output_mode")) in {"轻反馈", "深洞察"}:
        return "medium"
    return "low"


def infer_importance_reason(event: Dict[str, Any]) -> str:
    raw_text = normalize_text(event.get("raw_text"))
    if re.search(r"系统|架构|schema|路由|模块|Hermes|OpenClaw|Codex", raw_text, re.IGNORECASE):
        return "这条内容会影响 LifeOS 主干结构，而不只是一次性记录。"
    if re.search(r"孩子|家庭|生日|纪念", raw_text):
        return "这条内容带有长期关系和生命记忆价值。"
    if re.search(r"启发|意识到|发现", raw_text):
        return "这条内容包含认知更新，值得被长期复用。"
    return "这条内容超过普通留存，值得进入结构化理解。"


def map_feedback_mode(event: Dict[str, Any]) -> str:
    output_mode = normalize_text(event.get("output_mode"))
    if output_mode == "仅记录":
        return "record_only"
    if output_mode == "深洞察":
        return "dialogue_invite"
    return "light_feedback"


def should_continue_dialogue(event: Dict[str, Any]) -> bool:
    raw_text = normalize_text(event.get("raw_text"))
    return bool(re.search(r"怎么办|你怎么看|可以吗|能不能|是不是|为什么", raw_text)) or normalize_text(event.get("output_mode")) == "深洞察"


def _module_catalog() -> Dict[str, Dict[str, str]]:
    return {
        "hermes_control_system": {"name": "Hermes 总控系统", "type": "meta"},
        "unified_intake": {"name": "统一入口", "type": "meta"},
        "event_interpretation": {"name": "事件解释系统", "type": "meta"},
        "memory_system": {"name": "记忆系统", "type": "meta"},
        "feedback_system": {"name": "反馈系统", "type": "meta"},
        "route_system": {"name": "路由系统", "type": "meta"},
        "module_ledger_system": {"name": "模块台账系统", "type": "meta"},
        "supervisor_system": {"name": "监督系统", "type": "meta"},
        "thinking_system": {"name": "思考系统", "type": "domain"},
        "relationship_system": {"name": "关系系统", "type": "domain"},
        "learning_system": {"name": "学习系统", "type": "domain"},
        "business_system": {"name": "业务系统", "type": "domain"},
        "project_system": {"name": "目标/项目管理系统", "type": "domain"},
        "self_enhancement_system": {"name": "自我增强系统", "type": "domain"},
        "child_education_system": {"name": "孩子教育系统", "type": "domain"},
        "content_system": {"name": "内容传播系统", "type": "domain"},
    }


def infer_related_module_ids(event: Dict[str, Any]) -> List[str]:
    raw_text = normalize_text(event.get("raw_text"))
    routes = infer_lifeos_routes(event)
    module_ids: List[str] = []
    if re.search(r"Hermes|OpenClaw|Codex|总控|入口|schema|路由|模块|架构|源码|代码层", raw_text, re.IGNORECASE):
        module_ids.extend(["hermes_control_system", "event_interpretation", "route_system"])
    route_map = {
        "思考系统": "thinking_system",
        "关系系统": "relationship_system",
        "学习系统": "learning_system",
        "业务系统": "business_system",
        "目标/项目管理": "project_system",
        "自我增强系统": "self_enhancement_system",
        "孩子教育系统": "child_education_system",
        "内容传播系统": "content_system",
    }
    for route in routes:
        if route in route_map:
            module_ids.append(route_map[route])
    return unique_list(module_ids)


def build_phase1_event_row(event: Dict[str, Any]) -> Dict[str, Any]:
    now_ms = int(time.time() * 1000)
    return {
        "event_id": normalize_text(event.get("event_id")),
        "event_schema_version": "lifeos_phase1_event_v1",
        "captured_at": event.get("captured_at") or now_ms,
        "source": normalize_text(event.get("source")),
        "source_meta_json": dumps(event.get("source_meta") or {}),
        "raw_text": normalize_text(event.get("raw_text")),
        "raw_links_json": dumps([]),
        "raw_context_json": dumps({
            "scene_type": normalize_text(event.get("scene_type")),
            "delivery_id": normalize_text(event.get("delivery_id")),
            "record_ingest": _is_truthy(event.get("record_ingest")),
        }),
        "event_type": normalize_text(event.get("event_type")) or "self_expression",
        "input_type": infer_input_type(event),
        "expression_form": infer_expression_form(event),
        "scene_type": normalize_text(event.get("scene_type")),
        "signal_type": infer_signal_type(event),
        "emotion_tags_json": dumps(split_tags(event.get("emotion_tags"))),
        "energy_state": infer_energy_state(event),
        "role_signals_json": dumps(infer_role_signals(event)),
        "need_signals_json": dumps(split_tags(event.get("needs"))),
        "intention_signals_json": dumps(unique_list([normalize_text(event.get("intention_guess"))] if normalize_text(event.get("intention_guess")) else [])),
        "assumption_signals_json": dumps([]),
        "meaning_functions_json": dumps(infer_meaning_functions(event)),
        "idea_systems_json": dumps(infer_idea_systems(event)),
        "lifeos_routes_json": dumps(infer_lifeos_routes(event)),
        "handling_mode": infer_handling_mode(event),
        "importance_level": infer_importance_level(event),
        "importance_reason": infer_importance_reason(event),
        "should_feedback": 0 if map_feedback_mode(event) == "record_only" else 1,
        "feedback_mode": map_feedback_mode(event),
        "should_continue_dialogue": 1 if should_continue_dialogue(event) else 0,
        "related_module_ids_json": dumps(infer_related_module_ids(event)),
        "archive_markdown_path": "",
        "bitable_record_id": normalize_text(event.get("bitable_record_id")),
        "payload_json": dumps(event),
        "created_at": now_ms,
        "updated_at": now_ms,
    }


def build_phase1_feedback_row(event: Dict[str, Any]) -> Dict[str, Any]:
    now_ms = int(time.time() * 1000)
    contract = build_record_feedback_contract(event)
    title = normalize_text(contract.get("title"))
    subtitle = normalize_text(contract.get("subtitle"))
    sections = contract.get("sections") or []
    heard_summary = normalize_text(contract.get("summary"))
    insight_note = ""
    next_step = ""
    followup_question = ""
    closing_quote = subtitle
    for section in sections:
        section_title = normalize_text(section.get("title"))
        items = [normalize_text(item) for item in (section.get("items") or []) if normalize_text(item)]
        if not items:
            continue
        if "关键内容" in section_title:
            if not heard_summary:
                heard_summary = items[0]
        elif "真正重要" in section_title:
            insight_note = items[0]
        elif "行动方向" in section_title:
            next_step = items[0]
        elif "继续帮你做些什么" in section_title:
            followup_question = items[0]
    if not heard_summary and sections:
        first_items = sections[0].get("items") or []
        heard_summary = normalize_text(first_items[0]) if first_items else ""
    return {
        "feedback_id": f"fb_{normalize_text(event.get('event_id'))}",
        "event_id": normalize_text(event.get("event_id")),
        "feedback_mode": map_feedback_mode(event),
        "card_title": title,
        "card_subtitle": subtitle,
        "heard_summary": heard_summary,
        "core_signal": infer_importance_reason(event),
        "emotion_tags_json": dumps(split_tags(event.get("emotion_tags"))),
        "energy_state": infer_energy_state(event),
        "role_signals_json": dumps(infer_role_signals(event)),
        "structure_snapshot_json": dumps(
            {
                "input_type": infer_input_type(event),
                "expression_form": infer_expression_form(event),
                "meaning_functions": infer_meaning_functions(event),
                "lifeos_routes": infer_lifeos_routes(event),
                "handling_mode": infer_handling_mode(event),
            }
        ),
        "insight_note": insight_note or heard_summary,
        "importance_reason": infer_importance_reason(event),
        "next_step_suggestion": next_step,
        "followup_question": followup_question,
        "closing_quote": closing_quote,
        "card_payload_json": dumps(contract),
        "channel": "feishu_card",
        "channel_message_id": "",
        "generated_at": now_ms,
        "created_at": now_ms,
        "updated_at": now_ms,
    }


def build_phase1_route_row(event: Dict[str, Any]) -> Dict[str, Any]:
    now_ms = int(time.time() * 1000)
    feedback_mode = map_feedback_mode(event)
    handling_mode = infer_handling_mode(event)
    related_module_ids = infer_related_module_ids(event)
    primary_route = "archive_only"
    if related_module_ids:
        primary_route = "module_ledger_update"
    elif feedback_mode == "dialogue_invite":
        primary_route = "dialogue_queue"
    elif handling_mode == "project":
        primary_route = "project_candidate"
    elif handling_mode == "action":
        primary_route = "action_candidate"
    elif handling_mode == "watch":
        primary_route = "watchlist"
    elif feedback_mode != "record_only":
        primary_route = "feedback_only"
    secondary_routes: List[str] = []
    if feedback_mode != "record_only" and primary_route != "feedback_only":
        secondary_routes.append("feedback_only")
    if handling_mode == "watch" and primary_route != "watchlist":
        secondary_routes.append("watchlist")
    return {
        "route_id": f"route_{normalize_text(event.get('event_id'))}",
        "event_id": normalize_text(event.get("event_id")),
        "primary_route": primary_route,
        "secondary_routes_json": dumps(unique_list(secondary_routes)),
        "target_module_ids_json": dumps(related_module_ids),
        "target_systems_json": dumps(infer_lifeos_routes(event)),
        "route_reason": infer_importance_reason(event),
        "execution_status": "queued",
        "followup_needed": 1 if should_continue_dialogue(event) or handling_mode in {"project", "action", "watch"} else 0,
        "routed_at": now_ms,
        "created_at": now_ms,
        "updated_at": now_ms,
    }


def build_phase1_module_candidates(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    now_ms = int(time.time() * 1000)
    catalog = _module_catalog()
    candidates: List[Dict[str, Any]] = []
    for module_id in infer_related_module_ids(event):
        meta = catalog.get(module_id, {"name": module_id, "type": "domain"})
        candidates.append(
            {
                "module_id": module_id,
                "module_name": meta["name"],
                "module_type": meta["type"],
                "current_status": "defined",
                "module_goal": "",
                "problem_to_solve": "",
                "why_it_matters": infer_importance_reason(event),
                "input_sources_json": dumps([normalize_text(event.get("source"))]),
                "output_artifacts_json": dumps([]),
                "core_rules_json": dumps([]),
                "working_mechanism": "",
                "related_idea_systems_json": dumps(infer_idea_systems(event)),
                "related_lifeos_routes_json": dumps(infer_lifeos_routes(event)),
                "upstream_dependencies_json": dumps([]),
                "downstream_effects_json": dumps([]),
                "owner": "hiddenwangcc",
                "current_blockers": "",
                "next_action": "",
                "acceptance_criteria": "",
                "review_cycle": "",
                "last_reviewed_at": now_ms,
                "source_event_ids_json": dumps([normalize_text(event.get("event_id"))]),
                "source_feedback_ids_json": dumps([f"fb_{normalize_text(event.get('event_id'))}"]),
                "notes_md_path": "",
                "bitable_record_id": "",
                "created_at": now_ms,
                "updated_at": now_ms,
            }
        )
    return candidates


def build_phase1_storage_bundle(event: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "event_row": build_phase1_event_row(event),
        "feedback_row": build_phase1_feedback_row(event),
        "route_row": build_phase1_route_row(event),
        "module_candidates": build_phase1_module_candidates(event),
    }


def _markdown_body(event: Dict[str, Any], bundle: Dict[str, Any]) -> str:
    event_row = bundle["event_row"]
    feedback_row = bundle["feedback_row"]
    route_row = bundle["route_row"]
    lines = [
        f"# {event_row['event_id']}",
        "",
        "## Raw",
        "",
        event_row["raw_text"],
        "",
        "## First Interpretation",
        "",
        f"- input_type: {event_row['input_type']}",
        f"- expression_form: {event_row['expression_form']}",
        f"- scene_type: {event_row['scene_type']}",
        f"- signal_type: {event_row['signal_type']}",
        f"- energy_state: {event_row['energy_state']}",
        f"- importance_level: {event_row['importance_level']}",
        f"- importance_reason: {event_row['importance_reason']}",
        f"- handling_mode: {event_row['handling_mode']}",
        f"- lifeos_routes: {json.loads(event_row['lifeos_routes_json'])}",
        "",
        "## Feedback Snapshot",
        "",
        f"- card_title: {feedback_row['card_title']}",
        f"- heard_summary: {feedback_row['heard_summary']}",
        f"- insight_note: {feedback_row['insight_note']}",
        f"- next_step_suggestion: {feedback_row['next_step_suggestion']}",
        "",
        "## Routing",
        "",
        f"- primary_route: {route_row['primary_route']}",
        f"- target_module_ids: {json.loads(route_row['target_module_ids_json'])}",
        "",
        "## Source Meta",
        "",
        "```json",
        json.dumps(event.get("source_meta") or {}, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(lines).strip() + "\n"


def write_markdown_snapshot(event: Dict[str, Any], bundle: Dict[str, Any]) -> str:
    captured_at = int(bundle["event_row"]["captured_at"] or int(time.time() * 1000))
    ts = time.localtime(captured_at / 1000)
    monthly_dir = _markdown_root() / f"{ts.tm_year:04d}-{ts.tm_mon:02d}"
    monthly_dir.mkdir(parents=True, exist_ok=True)
    markdown_path = monthly_dir / f"{bundle['event_row']['event_id']}.md"
    markdown_path.write_text(_markdown_body(event, bundle), encoding="utf-8")
    return str(markdown_path)


def persist_phase1_shadow_records(event: Dict[str, Any], logger=None) -> Dict[str, Any]:
    if os.getenv("LIFEOS_PHASE1_ENABLED", "1").strip().lower() in {"0", "false", "no", "off"}:
        return {"enabled": False, "written": False}

    ensure_storage_ready()
    bundle = build_phase1_storage_bundle(event)
    markdown_path = write_markdown_snapshot(event, bundle)
    bundle["event_row"]["archive_markdown_path"] = markdown_path

    db_path = _db_path()
    with sqlite3.connect(db_path, timeout=1) as conn:
        _upsert(conn, "lifeos_events", bundle["event_row"], "event_id")
        _upsert(conn, "lifeos_feedback_cards", bundle["feedback_row"], "feedback_id")
        _upsert(conn, "lifeos_routes", bundle["route_row"], "route_id")
        for row in bundle["module_candidates"]:
            _upsert_module_candidate(conn, row)
        conn.commit()

    shadow_meta = {
        "db_path": str(db_path),
        "markdown_path": markdown_path,
        "event_schema_version": bundle["event_row"]["event_schema_version"],
        "primary_route": bundle["route_row"]["primary_route"],
        "module_ids": json.loads(bundle["route_row"]["target_module_ids_json"]),
    }
    event["lifeos_phase1"] = shadow_meta
    if logger:
        logger.info(
            "[lifeos-phase1] shadow write ok event=%s route=%s modules=%s",
            bundle["event_row"]["event_id"],
            bundle["route_row"]["primary_route"],
            ",".join(shadow_meta["module_ids"]) or "-",
        )
    return {"enabled": True, "written": True, **shadow_meta}
