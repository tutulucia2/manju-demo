# 漫剧剧本生成系统 Demo

这是一个面向客户演示的前端 Demo，按 6 步流程还原了漫剧项目 Agent 的核心界面：

1. 项目输入
2. 商业方案
3. 世界观推演
4. 人物卡
5. 爆款对标
6. 完整剧本生成

## 启动方式

在当前目录执行：

```bash
npm run start
```

然后打开：

```text
http://localhost:4173
```

如果 4173 端口被占用，也可以直接运行：

```bash
python3 -m http.server 8000
```

然后打开：

```text
http://localhost:8000
```

## API 骨架

当前目录还提供了一套用于后续联动 Agent 的 FastAPI 骨架，代码在：

```text
前端界面设计/agent_api/
```

建议启动方式：

```bash
python3 -m uvicorn agent_api.main:app --app-dir "/Users/a002/Documents/luciatutu/漫剧项目/前端界面设计" --reload --port 8010
```

启动后可用接口包括：

- `POST /api/project/init`
- `GET /api/project/{project_id}/state`
- `POST /api/proposals/generate`
- `POST /api/proposals/select`
- `POST /api/world/generate`
- `POST /api/characters/generate`
- `POST /api/characters/update`
- `POST /api/benchmarks/generate`
- `POST /api/script/generate`

当前这版是“可跑的骨架”：

- 已接入 `agent_mapper`
- 已支持内存态项目存储
- 已支持 demo 数据回填页面结构
- 后续只需要把 `agent_api/service.py` 里的 demo 生成逻辑替换成真实 Agent 调用
