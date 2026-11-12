# Task Center (任务中枢)

由 **AstrBot (IM 入口)** 与 **反重力 (Antigravity 本地特工)** 协同驱动的任务与产物中心。

## 📌 架构与工作流

```
[QQ / 微信]
    │ 1. 提出需求
    ▼
[AstrBot @ GCP]
    │ 2. 在 task-center 仓库建 Issue，打上 label: antigravity
    ▼
[GitHub Issue]
    │ 3. 本地反重力感知到 Issue
    ▼
[本地反重力 (Antigravity)]
    │ 4. 在 task-center/ 创建 issue-xxx 子目录
    │ 5. 自主解决任务、跑通验证
    │ 6. 提交 Git Commit 并向 Issue 汇报
    ▼
[AstrBot -> IM]
    └─ 7. QQ 收到任务完成汇报通知
```

## 📂 目录结构规范

每个 Issue 任务完成后，产物将归档在独立的子目录中：

```
task-center/
├── .github/
├── README.md
├── issue-1/      # Issue #1 的任务产物与交付成果
├── issue-2/      # Issue #2 的任务产物与交付成果
└── ...
```
