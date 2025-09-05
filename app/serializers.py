from rest_framework import serializers
from .models import Process, Route, WorkOrder, Task, RouteProcess

class ProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = Process
        fields = ['id', 'name', 'description']

class RouteProcessSerializer(serializers.ModelSerializer):
    """序列化工艺路线与工序的关系，包含顺序信息"""
    process = ProcessSerializer()
    
    class Meta:
        model = RouteProcess
        fields = ['id', 'process', 'order']
        read_only_fields = ['id']

class RouteProcessCreateUpdateSerializer(serializers.ModelSerializer):
    """用于创建和更新工艺路线与工序关系的序列化器"""
    class Meta:
        model = RouteProcess
        fields = ['process', 'order']

class RouteSerializer(serializers.ModelSerializer):
    # 使用嵌套序列化器显示关联的工序及其顺序
    processes = RouteProcessSerializer(source='routeprocess_set', many=True, read_only=True)
    # 用于创建和更新的工序数据
    process_relations = RouteProcessCreateUpdateSerializer(many=True, write_only=True, required=False)
    
    class Meta:
        model = Route
        fields = ['id', 'name', 'processes', 'process_relations']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        # 获取工序关系数据
        process_relations_data = validated_data.pop('process_relations', [])
        # 创建工艺路线
        route = Route.objects.create(**validated_data)
        # 创建工序关系
        for relation_data in process_relations_data:
            RouteProcess.objects.create(route=route, **relation_data)
        return route
    
    def update(self, instance, validated_data):
        # 获取工序关系数据
        process_relations_data = validated_data.pop('process_relations', None)
        # 更新工艺路线基本信息
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        
        # 如果提供了工序关系数据，则更新
        if process_relations_data is not None:
            # 清除现有关系
            instance.routeprocess_set.all().delete()
            # 创建新的关系
            for relation_data in process_relations_data:
                RouteProcess.objects.create(route=instance, **relation_data)
        
        return instance

class WorkOrderSerializer(serializers.ModelSerializer):
    # 显示工艺路线详情
    route = serializers.PrimaryKeyRelatedField(queryset=Route.objects.all())
    # 显示关联的任务数量
    task_count = serializers.SerializerMethodField()
    
    def get_task_count(self, obj):
        return obj.tasks.count()
    
    def validate_status(self, value):
        # 工单状态变更验证
        instance = self.instance
        if instance:
            # 草稿状态下，所有字段都可以修改，但状态只能改为已提交
            if instance.status == 'draft' and value != 'submitted':
                raise serializers.ValidationError("请先提交工单。")
            # 已经审核的工单，需要反审核后修改
            if instance.status == 'approved' and value == 'draft':
                raise serializers.ValidationError("请先反审核。")
            
        return value
    
    class Meta:
        model = WorkOrder
        fields = ['id', 'name', 'status', 'route', 'task_count', 'is_scheduled']
        read_only_fields = ['task_count']

class TaskSerializer(serializers.ModelSerializer):
    # 显示工单和工序详情
    work_order = serializers.PrimaryKeyRelatedField(queryset=WorkOrder.objects.all())
    process = serializers.PrimaryKeyRelatedField(queryset=Process.objects.all())
    
    # 显示工单和工序的名称信息
    work_order_name = serializers.ReadOnlyField(source='work_order.name')
    process_name = serializers.ReadOnlyField(source='process.name')
    
    def validate(self, data):
        # 验证已排产工单的任务状态变更
        instance = self.instance
        work_order = data.get('work_order') or (instance.work_order if instance else None)
        
        if work_order and work_order.is_scheduled:
            # 对于已排产的工单，不允许修改已完成或进行中的任务
            if instance and instance.status in ['in_progress', 'completed']:
                raise serializers.ValidationError("已排产工单的进行中或已完成任务不允许修改。")
            
            # 检查是否修改了任务状态
            if 'status' in data and instance:
                # 获取当前任务关联的工艺路线工序关系
                current_route_process = instance.route_process
                if not current_route_process:
                    # 如果没有关联的RouteProcess，则跳过这个验证
                    return data
                
                # 获取同一工艺路线中的所有工序及其顺序
                all_route_processes = work_order.route.routeprocess_set.all().order_by('order')
                
                # 找到当前任务在工艺路线中的位置
                current_order = current_route_process.order
                
                # 检查所有前置工序是否已完成
                for route_process in all_route_processes:
                    if route_process.order < current_order:
                        # 获取对应的任务
                        task = Task.objects.filter(
                            work_order=work_order,
                            route_process=route_process
                        ).first()
                        if task and task.status != 'completed':
                            raise serializers.ValidationError("只有当前置所有工序已完成时，才能修改该工序的状态。")
                
                # 检查所有后置工序是否为未生产状态
                for route_process in all_route_processes:
                    if route_process.order > current_order:
                        # 获取对应的任务
                        task = Task.objects.filter(
                            work_order=work_order,
                            route_process=route_process
                        ).first()
                        if task and task.status != 'pending':
                            raise serializers.ValidationError("只有当后置所有工序为未生产状态时，才能修改该工序的状态。")
        
        return data
    
    class Meta:
        model = Task
        fields = ['id', 'work_order', 'work_order_name', 'process', 'process_name', 'status']