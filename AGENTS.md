# RatShell Agent 开发规范

## 版本管理

- 版本号格式：`VX.X.X`
- 当前版本：`V1.2.3`
- **每次对代码的任何修改**（新增功能、修复 bug、重构等），必须在 `app/resources.py` 中递增版本号
- 版本号递增规则：
  - 大版本重构/不兼容变更 → X.0.0
  - 新增功能 → X.X.0
  - Bug 修复/小改动 → X.X.X

## 构建与运行

```bash
pip install -r requirements.txt
python main.py
```

## 项目结构

```
main.py         入口
app/
  resources.py  常量 + 主题样式表（版本号在此）
  main_window.py 主窗口
  ...
```

## 约定

- 所有修改必须同步更新 `APP_VERSION` 字符串（直接搜索即可定位）
- 修改完成后执行 `python main.py` 检查是否可启动
