from __future__ import annotations

from fastapi import HTTPException

from agent_mapper import CharacterItem, Step1Form, build_initial_agent_state, step4_characters_to_agent_update

from .store import InMemoryProjectStore, ProjectRecord


class AgentDemoService:
    """Safe public backend for the resume demo.

    This service intentionally does not import the private writer-room engine,
    internal prompts, or real customer data. It preserves the product workflow
    shape so the online demo can run safely from a public repository.
    """

    def __init__(self, store: InMemoryProjectStore) -> None:
        self.store = store

    def init_project(self, form: Step1Form) -> ProjectRecord:
        project_id = form.project_name.strip()
        state = build_initial_agent_state(form)
        state.update(
            {
                "project_id": project_id,
                "safe_backend_mode": True,
                "proposal_options": [],
                "characters": [],
            }
        )

        existing_record = self.store.get(project_id)
        if existing_record:
            return self.store.update(project_id, state_updates=state, current_step=1, status="initialized")
        return self.store.create(project_id, state)

    def get_project(self, project_id: str) -> ProjectRecord:
        record = self.store.get(project_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")
        return record

    def generate_proposals(self, project_id: str) -> ProjectRecord:
        record = self.get_project(project_id)
        state = dict(record.state)
        proposals = self._build_proposals(state)
        return self.store.update(
            project_id,
            state_updates={
                "proposal_options": proposals,
                "pmf_pitch_options": "\n\n".join(item["raw_text"] for item in proposals),
            },
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
            raise HTTPException(status_code=400, detail="Please select a proposal to continue.")

        record = self.get_project(project_id)
        state = dict(record.state)
        selected = selected_proposal_text.strip() or self._first_proposal_text(state)
        world = self._build_world(state, selected)
        characters = self._build_characters(state, selected)
        return self.store.update(
            project_id,
            state_updates={
                "selected_commercial_plan": selected,
                "wang_jing_feedback": proposal_feedback.strip(),
                "story_bible": world,
                "societal_deadlocks": [
                    "平台内容同质化导致前三秒留存变低",
                    "角色动机弱会让爽点只剩情节堆叠",
                    "视觉设定缺少统一资产规范会拉高制作返工",
                ],
                "trauma_profiles": [
                    "主角的核心创伤来自一次公开误判",
                    "反派的控制欲来自对失控局面的长期恐惧",
                    "搭档角色负责把理性目标拉回情感选择",
                ],
                "characters": characters,
                "established_characters": characters,
                "system_character_cards": self._characters_to_text(characters),
                "market_trend_benchmarks": "",
                "draft_output": "",
            },
            current_step=3,
            status="world_ready",
        )

    def generate_world(self, project_id: str) -> ProjectRecord:
        record = self.get_project(project_id)
        selected = record.state.get("selected_commercial_plan") or self._first_proposal_text(record.state)
        return self.store.update(
            project_id,
            state_updates={"story_bible": self._build_world(record.state, selected)},
            current_step=3,
            status="world_generated",
        )

    def generate_characters(self, project_id: str) -> ProjectRecord:
        record = self.get_project(project_id)
        selected = record.state.get("selected_commercial_plan") or self._first_proposal_text(record.state)
        characters = record.state.get("characters") or self._build_characters(record.state, selected)
        return self.store.update(
            project_id,
            state_updates={
                "characters": characters,
                "established_characters": characters,
                "system_character_cards": self._characters_to_text(characters),
            },
            current_step=4,
            status="characters_generated",
        )

    def regenerate_characters(self, project_id: str) -> ProjectRecord:
        record = self.get_project(project_id)
        characters = self._build_characters(record.state, record.state.get("selected_commercial_plan", ""), variant=True)
        return self.store.update(
            project_id,
            state_updates={
                "characters": characters,
                "established_characters": characters,
                "system_character_cards": self._characters_to_text(characters),
                "market_trend_benchmarks": "",
                "draft_output": "",
            },
            current_step=4,
            status="characters_regenerated",
        )

    def update_characters(self, project_id: str, characters: list[CharacterItem]) -> ProjectRecord:
        updates = step4_characters_to_agent_update(characters)
        normalized = updates.get("established_characters", [])
        return self.store.update(
            project_id,
            state_updates={
                "characters": normalized,
                "established_characters": normalized,
                "system_character_cards": self._characters_to_text(normalized),
            },
            current_step=4,
            status="characters_updated",
        )

    def generate_benchmarks(self, project_id: str) -> ProjectRecord:
        record = self.get_project(project_id)
        benchmarks = self._build_benchmarks(record.state)
        return self.store.update(
            project_id,
            state_updates={"market_trend_benchmarks": benchmarks},
            current_step=5,
            status="benchmarks_generated",
        )

    def generate_script(self, project_id: str) -> ProjectRecord:
        record = self.get_project(project_id)
        if not record.state.get("market_trend_benchmarks"):
            record = self.generate_benchmarks(project_id)
        script = self._build_script(record.state)
        return self.store.update(
            project_id,
            state_updates={
                "draft_output": script,
                "rolling_summary": "已完成商业方案、世界观、角色卡、爆款对标与第一集剧本初稿生成。",
                "current_status_book": {
                    "mode": "safe_public_backend",
                    "privacy": "no private prompts or customer data exposed",
                    "next": "replace generator methods with an LLM adapter when API keys are configured",
                },
            },
            current_step=6,
            status="script_generated",
        )

    def regenerate_script(self, project_id: str) -> ProjectRecord:
        return self.generate_script(project_id)

    def build_state_view(self, record: ProjectRecord) -> dict:
        state = record.state
        return {
            "projectId": record.project_id,
            "currentStep": record.current_step,
            "status": record.status,
            "step1": {
                "projectName": state.get("thread_id", ""),
                "coreIdea": state.get("current_task", ""),
                "commercialDirective": state.get("commercial_directive", ""),
                "storyBibleInput": state.get("established_bible", ""),
            },
            "step2": {
                "proposal_options": state.get("proposal_options", []),
                "selected_proposal_text": state.get("selected_commercial_plan", ""),
                "selected_proposal_id": self._selected_proposal_id(state),
                "raw_pitch_text": state.get("pmf_pitch_options", ""),
            },
            "step3": {
                "worldOutline": state.get("story_bible", ""),
                "societalDeadlocks": state.get("societal_deadlocks"),
                "traumaProfiles": state.get("trauma_profiles"),
                "selectedCommercialPlan": state.get("selected_commercial_plan", ""),
            },
            "step4": {
                "characters": state.get("characters") or state.get("established_characters") or [],
                "raw_character_cards_text": state.get("system_character_cards", ""),
            },
            "step5": {
                "benchmarkCases": state.get("market_trend_benchmarks", ""),
            },
            "step6": {
                "scriptText": state.get("draft_output", ""),
                "rollingSummary": state.get("rolling_summary", ""),
                "statusBook": state.get("current_status_book", {}),
            },
            "rawState": {
                "safe_backend_mode": True,
                "status": state.get("status", record.status),
            },
        }

    def _build_proposals(self, state: dict) -> list[dict]:
        project = state.get("thread_id", "未命名项目")
        idea = state.get("current_task", "一个高概念漫剧创意")
        directive = state.get("commercial_directive") or "竖屏漫剧，强钩子，高反转，适合面试演示"
        templates = [
            (
                "a",
                "误判重启局",
                "主角被系统性误判后，用一次次反转把对手拖进自己设计的局。",
                ["前三秒冤屈钩子", "中段身份反转", "结尾强悬念", "角色资产可复用"],
                "抖音 / 快手竖屏短剧",
                "偏爱强爽点、快节奏反转的泛女性与都市情绪受众",
            ),
            (
                "b",
                "黑箱共谋者",
                "所有人都以为主角在查真相，其实她在训练一个能反噬资本的叙事黑箱。",
                ["悬疑感", "高智感", "职场压迫", "视觉符号统一"],
                "B站 / 小红书剧情向漫剧",
                "喜欢赛博悬疑、女性成长和高概念设定的年轻受众",
            ),
            (
                "c",
                "替身协议",
                "主角发现自己只是爆款叙事里的替身，于是反过来篡改整套人设规则。",
                ["替身文学", "情感背叛", "规则反杀", "连续剧集扩展性强"],
                "微信视频号 / 付费短剧",
                "偏好情感冲突、身份错位和连续付费追更的人群",
            ),
        ]

        proposals = []
        for proposal_id, title, hook, highlights, platform, audience in templates:
            raw_text = (
                f"方案 {proposal_id.upper()}：《{title}》\n"
                f"项目：{project}\n"
                f"创意 Brief：{idea}\n"
                f"商业指令：{directive}\n"
                f"一句话梗概：{hook}\n"
                f"核心爽点：{'、'.join(highlights)}\n"
                f"平台适配：{platform}\n"
                f"受众定位：{audience}"
            )
            proposals.append(
                {
                    "id": proposal_id,
                    "title": title,
                    "hook": hook,
                    "highlights": highlights,
                    "platform": platform,
                    "audience": audience,
                    "raw_text": raw_text,
                }
            )
        return proposals

    def _build_world(self, state: dict, selected: str) -> str:
        project = state.get("thread_id", "未命名项目")
        idea = state.get("current_task", "一个高概念漫剧创意")
        return (
            f"【世界观框架】\n"
            f"{project} 发生在一个内容平台、资本评审和个人命运被算法紧密绑定的近未来都市。\n\n"
            f"【核心命题】\n"
            f"{idea}\n\n"
            f"【已选商业方案】\n"
            f"{selected or '主角在强压环境里完成身份反杀，并把个人创伤转化成可连续推进的剧集动力。'}\n\n"
            f"【剧集推进规则】\n"
            f"- 每集开头必须有一个视觉钩子或误判场面。\n"
            f"- 每集结尾留下一个新的身份、关系或规则反转。\n"
            f"- 角色造型、色彩和道具服务于可复用的漫剧资产生产。"
        )

    def _build_characters(self, state: dict, selected: str, *, variant: bool = False) -> list[dict]:
        accent = "银灰" if not variant else "暗红"
        return [
            {
                "id": "lead",
                "name": "林照",
                "hairStyle": "利落中短发，镜头中保持冷静轮廓",
                "hairColor": "黑色",
                "eyeColor": "深棕",
                "marks": f"左耳有{accent}色耳饰，象征她对系统规则的反向监听",
                "heightRatio": "偏高挑，肩颈线干净，适合强控制感构图",
                "outfits": ["深色长风衣 + 高领内搭", "白衬衫 + 黑色束腰马甲", "功能感短外套 + 数据终端"],
            },
            {
                "id": "rival",
                "name": "沈既白",
                "hairStyle": "后梳短发，边缘整洁",
                "hairColor": "深栗",
                "eyeColor": "冷灰",
                "marks": "右手无名指有旧戒痕，暗示被隐藏的盟约",
                "heightRatio": "高瘦，正装线条强，压迫感明显",
                "outfits": ["深灰西装 + 黑金镜框", "长款大衣 + 皮质手套", "无领黑衬衫 + 银色袖扣"],
            },
            {
                "id": "ally",
                "name": "阮秋",
                "hairStyle": "微卷短发，行动感强",
                "hairColor": "棕黑",
                "eyeColor": "琥珀",
                "marks": "手腕有数据纹身，负责把线索变成可执行策略",
                "heightRatio": "中等偏高，动作轻快，适合信息流镜头",
                "outfits": ["机能夹克 + 便携终端", "实验室工装外套", "连帽卫衣 + 数据挂件"],
            },
        ]

    def _build_benchmarks(self, state: dict) -> str:
        return (
            "【爆款对标】\n"
            "- 情绪入口：开场制造冤屈、背叛或身份错位，保证观众快速站队。\n"
            "- 剧集结构：每集 3 个信息点，1 个反转点，1 个付费/追更钩子。\n"
            "- 视觉资产：主角耳饰、反派戒痕、搭档数据纹身作为连续识别符号。\n\n"
            "【质检改写方向】\n"
            "- 删除解释性台词，改成动作和视觉证据。\n"
            "- 每场戏只保留一个主冲突，避免信息过载。\n"
            "- 结尾必须推进关系变化，而不是只抛设定。"
        )

    def _build_script(self, state: dict) -> str:
        project = state.get("thread_id", "未命名项目")
        idea = state.get("current_task", "一个高概念漫剧创意")
        return (
            f"# {project} 第一集：被系统误判的人\n\n"
            f"## 开场钩子\n"
            f"雨夜，林照站在巨大的平台审判屏前。屏幕弹出结论：她的创意被判定为剽窃。\n"
            f"人群开始拍摄，热搜倒计时只剩 10 秒。\n\n"
            f"## 第一场：公开处刑\n"
            f"主持人要求林照当场道歉。林照没有辩解，只盯着屏幕角落一串异常编号。\n"
            f"她低声说：这不是审判，这是提前写好的剧本。\n\n"
            f"## 第二场：暗线盟友\n"
            f"阮秋把一枚数据终端塞进她手里，终端显示：同样的误判在 72 小时内发生了 19 次。\n"
            f"林照意识到，自己不是唯一的受害者，而是被选中的样本。\n\n"
            f"## 第三场：反派入局\n"
            f"沈既白出现，替平台给出和解条件：签字，消失，保留体面。\n"
            f"林照看见他右手的戒痕，确认他和旧案有关。\n\n"
            f"## 结尾反转\n"
            f"林照点击终端，审判屏突然倒放。所有证据指向另一个名字：沈既白。\n"
            f"屏幕黑掉前，只剩一句话：真正的剧本，现在开始。\n\n"
            f"## 本集创意来源\n"
            f"{idea}"
        )

    def _characters_to_text(self, characters: list[dict]) -> str:
        return "\n\n".join(
            f"角色：{item.get('name')}\n"
            f"发型：{item.get('hairStyle')}\n"
            f"发色：{item.get('hairColor')}\n"
            f"瞳色：{item.get('eyeColor')}\n"
            f"特征：{item.get('marks')}\n"
            f"服装：{' / '.join(item.get('outfits', []))}"
            for item in characters
        )

    def _first_proposal_text(self, state: dict) -> str:
        proposals = state.get("proposal_options") or []
        if proposals:
            return proposals[0].get("raw_text", "")
        return ""

    def _selected_proposal_id(self, state: dict) -> str | None:
        selected = state.get("selected_commercial_plan", "")
        for proposal in state.get("proposal_options", []):
            if selected == proposal.get("raw_text") or proposal.get("title", "") in selected:
                return proposal.get("id")
        return None
