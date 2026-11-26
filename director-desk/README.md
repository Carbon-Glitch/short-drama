# 短剧导演台

与 Agent 共用作品，在浏览器中编辑剧本、视觉设定、分镜、图片/视频提示词，组织参考素材、选片，并进入 OpenFilm 剪辑。默认文本分镜＋全能参考，首尾帧按需选择。

## 从源码启动

保留完整仓库及同级 `short-drama*` 目录。基础依赖：Python 3.11+（含 tkinter）、Node.js 22.12+、npm。

Windows 双击 `Start-Director-Desk.cmd`。首次启动自动执行 `npm ci` 和前端构建，需要联网；后续启动复用界面。端口自动分配，浏览器自动打开。也可从仓库根目录手动运行：

```powershell
npm --prefix director-desk/web ci
npm --prefix director-desk/web run build
python -X utf8 director-desk/backend/server.py --port 4768
```

浏览器打开 `http://127.0.0.1:4768`。需要改变监听端口可修改 `--port`。

## 使用

1. 创建作品、导入剧本或导入已有项目；导入保留原目录，编辑发生在导演台副本。
2. 顶栏“规格”选择模型与画幅。按剧本 → 视觉设计 → 分镜 → 资产 → 视频制作推进，独立画布用于引用与生成条目。
3. 在“本机设置”按需连接生成服务、启用已登录的 Codex CLI。生成前检查提交预览；不自动花费生成额度。
4. 采用回片后建立初剪，进入 OpenFilm；顶部可返回导演台。剪辑需 FFmpeg/ffprobe，OpenFilm 可在“剪辑环境”准备，或用 `short-drama-edit/scripts/openfilm_bridge.py setup` 安装。

导演台默认读取仓库自带的 Skill。`DIRECTOR_SKILLS_HOME` 可显式指定另一套完整套件；只有仓库旁没有套件时才回退到 `~/.agents/skills`。供外部 Agent 发现的 Skill 仍按根 README 安装。

作品和本机配置默认存于 `~/.short-drama/director-desk`；`DIRECTOR_DESK_HOME` 可切换作品库。启动/构建日志在该目录的 `logs/`。项目备份通过界面导出；凭据和运行时不随作品导出。

已登记的外部项目支持五文档和参考素材的差异合并。未登记目录不会自动扫描。

[验证范围与限制](VALIDATION.md)。当前为源码预览，未提供安装包。
