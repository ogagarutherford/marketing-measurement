# Privacy and Measurement: What Changes What We Can See

*Analytical awareness, not legal advice. Compliance decisions belong with legal and data-protection teams.*

| Topic | What it is | Effect on measurement |
|---|---|---|
| **GDPR and consent** | Personal data such as tracking cookies needs a legal basis; for analytics and ads cookies in the EU this is usually consent | Visitors who decline are invisible to GA4 and ad pixels. In this dataset GA4 sees ~72% of orders, so GA4 numbers must be read as a sample, not the total |
| **Google Consent Mode v2** | Tells Google tags whether consent was given; without consent, tags send cookieless pings and Google models the gap | Reported numbers can mix observed and modelled conversions; required for EEA advertisers using Google ads features since 2024 |
| **First-party data** | Data a brand collects directly (orders, CRM, email) | The order system is complete and consent-independent for business outcomes; it becomes the measurement backbone |
| **Server-side tracking and conversion APIs** | Sending conversion events from the brand’s server to platforms (for example Meta’s Conversions API) | More reliable delivery than browser pixels, but still subject to consent |
| **DMA (Digital Markets Act)** | EU rules for “gatekeeper” platforms (such as Google and Meta), including limits on combining personal data across services without consent | Contributes to stricter consent requirements and less cross-service tracking, so less user-level data for attribution |
| **SKAdNetwork (SKAN) / AdAttributionKit** | Apple’s privacy-preserving attribution for iOS app installs: aggregated, delayed, no user-level data | Not relevant to Velora’s web shop today, but if Velora launched an app, iOS campaigns would be measured mainly through aggregated signals |

## Implications for Velora
1. Treat platform and GA4 numbers as **partial and biased views**; reconcile them against the order system.
2. Prefer **attribution-free** metrics (MER, geo tests) for budget decisions.
3. Use attribution to understand channel **roles**, not to award credit for causation.
