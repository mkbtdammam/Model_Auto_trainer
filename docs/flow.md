# Model Auto Trainer Flow Diagram (Mermaid)

Paste this into any Mermaid renderer (GitHub Markdown, Mermaid Live, etc.).

```mermaid
flowchart TD

  subgraph S[Data Sources]
    S1[Manual Entry\n(native speaker)]
    S2[CSV Bulk Upload]
    S3[LLM Generator\n(HF / Foundry / any)]
    S4[Audio/ASR (future)]
  end

  subgraph I[Ingestion Layer]
    I1[POST /records]
    I2[POST /import/csv]
    I3[POST /synthetic/ingest-jsonl]
    I4[Job: synthetic_ingest]
  end

  subgraph V[Validation + Dedup]
    V1[Rule Validator\n(length, required fields, PII hints)]
    V2[Script Detector\n(Malayalam/Manglish/Mixed)]
    V3[Duplicate Key\n(SHA256 input||output)]
  end

  subgraph D[SQLite DB]
    D1[(training_records)]
    D2[(jobs)]
  end

  subgraph R[Review Layer]
    R1[Reviewer UI\n/ui/review]
    R2[PATCH /records/{id}/review]
  end

  subgraph A[Automation Engine]
    A1[POST /jobs]
    A2[Worker\npython -m app.worker]
    A3[Job: auto_approve\n(policy gates)]
    A4[Job: export_approved]
    A5[Job: export_if_threshold]
    A6[Job: llm_judge (future)]
    A7[Job: trigger_training (future)]
  end

  subgraph T[Export + Train]
    T1[exports/approved_training_data.jsonl]
    T2[Fine-tune\n(Azure AI Foundry / HF Trainer)]
    T3[Eval + Deploy (future)]
  end

  S1 --> I1
  S2 --> I2
  S3 --> I3
  S3 --> I4
  S4 -.-> I1

  I1 --> V1
  I2 --> V1
  I3 --> V1
  I4 --> V1

  V1 --> V2 --> V3

  V3 -->|valid| D1
  V3 -->|duplicate| V3
  V3 -->|invalid| D1

  D1 -->|status=needs_review| R1
  R1 --> R2 --> D1

  A1 --> D2
  D2 --> A2
  A2 --> A3 --> D1
  A2 --> A4 --> T1
  A2 --> A5 --> T1
  A2 -.future.-> A6 -.future.-> D1
  A2 -.future.-> A7 -.future.-> T2

  D1 -->|approved only| T1 --> T2 --> T3

  classDef future stroke-dasharray: 5 5,opacity:0.7;
  class A6,A7,S4,T3 future;
```
