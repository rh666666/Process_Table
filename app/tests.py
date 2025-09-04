from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import WorkOrder, Task, Process, Route, RouteProcess

class WorkOrderAPITestCase(TestCase):
    def setUp(self):
        # 初始化测试客户端
        self.client = APIClient()
        self.work_order_url = "/api/workorders/"
        
        # 创建测试工序
        self.process = Process.objects.create(name="测试工序", description="测试工序描述")
        
        # 创建测试工艺路线
        self.route = Route.objects.create(name="测试工艺路线")
        # 使用RouteProcess中间表添加工序并设置顺序
        RouteProcess.objects.create(route=self.route, process=self.process, order=1)
        
        # 创建测试工单
        self.work_order = WorkOrder.objects.create(
            name="测试工单",
            status="draft",
            route=self.route
        )
        
    def test_route_process_order(self):
        """测试工艺路线中的工序顺序功能"""
        # 创建测试工序和工艺路线
        process_a = Process.objects.create(name="工序A", description="测试工序A")
        process_b = Process.objects.create(name="工序B", description="测试工序B")
        process_c = Process.objects.create(name="工序C", description="测试工序C")
        
        route = Route.objects.create(name="测试工艺路线")
        
        # 按特定顺序添加工序
        RouteProcess.objects.create(route=route, process=process_b, order=2)
        RouteProcess.objects.create(route=route, process=process_a, order=1)
        RouteProcess.objects.create(route=route, process=process_c, order=3)
        
        # 验证工序按order字段排序
        ordered_processes = list(route.processes.all())
        self.assertEqual(ordered_processes[0], process_a)  # order=1
        self.assertEqual(ordered_processes[1], process_b)  # order=2
        self.assertEqual(ordered_processes[2], process_c)  # order=3
        
        # 拆分工单后检查任务是否按顺序创建
        work_order = WorkOrder.objects.create(
            name="测试工单",
            status="approved",
            route=route
        )
        
        # 调用拆分工单方法
        from .views import WorkOrderViewSet
        WorkOrderViewSet().split_work_order(work_order)
        
        # 获取创建的任务，检查顺序
        tasks = Task.objects.filter(work_order=work_order).order_by('id')
        self.assertEqual(tasks.count(), 3)
        self.assertEqual(tasks[0].process, process_a)  # 第一个任务是order=1的工序
        self.assertEqual(tasks[1].process, process_b)  # 第二个任务是order=2的工序
        self.assertEqual(tasks[2].process, process_c)  # 第三个任务是order=3的工序

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

    def test_scheduled_work_order_cannot_modify_info(self):
        """测试已排产的工单不允许修改基本信息"""
        # 将工单状态设置为已排产
        self.work_order.status = "scheduled"
        self.work_order.save()

        # 尝试修改工单名称（基本信息）
        data = {"name": "修改后的工单名称"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        print(response.json())  # 调试输出
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("已排产的工单不允许修改基本信息", str(response.json()))

    def test_scheduled_work_order_cannot_change_status(self):
        """测试已排产的工单不允许变更状态"""
        # 将工单状态设置为已排产
        self.work_order.status = "scheduled"
        self.work_order.save()

        # 尝试将已排产状态的工单改为其他状态
        data = {"status": "approved"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        print(response.json())  # 调试输出
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("已排产的工单不允许变更状态", str(response.json()))

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
        
        # 创建测试工艺路线
        route = Route.objects.create(name="测试工艺路线")
        # 使用RouteProcess中间表添加工序并设置顺序
        RouteProcess.objects.create(route=route, process=process_a, order=1)
        RouteProcess.objects.create(route=route, process=process_b, order=2)
        RouteProcess.objects.create(route=route, process=process_c, order=3)
        RouteProcess.objects.create(route=route, process=process_d, order=4)

        # 2. 创建已排产工单
        work_order = WorkOrder.objects.create(
            name="已排产测试工单",
            status="scheduled",  # 已排产状态
            route=route
        )

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

        # 4. 测试场景1：修改工单的工艺路线（添加允许的工序）
        # 创建新的工艺路线，包含允许修改的工序和新工序
        new_route = Route.objects.create(name="新工艺路线")
        # 使用RouteProcess中间表添加工序并设置顺序
        RouteProcess.objects.create(route=new_route, process=process_b, order=1)
        RouteProcess.objects.create(route=new_route, process=new_process, order=2)
        
        data_allowed = {
            "route": new_route.id
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
        # 验证工艺路线已更新
        self.assertEqual(work_order.route.id, new_route.id)
        
        # 检查原有的进行中和已完成任务是否保留
        self.assertTrue(Task.objects.filter(work_order=work_order, process=process_c, status="in_progress").exists())
        self.assertTrue(Task.objects.filter(work_order=work_order, process=process_d, status="completed").exists())



class WorkOrderSplitTestCase(TestCase):
    def setUp(self):
        # 初始化测试客户端
        self.client = APIClient()
        self.split_url = "/api/workorders/split/"

        # 创建测试工序
        self.process1 = Process.objects.create(name="工序1", description="描述1")
        self.process2 = Process.objects.create(name="工序2", description="描述2")
        
        # 创建测试工艺路线并关联工序
        self.route = Route.objects.create(name="测试工艺路线")
        # 使用RouteProcess中间表添加工序并设置顺序
        RouteProcess.objects.create(route=self.route, process=self.process1, order=1)
        RouteProcess.objects.create(route=self.route, process=self.process2, order=2)

        # 创建测试工单
        self.work_order = WorkOrder.objects.create(
            name="测试工单",
            status="approved",  # 假设只有已审核的工单可以拆分
            route=self.route
        )

class TaskStatusChangeTestCase(TestCase):
    def setUp(self):
        # 初始化测试客户端
        self.client = APIClient()
        self.tasks_url = "/api/tasks/"

        # 创建测试工序
        self.process1 = Process.objects.create(name="工序1", description="描述1")
        self.process2 = Process.objects.create(name="工序2", description="描述2")
        self.process3 = Process.objects.create(name="工序3", description="描述3")
        
        # 创建测试工艺路线并关联工序
        self.route = Route.objects.create(name="测试工艺路线")
        # 使用RouteProcess中间表添加工序并设置顺序
        self.route_process1 = RouteProcess.objects.create(route=self.route, process=self.process1, order=1)
        self.route_process2 = RouteProcess.objects.create(route=self.route, process=self.process2, order=2)
        self.route_process3 = RouteProcess.objects.create(route=self.route, process=self.process3, order=3)

        # 创建测试工单
        self.work_order = WorkOrder.objects.create(
            name="测试工单",
            status="scheduled",  # 已排产状态
            route=self.route
        )

        # 创建任务并关联到RouteProcess
        self.task1 = Task.objects.create(
            work_order=self.work_order,
            process=self.process1,
            status="pending",
            route_process=self.route_process1
        )
        self.task2 = Task.objects.create(
            work_order=self.work_order,
            process=self.process2,
            status="pending",
            route_process=self.route_process2
        )
        self.task3 = Task.objects.create(
            work_order=self.work_order,
            process=self.process3,
            status="pending",
            route_process=self.route_process3
        )
    
    def test_change_task_status_with_all_previous_completed_and_next_pending(self):
        """测试当前置所有工序已完成、后置所有工序为未生产时，可以修改工序状态"""
        # 先将前置工序（工序1）标记为已完成
        self.task1.status = "completed"
        self.task1.save()
        
        # 验证可以修改工序2的状态
        data = {"status": "in_progress"}
        response = self.client.patch(f"{self.tasks_url}{self.task2.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "in_progress")
    
    def test_reject_change_task_status_with_previous_not_completed(self):
        """测试当前置工序未完成时，不允许修改工序状态"""
        # 前置工序（工序1）仍为未生产状态
        
        # 尝试修改工序2的状态
        data = {"status": "in_progress"}
        response = self.client.patch(f"{self.tasks_url}{self.task2.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 解码响应内容并检查错误消息
        content = response.content.decode('utf-8')
        self.assertIn("只有当前置所有工序已完成时，才能修改该工序的状态。", content)
    
    def test_reject_change_task_status_with_next_not_pending(self):
        """测试当后置工序不为未生产状态时，不允许修改工序状态"""
        # 先将前置工序（工序1）标记为已完成
        self.task1.status = "completed"
        self.task1.save()
        
        # 将后置工序（工序3）改为进行中状态
        self.task3.status = "in_progress"
        self.task3.save()
        
        # 尝试修改工序2的状态
        data = {"status": "in_progress"}
        response = self.client.patch(f"{self.tasks_url}{self.task2.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # 解码响应内容并检查错误消息
        content = response.content.decode('utf-8')
        self.assertIn("只有当后置所有工序为未生产状态时，才能修改该工序的状态。", content)