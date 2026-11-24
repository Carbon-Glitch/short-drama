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

新项目沿同一入口打开 OpenFilm 导演台。传项目根目录，按集切换；只有剧本或外部素材也能监测，不会因浏览创建剪辑稿。已有剪辑工程可从导演台进入原生时间线。用法、阶段暂停和跨 Agent 回执见[导演台](director-desk.md)。

    python scripts/dashboard_server.py --workspace <本机项目根> --open

省略 --open 时登记后台监测。旧文档台仍可传 --legacy；--status 和 --stop 用于旧文档台进程，不关闭共享的 OpenFilm Studio。

## 导出与交付

```bash
python3 {技能目录}/scripts/project_tool.py export <project> --out <项目外目录>
```

`export` 是当前状态快照，不声称审查或创作者接受；正式审批证据仍走 `package`/`verify`。导出排除输入、
交付目录和 `.short-drama/`，输出 manifest 与校验文件；目标目录必须在项目外。

生产保留预览与有效授权记录，按持续授权推进；范围或成本实质变化再确认。归档只复制用户点名的当前文档和成品，不补造审批、
哈希、隐藏状态或第二套内容。
