# 剪辑阶段契约

新工程以后期 film.html、VTT、镜头页和 Look 文件为当前来源；剪辑单是生成的可读报告。旧 Markdown 工程按其旧执行路径继续使用。剪辑主动重组素材、声音和视觉处理，沿既有文档与 bindings 交接影响故事或设计的变化。

## 本阶段规则

### `EDT`

| ID | Class | Knowledge |
|---|---|---|
| EDT-01 | structural_invariant | Every `CUT-...` binds one existing source item and one currently readable media file: `MOTION-...` for video, or `SHOT-...` / `IMG-...` for a still. A cut with no material source cannot exist. |
| EDT-02 | structural_invariant | Source windows and speed map to the actual timeline duration; use measured media lengths. Legacy Markdown arithmetic belongs to that legacy backend, while native still and shot-page durations follow the current film. |
| EDT-03 | structural_invariant | Editing selects and orders existing frames. It never rewrites dialogue, shot purpose, start/end state, or any upstream declared duration; a needed semantic change is reported to the owning document instead. |
| EDT-04 | reviewed_invariant | Dialogue retained in the film remains audibly complete. Picture may cut during a line if the sound remains continuous and the narrative is clear. OpenFilm supports independent sound clips, including video sound, so J/L cuts and sound bridges remain editable. |
| EDT-05 | structural_invariant | When subtitles are requested, every retained spoken line has a cue copied verbatim, including punctuation, from the screenplay into the current subtitle track. Rendering may transform punctuation for display. Transcription locates speech but does not replace the source text. |
| EDT-06 | structural_invariant | Repetition, source reuse and montage are creative choices; record their purpose and preserve the intended viewing progression. |
| EDT-07 | reviewed_invariant | Each cut's in-point and out-point land inside that material's usable band, and 取舍 names what is visible at each boundary rather than citing an abstract need for pace. |
| EDT-08 | craft_default | Check adjacent cuts for unintended visual jumps and duplicated information. Similar framing, deliberate repetition and jump cuts are valid when they serve the accepted narrative. |
| EDT-09 | craft_default | Do not mechanically redistribute trimmed time. Extend another beat only when its performance or readability benefits, and preserve explicit delivery-duration requirements. |
| EDT-10 | reviewed_invariant | Listen to joins for unintended changes in ambience or music. Use an appropriate documented audio treatment when needed; the built-in renderer does not execute prose mixing instructions. |
| EDT-11 | reviewed_invariant | Record unused shots with a reason: missing material, unusable quality, or an intentional narrative omission. |
| EDT-12 | craft_default | The delivered film is loudness-normalized to one declared target, and burned subtitles are the default for vertical short drama. |
| EDT-13 | craft_default | Distinguish a reference target from a required delivery duration. Report the gap and satisfy a fixed requirement or identify the material needed to do so. |
| EDT-14 | taste_option | Cut rhythm, whether a beat is held or clipped, and whether a moment repeats are creator choices; the suite records them and does not treat any of them as defects. |
| EDT-15 | structural_invariant | Rendering, duration match and file existence are technical outcomes. None of them may be reported as a statement about whether the film is good; quality goes to review or to the creator. |
| EDT-16 | reviewed_invariant | Compare shots within the same scene and lighting state using comparable image regions. Record corrections, then inspect the output. Whole-frame averages alone do not establish a mismatch; intentional lighting changes are valid. |
| EDT-17 | structural_invariant | After material is regenerated, re-measure the spoken spans and update its subtitle windows before rendering. The material-mtime warning is a prompt to check, not proof of alignment. |
| EDT-18 | taste_option | Choose grain and texture deliberately. In OpenFilm, execute the chosen treatment in a verified layer or source process; legacy renderer behavior applies only to its legacy projects. |
| EDT-19 | craft_default | A dialogue cut enters about 0.25 s before the line's speech onset and leaves about 0.4 s after the line ends, and lasts at least about 1.2 s. Locate these from the sounds that belong to the scripted line, so noise never stretches the cut. |
| EDT-20 | craft_default | Compare like surfaces within each scene. New OpenFilm projects store actual clip/look decisions; legacy automatic shot matching is not assumed to run in this backend. |

规则分级由高到低：`structural_invariant`（结构缺陷，阻断）、
`reviewed_invariant`（需证据判断）、`craft_default`（常用做法，可覆盖）、
`taste_option`（创作者选择，不作缺陷）。创作者已接受的事实优先于本表。

## 与上游阶段的分工

| 问题 | 归属 |
|---|---|
| 这句台词该怎么说 | `剧本.md` |
| 这一镜承担什么、起终状态是什么 | `分镜.md` |
| 这一镜怎么动、生成时说什么 | `视频提示词.md` |
| 这一段素材怎么来的、花了多少钱 | 生产运行记录 |
| **这一段素材哪几帧进成片** | **`剪辑单.md`** |
| 成片好不好看 | 审查，或创作者本人 |

生成结果与上游声明不符时，剪辑记录事实并取舍，同时把不符点名报告；不在剪辑单里修改上游声明
来让它们看起来一致。
