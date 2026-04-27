# 漫剧项目云端部署说明

## 目录

部署时请把这个目录作为项目根目录：

```text
漫剧项目_修复/漫剧项目/前端界面设计
```

## 后端：Render

1. 在 GitHub 新建仓库，上传本目录。
2. Render 新建 Web Service，连接该仓库。
3. Root Directory 选择本目录。
4. Build Command:

```bash
pip install -r agent_api/requirements.txt
```

5. Start Command:

```bash
uvicorn agent_api.main:app --host 0.0.0.0 --port $PORT
```

6. 部署成功后访问：

```text
https://你的-render-app.onrender.com/health
```

看到 `{"status":"ok"}` 就表示后端可用。

## 前端：Vercel

1. Vercel 新建 Project，连接同一个仓库。
2. Root Directory 选择本目录。
3. Framework Preset 选 Other。
4. Build Command 留空。
5. Output Directory 留空。
6. 部署前修改 `config.js`：

```js
window.MANJU_API_BASE = "https://你的-render-app.onrender.com";
```

## 当前版本说明

当前后端是可运行的流程版生成服务，API Key 不在前端。后续接真实大模型时，只需要在 `agent_api/service.py` 内替换生成逻辑，并把模型 Key 放到 Render 环境变量里。
