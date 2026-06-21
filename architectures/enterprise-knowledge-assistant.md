---
id: "ARCH-002"
slug: "enterprise-knowledge-assistant"
title: "Enterprise Knowledge Assistant"
type: "architecture"
evidence_level: "industry_observation"
source: "https://santismm.com/en/architectures/enterprise-knowledge-assistant"
---
# ARCH-002 — Enterprise Knowledge Assistant

> Evidence: industry_observation · Confidence: high · Source: industry_observation, paper

Canonical: https://santismm.com/en/architectures/enterprise-knowledge-assistant

A reference architecture for an internal knowledge assistant that answers employee questions from the company's own documents — wikis, policies, tickets, code — with citations and respecting each user's access permissions. It combines hybrid retrieval and reranking for grounding, permission-aware filtering for security, and an evaluation harness so answer quality is measured rather than assumed. The hard parts are not the model; they are retrieval quality, access control and evaluation.

## Key concepts

- Permission-aware retrieval: a user only ever retrieves documents they are allowed to see.
- Hybrid search + reranking: combine keyword and vector search, then rerank for precision.
- Citations: every answer links back to its source passages for verification.
- Evaluation: answer quality is scored against a curated set, continuously.

## Definition

The enterprise knowledge assistant architecture is a permission-aware RAG system that answers employee questions from internal documents with citations, scoped to each user's access rights and continuously evaluated for quality.

## Architecture

Content from many internal sources is ingested, chunked and embedded into a vector store, with each chunk tagged by its source document's access-control metadata. At query time the assistant routes the question, runs hybrid retrieval (keyword + vector) filtered to the user's permissions, reranks the candidates, and synthesizes a cited answer from the top passages.

Security is structural, not bolted on: the access-control filter is applied during retrieval so the model never even sees documents the user cannot access. A semantic cache serves repeated questions cheaply, and guardrails keep answers within policy and flag low-confidence cases.

Quality is governed by measurement: an evaluation harness scores answers for groundedness, correctness and citation accuracy against a curated set, and an optional evaluator-optimizer loop revises weak answers before they reach the user. Observability traces every query so failures can be diagnosed and fed back into the evals.

## Request flow

- 1. Ingest (offline): chunk and embed documents; tag each chunk with access-control metadata.
- 2. Route: classify the question and pick the retrieval strategy.
- 3. Retrieve: hybrid search filtered to the user's permissions (cache-checked first).
- 4. Rerank: reorder candidates for precision; keep the top passages.
- 5. Synthesize: generate a cited answer; optionally revise it via an evaluator loop.
- 6. Return & log: deliver answer with citations; trace and score for evaluation.

## Reference scenario

- Context: An illustrative internal assistant over a company's wiki, HR and IT policies, and engineering docs.
- Scenario: Employees ask natural-language questions ('how do I expense travel?', 'what's our on-call policy?'); the assistant answers with citations, never surfacing documents the asker cannot access, and says 'I don't know' rather than guessing when retrieval is weak.
- Technology: Ingestion pipeline, embeddings + vector store with ACL metadata, hybrid retrieval and reranking, an evaluation harness, and query tracing.
- Load: Steady internal traffic with strong query overlap (a few policies drive most questions), so the cache hit rate is high and embeddings dominate the offline cost.
- Results: Reference target: grounded, cited answers with no access-control leaks, and a measurable groundedness score that improves as retrieval is tuned. Treat all figures as things to measure on your corpus, not guarantees.

## KPIs

- Groundedness: Share of answers fully supported by the cited passages; the core quality metric for a RAG assistant.
- Retrieval recall@k: How often the right passage is in the top-k retrieved; most answer errors trace back to this.
- Access-control leak rate: Any answer surfacing a document the user couldn't access — the metric that must stay at zero.
- Cache hit rate & cost per query: Repeat-question coverage and unit cost; high overlap should make most queries cheap.
- Abstention quality: How often the assistant correctly says 'I don't know' instead of hallucinating on weak retrieval.

## Observed failure modes

- Permission bypass: a chunk inherits the wrong ACL and surfaces in a user's results.
- Retrieval gaps: the right document exists but chunking or embeddings miss it.
- Staleness: an answer cites a superseded policy because re-indexing lagged.
- Citation drift: the cited passage doesn't actually support the generated claim.

## Lessons learned

- Enforce access control inside retrieval, not after generation — filtering the prompt is too late.
- Most quality gains come from retrieval (chunking, hybrid search, reranking), not from a bigger model.
- Make 'I don't know' a first-class answer; a wrong confident answer is worse than an abstention.
- Stand up evaluation before scaling; without it, every change is a guess.

## FAQs

**Isn't this just RAG?**

RAG is the core, but the architecture is defined by what makes it enterprise-safe: permission-aware retrieval, citations, an evaluation harness and observability. Those are the parts that decide whether it can be trusted.

**Why enforce permissions during retrieval?**

So the model never sees documents the user can't access. Filtering after generation is too late — the content could already have leaked into the answer.

**How do you keep answers from hallucinating?**

Ground every answer in retrieved passages with citations, measure groundedness against an eval set, and let the assistant abstain when retrieval is weak rather than fill the gap.
