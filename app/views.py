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
        if instance.status == "approved" and request.data.get("status") == "draft":
            raise ValidationError({"error": "已审核的工单不能变更为草稿状态。"})
        # 如果工单状态改为已排产，则自动拆分工单
        if request.data.get("status") == "scheduled":
            self.split_work_order(instance)
        
        #已经排产的工单，只能修改待处理和未报工的任务
        if instance.status == "scheduled":
            tasks = instance.tasks.filter(status__in=["pending", "unreported"])
            allowed_process_ids = [task.process.id for task in tasks]
            if "processes" in request.data:
                for process_id in request.data["processes"]:
                    if process_id not in allowed_process_ids:
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
            processes = Process.objects.all()
            for process in processes:
                Task.objects.create(work_order=work_order, process=process)
            logger.info(f"工单 {work_order.id} 拆分成功。")
        except Exception as e:
            logger.error(f"工单 {work_order.id} 拆分失败: {str(e)}")
            raise ValidationError({"error": "工单拆分失败，请联系管理员。"})

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer