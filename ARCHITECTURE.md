# SourceAI Architecture

## High-level pipeline
ASCII diagram: query → planner → router → crawler → extractor → persist

## Module map
Table: sourceai/search/, sourceai/crawling/, ... — what each does

## Data flow
Step-by-step: "when a user POSTs /api/v1/search, ..."

## Interface boundaries
The 9 interfaces from Session 7 and where they sit

## Deterministic vs AI
The AI_ENABLED flag and what it changes

## Storage
Postgres tables, Redis usage, what's authoritative