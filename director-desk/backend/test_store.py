import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from store import Conflict, ProjectStore


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = ProjectStore.create(Path(self.temp.name) / "作品", "夜行")

    def apply(self, ops):
        return self.store.apply(self.store.state()["project"]["revision"], ops)

    def fixture(self):
        self.apply([
            {"type": "create", "id": "line", "kind": "dialogue", "data": {"text": "别回头", "name": "甲"}},
            {"type": "create", "id": "shot", "kind": "shot"},
            {"type": "create", "id": "unrelated", "kind": "shot"},
            {"type": "create", "id": "motion", "kind": "submission"},
            {"type": "bind", "source": "line", "target": "shot", "fields": ["text"]},
            {"type": "bind", "source": "shot", "target": "motion"},
        ])
        for identity in ["shot", "motion"]:
            self.store.review(identity, self.store.state()["project"]["revision"])

    def test_only_affected_dependencies_become_stale_and_snapshot_is_immutable(self):
        self.fixture()
        frozen = self.store.freeze("封版")
        original = self.store.snapshot(frozen)
        self.apply([{"type": "update", "id": "line", "patch": {"name": "林岚"}}])
        self.assertFalse(any(e["stale"] for e in self.store.state()["entities"]))
        state = self.apply([{"type": "update", "id": "line", "patch": {"text": "看着我"}}])
        self.assertEqual({e["id"] for e in state["entities"] if e["stale"]}, {"shot", "motion"})
        self.assertEqual(self.store.snapshot(frozen), original)

    def test_transaction_rolls_back_all_changes(self):
        self.fixture()
        before = self.store.state()
        with self.assertRaises(ValueError):
            self.apply([
                {"type": "update", "id": "line", "patch": {"text": "不能留下这次修改"}},
                {"type": "bind", "source": "missing", "target": "shot"},
            ])
        self.assertEqual(self.store.state(), before)

    def test_concurrent_writers_do_not_silently_overwrite(self):
        self.fixture()
        revision = self.store.state()["project"]["revision"]
        def write(text):
            try:
                self.store.apply(revision, [{"type": "update", "id": "line", "patch": {"text": text}}])
                return "saved"
            except Conflict:
                return "conflict"
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(write, ["用户改稿", "Agent改稿"]))
        self.assertCountEqual(results, ["saved", "conflict"])

    def test_draft_survives_reopen_and_external_change(self):
        self.fixture()
        self.store.save_draft("user", "line", 1, {"text": "未提交草稿"})
        self.apply([{"type": "update", "id": "line", "patch": {"text": "Agent修改"}}])
        reopened = ProjectStore(self.store.root)
        self.assertEqual(reopened.drafts("user")[0]["content"]["text"], "未提交草稿")

    def test_undo_redo_walk_history_and_new_edit_discards_redo(self):
        self.apply([{"type": "create", "id": "a", "kind": "scene", "data": {"name": "一"}}])
        self.apply([{"type": "update", "id": "a", "patch": {"name": "二"}}])
        self.apply([{"type": "update", "id": "a", "patch": {"name": "三"}}])
        self.store.undo(3)
        state = self.store.undo(4)
        self.assertEqual(state["entities"][0]["data"]["name"], "一")
        state = self.store.redo(5)
        self.assertEqual(state["entities"][0]["data"]["name"], "二")
        self.apply([{"type": "update", "id": "a", "patch": {"name": "新方向"}}])
        with self.assertRaises(ValueError):
            self.store.redo(7)

    def test_cycle_in_containment_is_rejected_without_writing(self):
        with self.assertRaises(ValueError):
            self.apply([
                {"type": "create", "id": "a", "kind": "scene", "data": {"parent_id": "b"}},
                {"type": "create", "id": "b", "kind": "scene", "data": {"parent_id": "a"}},
            ])
        self.assertEqual(self.store.state()["entities"], [])

    def test_downstream_cannot_be_reviewed_before_stale_upstream(self):
        self.fixture()
        self.apply([{"type": "update", "id": "line", "patch": {"text": "停"}}])
        with self.assertRaises(ValueError):
            self.store.review("motion", self.store.state()["project"]["revision"])


if __name__ == "__main__":
    unittest.main()
