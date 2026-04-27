from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Step1Form:
    project_name: str
    core_idea: str
    commercial_directive: str = ""
    story_bible_input: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProposalCard:
    id: str
    title: str
    hook: str
    highlights: list[str] = field(default_factory=list)
    platform: str = ""
    audience: str = ""
    raw_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Step2ViewModel:
    proposal_options: list[ProposalCard] = field(default_factory=list)
    selected_proposal_text: str = ""
    selected_proposal_id: str | None = None
    raw_pitch_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["proposal_options"] = [card.to_dict() for card in self.proposal_options]
        return data


@dataclass(slots=True)
class CharacterItem:
    id: str
    name: str
    hair_style: str = ""
    hair_color: str = ""
    eye_color: str = ""
    marks: str = ""
    height_ratio: str = ""
    outfits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CharacterEditForm:
    name: str
    hair_style: str = ""
    hair_color: str = ""
    eye_color: str = ""
    marks: str = ""
    height_ratio: str = ""
    outfit_a: str = ""
    outfit_b: str = ""
    outfit_c: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CharacterPageViewModel:
    characters: list[CharacterItem] = field(default_factory=list)
    raw_character_cards_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["characters"] = [item.to_dict() for item in self.characters]
        return data
