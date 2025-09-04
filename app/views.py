from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework import status
import logging
from .models import Process, Route, WorkOrder, Task
from .serializers import ProcessSerializer, RouteSerializer, WorkOrderSerializer, TaskSerializer
from rest_framework.views import APIView

logger = logging.getLogger(__name__)

class ProcessViewSet(viewsets.ModelViewSet):
    queryset = Process.objects.all()
    serializer_class = ProcessSerializer

class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.all()
    serializer_class = RouteSerializer

class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    serializer_class = WorkOrderSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get("status")
        
        # 约束状态流转
        # 1. 已审核的工单不能直接变更为草稿状态
        if instance.status == "approved" and new_status == "draft":
            raise ValidationError({"error": "已审核的工单不能变更为草稿状态。"})
            
        # 2. 只有草稿、已提交和已审核状态可以被修改
        # 但已排产状态的工单不允许修改基本信息（除了状态本身和工艺路线）
        if instance.status == "scheduled" and not new_status:
            # 检查请求中是否只包含route字段
            if not all(key == "route" for key in request.data.keys()):
                raise ValidationError({"error": "已排产的工单不允许修改基本信息。"})
            
        # 3. 已排产状态的工单不允许通过修改状态来回退
        if instance.status == "scheduled" and new_status and new_status != "scheduled":
            raise ValidationError({"error": "已排产的工单不允许变更状态。"})
            
        # 如果工单状态改为已排产，则自动拆分工单
        if new_status == "scheduled":
            self.split_work_order(instance)
        
        #已经排产的工单，只能修改未生产和未报工的任务
        if instance.status == "scheduled":
            # 获取当前工单的所有任务
            tasks = instance.tasks.all()
            # 获取允许修改的工序ID（未生产和未报工状态）
            allowed_process_ids = [task.process.id for task in tasks if task.status in ["pending", "unreported"]]
            
            if "processes" in request.data:
                for process_id in request.data["processes"]:
                    if process_id not in allowed_process_ids:
                        # 检查该工序ID对应的任务是否存在
                        existing_task = tasks.filter(process_id=process_id).first()
                        if existing_task and existing_task.status in ["in_progress", "completed"]:
                            return Response({"error": "已排产的工单只能修改待处理和未报工的工序。"}, status=status.HTTP_400_BAD_REQUEST)
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == "scheduled":
            return Response({"error": "已排产的工单不可删除。"}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    def split_work_order(self, work_order):
        # 拆分工单的逻辑
        try:
            # 获取工单关联的工艺路线中的所有工序，并按照顺序字段排序
            route_processes = work_order.route.routeprocess_set.all().order_by('order')
            
            # 记录创建/更新的任务数量
            created_count = 0
            
            for route_process in route_processes:
                # 检查是否已存在与该RouteProcess关联的任务
                existing_task = Task.objects.filter(
                    work_order=work_order,
                    route_process=route_process
                ).first()
                
                if not existing_task:
                    # 创建新任务，并关联到当前的RouteProcess
                    task = Task.objects.create(
                        work_order=work_order,
                        process=route_process.process,
                        status="pending",
                        route_process=route_process  # 关联到RouteProcess实例
                    )
                    created_count += 1
                    
                    # 记录日志，包含RouteProcess的ID和顺序
                    logger.debug(f"创建任务: 工单={work_order.id}, 工序={route_process.process.id}({route_process.process.name}), 顺序={route_process.order}")
            
            logger.info(f"工单 {work_order.id} 拆分成功，共创建 {created_count} 个新任务，工艺路线总工序数 {len(route_processes)}。")
        except Exception as e:
            logger.error(f"工单 {work_order.id} 拆分失败: {str(e)}")
            raise ValidationError({"error": "工单拆分失败，请联系管理员。"})

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        # 对于已排产工单的任务，限制修改权限
        if instance.work_order.status == "scheduled":
            # 检查是否修改了已完成或进行中的任务
            if instance.status in ["in_progress", "completed"]:
                raise ValidationError({"error": "已排产工单的进行中或已完成任务不允许修改。"})
        return super().update(request, *args, **kwargs)

class WorkOrderSplitView(APIView):
    """专门用于拆分工单的API视图"""
    
    def post(self, request, pk):
        try:
            work_order = WorkOrder.objects.get(pk=pk)
            # 检查工单是否已审核
            if work_order.status != "approved":
                return Response({"error": "只有已审核的工单才能拆分。"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 调用拆分工单的方法
            WorkOrderViewSet().split_work_order(work_order)
            
            # 更新工单状态为已排产
            work_order.status = "scheduled"
            work_order.save()
            
            serializer = WorkOrderSerializer(work_order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except WorkOrder.DoesNotExist:
            return Response({"error": "工单不存在。"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"拆分工单 {pk} 失败: {str(e)}")
            return Response({"error": "拆分工单失败，请联系管理员。"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)