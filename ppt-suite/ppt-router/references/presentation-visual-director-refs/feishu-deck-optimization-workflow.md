# 飞书 PPT 链接 → 诊断报告 → 优化 端到端流程

> 实测于 LB_Operation_Traffic_v8.pptx 优化（2026-08-08）。用户给 `feishu.cn/file/<token>` 链接要求"优化 PPT"时按此流程走。

## 1. 下载（file 类型）

```bash
# 确认 doc_type（file 类型 = feishu.cn/file/ 链接）
TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d '{"app_id":"<APP_ID>","app_secret":"<APP_SECRET>"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['tenant_access_token'])")
curl -s -X POST "https://open.feishu.cn/open-apis/drive/v1/metas/batch_query" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"request_docs":[{"doc_token":"<FILE_TOKEN>","doc_type":"file"}]}'

# ⚠️ 下载必须用 files 接口（medias 接口对 file 类型返回 0 字节！）
curl -s -L "https://open.feishu.cn/open-apis/drive/v1/files/<FILE_TOKEN>/download" \
  -H "Authorization: Bearer $TOKEN" -o /tmp/deck.pptx
```

凭证：default app `cli_aa9970856879dcd8` 可用（.env 读取）。

## 2. 渲染（soffice + pymupdf，用 /usr/bin/python3）

```bash
timeout 180 soffice --headless --convert-to pdf --outdir /tmp /tmp/deck.pptx
/usr/bin/python3 -c "
import pymupdf
doc = pymupdf.open('/tmp/deck.pdf')
for i in range(len(doc)):
    pix = doc[i].get_pixmap(dpi=130)
    pix.save(f'/tmp/render/P{i+1:02d}.png')
"
```

## 3. 文本溢出自动检查（先于视觉）

```python
import pymupdf
doc = pymupdf.open('/tmp/deck.pdf')
W, H = doc[0].rect.width, doc[0].rect.height
for i in range(len(doc)):
    for b in doc[i].get_text('blocks'):
        if b[2] > W-3 or b[3] > H-3 or b[0] < 0 or b[1] < 0:
            print(f'P{i+1} 溢出: {b[:4]} {b[4][:30]!r}')
```
页面底部标题贴边（y1 ≈ H-2~8）是常见小问题，列入 B 级优化。

## 4. 拼 3×3 总览图（PIL）

```python
from PIL import Image
imgs = [Image.open(f) for f in sorted(glob.glob('/tmp/render/P*.png'))]
w,h = imgs[0].size; pad=20; cols=3
grid = Image.new('RGB',(cols*w+pad*(cols+1), len(imgs)//cols*h+pad*(len(imgs)//cols+1)),(255,255,255))
for idx,img in enumerate(imgs):
    r,c = divmod(idx,cols); grid.paste(img,(pad+c*(w+pad), pad+r*(h+pad)))
```

## 5. 逐页 vision 诊断（并行调用）

`vision_analyze` 对每页 PNG 提问（deepseek 下实测可用）。并行 2-4 页一次。
- 关键页必查：封面（P1）、数据页、内容密集页、末页
- 提问模板：评估文字是否拥挤/大段堆叠？模块排版是否整齐？图表/数字是否突出？主要优化点？
- vision 输出常含具体优化建议（缺 logo、术语未解释、占比逻辑瑕疵等），逐条记录

## 6. 诊断报告分级（汇报给用户，确认方向后再动手）

- ✅ 已做对的（版式统一/无堆叠/图片角色正确）——先肯定，用户在意
- 🔧 可优化点分三级：
  - **A 数据可视化缺失**（占比/进度数据存在但纯文字 → 建议图表）——最优先，直接呼应"什么时候用图表"
  - **B 视觉打磨**（缺 logo、页脚贴边、说明条过长、流程缺箭头）
  - **C 术语统一**（缩写首次出现加全称；拼音缩写注释；X% 给参考范围）——涉及改文案，须用户拍板
- 给选项：A+B 全做（推荐，内容不动）/ 只做 A / A+B+C
- **等用户确认方向再开工**；做完出图片版 review（MEDIA 或飞书链接），确认后才交付 PPTX

## 踩坑记录

- `drive/v1/medias/{token}/download` 对 file 类型返回 0 字节 → 换 `drive/v1/files/{token}/download`
- lark-cli `doc download` 可能报 SCOPE_ERROR（缺 drive scopes）→ 直接 API 下载
- 首轮 PDF 转换后 python3（hermes venv）无 pymupdf → 用 `/usr/bin/python3`
- 所有 PPT 页常引用同一批模板图片资源，get_images() 计数会虚高（如每页都报 29），不要据此判断页面图片多少
