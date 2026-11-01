# Attribution Approach

**Data:** GA4 conversion paths (`raw_ga4_conversion_paths`), one row per touchpoint before a purchase, for consented users.

| Model | Rule | What it favours |
|---|---|---|
| Last-click | 100% to the final touch | Channels that close: brand search, direct, email, affiliate |
| First-click | 100% to the first touch | Channels that introduce: paid social, display |
| Linear | Equal share to every touch | Every touch equally |
| Position-based (U-shaped) | 40% first, 40% last, 20% shared by the middle (single touch: 100%; two touches: 50/50) | Both introducers and closers |

## What attribution can and cannot tell us
- It **describes** where customers came from; it does **not** prove what caused the purchase. A customer who would have bought anyway still leaves a path.
- All rule-based models only see **consented, clickable** touches: no unconsented users (~28% of orders), no ad views without a click.
- Brand search often closes journeys that other channels started, or that needed no marketing at all.
- So attribution answers “which channels appear in winning journeys?” The geo test answers “what happens to orders when we switch a channel off?” Budget decisions should rest on the second, informed by the first.
