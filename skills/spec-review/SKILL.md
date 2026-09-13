---
name: spec-review
description: Review a software specification treated as SPEC.md (the source of truth for the system under review) for completeness, internal consistency, semantic precision, implementability, and verifiability. Use it when auditing or grading a spec before implementation, or when asked how precisely it constrains both an implementer and a verifier. Applies a domain-agnostic four-pass method (comprehension, local precision, cross-consistency, implementation simulation) across 20 review dimensions (requirements, interfaces, data contracts, state/lifecycle, algorithms, failure and edge-case semantics, non-functional, security, observability, metrics, traceability), assigns each finding a CRITICAL/HIGH/MEDIUM/LOW severity, scores 0-5 per dimension, and yields a Level 0-4 maturity plus implementation-readiness verdict, writing a structured SPEC_REVIEW_REPORT.md.
license: MIT
---

# Specification Review Skill

## Purpose

This skill teaches an agent how to review a software specification for **completeness, consistency, precision, implementability, and verifiability**.

The skill is intentionally generic.

It MUST NOT assume:

* a particular programming language;
* a particular architecture;
* a particular application domain;
* a particular testing framework;
* a particular AI/LLM architecture;
* a particular specification format.

The document being reviewed is referred to as:

```text
SPEC.md
```

The reviewer must treat `SPEC.md` as the **source of truth for the system under review**.

---

# 1. Mission

Determine whether `SPEC.md` is sufficiently precise that:

1. an implementation agent can build the specified system;
2. two competent implementers are likely to build materially equivalent systems;
3. a verification agent can determine whether an implementation conforms;
4. failures and edge cases have defined behavior;
5. important claims in the specification can be traced to evidence;
6. the specification is internally consistent.

The reviewer is not being asked whether the system is a good product.

The reviewer is being asked whether the **specification adequately specifies the intended system**.

---

# 2. Fundamental review principle

Apply this question throughout the review:

> **What would a competent implementer still have to guess?**

Every meaningful guess is a potential specification defect.

However, not every implementation choice needs to be specified.

Distinguish between:

### Implementation freedom

A choice that can safely be left to the implementer because it does not affect externally observable behavior or conformance.

### Specification ambiguity

A missing decision that could cause materially different behavior between conforming implementations.

Only the latter is normally a defect.

---

# 3. Review dimensions

Review the specification across these dimensions.

## 3.1 Purpose and scope

Determine whether the specification clearly establishes:

* what system is being built;
* what problem it solves;
* who or what interacts with it;
* what is in scope;
* what is explicitly out of scope.

Check for requirements that implicitly introduce functionality outside the stated scope.

---

## 3.2 Terminology

Check whether important terms have stable meanings.

Look for:

* undefined terminology;
* overloaded terms;
* synonyms used as though they were different concepts;
* the same term used with different meanings;
* terms whose meaning changes between sections.

If terminology is normative, determine whether it is defined precisely enough to support implementation and testing.

---

## 3.3 Requirements

Determine whether requirements describe **observable obligations** rather than aspirations.

A strong requirement should make it possible to answer:

* What must happen?
* Under what conditions?
* To what input?
* With what result?
* Within what constraints?
* What happens if the condition cannot be satisfied?

Flag requirements expressed only as:

* goals;
* intentions;
* vague quality statements;
* architectural preferences;
* implementation suggestions.

---

## 3.4 Actors and interactions

Identify all meaningful actors, including where applicable:

* users;
* administrators;
* external services;
* APIs;
* automated processes;
* agents;
* models;
* background workers;
* scheduled processes.

For each interaction, determine:

* initiating event;
* inputs;
* outputs;
* state changes;
* success behavior;
* failure behavior.

---

## 3.5 Interfaces

For every externally or internally significant interface, check:

* inputs;
* outputs;
* types;
* required fields;
* optional fields;
* valid values;
* defaults;
* errors;
* side effects;
* ordering;
* idempotency where relevant;
* compatibility expectations.

An interface should not depend on undocumented assumptions.

---

## 3.6 Data model

Check every significant data object.

Determine whether the specification defines:

* identity;
* fields;
* types;
* required/optional status;
* valid ranges;
* enumerations;
* relationships;
* uniqueness;
* lifecycle;
* serialization;
* null/empty behavior.

Check that examples agree with formal definitions.

---

## 3.7 State and lifecycle

Where the system has state, reconstruct its state machine.

Check:

* initial state;
* valid states;
* transitions;
* transition triggers;
* terminal states;
* failure states;
* recovery;
* cancellation;
* retries;
* repeated operations.

Flag states or transitions that are implied but not defined.

---

## 3.8 Algorithms and deterministic behavior

For every normative algorithm determine whether implementation is sufficiently constrained.

Check:

* inputs;
* outputs;
* ordering;
* normalization;
* rounding;
* tie-breaking;
* boundary conditions;
* empty inputs;
* invalid inputs;
* numerical behavior;
* determinism.

Do not assume library behavior is part of the specification unless explicitly adopted.

---

## 3.9 Probabilistic or nondeterministic behavior

If the system contains nondeterministic components, determine:

* what is nondeterministic;
* what contract surrounds it;
* what the system guarantees despite nondeterminism;
* how outputs are validated;
* how failures are handled;
* how results are evaluated.

Do not mistake a prompt or informal instruction for a deterministic guarantee.

---

## 3.10 Error and failure semantics

Construct a failure model.

For each significant operation ask:

* What can fail?
* How is failure detected?
* What state results?
* Is the operation retried?
* How many times?
* With what delay?
* Is partial work preserved?
* Can the operation resume?
* Does failure propagate?
* What does the caller observe?

Undefined failure behavior is a common source of divergent implementations.

---

## 3.11 Edge cases

Systematically test conceptual boundaries.

Consider, where applicable:

* empty input;
* null input;
* missing input;
* malformed input;
* maximum input;
* minimum input;
* duplicate input;
* conflicting input;
* concurrent input;
* repeated operation;
* timeout;
* unavailable dependency;
* partial dependency failure;
* cancellation;
* resource exhaustion.

Do not assume every conceivable edge case must be specified.

Report cases where an unspecified edge case can materially affect conformance.

---

## 3.12 Non-functional requirements

Review requirements involving:

* performance;
* latency;
* throughput;
* memory;
* storage;
* scalability;
* reliability;
* availability;
* security;
* privacy;
* observability;
* compatibility;
* maintainability.

Ask whether each requirement is:

1. measurable;
2. testable;
3. associated with defined conditions.

For example:

```text
"The system must be fast."
```

is not a sufficiently precise performance requirement.

---

## 3.13 Security and trust boundaries

Identify:

* trust boundaries;
* privileged operations;
* authentication;
* authorization;
* input validation;
* secret handling;
* external dependencies;
* sensitive outputs;
* unsafe failure modes.

Only report omissions that matter given the system's stated scope.

Do not impose an unrelated security architecture.

---

## 3.14 Observability and provenance

Determine whether important system behavior can be understood after execution.

Where appropriate, check for:

* identifiers;
* timestamps;
* version information;
* inputs;
* outputs;
* decisions;
* errors;
* dependencies;
* configuration;
* provenance.

Ask:

> Can an engineer determine what happened and why?

---

## 3.15 Testing and verification

Determine whether the specification defines enough behavior to construct meaningful tests.

For every major requirement ask:

> What test would prove this requirement?

Then ask:

> Could two reasonable testers interpret the expected result differently?

Check:

* positive cases;
* negative cases;
* boundary cases;
* failure cases;
* integration behavior;
* invariant tests;
* performance tests where applicable.

---

## 3.16 Metrics and evaluation

For every metric determine:

* definition;
* formula where appropriate;
* units;
* population;
* denominator;
* aggregation;
* edge cases;
* interpretation.

A metric should be independently reproducible from specified evidence whenever possible.

Be especially suspicious of metrics that are directly supplied by the component being evaluated.

---

## 3.17 Traceability

Construct the chain:

```text
Intent
  ↓
Requirement
  ↓
Contract
  ↓
Invariant
  ↓
Test
  ↓
Evidence
```

Not every specification will explicitly contain every layer.

Nevertheless, identify broken relationships where they materially affect verification.

---

## 3.18 Internal consistency

Cross-check the entire document.

Look for contradictions involving:

* terminology;
* requirements;
* APIs;
* schemas;
* state transitions;
* defaults;
* filenames;
* command names;
* configuration;
* architecture;
* tests;
* metrics.

Later sections do not automatically override earlier ones.

If the document contains conflicting normative statements, report the conflict.

---

## 3.19 Architecture consistency

Determine whether the proposed architecture actually supports the requirements.

Check:

* component responsibilities;
* dependency direction;
* interfaces;
* data flow;
* state ownership;
* external dependencies;
* failure boundaries.

Do not redesign the architecture merely because another architecture might be preferable.

---

## 3.20 Implementation readiness

Adopt the perspective of the implementing agent.

Ask:

> If I were asked to implement this tomorrow, what questions would I have to ask?

Separate:

### Blocking questions

Questions whose answers could materially change implementation behavior.

### Non-blocking questions

Questions where a reasonable implementation choice can safely be made.

Only blocking questions should materially affect the readiness verdict.

---

# 4. Severity model

Every finding must receive one severity.

## CRITICAL

The specification is contradictory, impossible to implement as written, or fundamentally incapable of being verified.

## HIGH

A reasonable implementation could differ materially because an important behavior or semantic rule is missing or ambiguous.

## MEDIUM

The system is implementable, but the omission or ambiguity could cause defects, maintenance problems, or unreliable verification.

## LOW

Minor clarity, terminology, organization, or editorial issue.

Do not inflate severity.

---

# 5. Finding format

Every substantive finding must contain:

```text
ID
Severity
Location
Observation
Why it matters
Potential consequence
Recommended resolution
```

Use stable IDs:

```text
F-001
F-002
F-003
...
```

Example:

```markdown
### F-003 — Undefined tie-breaking

**Severity:** HIGH

**Location:** §4.2

**Observation**

The specification requires results to be returned in descending score order but does not
define ordering when two results have equal scores.

**Why it matters**

Two conforming implementations may return different result orders.

**Potential consequence**

Tests comparing ordered results may pass for one implementation and fail for another.

**Recommended resolution**

Define a deterministic secondary ordering key.
```

---

# 6. Do not over-specify

A good specification does not prescribe implementation details unnecessarily.

Do NOT flag the absence of:

* internal class names;
* private methods;
* specific libraries;
* specific algorithms;
* internal data structures;

unless the missing detail affects a stated requirement or externally observable behavior.

The goal is:

> **precise behavior with appropriate implementation freedom.**

---

# 7. Review methodology

Use four passes.

## Pass 1 — Comprehension

Read the entire specification without producing findings.

Build a mental model of:

```text
purpose
scope
actors
components
data
state
interactions
outputs
constraints
```

## Pass 2 — Local precision

Review each section for ambiguity, missing contracts, undefined behavior, and unverifiable requirements.

## Pass 3 — Cross-consistency

Compare the sections against one another.

Look for contradictions and stale references.

## Pass 4 — Implementation simulation

Pretend you are implementing the system.

Record every **blocking semantic question** that arises.

The final findings should primarily emerge from these four passes.

---

# 8. Review heuristics

Use these questions repeatedly:

### The implementation test

> Could two competent developers reasonably implement this differently?

### The test test

> Could two competent testers reasonably disagree about whether the implementation passes?

### The boundary test

> What happens at the smallest, largest, empty, invalid, duplicated, or failed case?

### The failure test

> What happens when this operation cannot complete?

### The provenance test

> Can we determine what happened after the fact?

### The contradiction test

> Does another part of the specification say something different?

### The evidence test

> What observable evidence proves this requirement was satisfied?

### The freedom test

> Is this missing detail actually important, or is it legitimate implementation freedom?

---

# 9. Quality dimensions

After the detailed review, score the specification from 0–5 in each dimension:

| Dimension                   | Score |
| --------------------------- | ----: |
| Scope clarity               |       |
| Terminology                 |       |
| Requirement precision       |       |
| Interface completeness      |       |
| Data-contract completeness  |       |
| State/lifecycle definition  |       |
| Algorithm precision         |       |
| Failure semantics           |       |
| Edge-case coverage          |       |
| Non-functional requirements |       |
| Security specification      |       |
| Observability/provenance    |       |
| Testability                 |       |
| Evaluation/metrics          |       |
| Traceability                |       |
| Internal consistency        |       |
| Architecture consistency    |       |
| Implementation readiness    |       |

Use:

```text
0 = absent
1 = seriously deficient
2 = weak
3 = adequate
4 = strong
5 = implementation-grade
```

Do not use document length as evidence of quality.

---

# 10. Overall maturity assessment

Classify the specification using the following maturity levels.

## Level 0 — Concept

Describes an idea but provides insufficient information for implementation.

## Level 1 — Direction

Provides architecture and requirements but leaves substantial semantic decisions to the implementer.

## Level 2 — Implementable

A competent engineer can implement the system, but important ambiguities, edge cases, or verification gaps remain.

## Level 3 — Implementation-grade

A competent coding agent can implement the system with minimal semantic inference, and conformance can be objectively tested.

## Level 4 — Verification-grade

In addition to Level 3, the specification provides unusually strong formal semantics, traceability, reproducibility, and mechanically checkable contracts.

Do not assign Level 4 merely because the specification is detailed.

---

# 11. Required output

Create:

```text
SPEC_REVIEW_REPORT.md
```

Use this structure:

```markdown
# Specification Review Report

## 1. Executive Summary

## 2. Overall Maturity

## 3. Findings Summary

## 4. Detailed Findings

## 5. Requirements Review

## 6. Interface and Data-Contract Review

## 7. State and Failure Review

## 8. Determinism and Algorithm Review

## 9. Edge-Case Review

## 10. Non-Functional Requirement Review

## 11. Security and Trust-Boundary Review

## 12. Observability and Provenance Review

## 13. Testing and Verification Review

## 14. Metrics and Evaluation Review

## 15. Traceability Review

## 16. Internal-Consistency Review

## 17. Architecture Review

## 18. Implementation-Agent Readiness

## 19. Quality Scorecard

## 20. Remediation Plan

## 21. Final Verdict
```

---

# 12. Executive Summary

State:

* overall maturity level;
* implementation readiness;
* number of findings by severity;
* most important strengths;
* most important weaknesses.

Do not repeat the entire review.

---

# 13. Requirements Review

Summarize:

* whether requirements are observable;
* whether they are sufficiently precise;
* whether important requirements are missing;
* whether requirements conflict.

---

# 14. Interface and Data-Contract Review

Summarize:

* interface completeness;
* schema precision;
* input/output ambiguity;
* serialization issues;
* compatibility concerns.

---

# 15. State and Failure Review

Summarize:

* state-machine completeness;
* failure semantics;
* retry behavior;
* cancellation;
* partial completion;
* recovery.

---

# 16. Testing and Verification Review

State whether:

* major requirements are testable;
* acceptance criteria are sufficiently precise;
* edge cases are covered;
* invariants are verifiable;
* expected outcomes are unambiguous.

---

# 17. Implementation-Agent Readiness

Answer:

> **Could a strong coding agent implement this specification without asking material semantic questions?**

Choose:

```text
YES
YES — WITH MINOR CLARIFICATIONS
NO — MATERIAL QUESTIONS REMAIN
NO — SPECIFICATION IS NOT IMPLEMENTABLE
```

List the minimum blocking questions.

---

# 18. Remediation plan

Divide findings into:

### P0 — Blocking

Must be resolved before implementation.

### P1 — Important

Should be resolved before implementation or before claiming conformance.

### P2 — Improvement

Can reasonably be deferred.

Do not recommend unnecessary redesign.

---

# 19. Final verdict

End with:

```text
Specification maturity:
<Level 0 | Level 1 | Level 2 | Level 3 | Level 4>

Implementation readiness:
<READY | READY WITH MINOR FIXES | NOT READY>

Primary blocker:
<one sentence or NONE>

Most important improvement:
<one sentence>
```

---

# 20. Final review principle

The purpose of specification review is not to make a document longer.

It is to reduce **semantic uncertainty**.

A specification is successful when:

> **The implementation agent knows what must be built, the verification agent knows how to determine whether it was built correctly, and neither has to rely on undocumented intent.**

