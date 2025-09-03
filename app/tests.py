from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import WorkOrder, Task, Process

class WorkOrderAPITestCase(TestCase):
    def setUp(self):
        # 初始化测试客户端
        self.client = APIClient()
        self.work_order_url = "/api/workorders/"
        
        # 创建测试工单
        self.work_order = WorkOrder.objects.create(
            name="测试工单",
            status="draft"
        )

    def test_submit_work_order(self):
        """测试提交工单（从草稿变为已提交）"""
        data = {"status": "submitted"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "submitted")

    def test_approve_work_order(self):
        """测试审核工单（从已提交变为已审核）"""
        self.work_order.status = "submitted"
        self.work_order.save()

        data = {"status": "approved"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "approved")

    def test_schedule_work_order(self):
        """测试排产工单（从已审核变为已排产）"""
        self.work_order.status = "approved"
        self.work_order.save()

        data = {"status": "scheduled"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "scheduled")

    def test_reject_status_change(self):
        """测试非法状态变更（如从已审核变为草稿）"""
        self.work_order.status = "approved"
        self.work_order.save()

        data = {"status": "draft"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        print(response.json())  # 调试输出
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], "已审核的工单不能变更为草稿状态。")

    def test_delete_work_order(self):
        """测试删除工单（已排产工单不可删除）"""
        self.work_order.status = "scheduled"
        self.work_order.save()

        response = self.client.delete(f"{self.work_order_url}{self.work_order.id}/", format="json")
        print(response.json())  # 调试输出
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], "已排产的工单不可删除。")

class WorkOrderSplitTestCase(TestCase):
    def setUp(self):
        # 初始化测试客户端
        self.client = APIClient()
        self.split_url = "/api/workorders/split/"

        # 创建测试工序
        self.process1 = Process.objects.create(name="工序1", description="描述1")
        self.process2 = Process.objects.create(name="工序2", description="描述2")

        # 创建测试工单
        self.work_order = WorkOrder.objects.create(
            name="测试工单",
            status="approved"  # 假设只有已审核的工单可以拆分
        )

    def test_split_work_order(self):
        """测试工单拆分为工序工单"""
        data = {
            "work_order_id": self.work_order.id,
            "processes": [self.process1.id, self.process2.id]  # 需要拆分的工序
        }
        response = self.client.post(self.split_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 验证是否生成了对应的工序工单
        tasks = Task.objects.filter(work_order=self.work_order)
        self.assertEqual(tasks.count(), 2)
        self.assertTrue(tasks.filter(process=self.process1).exists())
        self.assertTrue(tasks.filter(process=self.process2).exists())

    def test_split_invalid_work_order(self):
        """测试非法工单拆分（如状态不允许）"""
        self.work_order.status = "draft"  # 修改为草稿状态
        self.work_order.save()

        data = {
            "work_order_id": self.work_order.id,
            "processes": [self.process1.id, self.process2.id]
        }
        response = self.client.post(self.split_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], "只有已审核的工单可以拆分。")
