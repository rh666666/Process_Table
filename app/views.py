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
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.status == "scheduled":
            return Response({"error": "已排产的工单不可删除。"}, status=status.HTTP_400_BAD_REQUEST)
        return super().destroy(request, *args, **kwargs)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

class WorkOrderSplitView(APIView):
    def post(self, request, *args, **kwargs):
        work_order_id = request.data.get("work_order_id")
        process_ids = request.data.get("processes", [])

        try:
            work_order = WorkOrder.objects.get(id=work_order_id)
        except WorkOrder.DoesNotExist:
            return Response({"error": "工单不存在。"}, status=status.HTTP_404_NOT_FOUND)

        if work_order.status != "approved":
            return Response({"error": "只有已审核的工单可以拆分。"}, status=status.HTTP_400_BAD_REQUEST)

        processes = Process.objects.filter(id__in=process_ids)
        if not processes.exists():
            return Response({"error": "无效的工序 ID。"}, status=status.HTTP_400_BAD_REQUEST)

        # 拆分逻辑：为每个工序创建一个工序工单
        for process in processes:
            Task.objects.create(work_order=work_order, process=process)

        return Response({"message": "工单拆分成功。"}, status=status.HTTP_200_OK)
