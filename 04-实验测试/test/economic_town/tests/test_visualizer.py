"""阶段5 测试 —— 验证可视化和主入口"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile

from core.simulation import TownEconomy
from analysis.statistics import EconomyStats
from analysis.visualizer import Visualizer


class TestVisualizer(unittest.TestCase):

    def setUp(self):
        self.economy = TownEconomy(seed=42)
        self.economy.run(12)
        self.stats = EconomyStats(self.economy)
        self.stats.update_all()

    def test_plot_overview_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            viz = Visualizer(self.stats, output_dir=tmpdir)
            path = viz.plot_overview()
            self.assertTrue(os.path.exists(path))
            self.assertTrue(path.endswith(".png"))
            self.assertGreater(os.path.getsize(path), 1000)  # 非空文件

    def test_plot_financial_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            viz = Visualizer(self.stats, output_dir=tmpdir)
            path = viz.plot_financial()
            self.assertTrue(os.path.exists(path))

    def test_plot_production_creates_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            viz = Visualizer(self.stats, output_dir=tmpdir)
            path = viz.plot_production()
            self.assertTrue(os.path.exists(path))

    def test_plot_all_returns_three_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            viz = Visualizer(self.stats, output_dir=tmpdir)
            paths = viz.plot_all()
            self.assertEqual(len(paths), 3)
            for p in paths:
                self.assertTrue(os.path.exists(p))

    def test_output_dir_auto_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "a", "b", "charts")
            viz = Visualizer(self.stats, output_dir=nested)
            viz.plot_overview()
            self.assertTrue(os.path.isdir(nested))


class TestMainScript(unittest.TestCase):
    """测试主入口脚本（不依赖 LLM）"""

    def test_main_runs_without_error(self):
        """以非交互方式运行 main.py，跑 6 个月，不崩溃"""
        import subprocess
        result = subprocess.run(
            [sys.executable, "main.py", "--months", "6", "--no-llm"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.assertEqual(result.returncode, 0, msg=f"stderr: {result.stderr}")
        self.assertIn("仿真完成", result.stdout)
        self.assertIn("数据已导出", result.stdout)
        self.assertIn("图表已生成", result.stdout)

    def test_main_verbose_mode(self):
        """--verbose 模式下每月有状态输出"""
        import subprocess
        result = subprocess.run(
            [sys.executable, "main.py", "--months", "3", "--no-llm", "--verbose"],
            capture_output=True, text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("月份=1", result.stdout)
        self.assertIn("月份=2", result.stdout)
        self.assertIn("月份=3", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
