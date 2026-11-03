---
type: llm
focus: trace
weight: 1
---

The report flags getCircleSegment (called many times from the template) as work that re-runs on every render, and suggests computing it once
