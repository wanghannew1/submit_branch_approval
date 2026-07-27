# Project Rules

## 禁止调用子代理

本项目所有会话中，严禁调用任何子代理（sub-agent）。包括但不限于：`task()` 函数调用（无论是否指定 `category` 或 `subagent_type`）、`explore`、`librarian`、`oracle`、`metis`、`momus`、`quick`、`deep` 等所有分类的子代理。

所有工作必须由主会话直接完成，使用直接工具（read、write、edit、grep、glob、bash 等）进行操作。
