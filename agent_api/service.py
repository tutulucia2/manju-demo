from __future__ import annotations

import sys
import time
from threading import Lock, Thread
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from fastapi import HTTPException

from agent_mapper import (
    CharacterItem,
    Step1Form,
    agent_state_to_step2_view_model,
    agent_state_to_step4_view_model,
    build_initial_agent_state,
    step2_selection_to_agent_update,
    step4_characters_to_agent_update,
)

from .store import InMemoryProjectStore, ProjectRecord

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WRITER_ROOT = PROJECT_ROOT / "编剧"

if str(WRITER_ROOT) not in sys.path:
    sys.path.insert(0, str(WRITER_ROOT))

load_dotenv(PROJECT_ROOT / ".env")
load_dotenv(WRITER_ROOT / ".env")

from core.workflow import build_writers_room_graph  # noqa: E402


PIPELINE_RESET_STATE: dict[str, Any] = {
    "fast_demo_mode": True,
    "selected_commercial_plan": "",
    "target_pmf": "",
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
    "draft_output": "",
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
    "scene_tension_cd": 0,
}

POST_PROPOSAL_RESET_STATE: dict[str, Any] = {
    "story_bible": "",
    "established_characters": None,
    "system_character_cards": "",
    "established_keyframes": None,
    "current_genre": "",
    "market_trend_benchmarks": "",
    "next_agent_role": None,
    "next_framework_id": None,
    "societal_deadlocks": None,
    "trauma_profiles": None,
    "pressure_pulse_map": None,
    "physical_asset_seeds": None,
    "mutation_drift": None,
    "draft_output": "",
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
    "scene_tension_cd": 0,
}

WORLD_REGEN_RESET_STATE: dict[str, Any] = dict(POST_PROPOSAL_RESET_STATE)


class RealAgentRunner:
    def __init__(self) -> None:
        self._graph = None
        self._lock = Lock()

    @property
    def graph(self):
        if self._graph is None:
            self._graph = build_writers_room_graph()
        return self._graph

    def config(self, project_id: str) -> dict[str, Any]:
        return {"configurable": {"thread_id": project_id}}

    def update_state(self, project_id: str, updates: dict[str, Any]) -> None:
        self.graph.update_state(self.config(project_id), updates)

    def get_state(self, project_id: str) -> dict[str, Any]:
        state_snapshot = self.graph.get_state(self.config(project_id))
        return dict(state_snapshot.values) if state_snapshot and getattr(state_snapshot, "values", None) else {}

    def is_waiting_for_human(self, project_id: str) -> bool:
        state_snapshot = self.graph.get_state(self.config(project_id))
        return bool(state_snapshot and getattr(state_snapshot, "next", None))

    def run_phase_one(self, project_id: str, initial_state: dict[str, Any], *, force_regenerate: bool = False) -> dict[str, Any]:
        with self._lock:
            existing = self.get_state(project_id)
            if existing.get("pmf_pitch_options") and not force_regenerate:
                return existing

            if existing and force_regenerate:
                self.graph.update_state(
                    self.config(project_id),
                    {
                        "pmf_pitch_options": "",
                        "selected_commercial_plan": "",
                        "wang_jing_feedback": "",
                        "wang_jing_rejected": True,
                    },
                )
                for _ in self.graph.stream(None, self.config(project_id)):
                    pass
                return self.get_state(project_id)

            for _ in self.graph.stream(initial_state, self.config(project_id)):
                pass
            return self.get_state(project_id)

    def run_phase_two(self, project_id: str, selected_plan: str, proposal_feedback: str = "") -> dict[str, Any]:
        with self._lock:
            updates = {
                "selected_commercial_plan": selected_plan,
                "wang_jing_feedback": proposal_feedback,
                "wang_jing_rejected": False,
            }
            self.graph.update_state(self.config(project_id), updates)
            for _ in self.graph.stream(None, self.config(project_id)):
                pass
            return self.get_state(project_id)

    def regenerate_world_phase(self, project_id: str) -> dict[str, Any]:
        with self._lock:
            current_state = self.get_state(project_id)
            selected_plan = current_state.get("selected_commercial_plan", "")
            if not selected_plan:
                raise HTTPException(status_code=400, detail="请先确认商业方案，再重新生成世界观。")

            updates = dict(WORLD_REGEN_RESET_STATE)
            updates.update(
                {
                    "selected_commercial_plan": selected_plan,
                    "wang_jing_rejected": False,
                    "wang_jing_feedback": "",
                    "human_greenlight_approved": False,
                }
            )
            self.graph.update_state(self.config(project_id), updates, as_node="wang_jing")
            for _ in self.graph.stream(None, self.config(project_id)):
                pass
            return self.get_state(project_id)

    def run_phase_three(self, project_id: str) -> dict[str, Any]:
        with self._lock:
            for _ in self.graph.stream(None, self.config(project_id)):
                pass
            return self.get_state(project_id)

    def run_phase_four(self, project_id: str) -> dict[str, Any]:
        with self._lock:
            for _ in self.graph.stream(None, self.config(project_id)):
                pass
            return self.get_state(project_id)


class AgentDemoService:
    def __init__(self, store: InMemoryProjectStore) -> None:
        self.store = store
        self.runner = RealAgentRunner()
        self._benchmark_prefetching_projects: set[str] = set()
        self._prefetching_projects: set[str] = set()
        self._prefetch_lock = Lock()

    def init_project(self, form: Step1Form) -> ProjectRecord:
        project_id = form.project_name.strip()
        state = self._build_fresh_project_state(form)
        existing_graph_state = self.runner.get_state(project_id)
        if existing_graph_state:
            self.runner.update_state(project_id, state)

        existing_record = self.store.get(project_id)
        if existing_record:
            return self.store.update(project_id, state_updates=state, current_step=1, status="initialized")
        return self.store.create(project_id, state)

    def get_project(self, project_id: str) -> ProjectRecord:
        record = self.store.get(project_id)
        if record:
            return record

        existing_graph_state = self.runner.get_state(project_id)
        if existing_graph_state:
            return self.store.create(project_id, existing_graph_state)

        raise HTTPException(status_code=404, detail=f"项目不存在: {project_id}")

    def generate_proposals(self, project_id: str) -> ProjectRecord:
        record = self.get_project(project_id)
        latest_graph_state = self.runner.get_state(project_id)
        should_regenerate = bool(latest_graph_state.get("pmf_pitch_options"))
        graph_state = self.runner.run_phase_one(
            project_id,
            record.state,
            force_regenerate=should_regenerate,
        )
        if not graph_state.get("pmf_pitch_options"):
            raise HTTPException(status_code=500, detail="真实 Agent 未返回商业方案，请检查模型配置或日志。")

        return self.store.update(
            project_id,
            state_updates=graph_state,
            current_step=2,
            status="proposals_generated",
        )

    def select_proposal(
        self,
        project_id: str,
        *,
        selected_proposal_text: str,
        proposal_feedback: str = "",
        proposal_rejected: bool = False,
    ) -> ProjectRecord:
        if proposal_rejected:
            raise HTTPException(status_code=400, detail="当前 API 版本暂未开放打回重做，请先选择一套方案继续。")

        updates = step2_selection_to_agent_update(
            selected_proposal_text,
            proposal_feedback=proposal_feedback,
            proposal_rejected=proposal_rejected,
        )
        updates.update(POST_PROPOSAL_RESET_STATE)
        self.runner.update_state(project_id, updates)
        graph_state = self.runner.run_phase_two(project_id, selected_proposal_text, proposal_feedback)
        updated = self.store.update(
            project_id,
            state_updates=graph_state,
            current_step=4,
            status="characters_ready",
        )
        self._start_benchmark_prefetch(project_id)
        return updated

    def generate_world(self, project_id: str) -> ProjectRecord:
        graph_state = self.runner.regenerate_world_phase(project_id)
        if not graph_state.get("story_bible"):
            raise HTTPException(status_code=500, detail="真实 Agent 未重新生成世界观，请检查模型配置或日志。")

        return self.store.update(
            project_id,
            state_updates=graph_state,
            current_step=4,
            status="world_regenerated",
        )

    def generate_characters(self, project_id: str) -> ProjectRecord:
        record = self.get_project(project_id)
        latest_graph_state = self.runner.get_state(project_id)
        merged = latest_graph_state or record.state
        if not (merged.get("established_characters") or merged.get("system_character_cards")):
            raise HTTPException(status_code=400, detail="真实 Agent 尚未生成人物卡，请先完成前置流程。")

        updated = self.store.update(
            project_id,
            state_updates=merged,
            current_step=4,
            status="characters_generated",
        )
        self._start_benchmark_prefetch(project_id)
        return updated

    def regenerate_characters(self, project_id: str) -> ProjectRecord:
        current_state = self.runner.get_state(project_id) or self.get_project(project_id).state
        if not current_state.get("story_bible"):
            raise HTTPException(status_code=400, detail="请先完成人物世界观，再重新生成人物卡。")

        updates = {
            "established_characters": None,
            "system_character_cards": "",
            "established_keyframes": None,
            "current_genre": "",
            "market_trend_benchmarks": "",
            "next_agent_role": None,
            "next_framework_id": None,
            "draft_output": "",
            "qc_retry_count": 0,
            "qc_pass": False,
            "hook_pass": False,
            "aesthetic_pass": False,
            "qc_feedback_history": [],
            "current_status_book": {},
            "rolling_summary": "",
            "recent_dialogue_history": [],
            "retrieved_meta_rules": [],
            "scene_tension_cd": 0,
        }
        self.runner.graph.update_state(self.runner.config(project_id), updates, as_node="george_martin")
        graph_state = self.runner.run_phase_three(project_id)
        if not (graph_state.get("established_characters") or graph_state.get("system_character_cards")):
            raise HTTPException(status_code=500, detail="真实 Agent 未重新生成人物卡，请检查模型配置或日志。")

        updated = self.store.update(
            project_id,
            state_updates=graph_state,
            current_step=4,
            status="characters_regenerated",
        )
        self._start_benchmark_prefetch(project_id)
        return updated

    def update_characters(self, project_id: str, characters: list[CharacterItem]) -> ProjectRecord:
        updates = step4_characters_to_agent_update(characters)
        self.runner.graph.update_state(self.runner.config(project_id), updates)
        latest_graph_state = self.runner.get_state(project_id)
        merged_state = dict(latest_graph_state)
        merged_state.update(updates)
        return self.store.update(
            project_id,
            state_updates=merged_state,
            current_step=4,
            status="characters_updated",
        )

    def generate_benchmarks(self, project_id: str) -> ProjectRecord:
        record = self.get_project(project_id)
        latest_graph_state = self.runner.get_state(project_id)
        merged = latest_graph_state or record.state
        if not (merged.get("established_characters") or merged.get("system_character_cards")):
            raise HTTPException(status_code=400, detail="请先完成人物卡生成，再生成爆款对标。")
        if not merged.get("market_trend_benchmarks"):
            if self._is_benchmark_prefetching(project_id):
                merged = self._wait_for_prefetched_benchmarks(project_id)
            else:
                merged = self.runner.run_phase_three(project_id)
        if not merged.get("market_trend_benchmarks"):
            raise HTTPException(status_code=400, detail="真实 Agent 尚未产出爆款对标结果。")

        updated = self.store.update(
            project_id,
            state_updates=merged,
            current_step=5,
            status="benchmarks_generated",
        )
        self._start_script_prefetch(project_id, delay_seconds=1.5)
        return updated

    def generate_script(self, project_id: str) -> ProjectRecord:
        record = self.get_project(project_id)
        latest_graph_state = self.runner.get_state(project_id)
        merged = latest_graph_state or record.state
        if not merged.get("market_trend_benchmarks"):
            raise HTTPException(status_code=400, detail="请先完成爆款对标分析，再生成完整剧本。")
        if not merged.get("draft_output"):
            merged = self.runner.run_phase_four(project_id)
        if not merged.get("draft_output"):
            raise HTTPException(status_code=400, detail="真实 Agent 尚未生成剧本。")

        return self.store.update(
            project_id,
            state_updates=merged,
            current_step=6,
            status="script_generated",
        )

    def regenerate_script(self, project_id: str) -> ProjectRecord:
        current_state = self.runner.get_state(project_id) or self.get_project(project_id).state
        if not current_state.get("market_trend_benchmarks"):
            raise HTTPException(status_code=400, detail="请先完成爆款对标分析，再重新生成剧本。")

        updates = {
            "next_agent_role": None,
            "next_framework_id": None,
            "mutation_drift": None,
            "draft_output": "",
            "qc_retry_count": 0,
            "qc_pass": False,
            "hook_pass": False,
            "aesthetic_pass": False,
            "qc_feedback_history": [],
            "current_status_book": {},
            "rolling_summary": "",
            "recent_dialogue_history": [],
            "retrieved_meta_rules": [],
            "scene_tension_cd": 0,
        }
        self.runner.graph.update_state(self.runner.config(project_id), updates, as_node="market_spy")
        merged = self.runner.run_phase_four(project_id)
        if not merged.get("draft_output"):
            raise HTTPException(status_code=500, detail="真实 Agent 未重新生成剧本，请检查模型配置或日志。")

        return self.store.update(
            project_id,
            state_updates=merged,
            current_step=6,
            status="script_regenerated",
        )

    def _start_script_prefetch(self, project_id: str, *, delay_seconds: float = 0.0) -> None:
        with self._prefetch_lock:
            if project_id in self._prefetching_projects:
                return
            self._prefetching_projects.add(project_id)

        worker = Thread(
            target=self._prefetch_script_worker,
            args=(project_id, delay_seconds),
            daemon=True,
            name=f"script-prefetch-{project_id}",
        )
        worker.start()

    def _is_benchmark_prefetching(self, project_id: str) -> bool:
        with self._prefetch_lock:
            return project_id in self._benchmark_prefetching_projects

    def _wait_for_prefetched_benchmarks(self, project_id: str, *, timeout_seconds: float = 180.0) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            latest_graph_state = self.runner.get_state(project_id)
            if latest_graph_state.get("market_trend_benchmarks"):
                return latest_graph_state

            record = self.store.get(project_id)
            if record and record.state.get("market_trend_benchmarks"):
                return record.state

            if not self._is_benchmark_prefetching(project_id):
                break
            time.sleep(0.5)

        return self.runner.get_state(project_id) or self.get_project(project_id).state

    def _start_benchmark_prefetch(self, project_id: str) -> None:
        with self._prefetch_lock:
            if project_id in self._benchmark_prefetching_projects:
                return
            self._benchmark_prefetching_projects.add(project_id)

        worker = Thread(
            target=self._prefetch_benchmark_worker,
            args=(project_id,),
            daemon=True,
            name=f"benchmark-prefetch-{project_id}",
        )
        worker.start()

    def _prefetch_benchmark_worker(self, project_id: str) -> None:
        try:
            latest_graph_state = self.runner.get_state(project_id)
            if latest_graph_state.get("market_trend_benchmarks"):
                self._start_script_prefetch(project_id, delay_seconds=1.5)
                return

            if not (latest_graph_state.get("established_characters") or latest_graph_state.get("system_character_cards")):
                return

            merged = self.runner.run_phase_three(project_id)
            if merged.get("market_trend_benchmarks"):
                self.store.update(
                    project_id,
                    state_updates=merged,
                    current_step=4,
                    status="benchmarks_prefetched",
                )
                self._start_script_prefetch(project_id, delay_seconds=1.5)
        except Exception as exc:
            print(f"[Agent API] 后台预生成爆款对标失败({project_id}): {exc}")
        finally:
            with self._prefetch_lock:
                self._benchmark_prefetching_projects.discard(project_id)

    def _prefetch_script_worker(self, project_id: str, delay_seconds: float = 0.0) -> None:
        try:
            if delay_seconds > 0:
                time.sleep(delay_seconds)

            latest_graph_state = self.runner.get_state(project_id)
            if latest_graph_state.get("draft_output"):
                return

            merged = self.runner.run_phase_four(project_id)
            if merged.get("draft_output"):
                self.store.update(
                    project_id,
                    state_updates=merged,
                    current_step=6,
                    status="script_prefetched",
                )
        except Exception as exc:
            print(f"[Agent API] 后台预生成剧本失败({project_id}): {exc}")
        finally:
            with self._prefetch_lock:
                self._prefetching_projects.discard(project_id)

    def build_state_view(self, record: ProjectRecord) -> dict[str, Any]:
        step2 = agent_state_to_step2_view_model(record.state).to_dict()
        step4 = agent_state_to_step4_view_model(record.state).to_dict()
        return {
            "projectId": record.project_id,
            "currentStep": record.current_step,
            "status": record.status,
            "step1": {
                "projectName": record.state.get("thread_id", ""),
                "coreIdea": record.state.get("current_task", ""),
                "commercialDirective": record.state.get("commercial_directive", ""),
                "storyBibleInput": record.state.get("story_bible", ""),
            },
            "step2": step2,
            "step3": {
                "worldOutline": record.state.get("story_bible", ""),
                "societalDeadlocks": record.state.get("societal_deadlocks"),
                "traumaProfiles": record.state.get("trauma_profiles"),
                "selectedCommercialPlan": record.state.get("selected_commercial_plan", ""),
            },
            "step4": step4,
            "step5": {
                "benchmarkCases": record.state.get("market_trend_benchmarks", ""),
            },
            "step6": {
                "scriptText": record.state.get("draft_output", ""),
                "rollingSummary": record.state.get("rolling_summary", ""),
                "statusBook": record.state.get("current_status_book", {}),
            },
            "rawState": record.state,
        }

    def _infer_step(self, state: dict[str, Any]) -> int:
        if state.get("draft_output"):
            return 6
        if state.get("market_trend_benchmarks"):
            return 5
        if state.get("established_characters") or state.get("system_character_cards"):
            return 4
        if state.get("story_bible"):
            return 3
        if state.get("pmf_pitch_options"):
            return 2
        return 1

    def _build_fresh_project_state(self, form: Step1Form) -> dict[str, Any]:
        state = dict(PIPELINE_RESET_STATE)
        state.update(build_initial_agent_state(form))
        return state
