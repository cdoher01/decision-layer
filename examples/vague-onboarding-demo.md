# Vague Onboarding Demo

Run:

```bash
decision run --goal "Improve onboarding conversion" -- echo "draft onboarding fixes"
```

Expected behavior:

```text
status: needs_decision
stop_reason: decision_required: L1 direction-finding must clarify problem, metric, and evidence bar before execution
```

Why this matters: "Improve onboarding conversion" sounds actionable, but it is L1 direction-finding until the user, metric, bottleneck, and evidence bar are explicit. A normal agent may jump into copy changes or UI work. Decision Layer stops and asks for the decision first.
