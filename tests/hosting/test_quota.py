import unittest
from hosting.quota import ResourceQuotaManager


class TestResourceQuotaManager(unittest.TestCase):

    def test_basic_allocation(self):
        q = ResourceQuotaManager(total_cpu=8, total_memory_mb=8192, total_disk_mb=32768)
        q.allocate("ctr1", cpu=2, memory_mb=1024, disk_mb=4096)
        self.assertAlmostEqual(q.remaining_cpu(),    6.0)
        self.assertAlmostEqual(q.remaining_memory(), 7168.0)
        self.assertAlmostEqual(q.remaining_disk(),   28672.0)

    def test_fragmentation_cpu(self):
        """
        Cluster: 8 CPU
        Allocate 3 + 3 = 6 CPU used → 2 remaining
        Attempt 4 CPU → must fail.
        """
        q = ResourceQuotaManager(total_cpu=8, total_memory_mb=99999, total_disk_mb=99999)
        q.allocate("ctr1", cpu=3, memory_mb=100, disk_mb=100)
        q.allocate("ctr2", cpu=3, memory_mb=100, disk_mb=100)
        self.assertAlmostEqual(q.remaining_cpu(), 2.0)

        with self.assertRaises(ValueError) as ctx:
            q.allocate("ctr3", cpu=4, memory_mb=100, disk_mb=100)
        self.assertIn("Insufficient CPU", str(ctx.exception))

    def test_fragmentation_memory(self):
        q = ResourceQuotaManager(total_cpu=99, total_memory_mb=4096, total_disk_mb=99999)
        q.allocate("ctr1", cpu=1, memory_mb=2000, disk_mb=100)
        q.allocate("ctr2", cpu=1, memory_mb=2000, disk_mb=100)
        with self.assertRaises(ValueError) as ctx:
            q.allocate("ctr3", cpu=1, memory_mb=100, disk_mb=100)
        self.assertIn("Insufficient memory", str(ctx.exception))

    def test_release_frees_resources(self):
        q = ResourceQuotaManager(total_cpu=4, total_memory_mb=4096, total_disk_mb=32768)
        q.allocate("ctr1", cpu=4, memory_mb=4096, disk_mb=32768)
        with self.assertRaises(ValueError):
            q.allocate("ctr2", cpu=1, memory_mb=1, disk_mb=1)
        q.release("ctr1")
        alloc = q.allocate("ctr2", cpu=1, memory_mb=1, disk_mb=1)
        self.assertIsNotNone(alloc)

    def test_snapshot(self):
        q = ResourceQuotaManager(total_cpu=8, total_memory_mb=8192, total_disk_mb=32768)
        q.allocate("ctr1", cpu=2, memory_mb=512, disk_mb=1024)
        snap = q.snapshot()
        self.assertIn("ctr1", snap)
        self.assertEqual(snap["ctr1"].cpu, 2)


if __name__ == "__main__":
    unittest.main()
