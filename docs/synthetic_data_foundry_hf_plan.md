# Synthetic Data Generator Plan: Microsoft Foundry + Hugging Face

## Purpose

This module generates candidate training examples automatically, validates them, sends them to human review, and exports only approved records for fine-tuning.

Target use case:

- Kannur / North Malabar Malayalam slang
- dialect normalization
- dialect generation
- translation
- transliteration
- chat instruction examples
- evaluation benchmark creation

## Important rule

Synthetic data must not go directly into training.

Correct path:

```text
Generate candidate data
Validate automatically
Score quality
Detect duplicates
Send to native-speaker review
Approve or reject
Export only approved examples
Fine-tune
Evaluate
```

## Recommended roles

### Microsoft Foundry

Use Foundry for:

- choosing fine-tunable models
- running baseline model tests
- managing fine-tuning jobs
- evaluating model versions
- deploying models
- monitoring model behavior

### Hugging Face / Distilabel

Use Hugging Face tooling for:

- synthetic dataset generation
- LLM-as-judge evaluation
- dataset processing
- dataset versioning
- optional publication to a private Hugging Face dataset repository

## MVP synthetic generation tasks

### 1. Standard Malayalam to Kannur slang

Input:

```json
{"standard_malayalam": "നീ ഇന്ന് വീട്ടിലാണോ?"}
```

Output:

```json
{"kannur_slang": "ഇഞ്ഞി ഇന്ന് വീട്ടിലാണോ?"}
```

### 2. Kannur slang to Standard Malayalam

Input:

```json
{"kannur_slang": "ഇഞ്ഞി എവിടെയാ പോണേ?"}
```

Output:

```json
{"standard_malayalam": "നീ എവിടേക്ക് പോകുകയാണ്?"}
```

### 3. Kannur slang to English

Input:

```json
{"kannur_slang": "ഇഞ്ഞി ചായ കുടിച്ചോ?"}
```

Output:

```json
{"english": "Did you drink tea?"}
```

### 4. Manglish to Malayalam script

Input:

```json
{"manglish": "inji evideya pone?"}
```

Output:

```json
{"malayalam": "ഇഞ്ഞി എവിടെയാ പോണേ?"}
```

## Quality gates

Every generated record should be checked for:

- valid JSON structure
- correct task type
- duplicate content
- minimum length
- Malayalam script detection
- Manglish detection
- personal data leakage
- rude/offensive tone
- wrong regional dialect
- hallucinated meaning
- input/output mismatch

## Human review requirement

For dialect data, native speaker review is mandatory.

Synthetic records should use this lifecycle:

```text
synthetic_generated
synthetic_validated
needs_native_review
approved
rejected
exported
```

## Recommended dataset ratio

For dialect fine-tuning, do not use 100 percent synthetic data.

Suggested initial ratio:

```text
60 percent real native-speaker examples
30 percent synthetic examples approved by native speakers
10 percent hard negative / evaluation examples
```

## First implementation module

Create a generator service with this interface:

```text
POST /synthetic/generate
POST /synthetic/validate
POST /synthetic/send-to-review
GET  /synthetic/jobs
POST /export/approved
```

## Final export format

```jsonl
{"task":"dialect_generation","input":"നീ ഇന്ന് വീട്ടിലാണോ?","output":"ഇഞ്ഞി ഇന്ന് വീട്ടിലാണോ?","dialect":"Kannur / North Malabar","source_type":"synthetic_native_approved","quality_score":0.94}
{"task":"dialect_normalization","input":"ഇഞ്ഞി എവിടെയാ പോണേ?","output":"നീ എവിടേക്ക് പോകുകയാണ്?","dialect":"Kannur / North Malabar","source_type":"synthetic_native_approved","quality_score":0.91}
```

## Build priority

1. Generate 100 synthetic candidates.
2. Validate and remove weak records.
3. Native-speaker approve at least 50.
4. Export JSONL.
5. Test baseline model with and without this data.
6. Only then scale to thousands.
