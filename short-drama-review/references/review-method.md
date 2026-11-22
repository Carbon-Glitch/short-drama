# Evidence-Based Review Method

## Rule classification

- `structural_invariant`: objectively checkable integrity; validators may block it.
- `reviewed_invariant`: semantic integrity that needs cited evidence.
- `craft_default`: a recommended method that may change for a stated reason.
- `taste_option`: a chosen style is not itself a defect; weak realization of the agreed visual goal is still a valid creative finding.

## Governing know-how

- `REV-01` — Start from the audience experience and use the relevant integrity checks alongside the creative review.
- `REV-02` — Every finding names a bounded target, evidence, impact, required outcome, owner and severity.
- `REV-03` — A semantic-invention finding pairs the authoritative fact with the conflicting downstream fact.
- `REV-04` — 局部修改使用制作内自检并如实标明；整集跨阶段交付采用未参与创作的独立首看与连续性复核，作者自检不冒充首次观众。
- `REV-05` — Diagnose repeated/generic mechanisms at exact locations rather than applying an “AI-ish” label.
- `REV-06` — Alternative preferences remain notes unless the current choice violates an accepted constraint.
- `REV-07` — An end-to-end task authorizes responsible creative decisions; distinguish actual user choices from the Agent's design choices.

## Review scope

Start from the current creator-visible files and the constraints the creator has explicitly chosen. Use a focused in-task review, identifying what was actually read, seen or heard. Preserve the user's requested scope.

If a target changes during review, reread that target before recording the verdict. Do not recursively invalidate
unrelated findings.

## Creative outcomes and mechanical support

Mechanical examples:

- missing or duplicate Markdown IDs, broken links or unresolved references;
- unknown asset variants or contradictory camera flags;
- explicit segments not matching their declared duration;
- readable text conflicting with the accepted text policy;
- a stage document silently taking over facts owned by another document;
- delivery containing private or unapproved material.

Semantic examples:

- the promised striking visual design has collapsed into generic assets, with the missing shape/material/spatial choices identified;
- a key design or reaction exists somewhere in the footage but is unreadable at its intended payoff;

- downstream action changes story meaning;
- a conflict scene has no opposition or turn, or another kind of scene lacks a necessary state change;
- a keyframe implies several moments;
- action load crowds out performance;
- escalation repeats the same mechanism;
- a prompt preserves the wrong identity.

## Finding anatomy

A useful finding contains:

1. stable diagnostic/rule ID when one exists;
2. project-relative file plus heading ID, line number or shot when useful;
3. bounded quotation or conflicting facts;
4. audience, continuity or production impact;
5. required outcome and the facts that must stay unchanged, leaving replacement prose to the owner;
6. owner, severity and open/closed status.

“The dialogue is weak” is invalid. A finding should identify the exact exchange, say what fails to change, and tell
the write owner what outcome must be restored.

The review Markdown cites the current file name, heading ID, line number or a necessary short quotation directly.
It does not copy upstream snapshots, invent record IDs or create another version of the source material.

## Cross-layer synthesis

Trace important moves end to end: story fact, design priority, subject assets, image prompt and actual REF, shot boundary, optional keyframe, motion and next-shot state. For each important design, identify its concrete image/shot carrier and the details added downstream; distinguish intentional crop allocation, dependence on a planned reference, state-projection errors and true omissions. Check that every generated image has a real generation consumer; representative and per-cut frames are evaluated when their control route is chosen.

Resolve upstream meaning first; do not polish prompt wording when the shot or asset binding is wrong. Judge actual images for design fidelity and aesthetic strength, and dynamic footage for readable action, focus, lighting, reflection and material change.

## Revision and re-review

Group duplicate findings and route them to the owning skill. A revision request states the target outcome, preserve
set and review scope to rerun.

`REV-14`: a revision request names the smallest change at a cited location and the facts to preserve. Local
findings do not authorize a whole-episode rewrite. When the review compares a revision with the version before
it, any strong hook, payoff line, or comic beat that polishing removed is listed under `## 被删的强钩子` with its prior
location and a short quote, so the owner can decide whether to restore it.

On a later explicit re-review request, read the current version, confirm the required outcome, check the preserve
set and close or retain each affected finding. Prefer another uninvolved reviewer when available; otherwise disclose self-review.

## Anti-template review

Do not use a banned-word list. Look for repeated mechanisms, interchangeable character voices, abstract intensity
without playable behavior, generic quality adjectives burying identity, automatic reaction close-ups and decorative
camera movement. Cite location and impact while preserving deliberate genre rhythm.
