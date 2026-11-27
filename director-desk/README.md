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

## 创作选项

- 视觉设计：在「视觉主张与影像风格」中选本集色彩、成像与胶片风格；场面设计与地点条目选局部光色。
- 分镜：景别、机位角度、构图、焦点、透视分别选择，运镜可按顺序组合；本镜变化不覆盖默认设计。
- 图片/视频提示词：选中正文中的目标句子，再用该阶段的执行词库替换；可自由编辑预览，保留参考声明和周围模型段落。
- 上游依据：展开查看关联设计与镜头，可回来源修改。改变设计会标记关联下游待复核，已有素材不自动重生成。对齐分镜的 Agent 操作需由用户提交。

## 使用

1. 创建作品、导入剧本或导入已有项目；导入保留原目录，编辑发生在导演台副本。
2. 顶栏“规格”选择模型与画幅。按剧本 → 视觉设计 → 分镜 → 资产 → 视频制作推进，独立画布用于引用与生成条目。
3. 在“本机设置”按需连接生成服务、启用已登录的 Codex CLI。生成前检查提交预览；不自动花费生成额度。
4. 采用回片后建立初剪，进入 OpenFilm；顶部可返回导演台。剪辑需 FFmpeg/ffprobe，OpenFilm 可在“剪辑环境”准备，或用 `short-drama-edit/scripts/openfilm_bridge.py setup` 安装。

导演台默认读取仓库自带的 Skill。`DIRECTOR_SKILLS_HOME` 可显式指定另一套完整套件；只有仓库旁没有套件时才回退到 `~/.agents/skills`。供外部 Agent 发现的 Skill 仍按根 README 安装。

作品和本机配置默认存于 `~/.short-drama/director-desk`；`DIRECTOR_DESK_HOME` 可切换作品库。启动/构建日志在该目录的 `logs/`。项目备份通过界面导出；凭据和运行时不随作品导出。

已登记的外部项目支持五文档和参考素材的差异合并。未登记目录不会自动扫描。

[验证范围与限制](VALIDATION.md)。当前为源码预览，未提供安装包。

## 与本地 Agent 共用条目

`backend/cli.py entry-read` / `entry-update` 用 `--project <作品库项目目录> --entry <编号> --episode EP001` 定位条目。更新加 `--expected <读取时的项目版本>`，标准输入传 `{"fields":{"运镜":"回头时缓推"}}` 或 `{"text":"条目正文"}`。保存使用界面的版本检查、引用同步与撤销历史。

`backend/cli.py generation-prepare` 加 `--adapter <profile>`，直接准备该提示词条目；界面可继续查看并确认提交。生成准备共用套件的参考编译与正式任务记录。

独立文件项目使用同级 `short-drama/scripts/entry_tool.py` 修改条目，使用 `short-drama-produce/scripts/production_tool.py prepare-entry` 准备生成。操作细节见套件的项目操作与执行契约。
