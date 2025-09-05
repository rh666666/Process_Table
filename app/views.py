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
        
        if instance.status == "draft":
            if instance.is_scheduled:
                # 已排产的工单只能修改 route 字段
                if not all(key == "route" for key in request.data.keys()):
                    raise ValidationError({"error": "已排产的工单只能修改工艺路线。"})
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
                
        elif instance.status == "submitted" and not all(key == "status" for key in request.data.keys()):
            # 已提交状态下，只能修改 status 字段
            raise ValidationError({"error": "已提交的工单需要撤销提交后修改。"})
        elif instance.status == "approved" and not all(key == "status" for key in request.data.keys()):
            # 已审核状态下，只能修改 status 字段
            raise ValidationError({"error": "已审核的工单需要反审核后才能修改。"})
        
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_scheduled:
            return Response({"error": "已排产的工单不可删除。"}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

    def split_work_order(self, work_order):
        # 拆分工单的逻辑
        try:
            # 获取工单关联的工艺路线中的所有工序，并按照顺序字段排序
            route_processes = work_order.route.routeprocess_set.all().order_by('order')
            
            # 记录创建/更新的任务数量
            created_count = 0
            
            # 获取当前工单的所有任务
            existing_tasks = Task.objects.filter(work_order=work_order)
            
            # 获取当前工艺路线中的所有 RouteProcess 的 ID
            current_route_process_ids = [rp.id for rp in route_processes]
            
            # 删除不在当前工艺路线中的工序对应的任务
            for task in existing_tasks:
                if task.route_process.id not in current_route_process_ids:
                    task.delete()
                    logger.debug(f"删除任务: 工单={work_order.id}, 工序={task.process.id}({task.process.name})")

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
        if instance.work_order.is_scheduled:
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
            
            # 更新工单的已排产状态
            work_order.is_scheduled = True
            work_order.save()
            
            serializer = WorkOrderSerializer(work_order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except WorkOrder.DoesNotExist:
            return Response({"error": "工单不存在。"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"拆分工单 {pk} 失败: {str(e)}")
            return Response({"error": "拆分工单失败，请联系管理员。"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)