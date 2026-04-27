from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Step1InitRequest(BaseModel):
    project_name: str = Field(alias="projectName")
    core_idea: str = Field(alias="coreIdea")
    commercial_directive: str = Field(default="", alias="commercialDirective")
    story_bible_input: str = Field(default="", alias="storyBibleInput")

    model_config = {
        "populate_by_name": True,
    }


class InitProjectResponse(BaseModel):
    project_id: str = Field(alias="projectId")
    current_step: int = Field(alias="currentStep")
    status: str
    state: dict[str, Any]

    model_config = {
        "populate_by_name": True,
    }


class GenerateRequest(BaseModel):
    project_id: str = Field(alias="projectId")

    model_config = {
        "populate_by_name": True,
    }


class ProposalSelectRequest(BaseModel):
    project_id: str = Field(alias="projectId")
    selected_proposal_text: str = Field(alias="selectedProposalText")
    proposal_feedback: str = Field(default="", alias="proposalFeedback")
    proposal_rejected: bool = Field(default=False, alias="proposalRejected")

    model_config = {
        "populate_by_name": True,
    }


class CharacterItemPayload(BaseModel):
    id: str
    name: str
    hair_style: str = Field(default="", alias="hairStyle")
    hair_color: str = Field(default="", alias="hairColor")
    eye_color: str = Field(default="", alias="eyeColor")
    marks: str = ""
    height_ratio: str = Field(default="", alias="heightRatio")
    outfits: list[str] = Field(default_factory=list)

    model_config = {
        "populate_by_name": True,
    }


class CharacterUpdateRequest(BaseModel):
    project_id: str = Field(alias="projectId")
    characters: list[CharacterItemPayload]

    model_config = {
        "populate_by_name": True,
    }


class ApiEnvelope(BaseModel):
    project_id: str = Field(alias="projectId")
    current_step: int = Field(alias="currentStep")
    status: str
    data: dict[str, Any]

    model_config = {
        "populate_by_name": True,
    }
