# 章节索引与续跑操作

### S0 章节索引

各阶段共用 [章节索引脚本](../scripts/novel_index.py) 建立的章节边界，不各自重新切片。

```bash
python3 {技能目录}/scripts/novel_index.py index 输入/{原文文件} \
  --out 项目开发/source-analysis/_work/_index.next.json
python3 {技能目录}/scripts/novel_index.py verify \
  项目开发/source-analysis/_work/_index.next.json 输入/{原文文件}
# 项目工具可用时可选：
python3 {core 技能目录}/scripts/project_tool.py publish {项目根} \
  --owner short-drama-novel-analyze --artifact-id source-analysis:index \
  --output 项目开发/source-analysis/_index.json=项目开发/source-analysis/_work/_index.next.json \
  --input 输入/{原文文件}
```

独立运行时，将验证通过的 `_work/_index.next.json` 原子替换到正式的 `_index.json`，再进入 S1；不依赖可选的 core 发布命令。

脚本识别阿拉伯数字与中文数字章号（含 千 / 两，覆盖千章以上连载），**只认一种编号单位**
（章/回/节里出现最多的那个，其余记进 `ignored_heading_units`），只把**短的独立行**当标题
（以章号开头的正文段落记进 `long_heading_lines_skipped`），剔除开头的目录块，
按卷分段校验编号。它**不做编辑判断**——哪章重要、
讲了什么，是后面阶段的事。

`problems` 非空就停下报告，不要带着错表进 S1。常见四种：章号跳号（缺章或抓错标题）、
同卷内重号、正文极少的章（多半抓到了目录残留或卷首页）、无法解析的章号。
另外确认三个计数：`chapter_unit` 与 `ignored_heading_units`——一本用 `第N章` 分章、
用 `第N节` 分小节的书应当看到 `chapter_unit: 章` 且 `节` 被记入忽略计数，反过来说明分章单位
判断错了；`long_heading_lines_skipped` 明显偏大时，多半是这本书的章节标题确实很长，
需要与创作者确认后手写边界。

原文本身没有章节标题时索引会返回空表，此时与创作者确认按什么切分，把边界写进
`_work/_index.next.json`，通过 `verify` 后再按上面的公开生命周期发布——手写的行也要带齐
`sequence` / `line_start` / `line_end`，`verify` 会逐行检查并报出缺字段的行。

改了原文必须重建索引，不能沿用旧 span。`verify` 核对编号、顺序与行号覆盖，所以插行删行会被报出来；
但同行数的原地改写不会——那一步靠改原文的人自己重建，套件不比对字节。

```bash
python3 {技能目录}/scripts/novel_index.py verify \
  项目开发/source-analysis/_index.json 输入/{原文文件}
```
