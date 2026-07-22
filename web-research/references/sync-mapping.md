# Skill ↔ Feishu Doc 同步映射表

记录每个 Skill 对应的飞书文档 ID，用于后续更新操作。

## 格式
| Skill Name | Feishu Doc ID | URL | Status |
|------------|---------------|-----|--------|
| siff-schedule-planning | JRJYd1agmogzoixIcoyclX4lnCd | https://feishu.cn/docx/JRJYd1agmogzoixIcoyclX4lnCd | ✅ 行程文档（旧 SOP 文档 S150dtsqBoRugLxPppycFhBxn8e 已废弃） |

## 操作记录
- **2026-06-04**: 初次创建 siff-schedule-planning SOP 文档，Doc ID: S150dtsqBoRugLxPppycFhBxn8e
- **2026-06-05**: 创建实际观影行程文档，Doc ID: JRJYd1agmogzoixIcoyclX4lnCd（含已购票6场完整排片）
|---------|------|------|
| VE8JdUdL5onXmNxCtWqc6YCUng4 | ❌ 已删除 | API 返回 `1770003 resource deleted` (2026-06-05 验证) |

## 操作记录
- **2026-06-04**: 初次创建 siff-schedule-planning SOP 文档，放置于应用共享空间根目录，已赋予用户 full_access 权限。用户需手动移入「我的文件夹-Skills」。
- **2026-06-05**: 验证 VE8JdUdL5onXmNxCtWqc6YCUng4 已删除，S150dtsqBoRugLxPppycFhBxn8e 为活跃文档（Title: 📋 SIFF 观影行程定制 SOP, Revision: 4）。

## 注意事项
- 文档 ID 从创建 API 响应 `data.document.document_id` 或 URL `https://xxx.feishu.cn/docx/{doc_id}` 中提取。
- 更新 Skill 时，**必须**使用此表中记录的 Doc ID，严禁新建。
- 若用户移动了文档位置，Doc ID 不变，无需更新此表。
- 写入前先 `GET /docx/v1/documents/{doc_id}` 验证文档是否存在（返回 `1770003` 表示已删除）。
