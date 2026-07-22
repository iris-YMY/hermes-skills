# SSPanel / Metron Proxy Service Investigation

## Context
Chinese proxy/VPN services ("机场"/梯子) commonly use SSPanel-Uim or V2Board with the Metron theme. When evaluating a service for feasibility (registration, pricing, node quality), these patterns help.

## Identifying Panel Type
- **Metron theme markers**: CSS paths like `/theme/metron/css/style.bundle.css`, `/theme/img/` logo, particle animation on login/register pages
- **SSPanel API structure**: Endpoints like `/auth/register`, `/auth/login`, `/user` (dashboard redirect), `/shop` (plans)
- **V2Board markers**: Different API structure, uses `/api/v1/` prefix

## Registration Page Analysis (curl)
1. Fetch the register page HTML
2. Extract `<input>` fields to find required form fields (name, email, password, invitation code, email verification code)
3. Check for captcha: Tencent captcha, Cloudflare Turnstile, reCAPTCHA
4. Password rules are usually embedded in the page (min length, character class requirements)

## Extracting Inline `loginConfig` (Highest Signal, Easiest)
The registration page HTML contains an inline `<script>` with a `var loginConfig` object. This is far easier to read than the obfuscated `auth.min.js` and reveals critical config:

```bash
curl -sL "https://domain/auth/register" | grep -A20 "var loginConfig"
```

Key fields:
- `base_url` — **the real backend domain**. Registration links often use a different (Punycode/CDN) domain than the actual service. E.g., registration at `云梯.浙地珠宝.com` revealed `base_url: "https://my.yunti2.net"`. Always switch to this domain for further investigation (pricing pages, API endpoints).
- `register.code` — `false` means invitation codes are NOT required even if a code field is pre-filled (it just attributes the referrer).
- `switch.recaptcha` / `switch.turnstile` / `switch.tencent` — `false` means no human verification is enforced, making registration trivial.

## Email Verification Endpoint (Liveness Probe)
`POST /auth/send` with an email address actually sends a verification code and returns JSON:
```bash
curl -sL -X POST "https://domain/auth/send" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=test@example.com"
# → {"ret":1,"msg":"验证码发送成功，请查收邮件。"}
```
Use this to confirm the service is operational without registering. (Avoid using real emails for probing.)

## Analyzing Obfuscated auth.min.js
The Metron theme's `auth.min.js` is obfuscated but contains useful strings:
- API endpoints: `/auth/login`, `/auth/register`, `/password/reset`, `/password/token`
- Captcha types: `tencent`, `turnstile`, `recaptcha`
- Form field names: `name`, `email`, `passwd`, `repasswd`, `code`, `email_code`
- Feature flags: 2FA support (`2fa-code`), email verification, invitation codes

Extract readable strings from obfuscated JS:
```bash
curl -sL "https://domain/theme/metron/js/auth.min.js" | \
  grep -oP "'[^']{5,}'" | sort -u
```

## Registration via API (Confirmed Working 2026-06)

### ⚠️ Critical Pitfall: `emailcode` vs `email_code`
The HTML form field is `name="email_code"` (with underscore), but the **API parameter must be `emailcode`** (no underscore). Using `email_code` returns `{"ret":0,"msg":"您的邮箱验证码不正确"}` even with a correct code. This is the #1 gotcha in SSPanel registration.

### Registration Workflow
```bash
# 1. Send verification code
curl -sL -X POST "https://DOMAIN/auth/send" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: https://DOMAIN/auth/register" \
  -H "X-Requested-With: XMLHttpRequest" \
  --data-urlencode "email=USER@EMAIL.com"
# → {"ret":1,"msg":"验证码发送成功，请查收邮件。"}

# 2. Register (note: emailcode NOT email_code)
curl -sL -X POST "https://DOMAIN/auth/register" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Referer: https://DOMAIN/auth/register" \
  -H "X-Requested-With: XMLHttpRequest" \
  --data-urlencode "email=USER@EMAIL.com" \
  --data-urlencode "emailcode=CODE" \
  --data-urlencode "name=NICKNAME" \
  --data-urlencode "passwd=PASSWORD" \
  --data-urlencode "repasswd=PASSWORD" \
  --data-urlencode "code=INVITE_CODE" \
  --data-urlencode "agree=on"
# → {"ret":1,"msg":"注册成功！正在进入登录界面"}
```

Password requirements (enforced): ≥8 chars + uppercase + lowercase + digit + special char.

### Rate Limiting
`/auth/send` rate-limits per email: `{"ret":0,"msg":"此邮箱请求次数过多"}`. Wait ~60s between attempts. No cookies needed for send/register — the server binds verification codes by email address, not session.

### Login + Pricing Retrieval
```bash
# 1. Login (saves PHPSESSID + auth cookies)
curl -sL -X POST "https://DOMAIN/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -c cookies.txt \
  --data-urlencode "email=USER@EMAIL.com" \
  --data-urlencode "passwd=PASSWORD"
# → {"ret":1,"msg":"登录成功"}

# 2. Fetch shop page with session cookies
curl -sL "https://DOMAIN/user/shop" \
  -b cookies.txt \
  --max-time 30 -o shop.html
# Parse HTML for plan names, prices, traffic, device limits, speeds
```

Login sets: `PHPSESSID`, `expire_in`, `ip`, `key`, `email`, `uid` cookies. All subsequent requests must include these.

### Pricing Structure (Typical)
3 tiers × 3 billing cycles = 9 plans:
- **轻量版**: 5 devices, 100Mbps, 25+ nodes
- **高级版**: 10 devices, 200Mbps, 60+ nodes
- **旗舰版**: 15 devices, 500Mbps, 90+ nodes (includes exclusive nodes)
- Cycles: 季付 / 半年付 / 年付
- Payment: Alipay + WeChat Pay

## API Endpoints Probed (云梯 / my.yunti2.net, 2026-06)
All returned 404 HTML (not JSON) — pricing is not accessible without login:
- `/api/v1/guest/plan/fetch`, `/api/v1/guest/comm/config`, `/api/v1/guest/shop`
- `/shop`, `/user/shop`, `/plan`, `/user/plan`, `/pricing`
- `/user/announcement`, `/user/knowledge`, `/user/doc`, `/doc`
- `/about`, `/terms`, `/tos`, `/help`, `/faq`

The TOS modal (`#tos-modal`) in the registration page was present but empty — no actual terms content loaded.

## Server Recon (No Account Needed)
| Check | Command | Info Gained |
|-------|---------|-------------|
| DNS/CDN | `dig +short domain A` | CDN provider, CNAME chain |
| IP geolocation | `curl -sL ipinfo.io/IP/json` | Country, city, ISP/AS |
| TLS certificate | `openssl s_client -connect IP:443 -servername domain` | Issuer, validity, wildcard scope |
| HTTP → HTTPS redirect | `curl -v http://domain/` | Confirms server reachable, reveals real IP |

## Post-Registration Investigation (Dashboard, Nodes, Clients, SOP)

After login (with session cookies), extract deeper service info for feasibility evaluation and SOP creation.

### Dashboard Analysis (`/user`)
The dashboard HTML contains inline JS with high-value data:
- `importSublink(client)` / `qrcodeImport(client)` functions — reveal the subscription URL and supported client names
- `$crisp.push(["set", "session:data", ...])` — reveals UID, VIP level, VIP expiry, balance, traffic, registration time
- Step-by-step guide links (e.g., "下载客户端并按照教程安装" → `/user/help`)
- Announcement modals with protocol upgrade notices

Extract the subscription URL from JS:
```bash
curl -sL "https://DOMAIN/user" -b cookies.txt | grep -oE "var subUrl = '[^']+'"
# → var subUrl = 'https://154.21.83.60/qwvNavlp7v61NlNOuZ2XnPykGevvlVbP?token=TOKEN'
# The &via=CLIENT_NAME parameter is appended per-client for one-click import
```

### Node List (`/user/node`)
Fetch with session cookies to see available nodes (protocol, location, status, load):
```bash
curl -sL "https://DOMAIN/user/node" -b cookies.txt --max-time 30 -o node.html
```
Parse for: node names, protocols (VMess / ShadowsocksR / VLESS), regions (HK, US, DE...), online status, and class tier restrictions (`node.Classinsufficient()` onclick = requires higher plan).

### Client Compatibility (from `metron.min.js`)
The main JS (`/theme/metron/js/metron.min.js`) is obfuscated but contains client import URL schemes and platform support messages. Extract via string array deobfuscation:

| Client | URL Scheme | Platforms | VLESS |
|--------|-----------|-----------|-------|
| Clash / ClashX | `clash://install-config?url=` | Win/Mac/Android | ⚠️ Deprecating |
| ClashR | `clash://install-config?url=` | Win/Mac/Android | ⚠️ Deprecating |
| FlClash | `flclash://install-config?url=` | Win/Mac/Linux/Android | ✅ |
| Surge | `surge:///install-config?url=` | iOS/Mac | ✅ |
| Stash | `stash://install-config?url=` | iOS/Mac | ✅ |
| Surfboard | `surfboard://install-config?url=` | Android | ✅ |
| Shadowrocket | (QR code / manual) | iOS | ✅ |
| QuantumultX | (QR code / manual) | iOS | ✅ |

Extract readable strings from obfuscated metron.min.js:
```bash
curl -sL "https://DOMAIN/theme/metron/js/metron.min.js" | \
  grep -oP "'[^']{10,}'" | sort -u
```
Search for: client names (`flclash`, `surge`, `stash`, `shadowrocket`), import URL schemes (`://install-config?url=`), platform support messages (`一键导入仅支持`).

### Protocol Upgrade Notices
Check announcement modals in dashboard HTML for protocol migration notices (e.g., VMess/SSR → VLESS). These determine which clients remain compatible:
- Old Clash/ClashX will stop working after VLESS migration
- Recommended replacements: official client or FlClash (cross-platform)
- iOS typically stays on Shadowrocket

### SOP Generation
Once all data is gathered (pricing, nodes, clients, subscription URL), compile into a usage SOP covering:
1. Account login info (domain, email, password, backup URL)
2. Plan purchase (payment methods, plan tiers)
3. Client download (recommended client per platform, VLESS compatibility)
4. Subscription import (one-click vs manual URL paste vs QR code)
5. Node selection (available nodes by tier, protocols, locations)
6. Daily usage notes (subscription refresh, troubleshooting, traffic monitoring)

### Help/Documentation Pages
- `/user/help` — exists but may be empty (no articles). Don't rely on it for tutorials.
- `/tutorial` — typically 404 on SSPanel
- Client download links may only appear after purchasing a plan (dashboard "下载客户端" step)
- If help is empty, contact support via Crisp chat (right-bottom corner) or submit a ticket (`/user/ticket`)

## Common Findings
- Panel often behind Chinese CDN (e.g., 显云CDN / xancdns.top) with server in China
- Let's Encrypt TLS certificates common
- Pricing/plans require login — cannot be scraped without registration
- Some panels expose API at `/api/v1/guest/plan/fetch` (SSPanel) or `/api/v1/guest/comm/config` (V2Board), but many 404
- Help/documentation pages are frequently empty — gather info from dashboard JS + announcements instead
- Node visibility is tier-restricted: without a purchased plan, only "轻量" (lite) nodes are visible
- Subscription URLs contain personal tokens — advise user to reset via `/user/setting/sublink` if leaked
