# 原著候选 → 改编映射交接

原著分析阶段的候选身份不能在 develop 阶段被重新命名后悄悄丢失。`项目开发/adaptation-map.jsonl`
的每条映射保留候选来源和制作判断；没有对应值时明确写空或 `unresolved`。

| 原著分析字段 | 改编映射字段 | 处理 |
|---|---|---|
| `candidate_id` | `source_candidate_id` | 原样保留，作为跨阶段追踪键 |
| `source_span` / locator | `source_span` | 原样保留，指向原始材料范围 |
| `payoffs` | `payoff_ids` 或 `payoff_summary` | 保留观众回报及其在候选集的落点 |
| `carrier_change` | `disposition=change_carrier` + `new_carrier` | 说明从叙述、内心或说明换成何种可见/可听载体 |
| `production_load` | `production_load` | 保留制作负担；未知时写 `unresolved`，不静默删除 |
| `inherited_facts` | `preserved_facts` | 进入单集或系列承诺的事实逐条继承 |
| `unresolved` | `unresolved` / `lost_or_changed` | 未决继续未决；有意改变则说明损失和创作者决定 |
| 候选的剧情功能 | `preserved_functions` | 写它承担的选择、信息、权力、关系或因果桥 |

## 交接检查

每条映射至少能回答：来自哪条候选、保留了什么回报、换成什么载体、制作负担是什么、哪些事实仍未决、
进入哪一集以及会在哪个可见结果中兑现。合并、压缩、提前、删去和新增都必须写 `lost_or_changed`，
不能用“优化”“节奏更好”代替。
