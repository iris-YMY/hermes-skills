# SSPanel Metron Theme — Technical Reference

## Panel Identification
- Theme path: `/theme/metron/`
- JS files: `auth.min.js` (obfuscated), `metron.min.js`, `scripts.js`, `metron-plugin.js`
- Config object: `var loginConfig = { base_url, switch: {recaptcha, turnstile, tencent}, register: {code: bool}, tencent_appid }`
- `register.code: false` = invitation code optional (not required)

## Auth JS (auth.min.js) — Deobfuscation
The JS is obfuscated with a string array + index mapper:
- `a0_0xea05()` returns string array
- `a0_0x179c(hex)` maps hex to string: `strings[hex - 0xed]`
- 0xed = 237 decimal (base offset)

### Key strings in the array (index: value):
- [20]: `emailcode` ← API parameter name (NO underscore)
- [59]: `email_code` ← HTML form field name (WITH underscore)
- [40]: `/auth/login`
- [50]: `register_form`
- [78]: `POST`
- [145]: `email`
- [127]: `passwd`

## API Endpoints
| Endpoint | Method | Purpose | Auth |
|----------|--------|---------|------|
| `/auth/send` | POST | Send email verification code | None |
| `/auth/register` | POST | Register new account | None |
| `/auth/login` | POST | Login, returns session cookies | None |
| `/user/shop` | GET | View pricing/plans | Required |
| `/user/node` | GET | View node list | Required |
| `/user/setting/sublink` | GET | View/reset subscription link | Required |
| `/user/help` | GET | Documentation (often empty) | Required |

## No Public API
SSPanel Metron does NOT expose public pricing API:
- `/api/v1/guest/plan/fetch` → 404
- `/api/v1/guest/comm/config` → 404
- All pricing data requires login session

## Cloudflare Considerations
- Panel may be behind Cloudflare (cf-ray header)
- No Set-Cookie on page load — session only created at login
- `--resolve DOMAIN:443:IP` flag needed when DNS resolves to different IP than CDN
