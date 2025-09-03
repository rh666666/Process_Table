from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import WorkOrder, Task, Process, Route

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
        
    def test_scheduled_work_order_modify_processes(self):
        """测试已排产工单只能修改待处理和未报工状态的工序"""
        # 1. 创建测试工序
        process_a = Process.objects.create(name="工序A", description="测试工序A")
        process_b = Process.objects.create(name="工序B", description="测试工序B")
        process_c = Process.objects.create(name="工序C", description="测试工序C")
        process_d = Process.objects.create(name="工序D", description="测试工序D")
        new_process = Process.objects.create(name="新工序", description="用于测试的新工序")

        # 2. 创建已排产工单并关联初始工序
        work_order = WorkOrder.objects.create(
            name="已排产测试工单",
            status="scheduled"  # 已排产状态
        )
        # 关联所有工序
        work_order.processes.add(process_a, process_b, process_c, process_d)

        # 3. 为工单创建不同状态的任务（关联对应的工序）
        # 待处理任务（允许修改）
        task_pending = Task.objects.create(
            work_order=work_order,
            process=process_a,
            status="pending"
        )
        # 未报工任务（允许修改）
        task_unreported = Task.objects.create(
            work_order=work_order,
            process=process_b,
            status="unreported"
        )
        # 进行中任务（禁止修改）
        task_in_progress = Task.objects.create(
            work_order=work_order,
            process=process_c,
            status="in_progress"
        )
        # 已完成任务（禁止修改）
        task_completed = Task.objects.create(
            work_order=work_order,
            process=process_d,
            status="completed"
        )

        # 4. 测试场景1：修改允许的工序（待处理和未报工）
        # 准备数据：移除工序A，添加新工序（对应待处理任务）
        allowed_process_ids = [process_b.id, new_process.id]
        data_allowed = {
            "processes": allowed_process_ids
        }
        response_allowed = self.client.patch(
            f"{self.work_order_url}{work_order.id}/",
            data_allowed,
            format="json"
        )
        # 验证成功
        self.assertEqual(response_allowed.status_code, status.HTTP_200_OK)
        # 刷新工单数据
        work_order.refresh_from_db()
        # 验证工序已更新
        self.assertIn(new_process, work_order.processes.all())
        self.assertNotIn(process_a, work_order.processes.all())
        self.assertIn(process_b, work_order.processes.all())  # 未报工工序应保留

        # 5. 测试场景2：修改禁止的工序（进行中和已完成）
        # 准备数据：移除工序C（进行中）和D（已完成）
        forbidden_process_ids = [process_a.id, process_b.id]  # 只保留允许的旧工序
        data_forbidden = {
            "processes": forbidden_process_ids
        }
        response_forbidden = self.client.patch(
            f"{self.work_order_url}{work_order.id}/",
            data_forbidden,
            format="json"
        )
        # 验证失败
        self.assertEqual(response_forbidden.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "已排产的工单只能修改待处理和未报工的工序",
            response_forbidden.json()["error"]
        )
        # 验证工序未被非法修改
        work_order.refresh_from_db()
        self.assertIn(process_c, work_order.processes.all())  # 进行中工序应保留
        self.assertIn(process_d, work_order.processes.all())  # 已完成工序应保留

        # 6. 测试场景3：新增允许的工序（会创建待处理任务）
        data_add = {
            "processes": [process_a.id, process_b.id, process_c.id, process_d.id, new_process.id]
        }
        response_add = self.client.patch(
            f"{self.work_order_url}{work_order.id}/",
            data_add,
            format="json"
        )
        self.assertEqual(response_add.status_code, status.HTTP_200_OK)
        # 验证新工序已添加
        work_order.refresh_from_db()
        self.assertIn(new_process, work_order.processes.all())
        # 验证自动创建了待处理任务
        self.assertTrue(
            Task.objects.filter(
                work_order=work_order,
                process=new_process,
                status="pending"
            ).exists()
        )



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