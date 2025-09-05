# 工序表管理系统 API 文档

## 1. 概述

本文档描述了工序表管理系统的API接口，用于管理工序、工艺路线、工单和任务等数据。系统基于Django REST Framework开发，提供了完整的RESTful API接口。

## 2. 基础URL

所有API请求的基础URL为：`/api/`

## 3. API端点列表

| 资源 | 描述 | 基础URL |
|------|------|---------|
| 工序(Process) | 工序信息的管理 | `/api/processes/` |
| 工艺路线(Route) | 工艺路线的管理 | `/api/routes/` |
| 工单(WorkOrder) | 工单的管理 | `/api/workorders/` |
| 任务(Task) | 任务的管理 | `/api/tasks/` |
| 拆分工单 | 将审核后的工单拆分为任务 | `/api/workorders/<pk>/split/` |

## 4. 工序(Process) API

### 4.1 获取所有工序

**请求方法**: GET
**请求URL**: `/api/processes/`
**请求参数**: 无

**响应示例**: 
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "冲压",
      "description": "金属冲压成型工艺"
    },
    {
      "id": 2,
      "name": "焊接",
      "description": "金属部件焊接工艺"
    }
  ]
}
```

### 4.2 获取单个工序

**请求方法**: GET
**请求URL**: `/api/processes/<id>/`
**请求参数**: 无

**响应示例**: 
```json
{
  "id": 1,
  "name": "冲压",
  "description": "金属冲压成型工艺"
}
```

### 4.3 创建工序

**请求方法**: POST
**请求URL**: `/api/processes/`
**请求参数**: 
```json
{
  "name": "喷漆",
  "description": "表面喷漆处理工艺"
}
```

**响应示例**: 
```json
{
  "id": 3,
  "name": "喷漆",
  "description": "表面喷漆处理工艺"
}
```

### 4.4 更新工序

**请求方法**: PUT/PATCH
**请求URL**: `/api/processes/<id>/`
**请求参数**: 
```json
{
  "name": "喷漆(更新)",
  "description": "表面喷漆处理工艺(更新)"
}
```

**响应示例**: 
```json
{
  "id": 3,
  "name": "喷漆(更新)",
  "description": "表面喷漆处理工艺(更新)"
}
```

### 4.5 删除工序

**请求方法**: DELETE
**请求URL**: `/api/processes/<id>/`
**请求参数**: 无

**响应**: 204 No Content

## 5. 工艺路线(Route) API

### 5.1 获取所有工艺路线

**请求方法**: GET
**请求URL**: `/api/routes/`
**请求参数**: 无

**响应示例**: 
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "标准冲压件工艺路线",
      "processes": [
        {
          "id": 1,
          "process": {
            "id": 1,
            "name": "冲压",
            "description": "金属冲压成型工艺"
          },
          "order": 1
        },
        {
          "id": 2,
          "process": {
            "id": 2,
            "name": "焊接",
            "description": "金属部件焊接工艺"
          },
          "order": 2
        }
      ]
    }
  ]
}
```

### 5.2 获取单个工艺路线

**请求方法**: GET
**请求URL**: `/api/routes/<id>/`
**请求参数**: 无

**响应示例**: 
```json
{
  "id": 1,
  "name": "标准冲压件工艺路线",
  "processes": [
    {
      "id": 1,
      "process": {
        "id": 1,
        "name": "冲压",
        "description": "金属冲压成型工艺"
      },
      "order": 1
    },
    {
      "id": 2,
      "process": {
        "id": 2,
        "name": "焊接",
        "description": "金属部件焊接工艺"
      },
      "order": 2
    }
  ]
}
```

### 5.3 创建工艺路线

**请求方法**: POST
**请求URL**: `/api/routes/`
**请求参数**: 
```json
{
  "name": "新产品工艺路线",
  "process_relations": [
    {
      "process": 1,
      "order": 1
    },
    {
      "process": 2,
      "order": 2
    },
    {
      "process": 3,
      "order": 3
    }
  ]
}
```

**响应示例**: 
```json
{
  "id": 2,
  "name": "新产品工艺路线",
  "processes": [
    {
      "id": 3,
      "process": {
        "id": 1,
        "name": "冲压",
        "description": "金属冲压成型工艺"
      },
      "order": 1
    },
    {
      "id": 4,
      "process": {
        "id": 2,
        "name": "焊接",
        "description": "金属部件焊接工艺"
      },
      "order": 2
    },
    {
      "id": 5,
      "process": {
        "id": 3,
        "name": "喷漆",
        "description": "表面喷漆处理工艺"
      },
      "order": 3
    }
  ]
}
```

### 5.4 更新工艺路线

**请求方法**: PUT/PATCH
**请求URL**: `/api/routes/<id>/`
**请求参数**: 
```json
{
  "name": "新产品工艺路线(更新)",
  "process_relations": [
    {
      "process": 1,
      "order": 1
    },
    {
      "process": 3,
      "order": 2
    }
  ]
}
```

**响应示例**: 
```json
{
  "id": 2,
  "name": "新产品工艺路线(更新)",
  "processes": [
    {
      "id": 6,
      "process": {
        "id": 1,
        "name": "冲压",
        "description": "金属冲压成型工艺"
      },
      "order": 1
    },
    {
      "id": 7,
      "process": {
        "id": 3,
        "name": "喷漆",
        "description": "表面喷漆处理工艺"
      },
      "order": 2
    }
  ]
}
```

### 5.5 删除工艺路线

**请求方法**: DELETE
**请求URL**: `/api/routes/<id>/`
**请求参数**: 无

**响应**: 204 No Content

## 6. 工单(WorkOrder) API

### 6.1 获取所有工单

**请求方法**: GET
**请求URL**: `/api/workorders/`
**请求参数**: 无

**响应示例**: 
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "WO-2023-001",
      "status": "draft",
      "route": 1,
      "task_count": 0
    }
  ]
}
```

### 6.2 获取单个工单

**请求方法**: GET
**请求URL**: `/api/workorders/<id>/`
**请求参数**: 无

**响应示例**: 
```json
{
  "id": 1,
  "name": "WO-2023-001",
  "status": "draft",
  "route": 1,
  "task_count": 0
}
```

### 6.3 创建工单

**请求方法**: POST
**请求URL**: `/api/workorders/`
**请求参数**: 
```json
{
  "name": "WO-2023-002",
  "status": "draft",
  "route": 1
}
```

**响应示例**: 
```json
{
  "id": 2,
  "name": "WO-2023-002",
  "status": "draft",
  "route": 1,
  "task_count": 0
}
```

### 6.4 更新工单

**请求方法**: PUT/PATCH （强烈建议使用 PATCH 修改工单）
**请求URL**: `/api/workorders/<id>/`

**状态转换规则**: 
- 草稿状态(`draft`)：可以修改所有字段，但状态只能改为已提交(`submitted`)
- 已提交状态(`submitted`)：只能修改状态字段
- 已审核状态(`approved`)：需要反审核后才能修改
- 已排产的工单：只能修改工艺路线字段

**请求参数示例** (提交工单): 
```json
{
  "status": "submitted"
}
```

**响应示例**: 
```json
{
  "id": 2,
  "name": "WO-2023-002",
  "status": "submitted",
  "route": 1,
  "task_count": 0
}
```

### 6.5 删除工单

**请求方法**: DELETE
**请求URL**: `/api/workorders/<id>/`
**请求参数**: 无

**注意**: 已排产的工单不可删除

**响应**: 204 No Content 或 400 Bad Request (如果工单已排产)

## 7. 任务(Task) API

### 7.1 获取所有任务

**请求方法**: GET
**请求URL**: `/api/tasks/`
**请求参数**: 无

**响应示例**: 
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "work_order": 1,
      "process": 1,
      "status": "pending",
      "work_order_name": "WO-2023-001",
      "process_name": "冲压"
    },
    {
      "id": 2,
      "work_order": 1,
      "process": 2,
      "status": "pending",
      "work_order_name": "WO-2023-001",
      "process_name": "焊接"
    }
  ]
}
```

### 7.2 获取单个任务

**请求方法**: GET
**请求URL**: `/api/tasks/<id>/`
**请求参数**: 无

**响应示例**: 
```json
{
  "id": 1,
  "work_order": 1,
  "process": 1,
  "status": "pending",
  "work_order_name": "WO-2023-001",
  "process_name": "冲压"
}
```

### 7.3 创建任务

**请求方法**: POST
**请求URL**: `/api/tasks/`
**请求参数**: 
```json
{
  "work_order": 1,
  "process": 3,
  "status": "pending"
}
```

**响应示例**: 
```json
{
  "id": 3,
  "work_order": 1,
  "process": 3,
  "status": "pending",
  "work_order_name": "WO-2023-001",
  "process_name": "喷漆"
}
```

### 7.4 更新任务

**请求方法**: PUT/PATCH
**请求URL**: `/api/tasks/<id>/`

**注意**: 已排产工单的进行中或已完成任务不允许修改

**请求参数示例** (更新任务状态): 
```json
{
  "status": "in_progress"
}
```

**响应示例**: 
```json
{
  "id": 1,
  "work_order": 1,
  "process": 1,
  "status": "in_progress",
  "work_order_name": "WO-2023-001",
  "process_name": "冲压"
}
```

### 7.5 删除任务

**请求方法**: DELETE
**请求URL**: `/api/tasks/<id>/`
**请求参数**: 无

**响应**: 204 No Content

## 8. 拆分工单 API

### 8.1 拆分工单

**请求方法**: POST
**请求URL**: `/api/workorders/<pk>/split/`
**请求参数**: 无

**注意**: 只有已审核的工单才能拆分

**响应示例**: 
```json
{
  "id": 1,
  "name": "WO-2023-001",
  "status": "approved",
  "route": 1,
  "task_count": 2
}
```

## 9. 错误处理

系统会返回适当的HTTP状态码和错误信息：

| 状态码 | 错误信息示例 | 说明 |
|--------|-------------|------|
| 400 | {"error": "已排产的工单只能修改工艺路线。"} | 请求参数错误或操作不允许 |
| 404 | {"error": "工单不存在。"} | 请求的资源不存在 |
| 500 | {"error": "拆分工单失败，请联系管理员。"} | 服务器内部错误 |

## 10. 状态码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功 |
| 400 | 错误的请求 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

## 11. 数据模型关系图

- 工艺路线(Route)包含多个工序(Process)，通过RouteProcess中间表维护顺序
- 工单(WorkOrder)关联一条工艺路线
- 工单拆分为多个任务(Task)，每个任务对应工艺路线中的一个工序

## 12. 使用示例

### 12.1 创建工艺路线并添加工序

```javascript
// 创建工艺路线
fetch('/api/routes/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: '产品A工艺路线',
    process_relations: [
      { process: 1, order: 1 },
      { process: 2, order: 2 },
      { process: 3, order: 3 }
    ]
  })
})
.then(response => response.json())
.then(data => console.log(data));
```

### 12.2 创建工单并拆分

```javascript
// 创建工单
fetch('/api/workorders/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'WO-2023-003',
    status: 'draft',
    route: 1
  })
})
.then(response => response.json())
.then(workOrder => {
  // 提交工单
  return fetch(`/api/workorders/${workOrder.id}/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ status: 'submitted' })
  });
})
.then(response => response.json())
.then(workOrder => {
  // 审核工单
  return fetch(`/api/workorders/${workOrder.id}/`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ status: 'approved' })
  });
})
.then(response => response.json())
.then(workOrder => {
  // 拆分工单
  return fetch(`/api/workorders/${workOrder.id}/split/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  });
})
.then(response => response.json())
.then(data => console.log('工单拆分成功:', data));
```

## 13. 注意事项

1. 所有API请求需要根据系统配置进行身份验证
2. 操作工单时需要遵循状态转换规则
3. 拆分工单前请确保工单已审核
4. 已排产的工单和任务有特定的修改限制