---
name: ppt-delivery
description: PPT/Deck 正式交付规范（统一出口）。任何经 ppt-production-qa 验收 PASS 的 PPT 制品，正式交付前必须遵循本 skill：命名规范（项目-任务-日期-版本号）、归档位置（飞书云空间指定文件夹）、交付格式（pptx）、上传确认流程（视觉批准 ≠ 上传确认，须用户明确上传指令）、版本管理（新版本不覆盖历史版本）。触发词：交付、上传、归档、发文件、deliver。
---

# PPT 正式交付规范

PPT 生产流水线的最终出口。**前置条件：制品已通过 `ppt-production-qa` 验收（PASS / PASS_WITH_APPROVED_EXCEPTIONS）**。未验收或验收 FAIL 的制品禁止进入交付流程。

## 流水线位置

```
ppt-production-qa（验收 PASS）
  → ppt-delivery（本 skill：命名 → 归档 → 上传确认 → 交付）← 正式交付
```

## 1. 命名规范（用户确认，2026-08-08）

格式：**`xxxx（项目名称）-xxx（任务名称）-xxx（日期）-versionx（版本号）`**

- 项目名称：品牌/项目名（如 LB 提案 → `LB提案`）
- 任务名称：本次任务内容（如 `内容页改造`、`全渠道策略页`）
- 日期：任务产出日期，格式 `YYYYMMDD`（如 `20260808`）
- 版本号：`version` + 数字（如 `version1`、`version2`）
- 分隔符：统一用**英文连字符 `-`**，文件名内不再使用空格/中文标点/其他分隔符

示例：
- `LB提案-内容页改造-20260808-version8.pptx`
- `JACQUEMUS提案-全渠道策略-20260807-version3.pptx`

## 2. 归档位置（用户指定，2026-08-08）

- 飞书云空间文件夹（固定）：`https://e1kg6bc4dl9.feishu.cn/drive/folder/R4IHfas5VlWqpOdQzMbc5Kxvngh`
- 文件夹 token：`R4IHfas5VlWqpOdQzMbc5Kxvngh`（parent_type=explorer）
- 上传接口：`POST /drive/v1/files/upload_all`（user OAuth token + `drive:drive` scope），parent_node = 上述 token
- 上传成功后必须**回贴文件链接**（云空间链接），不得只报"已上传"

## 3. 交付格式

- 正式交付物格式：**pptx**（可编辑 PPTX）
- 用户额外要求时附 PDF 预览版，但**主交付物始终是 pptx**
- image-only 路径（rw-consulting-ppt）交付：image-only PPTX（每页一张整页图）或整页 PNG 包，打包规则按 `ppt-production-qa` image-only 模式

## 4. 上传确认流程（用户明确纠正，2026-08-08）

**视觉批准 ≠ 上传确认。** 两条确认必须分开、都必须获得：

1. **视觉批准**：用户对渲染图/预览说"可以""OK""这版好" → 仅代表内容与排版通过，**不代表允许上传**
2. **上传确认**：用户明确下达上传指令（如"上传吧""发我文件""传到云空间"）→ 才可执行上传

- 未收到明确上传指令前：不得上传云空间、不得发文件链接、不得交付 PPTX 附件
- 用户只说"看下""改一下""调整"→ 不构成任何批准
- 交付完成后告知用户文件名 + 云空间链接

## 5. 版本管理（用户明确要求，2026-08-08）

- **最新版本不得覆盖历史版本**：每个版本都是独立文件，按命名规范带版本号保存
- 迭代方式：新版本 = 新文件名（版本号递增），旧版本文件保留在原位不动
- 禁止行为：用 v9 覆盖 v8 文件、原地覆盖同名文件、删除历史版本
- 交付时若同项目有多个版本，可列出版本清单供用户追溯，但**不删除、不移动**任何历史文件

## 6. 交付清单（每次交付确认）

- [ ] 制品已通过 ppt-production-qa（记录 Mode / Status）
- [ ] 文件名符合命名规范（项目-任务-日期-versionN）
- [ ] 上传至指定云空间文件夹（token R4IHfas5VlWqpOdQzMbc5Kxvngh）
- [ ] 已获得用户明确上传指令（非仅视觉批准）
- [ ] 未覆盖任何历史版本
- [ ] 回贴文件链接

## 7. 相关技能

- 上游：ppt-production-qa（验收）、ppt-master / rw-consulting-ppt / ecommerce-proposal-ppt（生产）
- 路由：ppt-router（入口判定）
- 飞书上传细节：feishu-hermes-integration skill（user OAuth、upload_all、大文件处理）
