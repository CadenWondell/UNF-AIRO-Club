# Clinical background — Hypertension

## Why the problem matters
Hypertension is the most common modifiable cardiovascular risk factor and is often undiagnosed or
untreated even when elevated readings are recorded.

## The phenotype in plain language
A record "meets the phenotype" when blood pressure is elevated on at least two separate days, or
hypertension is diagnosed repeatedly or diagnosed and treated — excluding pregnancy-related and
secondary hypertension. Medication alone is not enough because beta-blockers, ACE inhibitors, and
ARBs are also used for atrial fibrillation, heart failure, and kidney disease. **Thresholds are
provisional** (ACC/AHA 2017 stage 1 from secondary summaries) pending reviewer verification.

## Why this is phenotype inference, not threshold reproduction
The model never sees blood-pressure readings, hypertension diagnoses, antihypertensives, or
hypertension-specific care. It infers the current state from body size, heart rate, metabolic and
renal labs, and utilization.

## Educational objective
Handle a label built from noisy repeated vitals and drugs with multiple indications, and examine
how index-time selection can create utilization differences.
