from __future__ import annotations

import re
from typing import Any, Mapping

from .schemas import (
    CharacterEditForm,
    CharacterItem,
    CharacterPageViewModel,
    ProposalCard,
    Step1Form,
    Step2ViewModel,
)

AgentStateLike = Mapping[str, Any]

DEFAULT_AGENT_FLAGS: dict[str, Any] = {
    "operation_mode": "generate",
    "fast_demo_mode": True,
    "selected_commercial_plan": "",
    "qc_retry_count": 0,
    "qc_pass": False,
    "hook_pass": False,
    "aesthetic_pass": False,
    "qc_feedback_history": [],
    "current_status_book": {},
    "rolling_summary": "",
    "recent_dialogue_history": [],
    "retrieved_meta_rules": [],
    "human_greenlight_approved": False,
    "wang_jing_rejected": False,
    "wang_jing_feedback": "",
    "draft_output": "",
    "scene_tension_cd": 0,
}


def build_initial_agent_state(form: Step1Form) -> dict[str, Any]:
    project_name = form.project_name.strip()
    core_idea = form.core_idea.strip()
    if not project_name:
        raise ValueError("project_name 不能为空")
    if not core_idea:
        raise ValueError("core_idea 不能为空")

    state = dict(DEFAULT_AGENT_FLAGS)
    state.update(
        {
            "thread_id": project_name,
            "current_task": core_idea,
            "commercial_directive": form.commercial_directive.strip(),
            "story_bible": form.story_bible_input.strip(),
            "target_pmf": "",
            "established_bible": form.story_bible_input.strip(),
            "established_characters": None,
            "system_character_cards": "",
            "established_keyframes": None,
            "current_genre": "",
            "market_trend_benchmarks": "",
            "wall_street_macro_report": "",
            "next_agent_role": None,
            "next_framework_id": None,
            "societal_deadlocks": None,
            "trauma_profiles": None,
            "pressure_pulse_map": None,
            "physical_asset_seeds": None,
            "mutation_drift": None,
            "pmf_pitch_options": "",
            "human_feedback": "",
        }
    )
    return state


def step2_selection_to_agent_update(
    selected_proposal_text: str,
    *,
    proposal_feedback: str = "",
    proposal_rejected: bool = False,
) -> dict[str, Any]:
    selected = selected_proposal_text.strip()
    if not selected and not proposal_rejected:
        raise ValueError("selected_proposal_text 不能为空")

    return {
        "selected_commercial_plan": selected,
        "wang_jing_feedback": proposal_feedback.strip(),
        "wang_jing_rejected": bool(proposal_rejected),
    }


def step4_characters_to_agent_update(characters: list[CharacterItem]) -> dict[str, Any]:
    return {
        "established_characters": [character_item_to_agent_dict(item) for item in characters]
    }


def character_edit_form_to_item(character_id: str, form: CharacterEditForm) -> CharacterItem:
    return CharacterItem(
        id=character_id,
        name=form.name.strip(),
        hair_style=form.hair_style.strip(),
        hair_color=form.hair_color.strip(),
        eye_color=form.eye_color.strip(),
        marks=form.marks.strip(),
        height_ratio=form.height_ratio.strip(),
        outfits=_compact_outfits([form.outfit_a, form.outfit_b, form.outfit_c]),
    )


def agent_state_to_step2_view_model(state: AgentStateLike) -> Step2ViewModel:
    raw_pitch_text = _string_value(state.get("pmf_pitch_options"))
    cards = _parse_proposal_cards(raw_pitch_text)
    selected_text = _string_value(state.get("selected_commercial_plan"))
    selected_id = _resolve_selected_proposal_id(cards, selected_text)

    return Step2ViewModel(
        proposal_options=cards,
        selected_proposal_text=selected_text,
        selected_proposal_id=selected_id,
        raw_pitch_text=raw_pitch_text,
    )


def agent_state_to_step4_view_model(state: AgentStateLike) -> CharacterPageViewModel:
    structured_characters = _normalize_established_characters(state.get("established_characters"))
    raw_character_cards_text = _string_value(state.get("system_character_cards"))
    characters = structured_characters or _parse_raw_character_cards(raw_character_cards_text)

    return CharacterPageViewModel(
        characters=characters,
        raw_character_cards_text=raw_character_cards_text,
    )


def character_item_to_agent_dict(item: CharacterItem) -> dict[str, Any]:
    return {
        "id": item.id,
        "name": item.name,
        "hairStyle": item.hair_style,
        "hairColor": item.hair_color,
        "eyeColor": item.eye_color,
        "marks": item.marks,
        "heightRatio": item.height_ratio,
        "outfits": _compact_outfits(item.outfits),
    }


def _normalize_established_characters(value: Any) -> list[CharacterItem]:
    if not isinstance(value, list):
        return []

    characters: list[CharacterItem] = []
    for index, raw_item in enumerate(value):
        if not isinstance(raw_item, Mapping):
            continue

        character_id = _string_value(raw_item.get("id")) or f"character_{index + 1}"
        characters.append(
            CharacterItem(
                id=character_id,
                name=_first_non_empty(raw_item, "name", "角色名称", fallback=f"角色{index + 1}"),
                hair_style=_first_non_empty(raw_item, "hairStyle", "hair_style", "发型"),
                hair_color=_first_non_empty(raw_item, "hairColor", "hair_color", "发色"),
                eye_color=_first_non_empty(raw_item, "eyeColor", "eye_color", "瞳色", "眼睛颜色"),
                marks=_first_non_empty(raw_item, "marks", "显著伤痕 / 特征", "显著特征"),
                height_ratio=_first_non_empty(raw_item, "heightRatio", "height_ratio", "身高比例"),
                outfits=_normalize_outfits(raw_item.get("outfits")),
            )
        )
    return characters


def _parse_proposal_cards(raw_text: str) -> list[ProposalCard]:
    if not raw_text.strip():
        return []

    sections = _split_proposal_sections(raw_text)
    cards: list[ProposalCard] = []
    for index, section in enumerate(sections):
        proposal_id = section["id"]
        content = section["content"]
        title = (
            _extract_field(content, ["标题", "方案名"])
            or _extract_title_from_heading(section["heading"], proposal_id)
            or _extract_title_from_section(content, proposal_id)
        )
        hook = _extract_field(content, ["1句话梗概", "一句话梗概", "1句梗概"]) or _extract_hook_fallback(content)
        platform = _extract_bracket_value(section["heading"])
        audience = _extract_audience(content, platform)
        highlights = _extract_highlights(content)

        cards.append(
            ProposalCard(
                id=proposal_id.lower(),
                title=title or f"方案 {proposal_id}",
                hook=hook,
                highlights=highlights,
                platform=platform,
                audience=audience,
                raw_text=content.strip(),
            )
        )

    if cards:
        return cards

    return [
        ProposalCard(
            id="a",
            title="方案 A",
            hook=raw_text.strip(),
            raw_text=raw_text.strip(),
        )
    ]


def _split_proposal_sections(raw_text: str) -> list[dict[str, str]]:
    normalized_text = re.sub(r"[*_`]+", "", raw_text)
    pattern = re.compile(
        r"(^|\n)\s*(?:[#>\-\s]|\d+\.\s*)*(?:[【\[][^】\]]+[】\]]\s*)?方案\s*([ABCabc])([^\n]*)",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(normalized_text))
    if not matches:
        return []

    sections: list[dict[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(normalized_text)
        heading = normalized_text[match.start(): match.end()].strip()
        content = normalized_text[start:end].strip()
        sections.append({"id": match.group(2).upper(), "heading": heading, "content": content})
    return sections


def _extract_title_from_heading(heading: str, proposal_id: str) -> str:
    quoted_match = re.search(r"[《“\"]([^》”\"]+)[》”\"]", heading)
    if quoted_match:
        return quoted_match.group(1).strip()

    colon_match = re.search(r"方案\s*[A-Z]\s*[：:]\s*(.+)", heading, re.IGNORECASE)
    if colon_match:
        return _cleanup_text(colon_match.group(1))

    return ""


def _extract_title_from_section(content: str, proposal_id: str) -> str:
    lines = [line.strip(" -*#\t") for line in content.splitlines() if line.strip()]
    for line in lines[1:4]:
        if any(keyword in line for keyword in ("一句话", "梗概", "核心爽点", "融合")):
            continue
        if len(line) <= 40:
            return line
    return f"方案 {proposal_id}"


def _extract_hook_fallback(content: str) -> str:
    lines = [line.strip(" -*#\t") for line in content.splitlines() if line.strip()]
    for line in lines:
        if "方案" in line and len(line) < 50:
            continue
        if line:
            return line
    return ""


def _extract_field(content: str, field_names: list[str]) -> str:
    normalized_content = re.sub(r"[*_`]+", "", content)
    for field_name in field_names:
        pattern = re.compile(
            rf"{re.escape(field_name)}\s*[:：]\s*(.+?)(?=\n\s*(?:[#>\-\s]*)?(?:\S+\s*[:：]|方案\s*[ABCabc]|$)|\Z)",
            re.DOTALL,
        )
        match = pattern.search(normalized_content)
        if match:
            return _cleanup_text(match.group(1))
    return ""


def _extract_bracket_value(heading: str) -> str:
    match = re.search(r"[【\[]([^】\]]+)[】\]]", heading)
    return match.group(1).strip() if match else ""


def _extract_audience(content: str, platform: str) -> str:
    explicit = _extract_field(content, ["受众定位", "受众"])
    if explicit:
        return explicit
    if "女性" in platform:
        return "女性受众"
    if "B站" in platform or "高知" in platform:
        return "高知 / 悬疑科幻受众"
    if "竖屏" in platform or "下沉市场" in platform:
        return "下沉市场 / 竖屏短剧受众"
    return ""


def _extract_highlights(content: str) -> list[str]:
    highlight_text = _extract_field(content, ["核心爽点", "核心亮点"])
    if highlight_text:
        parts = re.split(r"[、，,；;]\s*", highlight_text)
        cleaned = [_cleanup_text(part) for part in parts if _cleanup_text(part)]
        if cleaned:
            return cleaned[:4]

    bullets = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(("-", "•", "▸", "▶")):
            cleaned = _cleanup_text(stripped.lstrip("-•▸▶ ").strip())
            if cleaned:
                bullets.append(cleaned)
    return bullets[:4]


def _parse_raw_character_cards(raw_text: str) -> list[CharacterItem]:
    if not raw_text.strip():
        return []

    blocks = _split_character_blocks(raw_text)
    characters: list[CharacterItem] = []
    for index, block in enumerate(blocks):
        name = _extract_character_name(block) or f"角色{index + 1}"
        dna_text = _extract_labeled_block(block, ["不可变 DNA", "Immutable DNA"])
        wardrobe_lines = _extract_wardrobe_items(block)
        visual_fields = _extract_visual_fields_from_block(block, dna_text)

        characters.append(
            CharacterItem(
                id=f"character_{index + 1}",
                name=name,
                hair_style=visual_fields["hair_style"],
                hair_color=visual_fields["hair_color"],
                eye_color=visual_fields["eye_color"],
                marks=visual_fields["marks"],
                height_ratio=visual_fields["height_ratio"],
                outfits=_normalize_outfits(wardrobe_lines),
            )
        )
    return characters


def _split_character_blocks(raw_text: str) -> list[str]:
    pattern = re.compile(
        r"(^|\n)\s*(?:#{1,6}\s*)?(?:\*\*)?\s*(?:人物[一二三四五六七八九十\d]+|角色\s*[一二三四五六七八九十\d]+|主角姓名)\s*[:：]",
        re.MULTILINE,
    )
    matches = list(pattern.finditer(raw_text))
    if not matches:
        return [raw_text]

    blocks: list[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw_text)
        blocks.append(raw_text[start:end].strip())
    return blocks


def _extract_character_name(block: str) -> str:
    # Prefer the new explicit naming fields so UI stays aligned with downstream scripts.
    for label in ["后续剧本统一使用名", "正式姓名", "角色代称/标签"]:
        pattern = re.compile(rf"{re.escape(label)}\s*[:：]\s*(.+)")
        match = pattern.search(block)
        if not match:
            continue

        name = _cleanup_text(match.group(1))
        if not name:
            continue
        if label == "角色代称/标签":
            name = re.split(r"[，,、/]|（|\\(", name, maxsplit=1)[0].strip()
        return name

    for line in block.splitlines():
        cleaned_line = line.strip().replace("*", "").replace("#", "").strip()
        if not cleaned_line:
            continue

        match = re.search(
            r"(?:人物[一二三四五六七八九十\d]+|角色\s*[一二三四五六七八九十\d]+|主角姓名)\s*[:：]\s*(.+)",
            cleaned_line,
        )
        if not match:
            continue

        name = match.group(1).strip()
        name = re.sub(r"\s*-\s*.*$", "", name)
        return name.strip()

    return ""


def _extract_labeled_block(block: str, labels: list[str]) -> str:
    for label in labels:
        pattern = re.compile(
            rf"{re.escape(label)}[^\n]*[:：]\s*(.+?)(?=\n\s*[【\[]?.+[】\]]?\s*[:：]|\Z)",
            re.DOTALL,
        )
        match = pattern.search(block)
        if match:
            return _cleanup_text(match.group(1))
    return ""


def _extract_wardrobe_items(block: str) -> list[str]:
    lines = [raw_line.replace("*", "").strip() for raw_line in block.splitlines()]
    outfit_items: list[str] = []
    current_chunk: list[str] = []
    in_wardrobe_section = False

    def flush_chunk() -> None:
        if not current_chunk:
            return
        text = _cleanup_text(" ".join(part for part in current_chunk if part))
        if text:
            outfit_items.append(text)
        current_chunk.clear()

    for cleaned_line in lines:
        if not cleaned_line:
            continue

        if "Wardrobe Matrix" in cleaned_line or "服装方案矩阵" in cleaned_line or "胶囊衣橱库" in cleaned_line:
            in_wardrobe_section = True
            flush_chunk()
            continue

        if not in_wardrobe_section and "[Outfit_" not in cleaned_line and "[方案" not in cleaned_line:
            continue

        if re.search(r"\[Outfit_[A-Z]\]|\[方案\s*[A-Z一二三四五六七八九十]\]", cleaned_line):
            flush_chunk()
            current_chunk.append(cleaned_line)
            in_wardrobe_section = True
            continue

        if in_wardrobe_section and re.match(r"^(?:角色|人物|正式姓名|角色代称/标签|后续剧本统一使用名|【底层绝对不可变 DNA】|【不可变 DNA】|发型[:：]|发色[:：]|瞳色[:：]|显著|身高比例[:：])", cleaned_line):
            flush_chunk()
            in_wardrobe_section = False
            continue

        if in_wardrobe_section and re.match(r"^(?:Excelsior\b|好了[,，]|有了这些|去吧[,，]|各位[,，]|现在[,，])", cleaned_line, re.IGNORECASE):
            flush_chunk()
            in_wardrobe_section = False
            continue

        if in_wardrobe_section and current_chunk:
            current_chunk.append(cleaned_line)

    flush_chunk()
    return outfit_items[:4]


def _extract_visual_fields_from_dna_text(dna_text: str) -> dict[str, str]:
    if not dna_text:
        return {
            "hair_style": "",
            "hair_color": "",
            "eye_color": "",
            "marks": "",
            "height_ratio": "",
        }

    text = dna_text.strip().strip("()")
    parts = [part.strip() for part in re.split(r"[，,；;]", text) if part.strip()]

    hair_style = next((part for part in parts if "发" in part or "hair" in part.lower()), "")
    hair_color = next((part for part in parts if _looks_like_hair_color(part)), "")
    eye_color = next((part for part in parts if "眼" in part or "瞳" in part or "eye" in part.lower()), "")
    marks = next((part for part in parts if any(keyword in part.lower() for keyword in ("scar", "tattoo", "mark")) or any(keyword in part for keyword in ("伤", "疤", "纹身", "胎记"))), "")
    height_ratio = next((part for part in parts if _looks_like_height_ratio(part)), "")

    if not hair_style and parts:
        hair_style = parts[0]
    return {
        "hair_style": hair_style,
        "hair_color": hair_color,
        "eye_color": eye_color,
        "marks": marks,
        "height_ratio": height_ratio,
    }


def _extract_visual_fields_from_block(block: str, dna_text: str) -> dict[str, str]:
    visual_fields = _extract_visual_fields_from_dna_text(dna_text)

    field_patterns = {
        "hair_style": ["发型", "hair style"],
        "hair_color": ["发色", "hair color", "发型/发色"],
        "eye_color": ["瞳色", "眼睛颜色", "eye color"],
        "marks": ["显著胎记/伤痕", "显著胎记 / 伤痕", "显著伤痕 / 特征", "显著特征", "伤痕"],
        "height_ratio": ["身高比例", "height ratio"],
    }

    for key, labels in field_patterns.items():
        if visual_fields[key]:
            continue
        extracted = _extract_field_by_labels(block, labels)
        if extracted:
            visual_fields[key] = extracted

    if not visual_fields["hair_style"] and visual_fields["hair_color"]:
        inferred_style, normalized_color = _split_hair_style_and_color(visual_fields["hair_color"])
        if inferred_style:
            visual_fields["hair_style"] = inferred_style
            visual_fields["hair_color"] = normalized_color

    return visual_fields


def _extract_field_by_labels(block: str, labels: list[str]) -> str:
    for label in labels:
        pattern = re.compile(rf"{re.escape(label)}\s*[:：]\s*(.+)")
        match = pattern.search(block)
        if match:
            return _cleanup_text(match.group(1))
    return ""


def _normalize_outfits(value: Any) -> list[str]:
    if isinstance(value, list):
        return _compact_outfits([_string_value(item) for item in value])
    if isinstance(value, str):
        return _compact_outfits(re.split(r"\n+|[；;]", value))
    return []


def _compact_outfits(values: list[str]) -> list[str]:
    return [value.strip() for value in values if isinstance(value, str) and value.strip()]


def _resolve_selected_proposal_id(cards: list[ProposalCard], selected_text: str) -> str | None:
    if not selected_text:
        return None
    for card in cards:
        if selected_text == card.raw_text:
            return card.id
        if card.title and card.title in selected_text:
            return card.id
    return None


def _first_non_empty(data: Mapping[str, Any], *keys: str, fallback: str = "") -> str:
    for key in keys:
        value = _string_value(data.get(key))
        if value:
            return value
    return fallback


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _cleanup_text(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", value).strip(" -*#\n\t")
    cleaned = re.split(r"(?:^|\s)(?:提示词级描绘|Prompt)\s*[:：]", cleaned, maxsplit=1)[0].strip()
    return cleaned


def _split_hair_style_and_color(value: str) -> tuple[str, str]:
    text = _cleanup_text(value)
    if not text:
        return "", ""

    parts = [part.strip(" ，,。；;") for part in re.split(r"[，,。；;]", text) if part.strip(" ，,。；;")]
    if len(parts) < 2:
        return "", text

    color_keywords = ("黑", "棕", "金", "银", "白", "灰", "红", "蓝", "紫", "绿", "auburn", "brown", "black", "blonde", "silver", "white", "gray", "grey", "red", "blue", "green")
    color_index = None
    for index, part in enumerate(parts):
        lowered = part.lower()
        if any(keyword in part for keyword in color_keywords[:10]) or any(keyword in lowered for keyword in color_keywords[10:]):
            color_index = index
            break

    if color_index is None or color_index == 0:
        return "", text

    hair_style = "，".join(parts[:color_index]).strip()
    hair_color = "，".join(parts[color_index:]).strip()
    return hair_style, hair_color


def _looks_like_hair_color(part: str) -> bool:
    stripped = part.strip().lower()
    if "发" in part and part.strip() not in {"黑发", "金发", "白发", "银发", "棕发"}:
        return False
    if stripped in {"黑色", "深棕", "浅棕", "棕色", "金色", "银色", "白色", "灰色", "红色", "蓝色"}:
        return True
    if stripped in {"black", "brown", "blonde", "white", "silver", "gray", "grey", "red", "blue"}:
        return True
    if len(part.strip()) <= 4 and any(color in part for color in ("黑", "棕", "金", "银", "白", "灰", "红", "蓝")):
        return True
    return False


def _looks_like_height_ratio(part: str) -> bool:
    lowered = part.lower()
    if "身高" in part or "比例" in part:
        return True
    if any(keyword in lowered for keyword in ("tall", "slim", "ratio")):
        return True
    if any(keyword in part for keyword in ("高挑", "修长", "偏高", "肩宽", "头身比")):
        return True
    return False
