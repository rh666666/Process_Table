from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProcessViewSet, RouteViewSet, WorkOrderViewSet, TaskViewSet

# 创建router实例
router = DefaultRouter()
router.register(r'processes', ProcessViewSet)
router.register(r'routes', RouteViewSet)
router.register(r'workorders', WorkOrderViewSet)
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
