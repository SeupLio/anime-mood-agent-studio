from __future__ import annotations

from app.core.schemas import AgentAdvice, AgentStep, FusionResult, ImageSignal, TextSignal


ARCHETYPES = {
    "温柔治愈": {
        "tone": "温柔、共情、给出确定感",
        "opening": "我已经收到你的感受了。",
        "style": "像可靠的同伴一样安抚玩家，再给出清晰下一步。",
    },
    "冷静策士": {
        "tone": "理性、简洁、以方案为中心",
        "opening": "先把问题拆开来看。",
        "style": "承认情绪，但更强调判断、补偿和后续排查。",
    },
    "元气伙伴": {
        "tone": "明快、有行动感、不过度卖萌",
        "opening": "收到！这条反馈很关键。",
        "style": "快速响应玩家情绪，用积极语气推动后续行动。",
    },
}


def build_agent_advice(
    text: TextSignal | None,
    image: ImageSignal | None,
    fusion: FusionResult,
    archetype: str = "温柔治愈",
) -> AgentAdvice:
    profile = ARCHETYPES.get(archetype, ARCHETYPES["温柔治愈"])
    intent = _detect_intent(text)
    risk_level = _risk_level(fusion, intent)
    response_strategy = _strategy(fusion, intent, risk_level, profile)
    ops_actions = _ops_actions(fusion, intent, risk_level, image is not None)
    player_reply = _player_reply(profile, fusion, intent, risk_level)
    narrative_hook = _narrative_hook(fusion, intent)
    trace = [
        AgentStep(tool="detect_intent", observation=f"玩家意图识别为：{intent}"),
        AgentStep(tool="assess_emotion", observation=f"主情绪 {fusion.primary_emotion}，效价 {fusion.valence}，唤醒度 {fusion.arousal}"),
        AgentStep(tool="rank_liveops_risk", observation=f"风险等级：{risk_level}"),
        AgentStep(tool="select_response_style", observation=f"选择人设：{archetype}；语气：{profile['tone']}"),
        AgentStep(tool="draft_action_plan", observation="生成玩家回复、运营动作和剧情钩子"),
    ]
    return AgentAdvice(
        intent=intent,
        risk_level=risk_level,
        response_strategy=response_strategy,
        player_reply=player_reply,
        ops_actions=ops_actions,
        narrative_hook=narrative_hook,
        trace=trace,
    )


def _detect_intent(text: TextSignal | None) -> str:
    if text is None:
        return "scene_mood_check"
    terms = set(text.detected_terms)
    if {"骗氪", "退坑", "垃圾"} & terms:
        return "monetization_complaint"
    if {"期待", "等不及", "想抽", "想玩", "期待后续"} & terms:
        return "content_expectation"
    if {"担心", "焦虑", "怕"} & terms:
        return "uncertainty_or_anxiety"
    if {"喜欢", "好看", "惊艳", "治愈", "爱了"} & terms:
        return "positive_feedback"
    if text.valence < -0.35:
        return "negative_feedback"
    if text.valence > 0.35:
        return "positive_feedback"
    return "general_feedback"


def _risk_level(fusion: FusionResult, intent: str) -> str:
    if intent == "monetization_complaint":
        return "high"
    if fusion.valence < -0.45 and fusion.arousal > 0.45:
        return "high"
    if fusion.valence < -0.2 or fusion.arousal > 0.62:
        return "medium"
    return "low"


def _strategy(fusion: FusionResult, intent: str, risk_level: str, profile: dict[str, str]) -> str:
    if risk_level == "high":
        return f"{profile['style']} 优先承认情绪和损失感，避免争辩，并给出可验证的处理路径。"
    if intent == "content_expectation":
        return f"{profile['style']} 放大期待感，同时收集玩家最关注的角色、关卡或剧情点。"
    if intent == "positive_feedback":
        return f"{profile['style']} 感谢玩家反馈，并把正向情绪转化为可复用的内容洞察。"
    if fusion.primary_emotion in {"sadness", "fear"}:
        return f"{profile['style']} 先降低不确定性，再提供补偿、攻略或问题跟进入口。"
    return f"{profile['style']} 给出简短回应和下一步动作，保持对话继续。"


def _ops_actions(fusion: FusionResult, intent: str, risk_level: str, has_image: bool) -> list[str]:
    actions: list[str] = []
    if risk_level == "high":
        actions.append("标记为高优先级舆情样本，进入人工复核队列")
        actions.append("抽取关键词并关联版本、卡池、活动和支付日志")
    if intent == "monetization_complaint":
        actions.append("检查抽卡/付费描述是否存在认知落差，准备透明化解释")
    if intent == "content_expectation":
        actions.append("沉淀玩家期待点，用于后续剧情预热和角色 PV 标签")
    if fusion.primary_emotion in {"sadness", "fear"}:
        actions.append("提供降低焦虑的信息：概率、活动周期、补偿规则或攻略入口")
    if has_image:
        actions.append("保存图像氛围特征，辅助分析角色立绘或活动图的情绪表达")
    if not actions:
        actions.append("记录为普通反馈样本，进入情绪趋势看板")
    return actions


def _player_reply(profile: dict[str, str], fusion: FusionResult, intent: str, risk_level: str) -> str:
    opening = profile["opening"]
    if risk_level == "high":
        return (
            f"{opening} 这次体验让你产生了明显的不满，我们会优先核对相关活动和付费说明。"
            "如果你愿意补充区服、时间点或截图，我们可以更快定位问题。"
        )
    if intent == "content_expectation":
        return f"{opening} 你提到的期待点很有价值，我们会把它归入后续内容观察项，也会继续关注类似玩家的反馈趋势。"
    if intent == "positive_feedback":
        return f"{opening} 很高兴这段内容带来了正向体验，我们会记录触发好感的角色、画面和剧情元素，帮助后续内容保持这种感觉。"
    if fusion.primary_emotion in {"sadness", "fear"}:
        return f"{opening} 我能感受到这条反馈里有些担心。我们会先把规则和进度说明清楚，并把可能影响体验的部分交给团队复核。"
    return f"{opening} 我们会记录这条反馈，并结合更多样本判断它是否代表一个需要跟进的体验问题。"


def _narrative_hook(fusion: FusionResult, intent: str) -> str:
    if intent == "content_expectation":
        return "可作为角色前瞻台词：把玩家期待转化为“下一次相遇”的悬念。"
    if fusion.primary_emotion == "anger":
        return "可设计安抚型 NPC 分支：先承认冲突，再给玩家一个可执行目标。"
    if fusion.primary_emotion == "sadness":
        return "可设计陪伴型剧情节点：让角色回应失落，并给出小规模希望感。"
    if fusion.primary_emotion == "joy":
        return "可提炼高光演出标签：强化角色魅力、战斗爽点或治愈氛围。"
    return "可进入通用反馈池：观察同类情绪是否在版本节点集中出现。"

