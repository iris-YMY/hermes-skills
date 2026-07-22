---
name: feishu-doc-transfer
category: devops
description: 飞书文档转移至目标文件夹（含所有权转移）
---

# 飞书文档转移

## 流程（三步）

### Step 1: 添加用户为文档协作者
```
POST /drive/v1/permissions/{doc_id}/members?type=docx
tenant_token
body: {"member_type":"openid","member_id":"{user_ou}","perm":"full_access"}
```

### Step 2: 转移所有权
```
POST /drive/v1/permissions/{doc_id}/members/transfer_owner?type=docx
tenant_token
body: {"member_type":"openid","member_id":"{user_ou}"}
```

### Step 3: 移动文档
```
POST /drive/v1/files/{doc_id}/move
user_token（必须是用户OAuth token）
body: {"folder_token":"{target_folder}","type":"docx"}
```

## 要点
- 必须先 transfer_owner 再 move，否则报 `source parent no permission`
- move 必须用 user_token，tenant_token 报 `destination parent no permission`
- 转移后文档归属用户，链接不变
