# 项目操作、配置与交付

本页只在初始化项目、写入项目级决定、运行 Dashboard 或导出交付时读取。普通创作不加载这些运维细节。

## 初始化与项目档案

```bash
python3 {技能目录}/scripts/project_tool.py init ./my-drama --title "示例短剧"
```

用户已经明确语言、提示词语言、画幅、集数或目标时长时，首次 `init` 一并写入；未确认项保持未决定。
项目只建立配置和目录，不预建空的五份创作文档。

用户在会话中点名目标视频模型，而 `production_profile` 仍为 `unset` 时，先把模型、方言、原生时长、
参考方式和正文语言写入档案，再继续下游。生产档案只接受 `accepted` 或 `unset`；详细的发布、接受和
`set-authority` 命令见项目工具帮助和本技能历史示例。

节奏档案写入 `creator_authority.rhythm_profile`，只在创作者接受后供下游算术核对。缺失或未接受时不核对；
不要把套件默认数值当成跨项目门槛。

## 创作台与旧 Dashboard

新项目默认打开 OpenFilm 短剧创作台；多集时传 `--episode EP001` 选本次处理的集。已有 film.html 的集也可直接用剪辑技能的 `edit_tool.py open`。原文档台以 `--legacy` 显式打开，生产仍走现有 helper。

```bash
python3 {技能目录}/scripts/dashboard_server.py --workspace <workspace> --port 0 --detach --open
python3 {技能目录}/scripts/dashboard_server.py --workspace <workspace> --status
python3 {技能目录}/scripts/dashboard_server.py --workspace <workspace> --stop
```

Dashboard 展示剧本、视觉设定、分镜、提示词、成片和审查；它只读取文档中的真实绑定，不按文件名猜图片，
不负责工作流编排和媒体生产。没有绑定就显示空位。

## 导出与交付

```bash
python3 {技能目录}/scripts/project_tool.py export <project> --out <项目外目录>
```

`export` 是当前状态快照，不声称审查或创作者接受；正式审批证据仍走 `package`/`verify`。导出排除输入、
交付目录和 `.short-drama/`，输出 manifest 与校验文件；目标目录必须在项目外。

外部生产始终遵守 `preview -> explicit confirm -> run`。归档只复制用户点名的当前文档和成品，不补造审批、
哈希、隐藏状态或第二套内容。
