# GitHub 自动化陷阱 (2026-06-29 实战记录)

## 注册流程 (Signup)

### Arkose Labs CAPTCHA 阻断
- GitHub 使用 Arkose Labs 高级反机器人验证
- Headless browser 环境下 CAPTCHA iframe 无法加载（`js-octocaptcha-frame` 的 src 为空）
- 错误信号："You can't perform that action at this time"
- **解决方案**：必须人工完成注册，无法自动化

### 用户名规则
- ❌ 不允许下划线 `_`
- ✅ 只允许字母、数字、单个短横线 `-`
- ✅ 不能以短横线开头或结尾
- 示例：`iris_YMY` → 必须改为 `iris-YMY`

### 国家/地区选择
- Country dropdown 使用 Primer 组件，点击后不展开
- JavaScript 直接修改 hidden input 的 value 可以生效（`user_signup[country]` = `CN`）
- 但 UI 按钮文本不会同步更新

## 登录流程 (Login)

### 设备验证 (Device Verification)
- 从新设备登录必触发邮箱验证码
- 验证码有效期约 5 分钟，过期后需重新获取
- 错误信号："Incorrect verification code provided"

### Browser Session 不稳定
- CDP 频繁超时：`CDP command timed out: Page.navigate`
- 页面加载后 `browser_snapshot` 返回空（element_count: 0）
- 需要 `pkill -9 -f chrome` 强制重启浏览器
- 重启后所有表单数据丢失，需重新填写

### 表单交互陷阱
- `browser_type` 后 `ref` 可能失效（元素重新渲染）
- 解决方案：用 `browser_console` 直接操作 DOM
  ```javascript
  document.querySelector('#email').value = '...';
  document.querySelector('#email').dispatchEvent(new Event('input', {bubbles: true}));
  ```

## SSH Key 添加

- 登录后跳转 `/settings/ssh/new` 添加公钥
- 无特殊陷阱，标准流程

## GitHub CLI (gh) 安装

### Linux (Ubuntu)
- `apt install gh` 下载超时（14MB，网络慢）
- 备选：`snap install gh --classic`（更快）

### Windows (无管理员权限)
- ❌ `.msi` 安装包需要管理员权限
- ✅ `.zip` 免安装版可直接解压使用
- 下载链接：`https://github.com/cli/cli/releases/download/v{version}/gh_{version}_windows_amd64.zip`

## 最佳实践

1. **注册**：放弃自动化，提供注册信息让人工完成
2. **登录**：准备好快速输入验证码，5 分钟内完成
3. **浏览器重启**：遇到 CDP 超时就 `pkill -9 -f chrome`
4. **表单填写**：优先用 JavaScript 直接操作 DOM，避免 ref 失效
5. **SSH Key**：生成后直接提供公钥字符串，让人工添加
