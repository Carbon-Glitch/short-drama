# Storyboard, Keyframe, And Motion Rubric

## 目录

- [Coverage](#coverage-and-meaning)
- [Shot](#shot-purpose-and-geography)
- [Keyframe](#frozen-keyframe)
- [Motion](#motion)
- [Continuity](#cross-shot-continuity)
- [Rhythm profile](#rhythm-profile-shots)
- [Findings](#common-findings)
- [Production risks and authorized observations](#production-risk-and-authorized-observation-checklist-rev-08)

## Coverage and meaning

- Can every production-relevant action, line, sound, or on-screen text in `剧本.md` be traced to a shot or an explicit omission reason?
- Are omissions/repeats explained?
- Does each shot preserve the source action, dialogue, information, and reaction?
- Has downstream work invented or deleted a story fact?

## Shot purpose and geography

- For a high-value scene with an accepted coverage audition: did the approaches
  genuinely differ — in knowledge timing, audience alignment, performance space,
  strongest image, landing, losses, or production fit?
- Do the final shots in `分镜.md` implement the approach the creator selected?
- When a scene visual plan was used: do its start/end audience positions, spatial
  pressure, camera rhythm, reaction landing, and sound movement carry **one** dramatic turn?
- Does that plan stay clear of owning shot boundaries? (Ordinary scenes need no plan
  merely to satisfy a form.)
- What changes for audience or character by the shot end?
- Why is this a new shot?
- Do framing and camera behavior serve attention, alignment, pressure, reveal, or
  rhythm rather than decorate the prose?
- Does each shot's `运镜` line state a behavior and a reason chosen from the shot's
  purpose (`SHT-04`)? A stated lock-off with its reason passes, and a mostly locked episode
  is not a finding by itself. Flag a missing line, a bare 「运镜：固定」 without a reason,
  or a repeated fixed/moving choice that demonstrably weakens attention, information,
  performance, space, or rhythm; do not require movement at the peak.
- Are Location/View, axis, screen direction, eyelines, entrances, positions,
  hands, and props coherent?
- Are exact asset variants bound?
- Does the shot expose every fact it must carry while protecting
  facts the source withholds until a later action or cut?
- Do crop, occlusion, focus, back view, and offscreen space serve that information
  permission rather than accidentally reveal or conceal it?

### 声画承载与观看条件

- 镜头是否给了观众完成必要推断的可见/可听线索，而非只在“职责”字段声称完成？关键细节在当前画幅、遮挡、对焦和停留时间下是否可读？
- 关键台词、视觉发现与画面文字是否争夺同一个接收窗口？引用具体冲突时刻，不要求所有声画信息错开。
- 对话镜头是否在说话策略、听者反应、空间变化或第三方行动上承担工作？正反打、静止镜或高对白密度本身不是缺陷。
- 声画的同向、互补、对位或留白是否有剧情依据？不要把“没事”配颤抖、高潮撤音乐等惯例当成通用加分项，也不要为增加对位改写原意。
- 风格是否围绕叙事选择形成呼应，高潮的选择与后果是否有落点？具体指出装饰镜、同义强调或理解缺口，不要求零台词、全员反应或音乐拉满。

只有文字时报告设计意图、条件与风险；如果成片可访问，必须在正常速度、目标画幅和可听条件下检查实际表演、
声音空间、剪辑节奏和情绪效果。成片不可访问时保持这些维度为未验证，不能从静帧、脚本自检或生成成功状态
推定通过；也不设“视觉承载信息比例”或静音理解阈值。

## Rhythm profile: shots

Under the `REV-12` conditions in the [story rubric](rubric-story-script.md#rhythm-profile-rev-12),
measure two storyboard fields: the average shot length per scene (scene duration divided
by its shot count) against `target_avg_shot_seconds`, and the share of close-range shots
across the episode against `close_shot_share_min`. Close-range shots include 近景、特写、大特写 and 细节镜头;
divide their count by the episode's total shot count. The average is a
scene-level target; one long or short shot is not a finding. Also report durations folded
from screenplay word counts instead of the scene's sound timeline (`SHT-28`).

## Frozen keyframe

- Can all described facts exist in one still instant?
- Does it project the start state written for this shot?
- Are focal hierarchy, composition, camera/lens, geography, pose/gaze/hands/prop,
  expression, and light legible?
- Does it avoid ordered actions, performance arcs, camera moves, or transforming
  environments?
- Read the finished keyframe text, not the shot's intent: is every visible character,
  place, and prop whose identity, Look, or geography must stay recognizable listed in
  this shot's `视觉依据` (`SHT-22`)? A second body that entered the composition while the
  frame was being written is the usual miss.
- Does each declared 控制 scope stay inside what this frame can carry, and is nothing
  bound merely because it was bound in the previous shot (`SHT-24`)?
- When real reference images are bound, does every `REF-...` slot declare a 用途, so the
  shot says which start frame and which identity/geography/prop pictures it sends
  (`SHT-25`, `VID-24`)?
- Is anything the frames need kept consistent across shots — a carried prop, a garment —
  absent from `视觉设定.md` entirely, so it can appear in no shot's basis at all? The
  mechanical check cannot see this: an entry that does not exist cannot be reported missing.

## Motion

- Does it start from the accepted frame/boundary?
- Are subject actions ordered and feasible within the accepted duration while preserving the intended performance?
- Does performance change express the story move rather than stack synonyms?
- In multi-character motion: do the actors who actually change have distinct,
  readable triggers, choices, leaks, or landings — as this shot needs, not one
  identical arc per actor?
- Is attention handed off only where it truly transfers, rather than for
  synchronized reaction?
- Does any text-readiness claim cite the current creator-visible inputs and a real blocking gap?
- Does it avoid any claim about generated media quality or create a second readiness truth?
- Is camera behavior coherent and motivated?
- Are environment motion, dialogue, SFX, and audio included only when relevant?
- Does the described end match the storyboard's written end state without rewriting the next shot?
- When a reference frame carries appearance/composition, does motion prose retain only the visual facts this shot needs?
- Does every claim about text-bearing reference pixels cite a creator/reference-owner
  description or an authorized input-reference observation? Without that evidence,
  is admission still `unverified` instead of pretending a negative prompt solved it?
- For any selective transform, are the accepted trigger, exact target scope,
  end geometry/state, and preserve set explicit? Do non-target people, props,
  text surfaces, and spatial anchors keep their required position, count, and state?
- Does each media reference state its exact purpose, what may be copied, and what
  must not be copied, rather than treating all visible pixels as authority?

For a copyable body (`VID-22`, `VID-23`), check that actions and sound match the
source and that the timeline accounts for the intended ambience or silence.
A summary must not introduce a layer absent from the shot. H3's
`non_diegetic_music: N/A` is a valid empty music layer.

Report a concrete contradiction, omission or ambiguity. A negative clause is
not a defect by itself; do not impose a clause count or assume that negation
causes the model to generate the excluded content. Keep model-specific
observations scoped to their tested model and execution path.

For a pickup or alternate, ask these separately:

- Does the pickup/alternate identify its master? Keep candidate differences in ordinary notes and one formal `MOTION-...` with one copyable body per `SHOT-...`; a separate pickup first needs its own storyboard shot.
- Is every source obligation assigned to the master, this version, another named version or a requested storyboard revision?
- Are the changed items and the items that must remain unchanged explicit?
- Is replacement only requested here? The review Markdown decides whether to adopt the candidate; the owning skill then updates the formal body.

For music, ask these separately (`VID-14`):

- Is intent written as a relative entry/exit/duck against neighbouring shots,
  rather than an independent cue per shot?
- Do adjacent annotations actually join?
- Does the text ask for a per-shot music bed against an accepted timeline-layer plan?
- Whether a rendered clip carries a baked-in track is **not decidable here**. Cite it
  only from an authorized text observation record; otherwise keep it `unverified`
  and never infer a mix result from prose.

Explicit timing that does not sum exactly to its shot's accepted duration—over or
under—is a structural error. Untimed overload is a
reviewed feasibility question: cite which action/performance/story beat would be
lost, not a universal verbs-per-second formula.

Container arithmetic is a separate structural check (`VID-13`). Count the accepted
shots a delivery container carries, then confirm its duration equals the sum of
their accepted durations. For a multi-shot container, confirm the members are
contiguous in source order, share one geography/asset binding chain, do not cross a
scene boundary, and each remains independently reviewable. A space or subject jump
belongs on a member boundary; the same jump inside a member's timed segment is a
hidden cut. Report an arithmetic mismatch and a hidden cut as two findings, not one.

- Is the axis recorded as two named anchors, a stated working side, and a per-character
  screen position — rather than a placeholder?
- In a shot-reverse-shot pair, are the two screen directions complementary?
- Bare left/right always means **screen** left/right. Where a subject's own side is
  meant, does the text name the subject?

## Cross-shot continuity

Trace Look, injury, dirt/wetness, emotion/knowledge, position/facing/gaze, hands,
held prop, prop owner/state, location/time/weather/light, axis, and screen
direction. Distinguish unexplained contradiction from declared montage,
ellipsis, dream, or deliberate disorientation.

## Common findings

- beautiful shot with no dramatic purpose;
- dialogue covered but consequential reaction absent;
- anonymous asset or wrong variant;
- cross-location/time action hidden in one ordinary shot;
- keyframe contains “first/then/finally”;
- locked camera also pans or pushes in the same interval;
- motion invents a grab, injury, transfer, relationship change, or line;
- a selective transform removes, copies, or reshapes a non-target person, prop,
  text surface, or spatial anchor because its preserve set was unspecified;
- end pose/prop state disagrees with next start;
- every emotional beat uses the same close-up/push template;
- provider batching is mistaken for editorial shot structure.
- a narrowed pickup silently replaces the master and drops dialogue, reaction,
  reveal, end-state, or creator-directive obligations.

## Production-risk and authorized-observation checklist (REV-08)

本套件优先查看可访问的实际媒体。若当前环境无法读取或播放成片，先把下列项目当作文字风险，引用准确的
prompt/spec 说明为什么会造成执行歧义或违背已接受约束；只有创作者提供了授权的文字观察记录时，才能称为
已观察缺陷，并把该记录作为外部证据引用。没有媒体或观察记录时保持结果未知，不从任务成功、结果地址或
提示词存在推断成片质量。

需要项目校准时，先区分输入参考与生成结果。后一种观察须绑定准确的提示词/镜头标题、参考顺序、
制作形态/配置、观察方法和限制；先按 `REV-11` 选择处置，需要改动时再写最小修改项与保持项。
结论只在该项目和版本条件下有效。

短剧生产中需要防范的文字风险或获授权观察包括：

- on-screen text or subtitle residue despite a declared no-text constraint;
- a text-bearing reference admitted under no-text or exact-readable policy
  without an allowed surface or a crop, clean, mask, or replace decision;
- background music implied where the audio boundary allows sound effects only;
- wardrobe or look drift against the bound reference (re-describing clothes the
  reference already fixes invites drift — flag redundant appearance prose);
- 180° axis violation or eyeline mismatch across consecutive shots without a
  declared transition;
- lip-sync mismatch: dialogue bound to the wrong character, inner monologue
  written as mouthed speech, or extra lines the source dialogue never contained;
- explicit segment timings that do not sum exactly to the shot duration, in either direction;
- emotion-intensity mismatch between stated level and described performance
  (a declared 9/10 rage performed as mild irritation, or the reverse).
