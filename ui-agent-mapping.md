# UI 与 Agent 变量映射

## 1. 目的

这份文档用于定义：

- 前端页面字段怎么命名
- 前端提交时使用什么 payload 字段
- payload 最终映射到哪个 `AgentState` 字段
- 哪些字段是 `UI -> Agent`
- 哪些字段是 `Agent -> UI`
- 哪些字段允许人工修改后回写

这份文档的作用是作为后续“页面和 Agent 联动”的中间协议层，避免前端字段直接硬绑 `AgentState`。

---

## 2. 页面步骤总览

当前前端界面共 6 步：

1. 项目基础输入
2. 商业方案设计
3. 世界观推演
4. 人物卡生成
5. 爆款对标解析
6. 完整剧本生成

---

## 3. 映射原则

### 3.1 不建议前端直接绑定 AgentState

推荐链路：

`UI 字段 -> payload -> AgentState`

说明：

- `UI 字段`：服务页面交互
- `payload`：服务前后端接口
- `AgentState`：服务 LangGraph / Agent 工作流

---

### 3.2 字段方向定义

- `UI -> Agent`
  - 由用户在页面输入，提交到 Agent

- `Agent -> UI`
  - 由 Agent 生成后回填页面

- `UI <-> Agent`
  - 页面展示 Agent 结果，同时允许用户修改并写回

---

### 3.3 当前建议

- 第 1 页以 `UI -> Agent` 为主
- 第 2 页为用户确认后写入 Agent
- 第 3 页和第 5 页默认先做 `Agent -> UI`
- 第 4 页支持人工编辑已有角色后回写
- 第 6 页默认以 `Agent -> UI` 为主

---

## 4. 字段映射总表

| 页面步骤 | UI 字段名 | payload 字段名 | AgentState 字段名 | 方向 | 必填 | 备注 |
|---|---|---|---|---|---|---|
| 项目输入 | `projectName` | `project_id` | `thread_id` | UI -> Agent | 是 | 作为项目唯一标识 |
| 项目输入 | `coreIdea` | `current_task` | `current_task` | UI -> Agent | 是 | 当集核心动作 / 灵感 |
| 项目输入 | `commercialDirective` | `commercial_directive` | `commercial_directive` | UI -> Agent | 否 | 商业方向锁定，允许为空 |
| 项目输入 | `storyBibleInput` | `story_bible` | `story_bible` | UI -> Agent | 否 | 初始化世界观法则，允许为空 |
| 商业方案 | `selectedProposalId` | `selected_proposal_id` | 无直接对应 | UI -> Agent | 是 | 仅供前端记录选中卡片 |
| 商业方案 | `selectedProposalText` | `selected_commercial_plan` | `selected_commercial_plan` | UI -> Agent | 是 | 用户最终拍板内容 |
| 商业方案 | `proposalOptions` | `pmf_pitch_options` | `pmf_pitch_options` | Agent -> UI | 否 | 三套商业方案原文 |
| 商业方案 | `proposalFeedback` | `wang_jing_feedback` | `wang_jing_feedback` | UI -> Agent | 否 | 打回重做时使用 |
| 商业方案 | `proposalRejected` | `wang_jing_rejected` | `wang_jing_rejected` | UI -> Agent | 否 | 是否打回 |
| 世界观推演 | `worldOutline` | `story_bible` | `story_bible` | UI <-> Agent | 否 | 默认回显，可选允许人工修改 |
| 世界观推演 | `societalDeadlocks` | `societal_deadlocks` | `societal_deadlocks` | Agent -> UI | 否 | 学术沙盘产出 |
| 世界观推演 | `traumaProfiles` | `trauma_profiles` | `trauma_profiles` | Agent -> UI | 否 | 人物创伤 / 陷阱模型 |
| 人物卡 | `characters` | `established_characters` | `established_characters` | UI <-> Agent | 否 | 结构化角色列表，当前页面按“不可变 DNA + 服装矩阵”展示并支持编辑后回写 |
| 人物卡 | `characterCardsText` | `system_character_cards` | `system_character_cards` | Agent -> UI | 否 | Agent 原始文本版设定，当前页面不直接展示，建议保留给归档 / 调试 |
| 爆款对标 | `benchmarkCases` | `market_trend_benchmarks` | `market_trend_benchmarks` | Agent -> UI | 否 | 热门案例与策略 |
| 爆款对标 | `analysisConfirmed` | `analysis_confirmed` | 无直接对应 | UI -> Agent | 否 | 可作为前端流程控制字段 |
| 完整剧本 | `scriptText` | `draft_output` | `draft_output` | Agent -> UI | 否 | 最终剧本正文 |
| 完整剧本 | `rollingSummary` | `rolling_summary` | `rolling_summary` | Agent -> UI | 否 | 连载记忆摘要 |
| 完整剧本 | `statusBook` | `current_status_book` | `current_status_book` | Agent -> UI | 否 | 当前状态库 |

---

## 5. 分步骤详细映射

## 5.1 Step 1 项目基础输入

### 页面字段

- 项目代号 / 剧组名称
- 当集核心动作 / 灵感
- 商业指令 / 商业方向锁定
- Story Bible / 底层世界观法则

其中：

- `projectName` 必填
- `coreIdea` 必填
- `commercialDirective` 非必填
- `storyBibleInput` 非必填

### UI 字段定义

```ts
type Step1Form = {
  projectName: string
  coreIdea: string
  commercialDirective: string
  storyBibleInput: string
}
```

### 提交 payload

```json
{
  "project_id": "记忆回收站计划 01",
  "current_task": "女主发现前任通过系统篡改并回收了与她相关的所有记忆，她决定用被偷走的记忆反过来摧毁他。",
  "commercial_directive": "女性向、情绪反杀、强信息差、强记忆点，适配竖屏漫剧演示。",
  "story_bible": "近未来记忆系统已商品化，记忆可被删除、篡改、回收。任何亲密关系都可能被系统重新定义。"
}
```

### AgentState 映射

| payload | AgentState |
|---|---|
| `project_id` | `thread_id` |
| `current_task` | `current_task` |
| `commercial_directive` | `commercial_directive` |
| `story_bible` | `story_bible` |

### 备注

- 初始化时还需要补默认字段：
  - `operation_mode = "generate"`
  - `selected_commercial_plan = ""`
  - `qc_retry_count = 0`
  - `qc_pass = false`
  - `hook_pass = false`
  - `aesthetic_pass = false`
  - `qc_feedback_history = []`
  - `current_status_book = {}`
- 如果 `commercialDirective` 为空：
  - 允许 Agent 使用默认商业推演逻辑
- 如果 `storyBibleInput` 为空：
  - 允许后续世界观节点自行生成 `story_bible`

---

## 5.2 Step 2 商业方案设计

### 页面字段

- 三张方案卡
- 当前选中的方案
- 重新生成
- 返回
- 确认方案

### UI 字段定义

```ts
type ProposalCard = {
  id: "a" | "b" | "c"
  title: string
  hook: string
  highlights: string[]
  platform: string
  audience: string
}

type Step2State = {
  proposalOptions: ProposalCard[]
  selectedProposalId: "a" | "b" | "c" | null
  selectedProposalText: string
  proposalFeedback?: string
  proposalRejected?: boolean
}
```

### Agent -> UI

| AgentState | UI 字段 |
|---|---|
| `pmf_pitch_options` | `proposalOptions` |

### UI -> Agent

| UI 字段 | payload | AgentState |
|---|---|---|
| `selectedProposalText` | `selected_commercial_plan` | `selected_commercial_plan` |
| `proposalFeedback` | `wang_jing_feedback` | `wang_jing_feedback` |
| `proposalRejected` | `wang_jing_rejected` | `wang_jing_rejected` |

### 备注

- `selectedProposalId` 建议只在前端使用
- 真正写入 Agent 的建议是 `selected_commercial_plan`
- 最好把“方案摘要 + 原始提案全文”一起打包写入，避免后续节点失去上下文

---

## 5.3 Step 3 世界观推演

### 页面字段

- 世界观框架
- 主线冲突
- 全季节奏方向

### UI 字段定义

```ts
type Step3World = {
  worldOutline: string
  societalDeadlocks?: Record<string, unknown>
  traumaProfiles?: Record<string, unknown>
}
```

### Agent -> UI

| AgentState | UI 字段 |
|---|---|
| `story_bible` | `worldOutline` |
| `societal_deadlocks` | `societalDeadlocks` |
| `trauma_profiles` | `traumaProfiles` |

### 可选 UI -> Agent

如果这一步允许用户手动修改后确认，可写回：

| UI 字段 | payload | AgentState |
|---|---|---|
| `worldOutline` | `story_bible` | `story_bible` |

### 当前建议

- 第三步默认先做 `Agent -> UI`
- 如果后续开放人工微调，再把修改后的 `worldOutline` 回写

---

## 5.4 Step 4 人物卡生成

### 页面字段

- 角色列表
- 角色名称
- 发型
- 发色
- 眼睛颜色
- 显著伤痕 / 特征
- 身高比例
- 服装方案矩阵
- 服装方案 A
- 服装方案 B
- 服装方案 C
- 编辑弹窗
- 重新生成
- 返回 / 确认进入下一步

### UI 字段定义

```ts
type CharacterItem = {
  id: string
  name: string
  hairStyle: string
  hairColor: string
  eyeColor: string
  marks: string
  heightRatio: string
  outfits: string[]
}
```

### Agent -> UI

| AgentState | UI 字段 |
|---|---|
| `established_characters` | `characters` |

补充说明：

- 当前页面真正直接消费的是 `established_characters`
- `system_character_cards` 更适合作为原始文本资产保留，不建议当前 UI 直接渲染

### 结构说明

当前页面中的人物卡，已经按 Agent 的原始思路收敛为两层：

1. 不可变 DNA
- `hairStyle`
- `hairColor`
- `eyeColor`
- `marks`
- `heightRatio`

2. 服装方案矩阵
- `outfits[0]` -> 方案 A
- `outfits[1]` -> 方案 B
- `outfits[2]` -> 方案 C

这更接近 `斯坦李_角色塑造宗师` 中强调的：

- 不可变 DNA
- Wardrobe Matrix

### UI -> Agent

| UI 字段 | payload | AgentState |
|---|---|---|
| `characters` | `established_characters` | `established_characters` |

建议 payload 结构示意：

```json
{
  "established_characters": [
    {
      "id": "ellen",
      "name": "艾伦（Ellen）",
      "hairStyle": "中长黑发，线条利落，偏冷感层次",
      "hairColor": "黑色",
      "eyeColor": "冷灰蓝",
      "marks": "左耳有系统感银色耳饰，眉骨处有极淡旧伤痕",
      "heightRatio": "高挑修长，肩颈线条明显，镜头中偏强控制感比例",
      "outfits": [
        "银灰风衣，深色高领，极简系统感配饰",
        "深灰作战夹克，收束腰线，黑色长靴",
        "冷白衬衫，宽松长裤，室内裸耳造型"
      ]
    }
  ]
}
```

### 编辑弹窗字段

```ts
type CharacterEditForm = {
  name: string
  hairStyle: string
  hairColor: string
  eyeColor: string
  marks: string
  heightRatio: string
  outfitA: string
  outfitB: string
  outfitC: string
}
```

映射关系：

| 编辑字段 | CharacterItem |
|---|---|
| `name` | `name` |
| `hairStyle` | `hairStyle` |
| `hairColor` | `hairColor` |
| `eyeColor` | `eyeColor` |
| `marks` | `marks` |
| `heightRatio` | `heightRatio` |
| `outfitA` | `outfits[0]` |
| `outfitB` | `outfits[1]` |
| `outfitC` | `outfits[2]` |

### 当前建议

- 页面默认展示角色卡，并支持编辑已有角色
- 当前不支持前端新增 / 删除角色
- 编辑后的结构化角色数据建议回写到 `established_characters`
- `system_character_cards` 保留为 Agent 生成的原始文本版本
- 当前页面字段已经和 Agent 的“不可变 DNA + 多套衣橱”方向基本对齐
- 如果后续人物卡页继续保持当前版式，后端优先保证 `established_characters` 的结构稳定，不要让 UI 直接解析长文本

---

## 5.5 Step 5 爆款对标解析

### 页面字段

- 同题材热门案例
- 可复用爽点结构
- 平台传播设计

### UI 字段定义

```ts
type Step5Analysis = {
  benchmarkCases: string
  reusableHooks: string[]
  platformStrategy: string[]
  analysisConfirmed?: boolean
}
```

### Agent -> UI

| AgentState | UI 字段 |
|---|---|
| `market_trend_benchmarks` | `benchmarkCases` |

### UI -> Agent

当前建议：

- 这一步优先只做展示
- `analysisConfirmed` 可以只作为前端流程推进状态

---

## 5.6 Step 6 完整剧本生成

### 页面字段

- 剧本文本
- 复制
- 下载
- 返回

### UI 字段定义

```ts
type Step6Script = {
  scriptText: string
  rollingSummary?: string
  statusBook?: Record<string, unknown>
}
```

### Agent -> UI

| AgentState | UI 字段 |
|---|---|
| `draft_output` | `scriptText` |
| `rolling_summary` | `rollingSummary` |
| `current_status_book` | `statusBook` |

### 备注

- 如果后面要支持“继续生成下一集”
- 需要从当前页触发新的 payload：

```json
{
  "current_task": "承接上一集的结尾悬念，继续往下推进剧情，写出新的一集！",
  "target_pmf": "selected_commercial_plan",
  "hook_pass": true,
  "qc_pass": true,
  "qc_retry_count": 0
}
```

---

## 6. 页面与接口动作建议

## 6.1 Step 1 提交

建议动作：

- `POST /api/project/init`

作用：

- 创建项目
- 初始化 AgentState
- 返回项目状态

---

## 6.2 Step 2 方案生成 / 方案确认

建议动作：

- `POST /api/proposals/generate`
- `POST /api/proposals/select`
- `POST /api/proposals/regenerate`

---

## 6.3 Step 3 世界观生成

建议动作：

- `POST /api/world/generate`
- 可选 `POST /api/world/update`

---

## 6.4 Step 4 角色卡

建议动作：

- `POST /api/characters/generate`
- `POST /api/characters/update`

---

## 6.5 Step 5 爆款对标

建议动作：

- `POST /api/benchmarks/generate`

---

## 6.6 Step 6 剧本生成

建议动作：

- `POST /api/script/generate`
- `GET /api/project/:id/state`
- 可选 `POST /api/script/continue`

---

## 7. 待确认项

下面这些点建议你确认后，再进入真正联动开发：

### 7.1 世界观页是否允许用户修改后写回

如果允许：

- `worldOutline -> story_bible`

如果不允许：

- 只做展示

---

### 7.2 人物卡是否允许修改

当前建议：

- 允许编辑已有角色
- 编辑后的结构化数据写回 `established_characters`
- 不支持前端新增角色
- 不支持前端删除角色
- `system_character_cards` 作为只读原始产物保留

---

### 7.3 爆款对标页是否只展示

当前建议：

- 先只展示

---

### 7.4 商业方案页是否保存“原始三案全文”

当前建议：

- 保留
- 因为后续 Agent 很依赖商业提案上下文

---

## 8. 当前推荐落地顺序

建议开发顺序：

1. 先确认这份映射文档
2. 再补一份 API Contract 文档
3. 再开始做前端与 Agent 联调
4. 最后再优化字段命名和返回结构
