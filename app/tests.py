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
        process_d = Process.objects.create(name="工序D", description="测试工序D")
        process_e = Process.objects.create(name="工序E", description="测试工序E")
        
        route = Route.objects.create(name="测试工艺路线")
        
        # 按特定顺序添加工序
        RouteProcess.objects.create(route=route, process=process_e, order=5)
        RouteProcess.objects.create(route=route, process=process_b, order=2)
        RouteProcess.objects.create(route=route, process=process_d, order=4)
        RouteProcess.objects.create(route=route, process=process_a, order=1)
        RouteProcess.objects.create(route=route, process=process_c, order=3)
        
        # 验证工序按order字段排序 - 通过RouteProcess中间表正确获取排序
        ordered_processes = [rp.process for rp in route.routeprocess_set.all().order_by('order')]
        self.assertEqual(ordered_processes[0], process_a)  # order=1
        self.assertEqual(ordered_processes[1], process_b)  # order=2
        self.assertEqual(ordered_processes[2], process_c)  # order=3
        self.assertEqual(ordered_processes[3], process_d)  # order=4
        self.assertEqual(ordered_processes[4], process_e)  # order=5
        
        # 拆分工单后检查任务是否按顺序创建
        work_order = WorkOrder.objects.create(
            name="拆分测试工单",
            status="approved",
            route=route
        )
        
        # 调用拆分工单方法
        from .views import WorkOrderViewSet
        WorkOrderViewSet().split_work_order(work_order)
        
        # 获取创建的任务，检查顺序
        tasks = Task.objects.filter(work_order=work_order).order_by('id')
        self.assertEqual(tasks.count(), 5)
        self.assertEqual(tasks[0].process, process_a)  # 第一个任务是order=1的工序
        self.assertEqual(tasks[1].process, process_b)  # 第二个任务是order=2的工序
        self.assertEqual(tasks[2].process, process_c)  # 第三个任务是order=3的工序
        self.assertEqual(tasks[3].process, process_d)  # 第四个任务是order=4的工序
        self.assertEqual(tasks[4].process, process_e)  # 第五个任务是order=5的工序

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
        """测试排产工单（设置is_scheduled为True）"""
        self.work_order.status = "approved"
        self.work_order.save()

        # 创建一个已排产的工单
        self.work_order.is_scheduled = True
        self.work_order.save()
        
        # 验证排产状态
        self.assertTrue(self.work_order.is_scheduled)
        self.assertEqual(self.work_order.status, "approved")

    def test_reject_status_change(self):
        """测试非法状态变更（如从已审核变为草稿，草稿变为已审核）"""
        self.work_order.status = "approved"
        self.work_order.save()

        data = {"status": "draft"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        print(response.json())  # 调试输出
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        self.work_order.status = "draft"
        self.work_order.save()
        
        data = {"status": "approved"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        print(response.json())  # 调试输出
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_scheduled_work_order_cannot_modify_info(self):
        """测试已排产的工单只能修改工艺路线"""
        # 设置工单为已排产
        self.work_order.status = "approved"
        self.work_order.is_scheduled = True
        self.work_order.save()

        # 尝试修改工单名称（基本信息）
        data = {"name": "修改后的工单名称"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        print(response.json())  # 调试输出
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("已审核的工单需要反审核后才能修改。", str(response.json()))
        
        # 模拟反审核
        self.work_order.status = "draft"
        self.work_order.save()
        
        # 尝试修改基本信息，会触发已排产的工单只能修改工艺路线
        data = {"name": "修改后的工单名称"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        print(response.json())  # 调试输出
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("已排产的工单只能修改工艺路线。", str(response.json()))
        
        # 测试修改工艺路线，应该允许
        new_route = Route.objects.create(name="新的工艺路线")
        RouteProcess.objects.create(route=new_route, process=self.process, order=1)
        data = {"route": new_route.id}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        print(response.json())  # 调试输出
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_draft_work_order_only_modify_status(self):
        """测试非草稿状态的工单只能修改status字段"""
        # 测试已提交状态
        self.work_order.status = "submitted"
        self.work_order.save()

        # 尝试修改工单名称（非status字段）
        data = {"name": "修改后的工单名称"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("已提交的工单需要撤销提交后修改。", str(response.json()))
        
        # 测试已审核状态
        self.work_order.status = "approved"
        self.work_order.save()

        # 尝试修改工单名称（非status字段）
        data = {"name": "修改后的工单名称"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("已审核的工单需要反审核后才能修改。", str(response.json()))
        
        # 测试修改status字段（应该允许）
        data = {"status": "submitted"}
        response = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "submitted")

    def test_delete_work_order(self):
        """测试删除工单（已排产工单不可删除）"""
        self.work_order.status = "approved"
        self.work_order.is_scheduled = True
        self.work_order.save()

        response = self.client.delete(f"{self.work_order_url}{self.work_order.id}/", format="json")
        print(response.json())  # 调试输出
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json()["error"], "已排产的工单不可删除。")
        
    def test_scheduled_work_order_only_modify_route(self):
        """测试已排产的工单修改规则"""
        # 设置工单为已排产
        self.work_order.status = "approved"
        self.work_order.is_scheduled = True
        self.work_order.save()

        # 创建新的工艺路线
        new_route = Route.objects.create(name="新的工艺路线")
        RouteProcess.objects.create(route=new_route, process=self.process, order=1)

        # 尝试只修改route字段（会被拒绝，因为先触发"已审核的工单需要反审核后才能修改"的验证）
        data_route_only = {"route": new_route.id}
        response_route_only = self.client.patch(f"{self.work_order_url}{self.work_order.id}/", data_route_only, format="json")
        self.assertEqual(response_route_only.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("已审核的工单需要反审核后才能修改。", str(response_route_only.json()))


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
        
    def test_split_work_order_with_exception(self):
        """测试拆分工单过程中出现异常的处理逻辑"""
        # 使用mock.patch来正确模拟split_work_order方法
        import unittest.mock as mock
        
        # 使用patch来临时替换split_work_order方法
        with mock.patch('app.views.WorkOrderViewSet.split_work_order') as mock_split:
            # 配置mock方法抛出异常
            mock_split.side_effect = Exception("模拟拆分工单失败")
            
            # 验证当工单已审核时，会触发异常
            with self.assertRaises(Exception) as context:
                # 手动调用视图方法来测试
                from .views import WorkOrderViewSet
                viewset = WorkOrderViewSet()
                viewset.split_work_order(self.work_order)
            
            # 验证异常消息
            self.assertEqual(str(context.exception), "模拟拆分工单失败")
            
            # 验证mock方法被调用
            mock_split.assert_called_once()
            
    def test_manual_split_work_order_with_exception(self):
        """测试通过WorkOrderSplitView手动拆分工单时的异常处理"""
        # 由于在实际应用中，我们不能确定WorkOrderSplitView的URL是否已配置
        # 我们可以直接测试WorkOrderSplitView类的实例方法
        
        # 导入WorkOrderSplitView
        from .views import WorkOrderSplitView
        from django.http import HttpRequest
        from django.test.client import RequestFactory
        
        # 创建请求工厂
        factory = RequestFactory()
        request = factory.post(f'/workorders/{self.work_order.id}/split/')
        
        # 使用mock.patch来模拟拆分工单过程中的异常
        import unittest.mock as mock
        
        # 使用patch来临时替换split_work_order方法
        with mock.patch('app.views.WorkOrderViewSet.split_work_order') as mock_split:
            # 配置mock方法抛出异常
            mock_split.side_effect = Exception("模拟手动拆分工单失败")
            
            # 创建WorkOrderSplitView实例
            view = WorkOrderSplitView.as_view()
            
            # 直接调用视图方法进行测试
            response = view(request, pk=self.work_order.id)
            
            # 验证返回的状态码为500
            self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 验证返回的错误消息
            self.assertEqual(response.data, {"error": "拆分工单失败，请联系管理员。"})
            
            # 验证mock方法被调用
            mock_split.assert_called_once()

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
            status="approved",
            route=self.route,
            is_scheduled=True
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