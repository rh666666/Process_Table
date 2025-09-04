from django.db import models

class Process(models.Model):
    name = models.CharField(max_length=100, verbose_name="工序名称")
    description = models.TextField(blank=True, verbose_name="工序描述")

class RouteProcess(models.Model):
    """工序路线中间表，用于存储工序在工艺路线中的顺序"""
    route = models.ForeignKey('Route', on_delete=models.CASCADE, verbose_name="工艺路线")
    process = models.ForeignKey('Process', on_delete=models.CASCADE, verbose_name="工序")
    order = models.IntegerField(default=0, verbose_name="工序顺序")
    
    class Meta:
        ordering = ['order']
        unique_together = ['route', 'order']  # 确保每个工艺路线中的顺序唯一
        verbose_name = "工艺路线工序关系"
        verbose_name_plural = "工艺路线工序关系"

class Route(models.Model):
    name = models.CharField(max_length=100, verbose_name="工艺路线名称")
    processes = models.ManyToManyField(
        Process, 
        through='RouteProcess',
        through_fields=('route', 'process'),
        related_name="routes", 
        verbose_name="关联工序"
    )

class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('approved', '已审核'),
        ('scheduled', '已排产'),
    ]
    name = models.CharField(max_length=100, verbose_name="工单名称")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="状态")
    # 一个工单对应一条工艺路线
    route = models.OneToOneField(Route, on_delete=models.CASCADE, verbose_name="工艺路线")

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', '未生产'),
        ('unreported', '未报工'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
    ]
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="tasks", verbose_name="关联工单")
    process = models.ForeignKey(Process, on_delete=models.CASCADE, verbose_name="关联工序")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="任务状态")
    # 关联到工艺路线工序关系，用于处理重复工序的情况
    route_process = models.ForeignKey(
        'RouteProcess', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        verbose_name="关联工艺路线工序关系"
    )
