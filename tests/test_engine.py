"""
teonu-worldmodel — 测试套件
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from teonu_worldmodel import WorldModelEngine


class TestWorldModelEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.wm = WorldModelEngine(self.tmpdir)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_ingest_new_node(self):
        """测试创建新节点"""
        result = self.wm.ingest(
            node_id="test_node",
            title="测试节点",
            state={"value": 42},
            source="manual",
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["status"], "confirmed")

        # 验证文件存在
        node_path = Path(self.tmpdir) / "nodes" / "test_node.yaml"
        self.assertTrue(node_path.exists())

    def test_ingest_updates_existing(self):
        """测试更新现有节点"""
        self.wm.ingest("test_node", "测试", {"value": 1}, "manual")
        result = self.wm.ingest("test_node", "测试", {"value": 2}, "api")
        self.assertTrue(result["success"])

        # 验证 history 记录了更新
        import yaml
        node = yaml.safe_load((Path(self.tmpdir) / "nodes" / "test_node.yaml").read_text())
        self.assertEqual(len(node["history"]), 2)

    def test_infer_enforces_law1(self):
        """测试法则1：假设≠事实，confidence 必须 <= 0.6"""
        self.wm.ingest("node_a", "A", {"v": 1}, "manual")
        self.wm.ingest("node_b", "B", {"v": 2}, "manual")

        result = self.wm.infer(
            from_node_id="node_a",
            to_node_id="node_b",
            relation_label="影响",
            hypothesis="A 影响 B",
            base_confidence=0.9,  # 传入高置信度
        )
        self.assertTrue(result["success"])
        # 法则1强制：confidence 上限 0.6
        self.assertLessEqual(result["lwg_relation"]["confidence"], 0.6)
        self.assertTrue(result["lwg_relation"]["requires_validation"])

    def test_query_routes_correctly(self):
        """测试查询路由"""
        q_type = self.wm._route_query("最近体重趋势如何？")
        self.assertEqual(q_type, "trend")

        q_type = self.wm._route_query("要不要做这个决定？")
        self.assertEqual(q_type, "decision")

        q_type = self.wm._route_query("这个会不会影响健康？")
        self.assertEqual(q_type, "cross_domain")

    def test_compact_node(self):
        """测试节点压缩"""
        self.wm.ingest("test_compact", "压缩测试", {"v": 1}, "manual")

        import yaml
        from teonu_worldmodel import NodeCompactor
        node = yaml.safe_load((Path(self.tmpdir) / "nodes" / "test_compact.yaml").read_text())

        # 添加超过阈值的 history
        for i in range(15):
            node["history"].append({
                "timestamp": "2026-04-01",
                "status": "stable",
                "trigger": f"历史{i}",
            })

        compactor = NodeCompactor()
        compacted = compactor.compact(node)

        # 验证摘要化
        self.assertTrue(
            any(h.get("type") == "compaction_summary" for h in compacted["history"])
        )
        self.assertLess(len(compacted["history"]), 15)


if __name__ == "__main__":
    unittest.main()
