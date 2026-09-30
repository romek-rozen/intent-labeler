# api

FastAPI layer over `pipeline.analyze` - no logic of its own. Endpoints and payloads:
[docs/API.md](../../../docs/API.md). Install with the `[api]` extra; run
`uvicorn intent_labeler.api.app:app`. No authentication: put it behind your panel or a proxy.

## Flow

```mermaid
flowchart LR
    R1[POST /analyze/keyword] --> SS[serp_source + traffic]
    R2[POST /analyze/urls] --> PS[page_source]
    R3[POST /analyze/html-files] --> AH[page_source.apply_html]
    R4[POST /analyze/snapshot] --> SN[Snapshot.from_dict]
    SS --> PL[pipeline.analyze]
    PS --> PL
    AH --> PL
    SN --> PL
    PL --> FMT{format}
    FMT -->|json| J[analysis JSON]
    FMT -->|html| H[report.html]
    FMT -->|md| MD[report.md]
```

