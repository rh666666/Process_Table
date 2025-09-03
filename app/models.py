from django.db import models

class Process(models.Model):
    name = models.CharField(max_length=100, verbose_name="工序名称")
    description = models.TextField(blank=True, verbose_name="工序描述")

class Route(models.Model):
    name = models.CharField(max_length=100, verbose_name="工艺路线名称")
    processes = models.ManyToManyField(Process, related_name="routes", verbose_name="关联工序")

class WorkOrder(models.Model):
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('approved', '已审核'),
        ('scheduled', '已排产'),
    ]
    name = models.CharField(max_length=100, verbose_name="工单名称")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', verbose_name="状态")

class Task(models.Model):
    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name="tasks", verbose_name="关联工单")
    process = models.ForeignKey(Process, on_delete=models.CASCADE, verbose_name="关联工序")
    status = models.CharField(max_length=20, default='pending', verbose_name="任务状态")
