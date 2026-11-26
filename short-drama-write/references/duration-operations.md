# 时长估算与索引


用户问时长，或项目已接受节奏档案、需要核对 VO 占比时，才把索引写入系统临时目录。先用 Python 查询跨平台临时目录，把第一条命令打印的完整
路径原样替换进后两条命令的引号内。以下每条都是一行完整命令，不依赖 shell 变量或续行符；Windows
没有 `python3` 命令时使用 `py -3`。`--speaker` 的示例值必须替换为本集实际说话者。
项目配置存在时，可在第三条命令末尾加 `--project short-drama.json`。只有
`duration_estimate.py` 接受这个参数，第二条索引命令不接受：

```text
python3 -c "from pathlib import Path; import tempfile, uuid; print(Path(tempfile.gettempdir()) / ('short-drama-' + uuid.uuid4().hex + '.jsonl'))"
python3 "{技能目录}/scripts/screenplay_index.py" "剧集/EP001/剧本.md" --output "粘贴第一条命令输出的完整路径" --speaker "本集角色一" --speaker "本集角色二"
python3 "{技能目录}/scripts/duration_estimate.py" "剧集/EP001/剧本.md" --index "粘贴第一条命令输出的完整路径"
```

**改稿后重跑**：第二条命令写过一次的输出路径不能直接再写一次，会以 `already holds an index` 失败。
要保留原有块 ID，改稿前先保存旧剧本快照，重跑第二条命令时同时加
`--previous-index <同一路径>` 和 `--previous-source <旧剧本快照路径>`。没有旧快照或要从头重编号时，
加 `--no-previous`，也可以回到第一条命令另取一个临时路径。

估时前区分计数口径：`dialogue_characters` 包含标点，用于 `[VO]` 占比；`voiced_characters` 去掉标点，
脚本按它和语速换算秒数。数字和缩写仍按实际读法另行估计，不把两个计数混用。
项目已接受节奏档案、上限有效且本集有台词时，输出增加 `vo_share`：`[VO]` 字数占全部台词字数的比例、档案上限，以及是否超过。`[OS]` 计入全部台词，不计入 `[VO]`。
`[画面文字]`、`[SFX]`、`[转场]` 占用画面时间，但不在秒数里，输出的 `untimed` 列出它们的行数。
项目在 `format.pacing` 里另声明了 `on_screen_text_characters_per_second`（观众每秒读几个字）时，
`[画面文字]` 标签后的全部文字（含载体名）按它计入秒数（`on_screen_text_seconds`）。唱段按说话语速计时，实际通常更长。
画面文字多、唱段长的集，估算明显低于成片，要按这几项另加读字和停留时间再对照目标。

估算是参考，不是门禁；没有语速或动作段速率时只报告可数事实，不猜秒数。但任务已给目标时长时，
写作者仍须用真实朗读和动作通读判断能否容纳，并直接压缩重复节拍。

