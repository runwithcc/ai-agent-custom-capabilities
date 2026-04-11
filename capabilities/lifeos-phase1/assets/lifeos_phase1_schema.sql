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

CREATE INDEX IF NOT EXISTS idx_lifeos_events_captured_at
    ON lifeos_events (captured_at DESC);

CREATE INDEX IF NOT EXISTS idx_lifeos_events_input_type
    ON lifeos_events (input_type);

CREATE INDEX IF NOT EXISTS idx_lifeos_events_feedback_mode
    ON lifeos_events (feedback_mode);

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

CREATE INDEX IF NOT EXISTS idx_lifeos_feedback_event_id
    ON lifeos_feedback_cards (event_id);

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

CREATE INDEX IF NOT EXISTS idx_lifeos_modules_status
    ON lifeos_modules (current_status);

CREATE INDEX IF NOT EXISTS idx_lifeos_modules_type
    ON lifeos_modules (module_type);

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

CREATE INDEX IF NOT EXISTS idx_lifeos_routes_event_id
    ON lifeos_routes (event_id);

CREATE INDEX IF NOT EXISTS idx_lifeos_routes_primary_route
    ON lifeos_routes (primary_route);

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

CREATE INDEX IF NOT EXISTS idx_lifeos_supervisions_module_id
    ON lifeos_supervisions (module_id);
