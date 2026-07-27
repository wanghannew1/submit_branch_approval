# Excel 合并单元格填充策略

## 问题

用 openpyxl 读 Excel 时，合并单元格只有**左上角**有值，其余位置返回 `None`。这在解析组合表头时会导致问题：

```
K3:L3 合并 = "养老"
R3 col 10 = '养老' (左上角，有值)
R3 col 11 = None   (合并区域，被 openpyxl 置空)
```

当用 `["养老|个人"]` AND 关键字匹配时，col 11 的组合文本只有 `"单位16%"`，缺少 `"养老"`，永远匹配不上——即使 col 11 确实是"养老"类别下的子列（如养老单位/养老个人）。

## 方案

读取 Excel 后，用 `_fill_merged_cells()` 把合并单元格左上角的值**向右填充**到合并区域的所有 `None` 位置。

### 实现

`demo_app.py` — `_fill_merged_cells()`

```python
def _fill_merged_cells(ws, rows):
    """将合并单元格左上角的值填充到合并区域的其他单元格（仅填充 None 位置）。"""
    result = [list(row) for row in rows]
    for mc in ws.merged_cells.ranges:
        top_val = result[mc.min_row - 1][mc.min_col - 1]
        if top_val is None:
            continue
        for r in range(mc.min_row - 1, mc.max_row):
            for c in range(mc.min_col - 1, mc.max_col):
                if result[r][c] is None:
                    result[r][c] = top_val
    return result
```

在 `_read_sheet_rows()` 的 openpyxl 分支末尾调用：

```python
rows = list(ws.iter_rows(values_only=True))
return _fill_merged_cells(ws, rows)
```

> **注意**：只对 openpyxl 路径（`.xlsx`）生效。`.xls` 走 xlrd，不调用此函数——xlrd 对合并单元格的行为不同，实测不影响。

### 效果

| 位置 | 填充前 | 填充后 |
|------|--------|--------|
| R3 col 10 (K3，左上角) | `"养老"` | `"养老"` |
| R3 col 11 (L3，合并区) | `None` | `"养老"` ✅ |

### 为何只横向填充重要

组合表头场景中，合并单元格通常是**横向合并**（如 "养老" 跨两列，"本月扣款" 跨五列）。纵向合并（如标题行跨多行）也会被填充，但那些值通常与列匹配关键字无关，不影响搜索。

### 典型布局

天池酒店工资表（outstaff 格式）的表头结构：

```
R2: col 10 = "本月扣款" (合并 K2:O2，覆盖 col 10-14)
R3: col 10 = "养老"     (合并 K3:L3，覆盖 col 10-11)
    col 12 = "失业"     (合并 M3:N3，覆盖 col 12-13)
    col 14 = "工伤"
R4: col 10 = "个人8%"
    col 11 = "单位16%"
    col 12 = "个人0.3%"
    col 13 = "单位0.7%"
    col 14 = "单位0.48%"
```

填充后，组合文本（跨行合并）为：

| 列 | 组合文本 | AND 匹配 |
|----|----------|----------|
| col 10 | `本月扣款 养老 个人8%` | `["养老\|个人"]` → ✅ 养老个人 |
| col 11 | `本月扣款 养老 单位16%` | `["养老\|个人"]` → ❌ (缺"个人") |
| col 12 | `失业 个人0.3%` | `["失业\|个人"]` → ✅ 失业个人 |
| col 13 | `失业 单位0.7%` | `["失业\|个人"]` → ❌ (缺"个人") |
| col 14 | `工伤 单位0.48%` | `["工伤\|单位"]` → ✅ 工伤单位 |

### 健壮性

即使某张表的布局变成"单位在左、个人在右"（`col 10=单位16%, col 11=个人8%`），由于合并填充后 col 10 和 col 11 都有 `"养老"`，AND 匹配仍能正确找到个人列：

| 布局 | 个人在左 (现表) | 个人在右 (假设) |
|------|:--:|:--:|
| `["养老\|个人"]` → col 10 | ✅ (养老+个人) | ❌ (养老+单位) |
| `["养老\|个人"]` → col 11 | ❌ (养老+单位) | ✅ (养老+个人) |
| **结果** | **ep=col 10** | **ep=col 11** |
