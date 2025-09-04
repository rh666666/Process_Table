"""
URL configuration for Process_Table project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from app.views import ProcessViewSet, RouteViewSet, WorkOrderViewSet, TaskViewSet, WorkOrderSplitView

router = DefaultRouter()
router.register(r'processes', ProcessViewSet)
router.register(r'routes', RouteViewSet)
router.register(r'workorders', WorkOrderViewSet)
router.register(r'tasks', TaskViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),  # 确保 API 路由已包含
    # 新增拆分工单的API路由
    path('api/workorders/<int:pk>/split/', WorkOrderSplitView.as_view(), name='workorder_split'),
]
