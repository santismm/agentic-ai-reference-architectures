---
id: "ARCH-001"
slug: "customer-service-agent"
title: "Customer Service Agent"
type: "architecture"
evidence_level: "industry_observation"
source: "https://santismm.com/en/architectures/customer-service-agent"
---
# ARCH-001 — Customer Service Agent

> Evidence: industry_observation · Confidence: medium · Source: industry_observation, paper

Canonical: https://santismm.com/en/architectures/customer-service-agent

A reference architecture for an enterprise customer-service agent that resolves common requests end to end — answering from a grounded knowledge base, acting in the CRM and ticketing systems through tools, and escalating to a human when confidence is low or the action is high-impact. It pairs retrieval for grounding with risk-based human approval for safety, and is observable so every conversation can be evaluated and improved.

## Key concepts

- Grounding: answers come from retrieved, citable knowledge, not the model's memory.
- Tool use: the agent reads and writes to CRM/ticketing systems through well-described tools.
- Risk-based escalation: low-confidence or high-impact actions go to a human gate.
- Observability: every turn is traced so the system can be evaluated and improved.

## Definition

The customer service agent architecture is a grounded, tool-using conversational agent that resolves customer requests autonomously within guardrails, escalating to humans by risk and confidence, with full tracing for evaluation.

## Architecture

At the core is an orchestration loop that classifies the incoming request, retrieves relevant knowledge, decides whether it can answer or must act, and either responds, calls a tool, or escalates. Routing sends simple FAQs down a cheap retrieval-and-answer path and complex or sensitive cases down a richer, more careful path.

Grounding is non-negotiable: the agent answers from a retrieval layer over the help center and policy docs, and cites its sources. When the request requires an action — issuing a refund, changing an order, closing a ticket — the agent prepares the action and routes high-impact ones through a human approval gate before execution.

Cross-cutting layers make it safe and improvable: guardrails redact PII and block out-of-policy responses, a semantic cache absorbs repeated questions to cut cost and latency, and an observability layer traces every turn so conversations can be scored against an evaluation set.

## Request flow

- 1. Intake: the user message arrives; PII is detected and redacted for logging.
- 2. Route: classify intent and risk — FAQ, account action, or escalation candidate.
- 3. Retrieve: pull grounding passages from the knowledge base (cache-checked first).
- 4. Decide: answer from grounding, call a CRM/ticketing tool, or escalate.
- 5. Gate: high-impact actions pause for human approval; low-impact ones execute.
- 6. Respond: reply with citations; log the trace and outcome for evaluation.

## Reference scenario

- Context: An illustrative B2C support desk handling order, billing and account questions across chat and email.
- Scenario: Tier-1 requests (order status, password reset, policy questions) are resolved by the agent; refunds and account changes are drafted by the agent and approved by a human; anything ambiguous is escalated with full context.
- Technology: Orchestration loop, RAG over the help center, function-calling tools into the CRM, a risk-based approval gate, and conversation tracing.
- Load: Bursty, business-hours-heavy traffic with a long tail of rare intents; a small set of FAQs dominates volume, which the semantic cache absorbs.
- Results: Reference target: most Tier-1 volume deflected with grounded, cited answers; high-impact actions kept behind a human gate; cost concentrated on the rare, complex cases rather than the repetitive ones. Numbers depend on your traffic mix and should be measured, not assumed.

## KPIs

- Containment / deflection rate: Share of conversations resolved without a human; the headline value metric — but only meaningful alongside CSAT.
- Grounded-answer accuracy: How often answers are correct and supported by a citation, measured against an eval set.
- Escalation rate & quality: Share escalated to humans and whether those escalations were warranted; too high wastes the automation, too low risks bad outcomes.
- Cost per resolved conversation: Total tokens, tools and cache effect per resolution; routing and caching should keep this low on the common path.
- CSAT / resolution time: Customer satisfaction and time-to-resolution; guards against optimizing deflection at the expense of experience.

## Observed failure modes

- Retrieval misses or returns stale policy, so the agent answers confidently but wrongly.
- Tool errors (CRM timeouts, schema drift) leave actions half-applied without recovery.
- Escalation overload when the router sends too much to humans, defeating the automation.
- Cache false hits return a previous customer's context or an out-of-date answer.

## Lessons learned

- Ground first: invest in retrieval quality before expanding autonomy — most wrong answers are retrieval failures.
- Gate by risk, not by default; reserve human approval for irreversible or regulated actions.
- Scope the cache per customer/context and validate hits, or it leaks the wrong answer.
- Instrument from day one; you cannot improve what you cannot trace.

## FAQs

**How is this different from a chatbot?**

A chatbot answers; this architecture also acts — it uses tools to read and write enterprise systems — and it grounds answers in retrieved knowledge, escalating by risk rather than following fixed scripts.

**Why keep a human in the loop at all?**

Because some actions are irreversible or regulated. A risk-based approval gate keeps accountability with a person for high-impact steps while automating the safe majority.

**What makes it reliable?**

Grounding in retrieval, guardrails on inputs and outputs, and observability that lets you evaluate every conversation and catch regressions before they ship.
