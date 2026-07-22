# Tavily Setup & Registration (July 2026)

## Registration Pitfall: Cloudflare Turnstile Blocks Headless Browsers

Tavily's signup (`auth.tavily.com`) uses Auth0 + Cloudflare Turnstile.

**Symptoms in headless browser:**
- Turnstile iframe shows "Verifying..." indefinitely (never completes)
- Password field does not appear on signup page
- Clicking "Continue" fails with hidden error: `"We couldn't load the security challenge. Please try again."`
- Social login buttons (Google/GitHub/LinkedIn) are visible but also behind Turnstile

**Workaround:**
1. **Manual registration** — user registers in their own browser at [tavily.com](https://tavily.com) → "Try it for free"
2. **Social login** — "Continue with Google" or "Continue with GitHub" may bypass Turnstile on some browsers

## Free Tier Details
- Plan: Researcher (Free)
- Credits: 1,000/month
- No credit card required
- Student plan: also free

## API Key Configuration (post-registration)
After user provides API key:
```bash
# Add to ~/.env or Hermes config
echo "TAVILY_API_KEY=tvly-XXXXX" >> ~/.env
```

## Cost Comparison
See `tavily-cost-analysis.md` for per-query cost vs browser-based search (~55% savings per task).
