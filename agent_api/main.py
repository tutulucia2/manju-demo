from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent_mapper import CharacterItem, Step1Form

from .api_schemas import (
    ApiEnvelope,
    CharacterUpdateRequest,
    GenerateRequest,
    InitProjectResponse,
    ProposalSelectRequest,
    Step1InitRequest,
)
from .service import AgentDemoService
from .store import InMemoryProjectStore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STORE_PATH = PROJECT_ROOT / "data" / "project_store.json"

app = FastAPI(title="漫剧项目 Agent API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = InMemoryProjectStore(STORE_PATH)
service = AgentDemoService(store)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/project/init", response_model=InitProjectResponse)
def init_project(payload: Step1InitRequest) -> InitProjectResponse:
    form = Step1Form(
        project_name=payload.project_name,
        core_idea=payload.core_idea,
        commercial_directive=payload.commercial_directive,
        story_bible_input=payload.story_bible_input,
    )
    record = service.init_project(form)
    return InitProjectResponse(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        state=service.build_state_view(record),
    )


@app.get("/api/project/{project_id}/state", response_model=ApiEnvelope)
def get_project_state(project_id: str) -> ApiEnvelope:
    record = service.get_project(project_id)
    return ApiEnvelope(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        data=service.build_state_view(record),
    )


@app.post("/api/proposals/generate", response_model=ApiEnvelope)
def generate_proposals(payload: GenerateRequest) -> ApiEnvelope:
    record = service.generate_proposals(payload.project_id)
    return ApiEnvelope(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        data={"step2": service.build_state_view(record)["step2"]},
    )


@app.post("/api/proposals/select", response_model=ApiEnvelope)
def select_proposal(payload: ProposalSelectRequest) -> ApiEnvelope:
    record = service.select_proposal(
        payload.project_id,
        selected_proposal_text=payload.selected_proposal_text,
        proposal_feedback=payload.proposal_feedback,
        proposal_rejected=payload.proposal_rejected,
    )
    return ApiEnvelope(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        data=service.build_state_view(record),
    )


@app.post("/api/world/generate", response_model=ApiEnvelope)
def generate_world(payload: GenerateRequest) -> ApiEnvelope:
    record = service.generate_world(payload.project_id)
    return ApiEnvelope(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        data={"step3": service.build_state_view(record)["step3"]},
    )


@app.post("/api/characters/generate", response_model=ApiEnvelope)
def generate_characters(payload: GenerateRequest) -> ApiEnvelope:
    record = service.generate_characters(payload.project_id)
    return ApiEnvelope(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        data={"step4": service.build_state_view(record)["step4"]},
    )


@app.post("/api/characters/regenerate", response_model=ApiEnvelope)
def regenerate_characters(payload: GenerateRequest) -> ApiEnvelope:
    record = service.regenerate_characters(payload.project_id)
    return ApiEnvelope(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        data={"step4": service.build_state_view(record)["step4"]},
    )


@app.post("/api/characters/update", response_model=ApiEnvelope)
def update_characters(payload: CharacterUpdateRequest) -> ApiEnvelope:
    characters = [
        CharacterItem(
            id=item.id,
            name=item.name,
            hair_style=item.hair_style,
            hair_color=item.hair_color,
            eye_color=item.eye_color,
            marks=item.marks,
            height_ratio=item.height_ratio,
            outfits=item.outfits,
        )
        for item in payload.characters
    ]
    record = service.update_characters(payload.project_id, characters)
    return ApiEnvelope(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        data={"step4": service.build_state_view(record)["step4"]},
    )


@app.post("/api/benchmarks/generate", response_model=ApiEnvelope)
def generate_benchmarks(payload: GenerateRequest) -> ApiEnvelope:
    record = service.generate_benchmarks(payload.project_id)
    return ApiEnvelope(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        data={"step5": service.build_state_view(record)["step5"]},
    )


@app.post("/api/script/generate", response_model=ApiEnvelope)
def generate_script(payload: GenerateRequest) -> ApiEnvelope:
    record = service.generate_script(payload.project_id)
    return ApiEnvelope(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        data={"step6": service.build_state_view(record)["step6"]},
    )


@app.post("/api/script/regenerate", response_model=ApiEnvelope)
def regenerate_script(payload: GenerateRequest) -> ApiEnvelope:
    record = service.regenerate_script(payload.project_id)
    return ApiEnvelope(
        projectId=record.project_id,
        currentStep=record.current_step,
        status=record.status,
        data={"step6": service.build_state_view(record)["step6"]},
    )
