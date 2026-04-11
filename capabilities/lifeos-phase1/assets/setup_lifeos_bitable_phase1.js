#!/usr/bin/env node

const APP_ID = process.env.FEISHU_APP_ID || "";
const APP_SECRET = process.env.FEISHU_APP_SECRET || "";
const APP_TOKEN = process.env.LIFEOS_BITABLE_APP_TOKEN || process.env.FEELING_BITABLE_APP_TOKEN || "";
const EVENTS_TABLE_ID = process.env.LIFEOS_EVENTS_TABLE_ID || process.env.FEELING_BITABLE_TABLE_ID || "";
const MODULES_TABLE_ID = process.env.LIFEOS_MODULES_TABLE_ID || "";
const APPLY = process.argv.includes("--apply");
const TARGET = process.argv.includes("--modules") ? "modules" : "events";

if (!APP_ID || !APP_SECRET || !APP_TOKEN) {
  throw new Error("Missing FEISHU_APP_ID / FEISHU_APP_SECRET / LIFEOS_BITABLE_APP_TOKEN");
}

const FIELD_TYPES = {
  text: 1,
  singleSelect: 3,
  dateTime: 5,
  checkbox: 7,
};

function singleSelectOptions(names) {
  return names.map((name, index) => ({ name, color: index % 8 }));
}

const EVENT_FIELDS = [
  { field_name: "event_schema_version", type: FIELD_TYPES.text },
  { field_name: "captured_at", type: FIELD_TYPES.dateTime, property: { date_formatter: "yyyy/MM/dd HH:mm", auto_fill: false } },
  { field_name: "source", type: FIELD_TYPES.text },
  { field_name: "raw_text", type: FIELD_TYPES.text },
  { field_name: "input_type", type: FIELD_TYPES.singleSelect, property: { options: singleSelectOptions(["内心感受/念头", "人际触动", "网络信息", "读书", "行动过程", "冥想表达", "客观事件记录"]) } },
  { field_name: "expression_form", type: FIELD_TYPES.text },
  { field_name: "event_type", type: FIELD_TYPES.singleSelect, property: { options: singleSelectOptions(["self_expression", "capture", "request"]) } },
  { field_name: "scene_type", type: FIELD_TYPES.singleSelect, property: { options: singleSelectOptions(["复盘", "触动", "灵感", "情绪", "启发", "记录"]) } },
  { field_name: "signal_type", type: FIELD_TYPES.singleSelect, property: { options: singleSelectOptions(["灵感", "问题", "感受", "判断", "计划", "纪实"]) } },
  { field_name: "emotion_tags", type: FIELD_TYPES.text },
  { field_name: "energy_state", type: FIELD_TYPES.singleSelect, property: { options: singleSelectOptions(["低能量", "中能量", "高能量", "混合"]) } },
  { field_name: "role_signals", type: FIELD_TYPES.text },
  { field_name: "needs", type: FIELD_TYPES.text },
  { field_name: "intentions", type: FIELD_TYPES.text },
  { field_name: "assumptions", type: FIELD_TYPES.text },
  { field_name: "meaning_functions", type: FIELD_TYPES.text },
  { field_name: "idea_systems", type: FIELD_TYPES.text },
  { field_name: "lifeos_routes", type: FIELD_TYPES.text },
  { field_name: "handling_mode", type: FIELD_TYPES.singleSelect, property: { options: singleSelectOptions(["record", "process", "action", "project", "watch"]) } },
  { field_name: "importance_level", type: FIELD_TYPES.singleSelect, property: { options: singleSelectOptions(["low", "medium", "high"]) } },
  { field_name: "importance_reason", type: FIELD_TYPES.text },
  { field_name: "feedback_mode", type: FIELD_TYPES.singleSelect, property: { options: singleSelectOptions(["record_only", "light_feedback", "dialogue_invite"]) } },
  { field_name: "should_continue_dialogue", type: FIELD_TYPES.checkbox },
  { field_name: "related_module_ids", type: FIELD_TYPES.text },
  { field_name: "heard_summary", type: FIELD_TYPES.text },
  { field_name: "insight_note", type: FIELD_TYPES.text },
  { field_name: "next_step_suggestion", type: FIELD_TYPES.text },
  { field_name: "archive_markdown_path", type: FIELD_TYPES.text },
];

const MODULE_FIELDS = [
  { field_name: "module_name", type: FIELD_TYPES.text },
  { field_name: "module_type", type: FIELD_TYPES.singleSelect, property: { options: singleSelectOptions(["meta", "domain"]) } },
  { field_name: "current_status", type: FIELD_TYPES.singleSelect, property: { options: singleSelectOptions(["idea", "defined", "designing", "trial_running", "stable_running", "blocked", "upgrade_needed", "paused"]) } },
  { field_name: "module_goal", type: FIELD_TYPES.text },
  { field_name: "problem_to_solve", type: FIELD_TYPES.text },
  { field_name: "why_it_matters", type: FIELD_TYPES.text },
  { field_name: "related_idea_systems", type: FIELD_TYPES.text },
  { field_name: "related_lifeos_routes", type: FIELD_TYPES.text },
  { field_name: "current_blockers", type: FIELD_TYPES.text },
  { field_name: "next_action", type: FIELD_TYPES.text },
  { field_name: "acceptance_criteria", type: FIELD_TYPES.text },
  { field_name: "review_cycle", type: FIELD_TYPES.text },
  { field_name: "last_reviewed_at", type: FIELD_TYPES.dateTime, property: { date_formatter: "yyyy/MM/dd HH:mm", auto_fill: false } },
  { field_name: "source_event_ids", type: FIELD_TYPES.text },
  { field_name: "notes_md_path", type: FIELD_TYPES.text },
];

async function getTenantAccessToken() {
  const res = await fetch("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ app_id: APP_ID, app_secret: APP_SECRET }),
  });
  const data = await res.json();
  if (data.code !== 0 || !data.tenant_access_token) {
    throw new Error(`Failed to get tenant access token: ${JSON.stringify(data)}`);
  }
  return data.tenant_access_token;
}

async function listFields(token, tableId) {
  const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${APP_TOKEN}/tables/${tableId}/fields?page_size=500`;
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  const data = await res.json();
  if (data.code !== 0) {
    throw new Error(`Failed to list fields: ${JSON.stringify(data)}`);
  }
  return data.data?.items || [];
}

async function createField(token, tableId, field) {
  const url = `https://open.feishu.cn/open-apis/bitable/v1/apps/${APP_TOKEN}/tables/${tableId}/fields`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(field),
  });
  const data = await res.json();
  if (data.code !== 0) {
    throw new Error(`Create field failed for ${field.field_name}: ${JSON.stringify(data)}`);
  }
  return data.data?.field;
}

async function main() {
  const tableId = TARGET === "modules" ? MODULES_TABLE_ID : EVENTS_TABLE_ID;
  if (!tableId) {
    throw new Error(`Missing table id for target=${TARGET}`);
  }

  const plannedFields = TARGET === "modules" ? MODULE_FIELDS : EVENT_FIELDS;
  const token = await getTenantAccessToken();
  const existing = await listFields(token, tableId);
  const existingNames = new Set(existing.map((field) => field.field_name));

  console.log(`Mode: ${APPLY ? "APPLY" : "DRY_RUN"}`);
  console.log(`Target: ${TARGET} table_id=${tableId}`);

  for (const field of plannedFields) {
    const status = existingNames.has(field.field_name) ? "exists" : APPLY ? "create" : "would_create";
    console.log(`- [${status}] ${field.field_name}`);
    if (APPLY && !existingNames.has(field.field_name)) {
      await createField(token, tableId, field);
    }
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
