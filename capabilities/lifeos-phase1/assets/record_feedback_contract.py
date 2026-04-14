from __future__ import annotations

import re
from typing import Any, Dict, List

_EVENT_TYPE_LABELS = {
    "self_expression": "自我表达",
    "capture": "记录留存",
    "request": "带请求的表达",
}

_NEED_LABELS = {
    "rest": "休息",
    "clarity": "澄清",
    "support": "支持",
    "capture": "记录",
    "ritual": "纪念",
    "action": "行动",
    "expression": "表达",
    "organization": "整理",
    "feedback": "反馈",
    "help": "求助",
    "guidance": "建议",
    "decision": "判断",
}


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = "，".join(str(item).strip() for item in value if str(item).strip())
    return re.sub(r"\s+", " ", str(value)).strip()


def split_tag_text(value: Any) -> List[str]:
    text = normalize_text(value)
    if not text:
        return []
    parts = [item.strip() for item in re.split(r"\s*[,，]\s*", text) if item.strip()]
    return unique_list(parts)


def unique_list(values: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def extract_first_sentence(raw_text: str, limit: int = 72) -> str:
    if not raw_text:
        return ""
    parts = [segment.strip() for segment in re.split(r"[。！？!?；;\n]+", raw_text) if segment.strip()]
    summary = parts[0] if parts else raw_text
    return summary if len(summary) <= limit else summary[: limit - 1] + "…"


def _is_agent_runtime_discussion(raw_text: str) -> bool:
    raw_text = normalize_text(raw_text)
    if not raw_text:
        return False
    assistant_markers = r"codex|openclaw|hermes|claude ?code|chatgpt|atlas|bot|agent|机器人"
    runtime_markers = r"代码层|源码|提示词|llm|架构|schema|字段名|路由|服务器|部署|模块|工作流|流程|步骤|插件|github|repo|版本管理|同步到 ?github|文档留存|专门的文件夹|功能|调试|测试|验收|卡片|入库|反馈"
    if re.search(assistant_markers, raw_text, re.IGNORECASE) and re.search(runtime_markers, raw_text, re.IGNORECASE):
        return True
    if re.search(assistant_markers, raw_text, re.IGNORECASE):
        if re.search(r"读书|阅读|学习|记录我的想法|项目负责人|背景信息|阶段的重点|怎么做|每天准备怎么调整|辅助我进行阅读", raw_text):
            return False
    return False


def is_agent_strategy_note(event: dict) -> bool:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    topic_tags = split_tag_text(event.get("topic_tags"))
    return (
        any(tag in topic_tags for tag in ("Agent协作", "系统", "架构"))
        and _is_agent_runtime_discussion(raw_text)
    ) or _is_agent_runtime_discussion(raw_text)


def detect_agent_strategy_subtype(event: dict) -> str:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    if not is_agent_strategy_note(event):
        return ""
    if is_feature_debug_note(event):
        return "feature_debug"
    asset_score = sum(
        1
        for pattern in (
            r"文档留存",
            r"专门的文件夹",
            r"版本管理",
            r"同步到 ?github",
            r"新的 agent",
            r"可移动走",
        )
        if re.search(pattern, raw_text, re.IGNORECASE)
    )
    workflow_score = sum(
        1
        for pattern in (
            r"形成了一个逻辑",
            r"①|②|③|④|⑤|⑥",
            r"步骤",
            r"流程",
            r"逻辑过程",
            r"落到 agent",
        )
        if re.search(pattern, raw_text)
    )
    if asset_score >= 2:
        return "assetization"
    if workflow_score >= 2:
        return "workflow_sop"
    if re.search(r"github|repo|git|版本管理|文档留存|专门的文件夹|同步到 ?github|可移动走|新的 agent", raw_text, re.IGNORECASE):
        return "assetization"
    if re.search(r"atlas|浏览器|手机|mac|waylog|插件|文章|复利|接着 .*codex|接着 mac 上的 codex", raw_text, re.IGNORECASE):
        return "mobile_handoff"
    return "runtime_strategy"


def is_family_milestone_note(event: dict) -> bool:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    topic_tags = split_tag_text(event.get("topic_tags"))
    return bool(re.search(r"生日|周岁", raw_text)) and any(tag in topic_tags for tag in ("家庭", "孩子"))


def is_family_daily_moment(event: dict) -> bool:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    topic_tags = split_tag_text(event.get("topic_tags"))
    return bool(re.search(r"长寿面|第[二三四]碗|锅里做了好多|盛了一份", raw_text)) and any(
        tag in topic_tags for tag in ("家庭", "日常片段", "关系")
    )


def is_family_daily_joy_note(event: dict) -> bool:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    topic_tags = split_tag_text(event.get("topic_tags"))
    return bool(
        re.search(
            r"接孩子放学|放学|小狗狗|狗狗|蹦蹦跳跳|朝我奔跑过来|朝我跑过来|像小鸟一样|书包都没有背|作业都完成了",
            raw_text,
        )
    ) and any(tag in topic_tags for tag in ("家庭", "孩子", "宠物", "日常片段", "关系"))


def is_collaborative_method_note(event: dict) -> bool:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    topic_tags = split_tag_text(event.get("topic_tags"))
    return bool(
        re.search(r"共同学习|相互学习|做时学|学习方案|彼此在尝试着一些新方法|大家都可以相互学习|模式实在是太好了|有非常有价值的事情", raw_text)
    ) or (
        "学习" in topic_tags
        and bool(re.search(r"方法|模式|方案|启发|价值", raw_text))
    )


def is_stability_leadership_note(event: dict) -> bool:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    topic_tags = split_tag_text(event.get("topic_tags"))
    return bool(
        re.search(
            r"冥想|回到自己稳定的状态|把自己稳定住再去|更注重自己状态的稳定|先稳住自己|稳定住再去和大家交流|状态的稳定",
            raw_text,
        )
    ) or any(tag in topic_tags for tag in ("人物观察", "稳定机制", "领导方式"))


def is_learning_workflow_note(event: dict) -> bool:
    if is_collaborative_method_note(event):
        return False
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    topic_tags = split_tag_text(event.get("topic_tags"))
    return bool(
        re.search(r"读书|阅读|《好好思考》|记录我的想法|辅助我进行阅读|从开始阅读就发一条消息|不断地发消息|把背景信息同步给机器人|项目负责人", raw_text)
    ) or (
        "学习" in topic_tags
        and bool(re.search(r"阅读|读书|方法|思路|试试看", raw_text))
    )


def _translate_intensity(value: str) -> str:
    return {"low": "低", "medium": "中", "high": "高"}.get(value, value or "中")


def _display_needs(values: List[str]) -> str:
    if not values:
        return "留存"
    return "、".join(_NEED_LABELS.get(value, value) for value in values[:3])


def infer_emotion_words(event: dict) -> List[str]:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    emotion_tags = split_tag_text(event.get("emotion_tags"))
    emotions: List[str] = []
    if re.search(r"很幸福", raw_text):
        emotions.append("幸福")
    if re.search(r"200 多种 bug|调了四天|用了将近四天", raw_text):
        emotions.extend(["吃力", "投入"])
    if re.search(r"很喜欢", raw_text):
        emotions.append("喜欢")
    if re.search(r"试试看|看看效果|想试|尝试一次|希望", raw_text):
        emotions.append("期待")
    if re.search(r"充满期待|期待啊|这会给我带来什么", raw_text):
        emotions.extend(["期待", "兴奋"])
    if re.search(r"不会那么理想|不可能那么清楚|还没有调试|先试试看|先看看", raw_text):
        emotions.append("审慎")
    if re.search(r"终于|太好了|wow|非常开心|超级好|飞起来", raw_text, re.IGNORECASE):
        emotions.extend(["兴奋", "满足"])
    if re.search(r"担心|害怕|焦虑|不安", raw_text):
        emotions.extend(["担心", "不安"])
    if re.search(r"清楚了|想明白了|形成了一个逻辑|笃定", raw_text):
        emotions.append("笃定")
    if re.search(r"主 Agent|已经成为我的主 Agent", raw_text):
        emotions.extend(["笃定", "成型感"])
    if re.search(r"抱着 codex 睡", raw_text):
        emotions.append("投入")
    if re.search(r"温暖|幸福|爱", raw_text):
        emotions.append("温暖")
    emotions.extend(emotion_tags)
    return unique_list(emotions)[:3] or ["平静"]


def infer_hawkins_level(event: dict) -> str:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    scene_type = normalize_text(event.get("scene_type"))
    if is_agent_stage_recap_note(event):
        return "理性（400）"
    if re.search(r"爱|温暖|孩子|幸福", raw_text):
        return "爱（500）"
    if re.search(r"主 Agent|已经成为我的主 Agent|当前正在开发中", raw_text):
        return "理性（400）"
    if re.search(r"充满期待|期待啊|很喜欢|想试试看|会给我带来什么", raw_text):
        return "意愿（310）"
    if re.search(r"调试|测试|验收|判断|分析|字段名|schema|逻辑|流程|试试看|不会那么理想|不可能那么清楚", raw_text):
        return "理性（400）"
    if re.search(r"终于|太好了|wow|超级好|非常开心|很想", raw_text, re.IGNORECASE):
        return "意愿（310）"
    if re.search(r"担心|焦虑|害怕|不安", raw_text):
        return "勇气（200）"
    if scene_type in {"情绪", "触动"}:
        return "中性（250）"
    return "中性（250）"


def infer_feature_focus(event: dict) -> str:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    if re.search(r"卡片.*入库|入库.*卡片|卡片.*反馈|反馈.*卡片", raw_text):
        return "卡片反馈功能"
    if re.search(r"入库功能|记录入库|反馈功能", raw_text):
        return "记录入库功能"
    if re.search(r"工作流|流程", raw_text):
        return "协作工作流"
    return "系统功能"


def is_feature_debug_note(event: dict) -> bool:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    return bool(
        re.search(r"卡片|入库|反馈功能|调试|测试|试试看|看看效果|不会那么理想|还没有调试|验收", raw_text)
        and re.search(r"codex|hermes|chatgpt|agent", raw_text, re.IGNORECASE)
    )


def is_agent_stage_recap_note(event: dict) -> bool:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    has_stage_chain = bool(
        re.search(r"第一阶段", raw_text)
        and re.search(r"第二阶段", raw_text)
        and re.search(r"当前阶段", raw_text)
    )
    has_agent_context = bool(re.search(r"hermes|oc|cc|api|agent|bug|重新安装|文件夹", raw_text, re.IGNORECASE))
    return has_stage_chain and has_agent_context


def is_multi_machine_agent_trial_note(event: dict) -> bool:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    return bool(
        re.search(r"MPBM1|mba|macbook", raw_text, re.IGNORECASE)
        and re.search(r"龙虾|安装龙虾|跑龙虾", raw_text)
        and re.search(r"办公楼|办公团队|试试看|会给我带来什么|充满期待", raw_text)
    )


def _header_template(event: dict) -> str:
    if is_agent_stage_recap_note(event):
        return "green"
    if is_multi_machine_agent_trial_note(event):
        return "green"
    if detect_agent_strategy_subtype(event) == "feature_debug":
        return "orange"
    if is_agent_strategy_note(event):
        return "green"
    if is_stability_leadership_note(event):
        return "green"
    if is_family_daily_joy_note(event):
        return "green"
    if is_learning_workflow_note(event):
        return "green"
    if is_collaborative_method_note(event):
        return "green"
    if is_family_milestone_note(event):
        return "red"
    if is_family_daily_moment(event):
        return "green"
    dailynote = event.get("dailynote_sync")
    if isinstance(dailynote, dict) and dailynote.get("success"):
        return "green"
    if isinstance(dailynote, dict) and dailynote.get("fallback_to_openclaw"):
        return "orange"
    if isinstance(dailynote, dict) and dailynote.get("skipped"):
        return "blue"
    return "wathet"


def _ensure_question_prefix(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return "Q: 这条内容里最值得被看见的核心到底是什么？"
    if text.startswith("Q:"):
        return text
    return f"Q: {text}"


def strip_question_prefix(text: str) -> str:
    text = normalize_text(text)
    return re.sub(r"^Q:\s*", "", text)


def _header_copy(event: dict) -> tuple[str, str]:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    scene_type = normalize_text(event.get("scene_type")) or "记录"
    first = extract_first_sentence(raw_text, limit=28)
    dailynote = event.get("dailynote_sync")
    agent_subtype = detect_agent_strategy_subtype(event)

    if is_agent_stage_recap_note(event):
        return (
            "从 4 月 3 日开始连打四场硬仗，Hermes 已经成为我的主 Agent",
            _ensure_question_prefix("这轮从安装、隔离污染、修 API 到信息处理机制开发，你真正走通了什么？"),
        )
    if is_multi_machine_agent_trial_note(event):
        return (
            "受“办公楼-办公团队”隐喻触发，开始给第二台 MPBM1 试跑龙虾",
            _ensure_question_prefix("这次给第二台 MPBM1 装龙虾，你真正想验证的是什么？"),
        )
    if agent_subtype == "feature_debug":
        focus = infer_feature_focus(event)
        return (
            f"连续调试{focus}，当前初期阶段预期不会很高",
            _ensure_question_prefix(f"当前{focus}调试处于什么阶段？"),
        )
    if agent_subtype == "assetization":
        return (
            "把开发过程沉淀进专属文件夹，并开始用 GitHub 做版本托管",
            _ensure_question_prefix("这次系统建设真正往前推进到了哪里？"),
        )
    if agent_subtype == "mobile_handoff":
        return (
            "手机端表达接到 Codex 执行，开始形成跨设备推进链路",
            _ensure_question_prefix("这次跨设备协作真正打通了哪一段链路？"),
        )
    if agent_subtype == "workflow_sop":
        return (
            "AI 协作六步流程已经成型，开始进入可重复执行阶段",
            _ensure_question_prefix("当前 Agent 协作流程已经被你压缩成什么样的 SOP？"),
        )
    if agent_subtype == "runtime_strategy":
        return (
            "绕开反复调 bot，直接下到 agent / 代码层做稳定实现",
            _ensure_question_prefix("为什么这次你会判断应该直达 agent 或代码层？"),
        )
    if is_stability_leadership_note(event):
        return (
            "💡 真正成熟的推进者，会先稳住自己，再去处理复杂事情",
            _ensure_question_prefix("为什么有些人事情很多、变化很多，却仍然能把状态和事情一起做稳？"),
        )
    if is_learning_workflow_note(event):
        return (
            "💡 把阅读过程交给 AI 持续接住，理解就能边读边积累",
            _ensure_question_prefix("怎样才能让阅读不是读完就散，而是一路读一路长出理解？"),
        )
    if is_collaborative_method_note(event):
        return (
            "💡 团队真正被激活，是因为方法开始在协作里流动",
            _ensure_question_prefix("为什么有些团队会越做越会学，而且越学越能打？"),
        )
    if is_family_milestone_note(event):
        return (
            "💛 真正值得留下来的，是这一天你最想对孩子说的话",
            _ensure_question_prefix("孩子来到 10 岁这个节点，什么才是很多年后还会留下力量的礼物？"),
        )
    if is_family_daily_joy_note(event):
        return (
            "🏡 真正值得留下来的，是孩子朝你奔跑过来的那一刻",
            _ensure_question_prefix("为什么有些再普通不过的放学路上，会一下子把一家人的幸福感点亮？"),
        )
    if is_family_daily_moment(event):
        return (
            "🍜 真正让人舍不得忘的，是被家里接住的那个早晨",
            _ensure_question_prefix("为什么一个看起来普通的早晨，会在心里留下那么深的画面感？"),
        )

    if isinstance(dailynote, dict) and dailynote.get("success"):
        if scene_type == "启发":
            return (
                "💡 这条内容真正留下来的，是一条可复用的方法",
                _ensure_question_prefix("这次经历里，最值得被沉淀下来继续复用的方法是什么？"),
            )
        if scene_type == "复盘":
            return (
                "🧭 真正该留下来的，不是结果，而是下次还能继续用的方法",
                _ensure_question_prefix("这次经历过去之后，什么才是最值得下次继续带走的？"),
            )
        if scene_type == "情绪":
            return (
                "💬 这份感受真正想提醒你的，是那个还没被说透的核心",
                _ensure_question_prefix("这份感受背后，真正想被你看见的到底是什么？"),
            )
        return (
            "📝 真正值得留下来的，不只是信息，而是这条记录背后的意义",
            _ensure_question_prefix("这条记录里，最值得你以后反复回看的核心是什么？"),
        )
    if isinstance(dailynote, dict) and dailynote.get("fallback_to_openclaw"):
        return ("📥 这条内容已经先被接住了", _ensure_question_prefix("这条内容后续最值得展开的一层是什么？"))
    if isinstance(dailynote, dict) and dailynote.get("skipped"):
        return ("🗂️ 这条内容已经先被记下了", _ensure_question_prefix("这条内容里最该被继续展开的点是什么？"))

    if scene_type == "启发":
        return (
            "💡 这条启发真正重要的，是它已经在长成一条方法",
            _ensure_question_prefix(
                f"这段经历里，什么值得从灵光一闪变成稳定可用的方法？{'' if not first else f' {first}'}"
            ),
        )
    if scene_type == "情绪":
        return (
            "💬 这份感受真正重要的，是它在替你指出一个更深的需要",
            _ensure_question_prefix(
                f"这份感受背后，真正想被接住的是什么？{'' if not first else f' {first}'}"
            ),
        )
    if scene_type == "复盘":
        return (
            "🧭 这次复盘真正有价值的，是它在帮你沉淀下一次会更稳的方法",
            _ensure_question_prefix(
                f"这次经历过后，什么才是最值得被带走的？{'' if not first else f' {first}'}"
            ),
        )
    return (
        "📝 这条记录真正有价值的，是它在帮你留下一个以后还能继续用的抓手",
        _ensure_question_prefix(
            f"这条记录里，什么才是最值得你以后回看的？{'' if not first else f' {first}'}"
        ),
    )


def _human_tags(event: dict) -> List[str]:
    if is_agent_stage_recap_note(event):
        return ["阶段复盘", "主Agent", "系统建设"]
    if is_multi_machine_agent_trial_note(event):
        return ["多机实验", "龙虾部署", "系统隐喻"]
    agent_subtype = detect_agent_strategy_subtype(event)
    if agent_subtype == "feature_debug":
        focus = infer_feature_focus(event)
        return [focus, "早期验证", "反馈调试"]
    if agent_subtype == "assetization":
        return ["能力资产化", "版本管理", "系统建设"]
    if agent_subtype == "mobile_handoff":
        return ["移动接力", "工作流", "内容复利"]
    if agent_subtype == "workflow_sop":
        return ["Agent协作", "SOP", "推进链路"]
    if agent_subtype == "runtime_strategy":
        return ["Agent协作", "稳定机制", "操作方案"]
    if is_stability_leadership_note(event):
        return ["人物观察", "稳定机制", "领导方式"]
    if is_learning_workflow_note(event):
        return ["阅读方法", "AI辅助", "学习流程"]
    if is_collaborative_method_note(event):
        return ["启发", "共同学习", "方法模式"]
    if is_family_milestone_note(event):
        return ["家庭纪念", "成长节点", "爱"]
    if is_family_daily_joy_note(event):
        return ["家庭日常", "孩子", "幸福片段"]
    if is_family_daily_moment(event):
        return ["家庭日常", "被照顾", "烟火气"]
    scene_type = normalize_text(event.get("scene_type"))
    topic_tags = split_tag_text(event.get("topic_tags"))
    emotion_tags = split_tag_text(event.get("emotion_tags"))
    candidates = topic_tags[:2] + emotion_tags[:1]
    if scene_type and scene_type not in candidates and scene_type != "记录":
        candidates.insert(0, scene_type)
    return unique_list(candidates)[:3]


def _judgement_items(event: dict) -> List[str]:
    event_type = normalize_text(event.get("event_type"))
    scene_type = normalize_text(event.get("scene_type")) or "记录"
    emotion_tags = split_tag_text(event.get("emotion_tags"))
    state_tags = split_tag_text(event.get("state_tags"))
    needs = split_tag_text(event.get("needs"))
    intensity = _translate_intensity(normalize_text(event.get("intensity")).lower())
    agent_subtype = detect_agent_strategy_subtype(event)
    emotion_text = "、".join(infer_emotion_words(event))
    hawkins_level = infer_hawkins_level(event)

    if is_agent_stage_recap_note(event):
        return [
            "表达类型：阶段复盘 / 主 Agent 成型里程碑",
            f"情绪判断：{emotion_text}",
            f"当前能量：{hawkins_level}",
            "当前状态：你正在回看 Hermes 从安装到成型的几场关键硬仗，并确认它已经坐上主 Agent 的位置。",
            "你此刻更需要的：沉淀阶段路线、固定规则、继续模块化开发",
        ]
    if is_multi_machine_agent_trial_note(event):
        return [
            "表达类型：系统试验 / 多机部署启发",
            f"情绪判断：{emotion_text}",
            f"当前能量：{hawkins_level}",
            "当前状态：被“办公楼-办公团队”的组织化隐喻点燃，准备把它变成自己的真实试跑。",
            "你此刻更需要的：试跑、观察、记录变化",
        ]
    if agent_subtype == "feature_debug":
        return [
            "表达类型：功能调试 / 早期验收",
            f"情绪判断：{emotion_text}",
            f"当前能量：{hawkins_level}",
            "当前状态：在低预期前提下，主动做一轮真实测试，想看系统现在到底长成什么样",
            "你此刻更需要的：验收、补字段、继续调试",
        ]
    if agent_subtype == "assetization":
        return [
            "表达类型：系统建设 / 能力资产化",
            f"情绪判断：{emotion_text}",
            f"当前能量：{hawkins_level}",
            "当前状态：在把一次开发过程升级成可迁移、可管理的长期资产",
            "你此刻最在意的：留存、版本管理、未来接力",
        ]
    if agent_subtype == "mobile_handoff":
        return [
            "表达类型：工作流启发 / 协作设计",
            f"情绪判断：{emotion_text}",
            f"当前能量：{hawkins_level}",
            "当前状态：在打通手机端表达、浏览器分析和代码执行之间的接力",
            "你此刻最在意的：连续推进、低摩擦、内容复利",
        ]
    if agent_subtype == "workflow_sop":
        return [
            "表达类型：流程沉淀 / 方法确认",
            f"情绪判断：{emotion_text}",
            f"当前能量：{hawkins_level}",
            "当前状态：已经把一套 AI 协作方法从感觉变成可执行步骤",
            "你此刻最在意的：顺滑推进、稳定复现、直接出功能",
        ]
    if agent_subtype == "runtime_strategy":
        return [
            "表达类型：方法沉淀 / 架构判断",
            f"情绪判断：{emotion_text}",
            f"当前能量：{hawkins_level}",
            "当前状态：在把一次经验升级成可复用的方法",
            "你此刻最在意的：稳定性、可复用性、可传递性",
        ]
    if is_stability_leadership_note(event):
        return [
            "表达类型：人物观察 / 方法启发",
            "情绪判断：理解、欣赏",
            "当前能量：高",
            "当前状态：从观察一个人，提炼出一种更成熟的做事方式",
            "你此刻更需要的：整理、沉淀",
        ]
    if is_family_daily_joy_note(event):
        return [
            "表达类型：生活片段 / 触动",
            "情绪判断：开心、温暖",
            "当前能量：中高",
            "当前状态：被一个很有画面感的家庭瞬间打动",
            "你此刻更需要的：记录、留存",
        ]
    if is_learning_workflow_note(event):
        return [
            "表达类型：自我表达 / 启发",
            "情绪判断：轻松、振奋",
            "当前能量：中高",
            "当前状态：从困惑走向了一个可尝试的新方法",
            "你此刻更需要的：行动、整理",
        ]
    if is_collaborative_method_note(event):
        return [
            "表达类型：自我表达 / 启发",
            "情绪判断：振奋",
            "当前能量：高",
            "当前状态：在看见一种可以放大的学习模式",
            "你此刻更需要的：记录、整理",
        ]

    emotion_text = "、".join(infer_emotion_words(event))
    state_text = "、".join(state_tags[:3]) if state_tags else scene_type
    need_text = _display_needs(needs)
    type_text = _EVENT_TYPE_LABELS.get(event_type, "自我表达")
    return [
        f"表达类型：{type_text} / {scene_type}",
        f"情绪判断：{emotion_text}",
        f"当前能量：{infer_hawkins_level(event)}",
        f"当前状态：{state_text}",
        f"你此刻更需要的：{need_text}",
    ]


def _content_items(event: dict) -> List[str]:
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    return [raw_text] if raw_text else ["这条原始记录为空。"]


def _takeaway_items(event: dict) -> List[str]:
    if is_agent_stage_recap_note(event):
        return [
            "这条真正该留下来的，不是一句感悟，而是一条很清楚的成型路径：装好后的幸福、目录污染后的重装、API 空值排查、重新整顿理解，最后走到信息处理机制开发。",
            "你经历的不是普通调试，而是一段高代价的系统建设过程：将近 200 多种 bug、前后接近 8 天的排查与调整，才把 Hermes 推到可承担主 Agent 的位置。",
            "当前最关键的结果是：Hermes 已经不只是工具，而是开始成为那个理解你、承接你、帮助你处理大量感受与信息流的总控核心。",
        ]
    if is_multi_machine_agent_trial_note(event):
        return [
            "你真正想试的，不只是再装一台机器，而是想验证多台设备一起跑起来后，是否会带来更强的组织感、并行感和生产力想象。",
            "这条里最打动你的，不是“10 台 mba”这个数字本身，而是“每一台都是一个办公楼，里面住着一支办公团队”这个系统隐喻。",
            "你已经开始把外部看到的一个强隐喻，转成自己的多机 agent 实验样本了。",
        ]
    agent_subtype = detect_agent_strategy_subtype(event)
    if agent_subtype == "feature_debug":
        return [
            "你现在不是在追求一步到位，而是在承认维度还没调齐的前提下，先做一轮真实验收。",
            "这条里真正形成的判断是：卡片反馈功能已经到了可以开始试的阶段，但你对当前效果的预期仍然很克制。",
            "你不是在单纯试功能，而是在用一次真实输入，倒逼 event schema 和反馈层继续往贴近你自己的方向迭代。",
        ]
    if agent_subtype == "assetization":
        return [
            "你不只是在开发功能，而是在把整个开发过程、能力文件和说明沉淀成一个可迁移的能力资产层。",
            "这条最关键的不是“又做了一个功能”，而是你要求文档、脚本、流程、GitHub 仓库和 Hermes 内文件夹全部对齐了。",
            "一旦这层资产化做稳，未来即便换主 Agent，你也不会失去已经沉淀下来的系统能力。",
        ]
    if agent_subtype == "mobile_handoff":
        return [
            "你真正抓到的亮点，不是 Atlas 或 Codex 单独多强，而是它们开始形成跨设备接力的工作流了。",
            "这条里很有价值的一层，是浏览器侧理解问题、代码侧落实功能、内容侧继续复利这三步开始串起来了。",
            "你已经不只是在找工具，而是在找一条能让表达、执行和产出连续流动的协作链。",
        ]
    if agent_subtype == "workflow_sop":
        return [
            "你已经把自己的 Agent 协作方式压缩成了一条很清晰的执行流程：有感就发、让 ChatGPT 理解、让 Codex 落地、再回到 GitHub 和 agent 上验证。",
            "这条最有价值的地方，不只是步骤清晰，而是你把“自己负责真实表达，Agent 负责理解和执行”分工得越来越稳定了。",
            "这其实已经是一条可复用的个人 AI 协作 SOP，而不只是当下的一次顺手操作。",
        ]
    if agent_subtype == "runtime_strategy":
        return [
            "真正高效的做法，不是隔着 bot 反复调，而是直接去动 agent 或代码层。",
            "如果目标是稳定发生，只靠提示词和 LLM 不够，最好落到程序、结构或源码层。",
            "Codex / cc 这类直接接管 Hermes 运行层的方式，更适合做这类底层操作。",
        ]
    if is_stability_leadership_note(event):
        return [
            "你真正看到的，不是潘总事情很多，而是他会主动把自己调回稳定，再去交流、碰撞和处理事务。",
            "这不是一个人的临场反应，而是一种很成熟的状态管理方式：先稳自己，再做事，再对外互动。",
            "你后面想把谈话整理给 AI 再返还给他，本质上也是在帮这种稳定机制继续发挥作用。",
        ]
    if is_family_daily_joy_note(event):
        return [
            "你真正想留下来的，不只是“接孩子放学”这件事，而是那个小狗也在、孩子也在、整个人朝你奔跑过来的完整幸福感。",
            "这条最有力量的地方，是它特别有画面感：像小鸟一样跑过来，这一幕会让你以后回看时一下子回到当时。",
            "后面你去加满油、一起回家，也让这条记录有了一种很完整的生活感和被照顾好的节奏。",
        ]
    if is_learning_workflow_note(event):
        return [
            "你真正抓到的，不只是“怎么读书”，而是“怎么把阅读过程变成一个持续被接住的流程”。",
            "这条方法的关键，不是读完再总结，而是从开始阅读就持续记录、持续整理。",
            "AI 在这里不是主角，而是一个能陪你边读边记、边读边整理的辅助结构。",
        ]
    if is_collaborative_method_note(event):
        return [
            "这不只是记录一个事例，你已经从里面提炼出了一条后续可以继续使用的方法。",
            "真正有价值的，不是某个人单独做得好，而是大家在真实推进中可以互相学习、互相借力。",
            "你看到的是一种“做时学”的模式，它会让方法在团队里扩散得更快。",
        ]
    if is_family_milestone_note(event):
        return [
            "这不只是生日记录，而是你在面对孩子成长节点时的爱、满足和一点不知所措。",
            "你真正想留下来的，不只是“今天送什么”，而是“我想对他说什么”。",
            "写信本身已经很接近这条里最好的礼物了。",
        ]
    if is_family_daily_moment(event):
        return [
            "你真正想留下来的不是“三碗面”这个事实，而是那个被家里接住的早晨。",
            "这条里有一种自然的被照顾感，也有一点生活里的好笑。",
            "它值得被记住，是因为它很有烟火气，也很有你们家的味道。",
        ]
    instant_feedback = normalize_text(event.get("instant_feedback"))
    if instant_feedback:
        return [instant_feedback]
    return ["这条里有值得留存的一层，我已经先替你接住了。"]


def _value_items(event: dict) -> List[str]:
    if is_agent_stage_recap_note(event):
        return [
            "这条对你重要，不是因为它总结出了一条抽象方法，而是因为它记录了 Hermes 作为主 Agent 真正成型的阶段证据。",
            "它和你的关系很深，因为你不是在玩工具，而是在用高强度排障和系统整顿，把一个 agent 调成可以进入你 LifeOS 主干的位置。",
        ]
    if is_multi_machine_agent_trial_note(event):
        return [
            "这条对你重要，是因为它把一个外部隐喻转成了你的系统实验：你想看多机运行会不会让助手体系从单点协作走向组织化协作。",
            "它和你的关系很近，因为你天然偏爱稳定运转的系统，而这次试跑正好在验证“更多机器、更多分工、更多并行”会不会更接近你要的那种帅气秩序感。",
        ]
    agent_subtype = detect_agent_strategy_subtype(event)
    if agent_subtype == "feature_debug":
        return [
            "这条对你重要，不只是因为你在测试功能，而是因为你已经从设计讨论跨进了真实验收阶段。",
            "它和你当前的 Hermes / LifeOS 建设直接相关，因为每一次真实测试，都会反向暴露标题系统、反馈层、字段层和路由层哪里还不够像你。",
        ]
    if agent_subtype == "assetization":
        return [
            "这条真正重要的地方，是你把“开发完成”往前推了一层，变成了“能力被收纳、被管理、被版本化、能被新 agent 接力”。",
            "它有价值，因为这意味着你在搭的不是一次性功能，而是能随着 LifeOS 一起长期复利的能力底座。",
        ]
    if agent_subtype == "mobile_handoff":
        return [
            "这条真正重要的地方，是你在寻找一种低摩擦、高连续性的推进方式，而不是再多装一个工具。",
            "它有价值，因为一旦手机端、浏览器端和代码端之间开始无缝接力，你的真实表达就更容易直接变成功能和内容资产。",
        ]
    if agent_subtype == "workflow_sop":
        return [
            "这条真正重要的地方，是你已经开始把自己的 AI 协作方式做成标准流程，而不是每次临时即兴。",
            "它有价值，因为一旦这条 SOP 稳下来，你的人生表达、系统建设和功能实现之间就会越来越短路由。",
        ]
    if agent_subtype == "runtime_strategy":
        return [
            "你真正主张的核心价值点，是“稳定性来自结构和代码层，而不是来自反复沟通”。",
            "这有价值，因为它把一次临场经验升级成了一条可复用的方法，后面无论是协作、实现还是教学，都能直接拿来用。",
        ]
    if is_stability_leadership_note(event):
        return [
            "你真正看见的核心价值点，是一个人能不能把自己先稳住，决定了他后面交流、判断和推进事情的质量。",
            "这有价值，因为它不是一句泛泛的感受，而是一条能直接迁移到管理、协作和日常工作的稳定机制。",
        ]
    if is_family_daily_joy_note(event):
        return [
            "这条真正重要的地方，不只是放学接回来了，而是你把一个家庭阶段里很鲜活的幸福感留住了。",
            "这有价值，因为以后你回看时，记起的不只是事情，而是孩子朝你跑来时那种轻快、明亮和安心。",
        ]
    if is_learning_workflow_note(event):
        return [
            "你真正看见的核心，不是一本书怎么读完，而是怎样让阅读过程本身变成一个不断生成理解的系统。",
            "这有价值，因为它把原本容易中断、容易遗忘的阅读，变成了一个可以持续积累、持续沉淀的方法。",
        ]
    if is_collaborative_method_note(event):
        return [
            "你真正主张的核心价值点，不只是发生了什么，而是团队在真实工作里可以边做边学、彼此带动。",
            "这有价值，因为它已经不只是信息，而是一种能够帮助团队后续判断、回看或继续展开的抓手。",
        ]
    if is_family_milestone_note(event):
        return [
            "你主张的核心价值点，不是把节点过得多完整，而是把爱、纪念感和你真正想说的话留下来。",
            "这有价值，因为很多年后真正能留下力量的，往往不是流程，而是当时你怎样认真地爱过、看见过。",
        ]
    if is_family_daily_moment(event):
        return [
            "你主张的核心价值点，是日常里那些微小但真实的被照顾感，本身就值得被记住。",
            "这有价值，因为回头看时，往往不是大事件，而是这些细碎片段最能把一个阶段的幸福感重新带回来。",
        ]
    return [
        "这条真正重要的地方，不只是发生了什么，而是你为什么会觉得它值得留住。",
        "它的价值在于，它已经不只是信息，而是一个能帮助你后续判断、回看或继续展开的抓手。",
    ]


def _action_items(event: dict) -> List[str]:
    if is_agent_stage_recap_note(event):
        return [
            "把这五个阶段整理成一张“Hermes 主 Agent 成型路线图”，每一阶段写清问题、代价、关键判断和最终产出。",
            "把“目录隔离防污染”和“API 返回空值排查”各沉淀成一份 SOP，后面遇到类似问题时直接复用。",
            "把“信息处理机制”正式定义成 LifeOS 模块，写清输入、理解、反馈、存储和路由五个环节。",
        ]
    if is_multi_machine_agent_trial_note(event):
        return [
            "把这台 MPBM1 标成“多机龙虾实验样本 002”，写清它准备承担什么角色、常驻什么任务、想观察什么变化。",
            "为这轮试跑设 3 个观察指标：并行感有没有增强、组织感有没有变强、你自己的期待感会不会落到真实生产力上。",
            "等它跑起来后，补一条简短复盘：这台机器更像“办公楼”，还是更像“多开了一个窗口”？",
        ]
    agent_subtype = detect_agent_strategy_subtype(event)
    if agent_subtype == "feature_debug":
        return [
            "把这次返回按标题记忆度、问答配对度、内容贴身度、人我关系度、结构解释度、行动开发感 6 个维度逐项打分。",
            "把最明显失真的地方标出来，优先改标题系统、情绪判断和下一步建议这三层。",
            "把这条样本保留为“卡片反馈调试样本 001”，后面继续作为回归用例反复验证。",
        ]
    if agent_subtype == "assetization":
        return [
            "把“文档留存 + 专属文件夹 + Git 管理 + GitHub 发布 + Hermes 同步”沉淀成固定发布规范。",
            "给这个能力资产层补一份 onboarding 说明，让新的 agent 一进来就能读懂并接手。",
            "后面每做出一个功能，都按同一模板补齐：设计说明、脚本、部署方式、验证方法。",
        ]
    if agent_subtype == "mobile_handoff":
        return [
            "把“手机表达 -> Atlas/ChatGPT 整理 -> Codex 落地 -> 内容复利”画成一条标准工作流。",
            "先挑一个最值得复利的产出类型试跑，例如把一次开发对话自动沉淀成文章或方法卡。",
            "把浏览器端和代码端各自负责什么定清楚，这条接力链会更顺。",
        ]
    if agent_subtype == "workflow_sop":
        return [
            "把你刚形成的六步逻辑整理成一张 SOP 卡，后面每次推进都按同一条链路跑。",
            "顺手给每一步标注负责主体：你负责真实表达，ChatGPT 负责理解，Codex 负责落地，GitHub 负责版本管理，agent 负责验收。",
            "后面再补一条异常处理规则：中间哪一步卡住了，应该回到哪里继续推进。",
        ]
    if agent_subtype == "runtime_strategy":
        return [
            "把这条沉淀成一条固定原则：不要隔着 bot 反复说，优先直达 agent 或代码层。",
            "顺手画出一条最小操作链路，例如“需求 -> Codex -> Hermes 代码层 -> 生效”。",
            "把“提示词不保证稳定，程序和代码层更稳定”写成系统约束，后面很多判断会更快。",
        ]
    if is_stability_leadership_note(event):
        return [
            "把这条沉淀成一张方法卡：先稳自己 -> 再处理事务 -> 再进入交流和碰撞。",
            "提炼他是怎么把自己调回稳定的，比如冥想、停顿、回收注意力，这些都可以拆成具体动作。",
            "把“聊完 -> AI 整理 -> 返还给对方”这条链路固定下来，后面这类高价值对话会更容易沉淀和复用。",
        ]
    if is_family_daily_joy_note(event):
        return [
            "给这条留一个有画面感的小标题，让你以后看到标题就能立刻回到那个场景里。",
            "顺手补一句“我为什么这么想把这一幕记下来”，这样以后回看时会更有力量。",
            "把这类孩子、宠物、回家路上的幸福片段继续积累下去，它们会慢慢变成你很珍贵的一组家庭样本。",
        ]
    if is_learning_workflow_note(event):
        return [
            "先用一本书或一个主题试跑这套方法，不追求大而全，只验证它是不是真的能帮你持续读下去。",
            "把“边读边记”的最小流程固定下来，例如：阅读 -> 发一条消息 -> AI 帮你留存 -> 继续推进。",
            "等你跑顺以后，再补一份自己的阅读模板，后面会更省力。",
        ]
    if is_collaborative_method_note(event):
        return [
            "把这段内容拆成 2 到 3 个关键点，后面复用或回看都会更轻松。",
            "如果愿意，可以顺着这条再往下追问一层，把真正最重要的点继续挖出来。",
            "把“做时学”整理成一条可传播的方法说明，后面团队更容易复用。",
        ]
    if is_family_milestone_note(event):
        return [
            "先把那封信写出来，不求完整，只写你最想对孩子说的 3 句话。",
            "给今天留一个可回看的纪念物，让 10 岁这个节点有一个能被保存下来的载体。",
            "顺手记下这 10 年里你最珍惜的 3 个瞬间，后面会更容易写得深，也更容易回看。",
        ]
    if is_family_daily_moment(event):
        return [
            "给这条留一个带画面感的小标题，让你以后回看时能立刻回到那个场景里。",
            "再补一句“我为什么想记下这一幕”，这样以后不只记得事情，也记得当时的感觉。",
            "把这类有烟火气的小片段继续积累下去，它们会慢慢形成你生活里很有力量的一组样本。",
        ]
    needs = split_tag_text(event.get("needs"))
    raw_text = normalize_text(event.get("raw_text") or event.get("message"))
    items: List[str] = []
    if any(code in needs for code in ("feedback", "clarity", "help", "guidance", "decision")):
        items.append("把这条里最关键的问题压缩成一句，后面继续展开时会更稳。")
    if len(raw_text) >= 60:
        items.append("把这段内容拆成 2 到 3 个关键点，后面复用或回看都会更轻松。")
    items.append("如果你愿意，可以顺着这条再往下追问一层，把真正最重要的点继续掘出来。")
    return unique_list(items)[:3]


def _help_items(event: dict) -> List[str]:
    if is_agent_stage_recap_note(event):
        return [
            "我可以帮你把这条阶段复盘整理成一张真正可回看的里程碑卡。",
            "我可以继续把这四场硬仗拆成 SOP，变成后面搭 agent 时可复用的操作资产。",
            "我也可以继续陪你把“信息处理机制”往正式模块设计推进下去。",
        ]
    if is_multi_machine_agent_trial_note(event):
        return [
            "我可以帮你把“多机龙虾实验”整理成一张实验卡，写清机器编号、角色、任务和观察指标。",
            "我可以继续帮你把这条隐喻往 Hermes / LifeOS 的分工体系里翻译，看看后面能不能长成真正的组织结构。",
            "我也可以陪你做下一轮复盘，判断这次试跑到底带来了真实增益，还是只是多了一台设备。",
        ]
    agent_subtype = detect_agent_strategy_subtype(event)
    if agent_subtype == "feature_debug":
        return [
            "我可以帮你把这次返回逐区打分，并把问题直接回写到反馈生成器。",
            "我可以继续把这条样本变成标题生成、问答配对、情绪映射的回归用例。",
            "我可以直接继续改代码并部署到 Hermes，再让你测下一轮。",
        ]
    if agent_subtype == "assetization":
        return [
            "我可以帮你把这套能力资产发布规范整理成一份固定模板。",
            "我可以继续帮你把每次开发会话自动沉淀到专属文件夹和 GitHub。",
            "我可以把“换 agent 也能接力”的 onboarding 文档继续补完整。",
        ]
    if agent_subtype == "mobile_handoff":
        return [
            "我可以帮你把这条跨设备工作流整理成一张清晰的流程图或说明卡。",
            "我可以继续帮你挑出最值得先做自动化的那一步。",
            "我可以把这条链路往“输入一次、产出多份内容资产”的方向继续设计。",
        ]
    if agent_subtype == "workflow_sop":
        return [
            "我可以帮你把这六步 SOP 压成一张真正可执行的操作卡。",
            "我可以继续帮你给每一步补上输入、输出和异常处理规则。",
            "我可以把这条个人 AI 协作法整理成一份更适合后续复盘和传播的说明文档。",
        ]
    if agent_subtype == "runtime_strategy":
        return [
            "我可以把这条整理成一张可复用的 SOP / 原则卡。",
            "我可以直接把这条原则落进 Hermes 的实现里。",
            "我可以继续陪你把它拆成完整的分层方案和执行路径。",
        ]
    if is_stability_leadership_note(event):
        return [
            "我可以帮你把这条观察整理成一张“稳定机制”方法卡。",
            "我可以陪你把这类人物观察继续提炼成可复用的管理样本。",
            "我可以直接帮你把“谈话 -> AI整理 -> 返还”做成固定的工作流。",
        ]
    if is_family_daily_joy_note(event):
        return [
            "我可以帮你给这条取一个更有画面感的小标题。",
            "我可以继续帮你把这类家庭幸福片段整理成长期可回看的样本集。",
            "我可以陪你把这条再压缩成一段更适合以后回看的短记录。",
        ]
    if is_learning_workflow_note(event):
        return [
            "我可以帮你把这套阅读流程整理成一张可执行的卡片。",
            "我可以陪你把这套方法拆成一个最小可运行版本。",
            "我可以继续帮你把这套阅读方法沉淀成长期可复用的系统。",
        ]
    if is_collaborative_method_note(event):
        return [
            "我可以帮你把这条压缩成一个更清晰的问题。",
            "我可以继续把这条往更深一点的洞察方向展开。",
            "我可以把这条整理成一份更明确的行动清单。",
        ]
    if is_family_milestone_note(event):
        return [
            "我可以帮你把这封信先起一个开头。",
            "我可以陪你一起挑出今天最值得留下的 3 个瞬间。",
            "我可以帮你把这条整理成一份更完整的纪念卡片。",
        ]
    if is_family_daily_moment(event):
        return [
            "我可以帮你把这条压缩成一个更有画面感的标题。",
            "我可以陪你把这类生活片段整理成一个长期的家庭样本集。",
            "我可以继续帮你从这条里提炼更细的关系感和生活感。",
        ]
    return [
        "我可以帮你把这条压缩成一个更清晰的问题。",
        "我可以继续把这条往深一点的洞察方向展开。",
        "我可以把这条整理成一份更明确的行动清单。",
    ]


def _normalize_contract_items(value: Any, limit: int = 4) -> List[str]:
    def _low_signal(text: str) -> bool:
        normalized = normalize_text(text).lower()
        return normalized in {"无", "暂无", "没有", "不适用", "n/a", "na", "-", "none", "null"}

    if isinstance(value, list):
        items = [normalize_text(item) for item in value if normalize_text(item) and not _low_signal(item)]
    else:
        text = normalize_text(value)
        items = [text] if text and not _low_signal(text) else []
    return unique_list(items)[:limit]


def _memory_snapshot_items(event: dict) -> List[str]:
    items: List[str] = []
    observation = normalize_text(event.get("memory_observation"))
    topics = split_tag_text(event.get("memory_topics"))
    preferences = split_tag_text(event.get("user_preference_updates"))
    if observation:
        items.append(observation)
    if topics:
        items.append(f"这次会记到：{' / '.join(topics[:4])}")
    if preferences:
        items.append(f"也会继续记住你的偏好：{'；'.join(preferences[:3])}")
    return unique_list(items)


def _long_term_snapshot_items(event: dict) -> List[str]:
    items: List[str] = []
    decision = normalize_text(event.get("long_term_library_decision"))
    category = normalize_text(event.get("long_term_library_category"))
    if decision:
        items.append(decision)
    elif category:
        items.append(f"先按「{category}」归类。")
    return unique_list(items)


def _build_llm_feedback_contract(event: dict) -> Dict[str, Any]:
    payload = event.get("llm_feedback_contract")
    if not isinstance(payload, dict):
        return {}

    title, subtitle = _header_copy(event)
    llm_title = normalize_text(payload.get("title"))
    llm_subtitle = normalize_text(payload.get("subtitle"))
    llm_summary = normalize_text(payload.get("summary"))
    llm_tags = _normalize_contract_items(payload.get("tags"), limit=3)
    judgement_items = _normalize_contract_items(payload.get("judgement_items"), limit=5) or _judgement_items(event)
    takeaway_items = _normalize_contract_items(payload.get("takeaway_items"), limit=5) or _takeaway_items(event)
    value_items = _normalize_contract_items(payload.get("value_items"), limit=4) or _value_items(event)
    memory_items = _normalize_contract_items(payload.get("memory_items"), limit=4) or _memory_snapshot_items(event)
    long_term_items = _normalize_contract_items(payload.get("long_term_items"), limit=4) or _long_term_snapshot_items(event)
    action_items = _normalize_contract_items(payload.get("action_items"), limit=4) or _action_items(event)
    help_items = _normalize_contract_items(payload.get("help_items"), limit=4) or _help_items(event)

    has_llm_signal = any(
        [
            llm_title,
            llm_subtitle,
            llm_summary,
            llm_tags,
            judgement_items,
            takeaway_items,
            value_items,
            memory_items,
            long_term_items,
            action_items,
            help_items,
        ]
    )
    if not has_llm_signal:
        return {}

    sections = [
        {"title": "🧾 内容", "items": _content_items(event)},
        {"title": "🧭 我对这条的判断", "items": judgement_items},
        {"title": "🎯 我替你提炼出的关键内容", "items": takeaway_items},
        {"title": "💡 这条真正重要的地方", "items": value_items},
    ]
    if memory_items:
        sections.append({"title": "🧠 Hermes 记住了什么", "items": memory_items})
    if long_term_items:
        sections.append({"title": "🗂️ 长期库建议", "items": long_term_items})
    sections.extend(
        [
            {"title": "🪜 下一步行动方向的建议", "items": action_items},
            {"title": "🤝 你需要我继续帮你做些什么吗？", "items": help_items},
        ]
    )

    note_text = ""
    status = event.get("status")
    if isinstance(status, dict) and normalize_text(status.get("archive")) == "failed":
        note_text = "归档出了点问题，我会继续补处理。"

    return {
        "header_template": _header_template(event),
        "title": llm_title or title,
        "subtitle": llm_subtitle or subtitle,
        "tags": llm_tags or _human_tags(event),
        "summary": llm_summary or (takeaway_items[0] if takeaway_items else extract_first_sentence(normalize_text(event.get("raw_text")))),
        "sections": sections,
        "note_text": note_text,
    }


def build_record_feedback_contract(event: dict) -> Dict[str, Any]:
    llm_contract = _build_llm_feedback_contract(event)
    if llm_contract:
        return llm_contract

    title, subtitle = _header_copy(event)
    sections = [
        {"title": "🧾 内容", "items": _content_items(event)},
        {"title": "🧭 我对这条的判断", "items": _judgement_items(event)},
        {"title": "🎯 我替你提炼出的关键内容", "items": _takeaway_items(event)},
        {"title": "💡 这条真正重要的地方", "items": _value_items(event)},
        {"title": "🪜 下一步行动方向的建议", "items": _action_items(event)},
        {"title": "🤝 你需要我继续帮你做些什么吗？", "items": _help_items(event)},
    ]

    note_text = ""
    status = event.get("status")
    if isinstance(status, dict) and normalize_text(status.get("archive")) == "failed":
        note_text = "归档出了点问题，我会继续补处理。"

    return {
        "header_template": _header_template(event),
        "title": title,
        "subtitle": subtitle,
        "tags": _human_tags(event),
        "summary": _takeaway_items(event)[0],
        "sections": sections,
        "note_text": note_text,
    }


def render_record_feedback_text(contract: Dict[str, Any]) -> str:
    lines = [contract.get("title", "").strip(), contract.get("subtitle", "").strip()]
    for section in contract.get("sections", []):
        title = normalize_text(section.get("title"))
        items = section.get("items") or []
        if title:
            lines.append(title)
        for index, item in enumerate(items, start=1):
            text = normalize_text(item)
            if text:
                lines.append(f"{index}. {text}")
    note_text = normalize_text(contract.get("note_text"))
    if note_text:
        lines.append(f"补充说明：{note_text}")
    return "\n".join(line for line in lines if line).strip()
