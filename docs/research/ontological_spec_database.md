# Ontological Spec Database

## USER

Here is a sample spec document; I currently use similar spec documents to first create implementation plan and if document is complex, a set of detailed implementation plans for different phases of implementation. What if the SPEC.md was converted into ontological database that fully captured the semantics of the spec, and then we could create implementation plans and check conformance of implementation to spec based on that database?

## ASSISTANT

Yes. In fact, I think this is a natural next step from the Level-3 SPEC.md approach you've been developing.

Your current SPEC.md is already **much closer to a semantic model than an ordinary requirements document**. It contains entities, relationships, constraints, state transitions, contracts, invariants, tests, traceability, decisions, and provenance. For example, the document explicitly says that the specification is the source of truth and that implementation and verification are derived from it. [SPEC.md L497-498](SPEC.md#L497-L498)

The interesting idea is to make that implicit semantic model **explicit and machine-operable**.

## 1. The fundamental shift

Today you have roughly:

```text
                    SPEC.md
                       │
              ┌────────┴────────┐
              ▼                 ▼
       Implementation       Test Plan
              │                 │
              ▼                 ▼
           Code              Tests
```

What you're proposing is:

```text
                       SPEC.md
                          │
                          ▼
                 Semantic extraction
                          │
                          ▼
                 ┌─────────────────┐
                 │ Specification   │
                 │ Ontology / DB   │
                 └─────────────────┘
                    │      │      │
          ┌─────────┘      │      └──────────┐
          ▼                ▼                 ▼
   Implementation     Implementation      Conformance
       Plan             Plan Phase 2        Analysis
          │                │                 │
          ▼                ▼                 ▼
        Code             Code             Evidence
          └────────────────┴─────────────────┘
                           │
                           ▼
                    Specification
                    conformance
```

And this is more powerful than merely putting the SPEC into a database.

The important distinction is:

> **The database stores the semantics of the specification, not merely its text.**

---

# 2. Your SPEC already contains an ontology

Consider just a few things in your sample.

You have entities:

```text
Application
User
Engine
Worker
MainWindow
Requirement
Contract
Invariant
Constraint
EdgeCase
Test
Decision
State
Event
Component
DataStructure
```

You have relationships:

```text
Requirement ──realized_by──> Component
Requirement ──verified_by──> Test

Invariant ──constrains──> Component
Invariant ──verified_by──> Test

Constraint ──measured_by──> Test

EdgeCase ──requires_behavior──> Component

Event ──transitions──> State

Contract ──implemented_by──> Component

Test ──provides_evidence_for──> Requirement
```

And properties:

```text
Requirement:
    normative = true
    priority = ...
    statement = ...

Constraint:
    metric = p95_latency
    operator = <
    threshold = 50ms

State:
    allowed_controls = ...

Decision:
    status = confirmed/open
    alternatives = ...
```

Your traceability matrix is especially revealing. It explicitly maps specification objects to implementation ownership and verification evidence. [SPEC.md L421-437](SPEC.md#L421-L437)

That's already a graph.

---

# 3. But I would not make the ontology a replacement for SPEC.md

I would make the ontology the **canonical semantic representation**, with SPEC.md becoming one projection of it.

Something like:

```text
                  ┌────────────────────┐
                  │ Specification      │
                  │ Semantic Model      │
                  │                    │
                  │ ontology + rules   │
                  │ + evidence + graph │
                  └─────────┬──────────┘
                            │
              ┌─────────────┼──────────────┐
              ▼             ▼              ▼
          SPEC.md       Plan.md       Conformance
          projection    projection       report
```

This is an important architectural distinction.

Markdown is excellent for humans.

The semantic model is excellent for machines.

So:

> **SPEC.md becomes a human-readable serialization/view of the specification model.**

That also solves a problem you've already encountered with Level-3 specifications: keeping implementation, tests, and specification synchronized.

---

# 4. The really interesting part: implementation becomes another semantic graph

Suppose the implementation produces:

```python
class MonteCarloEngine:
    ...
```

Instead of merely asking an LLM:

> "Does this code satisfy SPEC.md?"

you construct an **implementation model**.

For example:

```text
Implementation
    │
    ├── Component
    │      └── MonteCarloEngine
    │
    ├── Method
    │      └── run_batch
    │
    ├── Dependency
    │      └── numpy
    │
    └── Behavior
           ├── generates points
           ├── counts hits
           └── updates totals
```

Then conformance becomes a graph comparison / logical validation problem:

```text
SPECIFICATION GRAPH
        │
        │ conformance rules
        ▼
IMPLEMENTATION GRAPH
        │
        ▼
   Evidence Graph
```

This is substantially more interesting than conventional static analysis.

---

# 5. For example, I-002 becomes machine-checkable

Your specification says:

> A point is a hit iff `x² + y² <= 1.0`. This is the only hit rule. [SPEC.md L299-306](SPEC.md#L299-L306)

In an ontology you could represent something conceptually like:

```yaml
Invariant:
  id: I-002
  subject: MonteCarloEngine.is_hit
  predicate: hit_rule
  condition:
    expression: x*x + y*y <= 1.0
  exclusivity: true
  verification:
    - T-02
```

Now an analyzer can discover from the implementation:

```python
is_hit = x*x + y*y <= 1.0
```

and establish:

```text
I-002
  │
  ├── requires ──> hit(x,y) ↔ x²+y²≤1
  │
  └── evidence <── implementation AST/IR
```

That's a **conformance proof obligation**, rather than an LLM judgment.

---

# 6. State machines become particularly powerful

Your `AppState` specification is already essentially a formal transition system. [SPEC.md L72-121](SPEC.md#L72-L121)

You could represent:

```text
State
 ├── IDLE
 ├── RUNNING
 ├── PAUSED
 ├── COMPLETED
 └── ERROR

Transition
 ├── Start
 ├── Pause
 ├── Resume
 ├── Reset
 ├── RunComplete
 └── WorkerCrash
```

with relations:

```text
IDLE --Start--> RUNNING
RUNNING --Pause--> PAUSED
PAUSED --Resume--> RUNNING
RUNNING --RunComplete--> COMPLETED
RUNNING --WorkerCrash--> ERROR
ANY --Reset--> IDLE
```

Then conformance can ask:

```text
Does implementation contain all required transitions?

Does it permit forbidden transitions?

Are side effects attached to the correct transitions?

Are controls enabled according to the state model?
```

That can be partly verified **without an LLM at all**.

---

# 7. Your test suite becomes evidence, not the specification

This is another important conceptual improvement.

Currently:

```text
I-006 → T-01, T-14
```

means the tests verify the invariant. [SPEC.md L306-309](SPEC.md#L306-L309)

In the semantic model I'd represent:

```text
I-006
   │
   ├── obligation
   │
   ├── verified_by ──> T-01
   │
   └── verified_by ──> T-14
```

But now you can add:

```text
T-01
   │
   ├── executes_on ──> Implementation v37
   ├── result ──> PASS
   ├── timestamp ──> ...
   └── evidence ──> pytest artifact
```

So the model distinguishes:

**Specification**

from

**Implementation**

from

**Verification evidence**.

That distinction is extremely important.

---

# 8. This leads to a much stronger notion of conformance

I'd define something like:

$$
\text{Conformance}
=
f(
\text{specification},
\text{implementation},
\text{evidence}
)
$$

rather than:

$$
\text{Conformance}
=
LLM(\text{SPEC.md},\text{source code})
$$

The second can be useful, but it should not be the fundamental architecture.

You want multiple levels of evidence:

### Level 1 — structural

```text
Required class exists
Required method exists
Required signal exists
Required dependency exists
```

### Level 2 — behavioral

```text
run_batch() produces required outputs
state transitions occur correctly
exceptions produce required signals
```

### Level 3 — invariant

```text
processed >= total_hits
estimate = 4h/N
```

### Level 4 — performance

```text
p95 UI latency < 50ms
memory <= 60,000 points
```

### Level 5 — probabilistic

```text
empirical variance agrees with theoretical variance
3σ coverage satisfies criterion
```

### Level 6 — semantic

```text
implementation actually realizes the intended behavior
```

That last category is where an LLM/agent can be extremely valuable.

---

# 9. The ontology should therefore contain *obligations*

I think this is the key concept for your Specification Engineering work.

Instead of merely:

```text
Requirement R-09
```

represent:

```text
Obligation O-009

subject:
    Application

must:
    remain_responsive

condition:
    computation == millions_of_samples

constraint:
    p95(event_response) < 50ms

scope:
    interval_ms >= 1

evidence:
    T-07
```

Now an implementation plan can be generated from **unresolved obligations**.

For example:

```text
O-009
 │
 ├── requires_component ──> Worker
 │
 ├── requires_mechanism ──> Background execution
 │
 ├── requires_mechanism ──> Progress throttling
 │
 └── requires_verification ──> Event-loop latency test
```

The implementation planner doesn't have to "understand the document" from scratch.

It queries the semantic model.

---

# 10. Implementation planning becomes graph traversal

This is where I think your idea gets really interesting.

Suppose you ask:

> Generate implementation plan.

The planner traverses:

```text
Requirements
    ↓
Contracts
    ↓
Invariants
    ↓
Constraints
    ↓
Dependencies
    ↓
Components
    ↓
Interfaces
    ↓
Tests
```

and produces:

```text
Phase 1 — Core domain model
    C-01
    I-001..I-006
    T-01..T-05

Phase 2 — Worker
    C-02
    C-03
    K-06
    E-05
    T-06
    T-16

Phase 3 — UI
    C-05
    C-06
    R-03..R-07
    T-13
    T-17

Phase 4 — Integration
    R-09/R-10
    K-01/K-05
    T-07

Phase 5 — statistical validation
    T-09..T-12
```

Notice what happened:

**The phases aren't invented by the LLM.**

They're derived from the dependency graph.

The LLM's job becomes deciding *how best to execute* the graph.

---

# 11. Even better: plans themselves become semantic objects

Don't make the implementation plan just Markdown.

Model:

```text
ImplementationPlan
    │
    ├── Phase
    │     ├── Objective
    │     ├── Inputs
    │     ├── Tasks
    │     ├── Dependencies
    │     ├── Preconditions
    │     ├── Deliverables
    │     └── Verification
    │
    └── satisfies ──> Obligations
```

Then:

```text
SPEC
 ↓
PLAN
 ↓
IMPLEMENTATION
 ↓
EVIDENCE
```

becomes a traceable chain.

---

# 12. You can then ask a much more interesting question

Not:

> "Is the implementation correct?"

but:

> **"Which specification obligations currently lack sufficient evidence?"**

For example:

```text
Conformance Status

R-01   ✓ proven
R-02   ✓ proven
R-03   ✓ proven
R-04   ✓ proven
R-05   ✓ proven
R-06   ✓ proven
R-07   ✓ proven
R-08   ✓ proven
R-09   ⚠ partially proven
R-10   ✓ proven
R-11   ✓ proven

I-001   ✓
I-002   ✓
...
K-01    ⚠ benchmark evidence stale
K-02    ✓
K-03    ✓
K-04    ⚠ informative measurement missing
K-05    ✓
K-06    ✓
```

This is much closer to **continuous specification conformance**.

---

# 13. It also solves specification drift

Imagine you change:

```text
K-01:
p95 < 50 ms
```

to:

```text
K-01:
p95 < 30 ms
```

The semantic system can immediately propagate the change:

```text
K-01
 │
 ├── T-07
 │
 ├── Worker architecture
 │
 ├── throttle design
 │
 └── Phase 4 implementation plan
```

and mark:

```text
T-07 = INVALIDATED
Phase 4 = NEEDS_REVIEW
Conformance = UNKNOWN
```

That's something Markdown-based workflows don't naturally provide.

---

# 14. Decisions become first-class semantic objects too

Your D-01 through D-09 are particularly valuable. [SPEC.md L473-486](SPEC.md#L473-L486)

For example:

```text
D-08
  RNG draw order
       │
       ├── affects → C-01
       ├── affects → I-006
       ├── affects → T-01
       └── affects → T-14
```

If D-08 changes:

```text
D-08 changed
      ↓
dependency propagation
      ↓
I-006 potentially invalid
      ↓
T-01/T-14 invalidated
      ↓
implementation review required
```

This starts looking like **configuration management for semantics**, rather than document version control.

---

# 15. I would use a hybrid architecture

I wouldn't necessarily jump immediately to a pure RDF/OWL system.

I'd start with a typed semantic model such as:

```text
Specification
├── Actors
├── Goals
├── Requirements
├── Components
├── Interfaces
├── DataTypes
├── States
├── Events
├── Transitions
├── Invariants
├── Constraints
├── EdgeCases
├── Decisions
├── Tests
├── Evidence
└── Traceability
```

and explicit predicates:

```text
requires
realizes
constrains
depends_on
transitions_to
verified_by
evidenced_by
invalidates
derived_from
conflicts_with
supersedes
```

Then put a **rule engine** on top.

You don't necessarily need heavyweight OWL reasoning initially.

A graph database + schema + constraint/rule layer could get you remarkably far.

---

# 16. The LLM then becomes a semantic compiler

This suggests an architecture I find particularly compelling for your AI-native Specification Engineering idea:

```text
                    Natural language
                           │
                           ▼
                    ┌─────────────┐
                    │ LLM         │
                    │ extraction  │
                    └──────┬──────┘
                           ▼
                  Semantic Specification
                           │
                  ┌────────┴────────┐
                  │                 │
                  ▼                 ▼
             Rule Engine       Graph Queries
                  │                 │
                  └────────┬────────┘
                           ▼
                    Agent Planner
                           │
                           ▼
                    Implementation
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
        Static Analysis             Tests/Evals
             │                           │
             └─────────────┬─────────────┘
                           ▼
                    Evidence Graph
                           │
                           ▼
                 Conformance Engine
```

The LLM is no longer the source of truth.

It is a **compiler between human intent and a formal semantic representation**, and later a reasoning component operating over that representation.

That is a much safer architecture.

---

# 17. There is one major difficulty

The hardest problem isn't storing the ontology.

It is **semantic extraction**.

Your SPEC contains statements such as:

> "The worker computes at full speed but emits progress no more often than every interval_ms."

That isn't just an entity/property.

It contains:

- actors
- temporal semantics
- quantitative constraints
- causality
- exceptions
- scope
- measurement methodology

Likewise:

> "The stream is consumed in the same order whatever the batch size..."

contains a **cross-implementation equivalence property**.

So your ontology needs to represent more than:

```text
subject → predicate → object
```

You need something closer to:

```text
Claim
 ├── subject
 ├── predicate
 ├── object
 ├── modality
 ├── conditions
 ├── scope
 ├── temporal semantics
 ├── quantitative constraints
 ├── exceptions
 ├── provenance
 └── verification obligations
```

This is where your Level-3 → Level-4 trajectory becomes quite interesting.

---

# 18. I would actually define a new concept: the Specification Knowledge Graph

You could call the artifact:

**SKG — Specification Knowledge Graph**

with:

```text
SPEC.md
   │
   │ compile
   ▼
Specification Knowledge Graph
   │
   ├── Semantic specification
   ├── Requirement graph
   ├── Behavior/state graph
   ├── Contract graph
   ├── Constraint graph
   ├── Decision graph
   ├── Test/evaluation graph
   ├── Implementation graph
   └── Evidence graph
```

And then define three fundamental operations:

### `compile`

```text
SPEC.md → SKG
```

### `plan`

```text
SKG → ImplementationPlan
```

### `verify`

```text
SKG + Implementation + Evidence → ConformanceReport
```

And potentially:

### `render`

```text
SKG → SPEC.md
SKG → PLAN.md
SKG → TRACEABILITY.md
SKG → CONFORMANCE.md
```

That gives you a **bidirectional specification system**, rather than a document-centric system.

---

# 19. And there's an even deeper implication

Your current doctrine says:

> requirements express intent; specification operationalizes intent into observable behavior and correctness conditions. [SPEC.md L13-14](SPEC.md#L13-L14)

The ontological version could be:

> **Specification Engineering is the construction and maintenance of a machine-operable semantic model of system intent, behavior, constraints, and evidence.**

Then:

**Requirements Engineering**

```text
What do we want?
```

**Specification Engineering**

```text
What precisely does it mean?
```

**Implementation Planning**

```text
What must we build to realize that meaning?
```

**Implementation**

```text
What did we actually build?
```

**Verification**

```text
What evidence demonstrates realization?
```

**Conformance Engineering**

```text
Does what we built satisfy what we specified?
```

That's a coherent engineering discipline.

And your current SPEC.md is already an excellent candidate for the **first test case of such a system**: it has 11 requirements, 6 contracts, 9 invariants, 6 constraints, 13 active edge cases, 18 tests/evals, 9 decisions, and a comprehensive traceability graph. [SPEC.md L54-67](SPEC.md#L54-L67) [SPEC.md L297-309](SPEC.md#L297-L309) [SPEC.md L316-326](SPEC.md#L316-L326)

**I would not start by designing the database schema, though.** I would first take this exact SPEC.md and construct a **Specification Ontology v0.1**: define the semantic entity types, relationships, predicates, obligation model, evidence model, and a small rule language. Then we could see which parts of this SPEC cannot be represented cleanly. That exercise would likely reveal the architecture much more effectively than designing the ontology abstractly.

## USER

Take a shot at constructing **Specification Ontology v0.1**

## ASSISTANT

Yes. I would make v0.1 deliberately **small, typed, and operational** rather than attempting to build a full formal ontology such as OWL from day one.

The goal should be:

> **Capture enough semantics that an agent can derive plans, identify dependencies, generate verification obligations, and determine what evidence is still missing—without having to repeatedly reinterpret the original prose.**

Your Monte Carlo specification is an unusually good test case because it already contains nearly all the primitives we need: requirements, contracts, state machines, invariants, constraints, edge cases, tests, decisions, dependencies, and traceability. [SPEC.md L54-67](SPEC.md#L54-L67)

Below is my first shot.

:::writing{variant="document" id="58321" title="Specification Ontology v0.1"}

# Specification Ontology v0.1

## 1. Purpose

Specification Ontology v0.1 (SO-0.1) defines a machine-operable semantic model for representing a software specification independently of its human-readable document representation.

The ontology is intended to support four primary operations:

1. **Specification compilation** — convert a human-authored specification into a semantic model.
2. **Implementation planning** — derive implementation work, dependencies, phases, and verification obligations from the model.
3. **Conformance analysis** — compare an implementation and its verification evidence against the specification.
4. **Specification maintenance** — propagate changes to requirements, decisions, contracts, constraints, and other specification elements through their dependency graph.

The ontology does not attempt to encode arbitrary natural language. It represents the portions of a specification that can be expressed as:

- entities,
- relationships,
- behaviors,
- contracts,
- constraints,
- invariants,
- decisions,
- obligations,
- verification criteria,
- evidence,
- dependencies, and
- provenance.

---

# 2. Design Principles

## 2.1 Specification is semantic, not textual

The canonical object is the semantic specification model.

A Markdown document such as `SPEC.md` is a human-readable projection of that model.

```text
Semantic Specification
        │
        ├──→ SPEC.md
        ├──→ Implementation Plan
        ├──→ Test Plan
        ├──→ Traceability Report
        └──→ Conformance Report
```

The Markdown representation must not be the only source of semantic information.

---

## 2.2 Intent and operational specification are distinct

The ontology distinguishes between:

```text
Intent
  ↓
Requirement
  ↓
Operational Specification
  ↓
Obligation
  ↓
Implementation
  ↓
Evidence
```

A requirement expresses what is wanted.

A specification element expresses what must be true or observable.

An obligation is a condition that an implementation must satisfy.

Evidence establishes whether the obligation has been satisfied.

---

## 2.3 Normativity is explicit

Every normative statement has a modality.

```text
MUST
SHALL
SHOULD
MAY
INFORMATIVE
```

For v0.1:

| Modality | Meaning |
|---|---|
| `MUST` | mandatory |
| `SHALL` | mandatory |
| `SHOULD` | strong recommendation |
| `MAY` | optional |
| `INFORMATIVE` | does not create a conformance obligation |

This preserves the distinction already established in the sample specification. [SPEC.md L3-12](SPEC.md#L3-L12)

---

# 3. Top-Level Model

A `Specification` is the root object.

```yaml
Specification:
  id:
  name:
  version:
  status:
  purpose:
  scope:
  non_goals:

  actors: []
  goals: []

  requirements: []
  components: []
  interfaces: []
  data_types: []

  states: []
  events: []
  transitions: []

  contracts: []
  invariants: []
  constraints: []
  edge_cases: []

  decisions: []

  tests: []
  evaluations: []

  dependencies: []

  obligations: []

  traceability: []

  provenance: []

  revision_history: []
```

The important design decision is that these are not merely sections of a document.

They are **typed nodes in a semantic graph**.

---

# 4. Core Entity Taxonomy

## 4.1 Entity hierarchy

```text
SpecificationElement
│
├── Intent
│   ├── Requirement
│   └── Goal
│
├── SystemModel
│   ├── Actor
│   ├── Component
│   ├── Interface
│   ├── DataType
│   ├── State
│   ├── Event
│   └── Transition
│
├── BehavioralSpecification
│   ├── Contract
│   ├── Invariant
│   ├── Constraint
│   └── EdgeCase
│
├── Decision
│
├── Verification
│   ├── Test
│   ├── Evaluation
│   └── Evidence
│
├── Planning
│   ├── Obligation
│   ├── WorkItem
│   └── ImplementationPhase
│
└── Provenance
    ├── Source
    └── Revision
```

---

# 5. SpecificationElement

Every semantic object has a common identity.

```yaml
SpecificationElement:
  id: string
  type: string

  title: string?
  description: string?

  modality: MUST | SHALL | SHOULD | MAY | INFORMATIVE

  status:
    proposed
    confirmed
    active
    deprecated
    retired

  priority:
    critical
    high
    medium
    low
    informative

  tags: []

  source_refs: []
```

The `id` is globally unique within the specification.

Examples:

```text
R-01
C-01
I-006
K-01
E-05
T-07
D-08
O-014
```

Existing identifiers in the sample specification map naturally to this model. [SPEC.md L297-309](SPEC.md#L297-L309)

---

# 6. Intent

## 6.1 Requirement

A requirement captures externally expressed intent.

```yaml
Requirement:
  id:
  statement:
  modality:
  actor_refs: []
  goal_refs: []
  priority:
  acceptance_obligations: []
```

Example:

```yaml
id: R-08
type: Requirement

statement:
  "The user shall be able to supply an optional RNG seed
   to make a run reproducible."

modality: SHALL

acceptance_obligations:
  - O-R08-1
```

---

## 6.2 Goal

A goal describes why something exists.

```yaml
Goal:
  id:
  statement:
  actor_refs: []
  parent_goal:
```

The sample's statement that the primary product surface is a real-time convergence experience is a goal/context object rather than an implementation requirement. [SPEC.md L20-29](SPEC.md#L20-L29)

---

# 7. System Model

## 7.1 Actor

```yaml
Actor:
  id:
  name:
  kind: human | system | component | external
  goals: []
```

Example:

```yaml
Actor:
  id: ACT-USER
  name: User
  kind: human
```

The sample specification identifies User, Engine, Worker, and UI as actors/system participants. [SPEC.md L40-47](SPEC.md#L40-L47)

---

## 7.2 Component

```yaml
Component:
  id:
  name:
  responsibility:
  interfaces: []
  dependencies: []
  owned_obligations: []
```

Example:

```yaml
id: CMP-ENGINE
name: MonteCarloEngine

responsibility:
  "Produce deterministic Monte Carlo batches without GUI dependencies."

interfaces:
  - C-01

owned_obligations:
  - I-001
  - I-002
  - I-003
  - I-004
  - I-005
  - I-006
```

---

## 7.3 Interface

An interface defines an externally observable contract.

```yaml
Interface:
  id:
  name:
  owner:
  operations: []
  inputs: []
  outputs: []
  preconditions: []
  postconditions: []
  side_effects: []
  exceptions: []
```

For the sample:

```yaml
id: C-01
type: Interface
name: MonteCarloEngine
owner: CMP-ENGINE

operations:
  - __init__
  - run_batch
  - estimate
  - standard_error
  - z_score
```

The existing C-01 contract is therefore represented as a structured interface rather than a block of Python-oriented prose. [SPEC.md L161-199](SPEC.md#L161-L199)

---

## 7.4 DataType

```yaml
DataType:
  id:
  name:
  fields: []
  constraints: []
  nullable_fields: []
```

Example:

```yaml
id: DT-PROGRESS
name: Progress

fields:
  - processed: int
  - estimate: float
  - error_abs: float
  - standard_error: float?
  - z_score: float?
  - batch_x: float[]
  - batch_y: float[]
  - batch_is_hit: bool[]
```

This corresponds directly to the sample's C-04 data structures. [SPEC.md L226-235](SPEC.md#L226-L235)

---

# 8. Behavioral Model

## 8.1 State

```yaml
State:
  id:
  name:
  meaning:
  enabled_controls: []
  entry_actions: []
  exit_actions: []
```

Example:

```yaml
id: STATE-RUNNING
name: RUNNING

meaning:
  "Worker is actively producing samples."

enabled_controls:
  - Pause
  - Reset
```

---

## 8.2 Event

```yaml
Event:
  id:
  name:
  parameters: []
  source:
```

Example:

```yaml
id: EVT-START
name: Start

parameters:
  - N
  - B
  - seed
```

---

## 8.3 Transition

A transition connects state, event, guard, and effects.

```yaml
Transition:
  id:
  source_state:
  event:
  guard:
  target_state:
  side_effects: []
```

Example:

```yaml
id: TR-START

source_state:
  - IDLE
  - COMPLETED
  - ERROR

event: EVT-START

guard:
  valid(N, B, seed)

target_state: RUNNING

side_effects:
  - reset_counters
  - clear_charts
  - construct_engine(seed)
  - start_worker
```

This directly captures the transition semantics currently distributed across the state diagram and transition table. [SPEC.md L97-120](SPEC.md#L97-L120)

---

# 9. Behavioral Specification

This is the most important part of the ontology.

## 9.1 Contract

A contract specifies behavior at an interface boundary.

```yaml
Contract:
  id:
  subject:
  operation:
  preconditions: []
  postconditions: []
  guarantees: []
  side_effects: []
  failure_behavior: []
```

Example:

```yaml
id: C-01-RUNBATCH

subject: CMP-ENGINE
operation: run_batch

preconditions:
  - n >= 0

postconditions:
  - processed increases by n
  - total_hits <= processed
  - x.shape == (n,)
  - y.shape == (n,)
  - is_hit[i] == (x[i]^2 + y[i]^2 <= 1)

guarantees:
  - draw_order_is_pinned
```

---

# 10. Invariant

An invariant expresses a proposition that must remain true.

```yaml
Invariant:
  id:
  subject:
  expression:
  scope:
  modality:
  violation_behavior:
  verification:
```

Example:

```yaml
id: I-005
type: Invariant

subject: CMP-ENGINE

expression:
  processed >= previous(processed)
  AND
  total_hits >= previous(total_hits)
  AND
  total_hits <= processed

scope: all_valid_runs

modality: MUST

verification:
  - T-04
```

This is directly derived from I-005 in the sample. [SPEC.md L303-306](SPEC.md#L303-L306)

---

# 11. Constraint

An invariant says something must always be true.

A constraint additionally specifies a **measurable property, threshold, metric, or resource bound**.

```yaml
Constraint:
  id:
  subject:
  metric:
  operator:
  threshold:
  unit:
  scope:
  measurement_method:
  verification:
```

Example:

```yaml
id: K-01

subject: MainWindow

metric: event_response_latency_p95
operator: <
threshold: 50
unit: ms

scope:
  state: RUNNING
  interval_ms: ">= 1"

measurement_method:
  probe_interval: 100ms
  duration: run_duration

verification:
  - T-07
```

This converts the current prose constraint into an executable semantic object. [SPEC.md L316-325](SPEC.md#L316-L325)

---

# 12. EdgeCase

An edge case defines a situation and required behavior.

```yaml
EdgeCase:
  id:
  trigger:
  preconditions: []
  required_behavior: []
  forbidden_behavior: []
  resulting_state:
  verification:
```

Example:

```yaml
id: E-05

trigger:
  "start_run is called while a run is live"

required_behavior:
  - return False
  - preserve_live_run
  - create_no_second_worker

forbidden_behavior:
  - create_second_worker

verification:
  - T-06
```

This makes the distinction between ordinary behavior and failure/edge behavior explicit. [SPEC.md L329-345](SPEC.md#L329-L345)

---

# 13. Decision

A decision captures a choice made where the specification does not uniquely determine an answer.

```yaml
Decision:
  id:
  question:
  selected_option:
  alternatives: []
  rationale:
  status:
    open
    confirm
    confirmed
    overturned
  affects: []
  owner:
  history: []
```

Example:

```yaml
id: D-08

question:
  "What RNG draw order is required?"

selected_option:
  "rng.random((n, 2))"

alternatives:
  - "rng.random(n) twice"

status: confirm

affects:
  - C-01
  - I-006
  - T-01
  - T-14
```

The important property is `affects`.

A decision is therefore a **dependency node**, not merely historical documentation.

The sample already makes these dependencies explicit. [SPEC.md L477-486](SPEC.md#L477-L486)

---

# 14. Obligation

## 14.1 The central concept

An `Obligation` is the bridge between specification and implementation.

A requirement may produce one or more obligations.

A contract may produce obligations.

An invariant is itself an obligation.

A constraint is an obligation.

An edge case may produce obligations.

```text
Requirement
     │
     ▼
 Obligation
     │
     ├── requires implementation
     ├── requires verification
     └── requires evidence
```

Definition:

```yaml
Obligation:
  id:
  source:
  subject:
  proposition:
  modality:
  scope:
  dependencies: []

  realization:
    required:
    implementation_targets: []

  verification:
    required:
    verification_methods: []

  status:
    unresolved
    planned
    implemented
    verified
    failed
    waived
```

Example:

```yaml
id: O-I006

source: I-006

subject: MonteCarloEngine

proposition:
  "For a fixed seed and N, the generated point sequence
   is independent of batch size."

realization:
  required: true
  implementation_targets:
    - MonteCarloEngine.__init__
    - MonteCarloEngine.run_batch

verification:
  required: true
  verification_methods:
    - T-01
    - T-14
```

This is arguably the most important addition beyond your current SPEC.md model.

---

# 15. Verification Model

## 15.1 VerificationMethod

A test or evaluation is a method for establishing an obligation.

```yaml
VerificationMethod:
  id:
  type:
    unit_test
    integration_test
    system_test
    property_test
    statistical_eval
    performance_test
    manual_eval
    static_analysis
    formal_check

  target_obligations: []

  procedure:
  pass_condition:
  environment:
  artifacts:
```

---

## 15.2 Test

`Test` specializes `VerificationMethod`.

```yaml
Test:
  id:
  type:
  target_obligations: []
  setup:
  stimulus:
  expected_result:
  pass_condition:
```

Example:

```yaml
id: T-03

type: unit_test

target_obligations:
  - I-003
  - I-004
  - I-009
  - E-12

pass_condition:
  |
  estimate == 4*h/processed
  AND
  standard_error ==
    4*sqrt(p*(1-p)/processed)
  AND
  z_score ==
    error_abs / standard_error
```

The sample's T-03 is already almost in this form. [SPEC.md L364-370](SPEC.md#L364-L370)

---

# 16. Probabilistic Evaluation

Tests and statistical evaluations should be distinct.

A deterministic test establishes:

```text
Given X
Expected Y
```

A statistical evaluation establishes:

```text
For population P
Under sampling procedure S
Property Q should hold
within statistical tolerance T
```

```yaml
StatisticalEvaluation:
  id:
  population:
  sample_count:
  repetitions:
  randomization:
  statistic:
  expected_distribution:
  tolerance:
  confidence_level:
  pass_condition:
```

Example:

```yaml
id: T-10

type: statistical_eval

population:
  seeds >= 50

sample_size:
  N = 100000

statistic:
  empirical_variance

expected:
  16*p*(1-p)/N
  where p = pi/4

tolerance:
  relative_error <= 20%
```

This distinction is important because the sample explicitly treats T-09 through T-12 as probabilistic/statistical evaluations rather than ordinary deterministic tests. [SPEC.md L373-379](SPEC.md#L373-L379)

---

# 17. Evidence

A test is not evidence.

A test is a **method** for producing evidence.

```text
Specification
      │
      ▼
  Obligation
      │
      ▼
 Verification Method
      │
      ▼
   Execution
      │
      ▼
   Evidence
```

```yaml
Evidence:
  id:
  verification_method:
  obligation:
  implementation_version:
  environment:
  execution_time:
  result:
    PASS
    FAIL
    INCONCLUSIVE

  measurements: {}
  artifacts: []
  provenance:
```

Example:

```yaml
id: EV-T07-20260916-001

verification_method: T-07
obligation: K-01

implementation_version: git:abc123

environment:
  platform: reference_hardware
  qt_platform: offscreen

result: PASS

measurements:
  p95_latency_ms: 37.2
  probes: 841
```

This distinction gives the system a notion of **current conformance**, rather than simply "there is a test for this."

---

# 18. Provenance

Every semantic claim should retain its source.

```yaml
SourceReference:
  id:
  artifact:
  location:
  excerpt:
  extraction_method:
    human
    llm
    parser
    inferred
  confidence:
```

For example:

```yaml
source_refs:
  - artifact: SPEC.md
    location: "s6 / I-006"
    extraction_method: llm
```

This allows the semantic database to answer:

> "Why does the ontology believe this requirement exists?"

That is essential for trust.

---

# 19. Relationships

The ontology is fundamentally a graph.

Core relations:

```text
contains
defines
refines
derives_from

requires
motivates
realizes
implemented_by
owned_by

depends_on
constrains
affects
conflicts_with
supersedes

transitions_to
triggered_by
guards

verified_by
produces_evidence
evidenced_by

invalidates
satisfies
violates

derived_from
originates_from
```

---

# 20. Relationship Semantics

## 20.1 `refines`

```text
Requirement → Contract
Requirement → Invariant
Requirement → Constraint
```

Meaning:

> The target provides a more operational definition of the source.

---

## 20.2 `realized_by`

```text
Requirement → Component
Requirement → Interface
Requirement → Behavior
```

Meaning:

> The target is responsible for realizing the requirement.

---

## 20.3 `constrains`

```text
Invariant → Component
Constraint → Component
Constraint → Interface
```

Meaning:

> The target must satisfy the source.

---

## 20.4 `verified_by`

```text
Requirement → Test
Invariant → Test
Constraint → Test
EdgeCase → Test
```

Meaning:

> The verification method is intended to establish satisfaction.

It does **not** mean the requirement currently passes.

That requires evidence.

---

## 20.5 `evidenced_by`

```text
Obligation → Evidence
```

Meaning:

> This concrete evidence supports the proposition.

---

## 20.6 `depends_on`

Generic dependency:

```text
A → depends_on → B
```

Changing B potentially invalidates A.

This relationship is central to change impact analysis.

---

# 21. Traceability is now a graph, not a table

Your current traceability matrix contains relationships such as:

```text
R-01 → MonteCarloEngine.run_batch → T-02,T-05,T-09
R-08 → MonteCarloEngine(seed) → T-01,T-14
R-09 → Worker + throttle → T-07
```

[SPEC.md L425-437](SPEC.md#L425-L437)

In SO-0.1 this becomes:

```text
R-08
 │
 ├──refines──> I-006
 │
 ├──realized_by──> C-01
 │
 ├──realized_by──> C-02
 │
 └──verified_by──> T-14
                         │
                         └──produces──> Evidence
```

The matrix is then simply a **view generated from the graph**.

---

# 22. Formal Expressions

The ontology needs an expression representation.

v0.1 should support at least:

```text
boolean expressions
arithmetic expressions
comparisons
quantifiers
set membership
temporal predicates
probabilistic predicates
resource metrics
```

Examples:

```text
x*x + y*y <= 1.0

processed <= N

total_hits <= processed

p95(event_latency) < 50ms

standard_error = 4*sqrt(p*(1-p)/N)

state == RUNNING

eventually processed == N
```

A minimal expression AST could be:

```yaml
Expression:
  operator:
  operands: []
```

Example:

```yaml
operator: LE
operands:
  - expression:
      operator: ADD
      operands:
        - MUL(x,x)
        - MUL(y,y)
  - 1.0
```

The actual expression language should be defined separately from the ontology.

---

# 23. Scope

Every proposition needs a scope.

```yaml
Scope:
  states: []
  actors: []
  components: []
  operations: []
  input_conditions: []
  parameter_constraints: []
  temporal_scope:
  environmental_scope:
```

For example, K-01 is not universally applicable.

It applies:

```text
state = RUNNING
interval_ms >= 1
```

This prevents a common specification error where a constraint is accidentally interpreted as universal.

The sample explicitly scopes K-01 this way. [SPEC.md L320-324](SPEC.md#L320-L324)

---

# 24. Modality and Conformance

For v0.1:

```text
MUST / SHALL
    → mandatory obligation

SHOULD
    → recommendation
    → deviation requires justification

MAY
    → optional

INFORMATIVE
    → no conformance obligation
```

Therefore:

```yaml
Obligation:
  modality: MUST
```

can produce:

```text
UNSATISFIED
```

whereas:

```yaml
Obligation:
  modality: SHOULD
```

may produce:

```text
SATISFIED
DEVIATION_JUSTIFIED
DEVIATION_UNJUSTIFIED
```

---

# 25. Conformance State

Every obligation has a conformance state.

```text
UNKNOWN
    ↓
PLANNED
    ↓
IMPLEMENTED
    ↓
VERIFIED
    ↓
CONFORMANT
```

Alternative branches:

```text
IMPLEMENTED → VERIFICATION_FAILED
IMPLEMENTED → VERIFICATION_INCONCLUSIVE
VERIFIED    → EVIDENCE_STALE
ANY         → WAIVED
```

A useful rule is:

```text
implemented ≠ conformant
```

and:

```text
test_exists ≠ verified
```

Only evidence can establish current verification status.

---

# 26. Conformance Rules

SO-0.1 should define a small rule system.

### Rule C-001 — Mandatory obligation

```text
IF obligation.modality ∈ {MUST, SHALL}
AND obligation.status != VERIFIED
THEN conformance != CONFORMANT
```

### Rule C-002 — Failed evidence

```text
IF obligation has current evidence
AND evidence.result == FAIL
THEN obligation.status = FAILED
```

### Rule C-003 — Stale evidence

```text
IF implementation_version(evidence)
   != current_implementation_version
THEN evidence.status = STALE
```

### Rule C-004 — Missing realization

```text
IF mandatory obligation
AND no implementation target realizes obligation
THEN status = UNREALIZED
```

### Rule C-005 — Missing verification

```text
IF mandatory obligation
AND no verification method exists
THEN status = UNVERIFIABLE
```

### Rule C-006 — Broken traceability

```text
IF requirement has no realization
OR requirement has no verification path
THEN traceability_status = INCOMPLETE
```

### Rule C-007 — Dependency invalidation

```text
IF specification element X changes
THEN all dependent verification evidence may become STALE
```

---

# 27. Implementation Model

The ontology should not stop at the specification.

It needs a second graph describing the actual implementation.

```text
Implementation
│
├── Package
├── Module
├── Class
├── Function
├── Method
├── Variable
├── Interface
├── Dependency
├── Thread
├── DataFlow
└── Behavior
```

For example:

```yaml
ImplementationComponent:
  id:
  source_location:
  language:
  symbol:
  type:
  implements: []
  calls: []
  imports: []
```

This creates:

```text
Specification Component
          │
          │ implemented_by
          ▼
Implementation Component
```

---

# 28. Example: I-002

Specification:

```yaml
id: I-002
type: Invariant

subject: MonteCarloEngine

expression:
  is_hit == (x*x + y*y <= 1.0)

verification:
  - T-02
```

Implementation:

```yaml
id: IMPL-MCE-ISHIT

symbol: MonteCarloEngine.run_batch

behavior:
  is_hit = x*x + y*y <= 1.0
```

Conformance relationship:

```text
I-002
 │
 ├──requires──>
 │
 ▼
is_hit(x,y) ↔ x²+y²≤1
 │
 │ satisfied_by
 ▼
MonteCarloEngine.run_batch
 │
 │ verified_by
 ▼
T-02
 │
 │ produces
 ▼
EV-T02-...
```

This is the basic semantic-conformance loop.

---

# 29. Implementation Planning Model

Planning becomes another semantic layer.

```yaml
ImplementationPhase:
  id:
  objective:
  prerequisites: []
  work_items: []
  obligations_addressed: []
  deliverables: []
  verification: []
```

```yaml
WorkItem:
  id:
  description:
  target_component:
  prerequisites: []
  satisfies: []
  produces: []
```

A planner can therefore derive:

```text
Obligations
      ↓
Dependencies
      ↓
Components
      ↓
Work Items
      ↓
Phases
```

rather than generating an implementation plan solely from document prose.

---

# 30. Automatic Phase Derivation

For example:

```text
I-001..I-006
      ↓
MonteCarloEngine
      ↓
Phase 1: Core Engine

C-02,C-03,K-06
      ↓
EstimationWorker
      ↓
Phase 2: Worker

C-05,C-06,R-05,R-06
      ↓
MainWindow
      ↓
Phase 3: Visualization

K-01,K-05,I-008
      ↓
Worker + UI integration
      ↓
Phase 4: Responsiveness

T-09..T-12
      ↓
Statistical behavior
      ↓
Phase 5: Statistical validation
```

The phase boundaries are therefore derived from the dependency graph.

---

# 31. Dependency Graph

Every semantic object may participate in dependencies.

```text
Dependency:
  source:
  target:
  kind:
    structural
    behavioral
    temporal
    verification
    implementation
    decision
  reason:
```

Example:

```text
D-08
 │
 ├──affects──> I-006
 │
 ├──affects──> C-01
 │
 ├──affects──> T-01
 │
 └──affects──> T-14
```

Changing D-08 therefore creates an impact set.

---

# 32. Change Impact Analysis

Given:

```text
change(D-08)
```

the system traverses:

```text
D-08
 ↓
I-006
 ↓
C-01
 ↓
MonteCarloEngine
 ↓
T-01,T-14
 ↓
existing evidence
```

and produces:

```yaml
ImpactReport:
  changed:
    - D-08

  affected:
    - I-006
    - C-01
    - T-01
    - T-14
    - implementation.MonteCarloEngine

  evidence_invalidated:
    - EV-T01-...
    - EV-T14-...

  plan_revisions_required:
    - Phase-1
```

This is one of the strongest reasons to have the semantic graph.

---

# 33. Specification Compilation

The first agent operating on SO-0.1 should be a **Specification Compiler**.

Input:

```text
SPEC.md
```

Output:

```text
Specification Graph
```

The compiler should perform:

```text
1. Parse explicit structures
2. Identify semantic entities
3. Extract relationships
4. Extract propositions
5. Extract constraints
6. Extract state machines
7. Extract verification relationships
8. Extract decisions
9. Extract provenance
10. Detect unresolved ambiguity
11. Generate obligations
12. Validate ontology consistency
```

Critically, the compiler should be allowed to say:

```text
UNRESOLVED
```

rather than inventing semantics.

---

# 34. Confidence and Human Ratification

Semantic extraction should carry confidence.

```yaml
Extraction:
  source:
  semantic_object:
  confidence:
  method:
  requires_ratification:
```

For example:

```yaml
confidence: 0.96
requires_ratification: false
```

or:

```yaml
confidence: 0.61
requires_ratification: true
```

This is particularly appropriate for ambiguous prose.

A human can then ratify:

```text
EXTRACTED → CONFIRMED
```

without modifying the underlying ontology manually.

---

# 35. Generated Views

Once the semantic model exists, documents become views.

## SPEC.md

```text
semantic specification → human-readable specification
```

## PLAN.md

```text
obligations + dependencies → implementation plan
```

## TEST_PLAN.md

```text
verification obligations → test plan
```

## TRACEABILITY.md

```text
graph relationships → traceability matrix
```

## CONFORMANCE.md

```text
implementation + evidence → conformance report
```

## CHANGE_IMPACT.md

```text
changed nodes → affected graph
```

This is the architectural payoff.

---

# 36. Minimal Physical Representation

I would initially avoid committing to a particular graph database.

The canonical logical representation could simply be JSON/YAML.

For example:

```yaml
specification:
  id: SPEC-MONTE-CARLO-PI
  version: 0.2

  requirements:
    - id: R-01
      ...

  components:
    - id: CMP-ENGINE
      ...

  relationships:
    - source: R-01
      predicate: realized_by
      target: CMP-ENGINE

  obligations:
    - id: O-I006
      ...

  verification:
    - id: T-01
      ...

  evidence:
    - id: EV-T01-001
      ...
```

A graph database can then be added behind this logical model.

---

# 37. Suggested Storage Architecture

I would probably use three layers:

```text
             ┌────────────────────────┐
             │ Semantic API / Query    │
             └───────────┬────────────┘
                         │
              ┌──────────┴───────────┐
              │                      │
       Graph representation     Rule engine
              │                      │
              └──────────┬───────────┘
                         │
                Persistent storage
```

The persistent implementation could initially be:

```text
SQLite
    +
JSON/JSONL
    +
typed schema
```

rather than immediately adopting a specialized graph database.

The important part is the **semantic API**, not the storage engine.

---

# 38. Semantic Query Language

The system should eventually support queries such as:

```text
Which requirements have no implementation?

Which mandatory obligations are unverified?

Which components realize R-09?

What constraints apply to MainWindow?

Which tests verify I-006?

What changes would invalidate T-01?

Which implementation phases depend on D-08?

Which specification elements have no provenance?

Which obligations have conflicting requirements?

Which constraints cannot currently be measured?

What behavior is required when the worker crashes?
```

These are graph queries rather than document searches.

---

# 39. A Very Important Distinction

SO-0.1 should distinguish:

```text
SEMANTIC FACT
```

from

```text
ASSERTION
```

from

```text
EVIDENCE
```

For example:

```text
I-006 says:

"For fixed seed and N, result is independent of batch size."
```

This is a **specification assertion**.

T-01 says:

```text
Test batch-size independence.
```

This is a **verification method**.

The result:

```text
seed=42
N=1,000,000
B=1000   → estimate X
B=7919   → estimate X
```

is **evidence**.

Only the third is an observation about the implementation.

This separation prevents the semantic database from confusing:

> "The specification says X"

with:

> "The implementation does X."

---

# 40. Conformance is therefore a reasoning problem

The ultimate model becomes:

```text
                SPECIFICATION
                     │
                     ▼
                 OBLIGATIONS
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
   IMPLEMENTATION         VERIFICATION
          │                     │
          └──────────┬──────────┘
                     ▼
                  EVIDENCE
                     │
                     ▼
              CONFORMANCE
```

The conformance engine evaluates:

$$
C(O,I,E)
$$

where:

- $O$ = specification obligations,
- $I$ = implementation,
- $E$ = verification evidence.

---

# 41. v0.1 Conformance States

The first version should produce something like:

```text
CONFORMANT
NON_CONFORMANT
PARTIALLY_CONFORMANT
UNVERIFIED
UNREALIZED
UNVERIFIABLE
STALE
INCONCLUSIVE
WAIVED
UNKNOWN
```

Importantly, `UNKNOWN` should be a legitimate result.

An AI-native specification system should **never convert missing knowledge into conformance**.

---

# 42. Example: Complete Semantic Chain

For the Monte Carlo specification:

```text
R-08
│
│ refines
▼
I-006
│
│ creates
▼
O-I006
│
├── realized_by
│       │
│       ▼
│   MonteCarloEngine.__init__
│   MonteCarloEngine.run_batch
│
└── verified_by
        │
        ▼
       T-01
        │
        ▼
    execution
        │
        ▼
     Evidence
        │
        ▼
   CONFORMANT
```

This is the smallest useful unit of Specification Engineering.

---

# 43. Ontology v0.1 Core Schema

The minimum viable ontology is therefore:

```text
SpecificationElement

Intent:
    Requirement
    Goal

SystemModel:
    Actor
    Component
    Interface
    DataType
    State
    Event
    Transition

Behavior:
    Contract
    Invariant
    Constraint
    EdgeCase

Decision:
    Decision

Planning:
    Obligation
    WorkItem
    ImplementationPhase

Verification:
    Test
    StatisticalEvaluation
    Evidence

Provenance:
    SourceReference
    Revision
```

with the following essential relations:

```text
contains
refines
derives_from

realized_by
implemented_by
owned_by

requires
depends_on
constrains
affects
conflicts_with
supersedes

triggered_by
transitions_to
guards

verified_by
produces_evidence
evidenced_by

satisfies
violates
invalidates
```

---

# 44. What v0.1 Deliberately Does Not Attempt

Do not put everything into the first ontology.

Specifically, v0.1 does not attempt to fully formalize:

- arbitrary natural language,
- complete temporal logic,
- full UML semantics,
- complete programming-language semantics,
- distributed-systems semantics,
- formal proofs,
- ontology alignment across organizations,
- automatic requirements elicitation,
- automatic architectural optimization.

Those can come later.

The initial objective is narrower:

> **Represent the semantic structure already present in a good Level-3 specification.**

---

# 45. The Proposed Architecture

The complete v0.1 system can therefore be visualized as:

```text
                         ┌───────────────┐
                         │    Human      │
                         │    Intent     │
                         └───────┬───────┘
                                 │
                                 ▼
                         ┌───────────────┐
                         │ Specification │
                         │     Agent     │
                         └───────┬───────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Specification Knowledge │
                    │         Graph            │
                    │                         │
                    │ Requirements            │
                    │ Contracts               │
                    │ Invariants              │
                    │ Constraints             │
                    │ States                  │
                    │ Decisions               │
                    │ Obligations             │
                    │ Tests                   │
                    │ Evidence                │
                    └───────────┬─────────────┘
                                │
              ┌─────────────────┼──────────────────┐
              │                 │                  │
              ▼                 ▼                  ▼
        Plan Generator    Test Generator    Conformance
              │                 │              Engine
              ▼                 ▼                  ▲
       Implementation      Verification           │
           Plan              Plan                 │
              │                 │                  │
              └──────────┬──────┘                  │
                         ▼                         │
                   Implementation ────────────────┘
                         │
                         ▼
                      Evidence
```

---

# 46. The Key Concept

The deepest change introduced by SO-0.1 is this:

**Today:**

```text
SPEC.md
   ↓
LLM interpretation
   ↓
Plan
```

**With Specification Ontology:**

```text
SPEC.md
   ↓
semantic compilation
   ↓
Specification Knowledge Graph
   ↓
obligations + dependencies
   ↓
Implementation Plan
```

and later:

```text
Implementation
      +
Verification Evidence
      ↓
Conformance Engine
      ↓
Specification Knowledge Graph
      ↓
CONFORMANCE REPORT
```

The Markdown document ceases to be the thing the agent repeatedly "reads and understands."

It becomes **one serialization of a persistent semantic model**.

That is, in my view, the architectural move that takes your current Level-3 SPEC approach toward a genuinely **AI-native Specification Engineering system**.

:::

### One thing I would change from your current terminology

I would seriously consider making **Obligation** the central abstraction of the entire system.

Your current SPEC has requirements, contracts, invariants, constraints, edge cases, and tests as somewhat parallel categories. The ontology reveals that they have a common underlying purpose:

> **They create propositions that an implementation must satisfy and that can, in principle, be verified.**

That gives us:

```text
Requirement
Contract
Invariant
Constraint
Edge Case
       │
       ▼
   Obligation
       │
       ├───────────────┐
       ▼               ▼
 Realization       Verification
       │               │
       ▼               ▼
Implementation      Evidence
       └───────┬───────┘
               ▼
          Conformance
```

I think **that is the conceptual center of the ontology**.

And there is a very concrete next experiment: take your actual 499-line `SPEC.md` and **compile all of it into an SO-0.1 instance**, not just a toy example. That would expose exactly where the ontology is insufficient—particularly around mathematical expressions, temporal behavior, probabilistic assertions, UI semantics, and the distinction between *verification method* and *verification evidence*. The resulting instance would also give us enough material to design the actual schema/API rather than designing it in the abstract.

## USER

by "compile all of it" you mean create create YAML version per SO-0.1? Or do you actually mean: "construct an agent that can take SPEC and produce YAML"? Or something else?

## ASSISTANT

Yes — I meant **something more fundamental than simply converting `SPEC.md` into YAML**.

There are really **three different things**, and I was conflating them:

### 1. YAML representation of the ontology

This is just the **data representation**:

```yaml
specification:
  id: MCPI-SPEC
  version: "0.2"

requirements:
  - id: R-08
    title: Reproducible runs
    ...

invariants:
  - id: I-006
    title: Batch-independent determinism
    ...

contracts:
  - id: C-01
    ...
```

This would be useful, but by itself it doesn't buy us much. It's essentially a structured serialization of `SPEC.md`.

---

### 2. Compiling `SPEC.md` into an SO-0.1 semantic model

This is what I **actually mean by "compile all of it."**

The input is your existing human-authored specification:

```text
SPEC.md
   │
   ▼
Specification Compiler
   │
   ▼
SO-0.1 Semantic Model
```

The output might happen to be YAML:

```text
spec.yaml
```

but the important thing is that the YAML is merely the **serialization of the ontology instance**.

For example, your:

> I-006: fixed seed + N produces same sequence/results regardless of batch size/delivery chunking

wouldn't merely become a YAML paragraph. The compiler would recognize that this is an **Invariant**, identify its entities and relationships, and represent its semantics approximately as:

```yaml
id: I-006
type: Invariant
statement:
  type: equivalence
  left:
    operation: run
    parameters:
      seed: $seed
      N: $N
    execution:
      batch_size: $b1
  right:
    operation: run
    parameters:
      seed: $seed
      N: $N
    execution:
      batch_size: $b2

scope:
  component: MonteCarloEngine

realized_by:
  - C-01
  - ...

verified_by:
  - T-01
  - T-14
```

The exact representation would need to be designed carefully, but **that's the conceptual leap**.

The compiler is therefore doing semantic interpretation, not Markdown → YAML conversion.

---

### 3. The agent that performs the compilation

And **yes, ultimately I mean constructing an agent/tool that does #2.**

Something like:

```text
                  ┌─────────────────────┐
                  │      SPEC.md        │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Specification       │
                  │ Compiler Agent      │
                  └──────────┬──────────┘
                             │
                 parse + classify
                 extract entities
                 infer relationships
                 normalize expressions
                 detect inconsistencies
                 resolve references
                 assign provenance
                             │
                             ▼
                  ┌─────────────────────┐
                  │ SO-0.1 Semantic     │
                  │ Specification Model │
                  └──────────┬──────────┘
                             │
                       serialize
                             │
                             ▼
                  ┌─────────────────────┐
                  │ specification.yaml  │
                  └─────────────────────┘
```

But there's an important additional step:

## I would not make the LLM the "compiler"

I'd make the architecture more like a **compiler pipeline**.

```text
SPEC.md
   │
   ├── Markdown parser
   │
   ▼
Structured document
   │
   ├── semantic extraction
   │        ↑
   │      LLM
   │
   ▼
Candidate SO model
   │
   ├── ontology validation
   │
   ├── reference resolution
   │
   ├── consistency checking
   │
   ├── constraint validation
   │
   └── provenance tracking
   │
   ▼
Canonical Specification Graph
```

The LLM is particularly useful for the **semantic extraction** step:

> "This paragraph describes an invariant."

> "This sentence establishes a constraint on event-loop latency."

> "C-01 references the `MonteCarloEngine` component."

> "D-08 modifies the interpretation of I-006."

But the resulting semantic model should be validated by deterministic machinery.

---

# And there is a fourth thing

This is where I think the idea becomes much more interesting.

I don't think we ultimately want:

```text
SPEC.md → YAML
```

I think we want:

```text
                       ┌──────────────┐
                       │   SPEC.md    │
                       └──────┬───────┘
                              │
                         compile
                              ▼
                  ┌──────────────────────┐
                  │ Specification Graph  │
                  │       SO-0.1         │
                  └──────────┬───────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
          Planning       Verification    Documentation
              │              │              │
              ▼              ▼              ▼
        IMPLEMENTATION   CONFORMANCE     SPEC.md
           PLAN.md         REPORT.md     TRACEABILITY
```

In other words, **the ontology becomes the intermediate representation (IR) of specification engineering.**

That's the analogy I'd emphasize.

### Traditional compiler

```text
Source code
    ↓
AST
    ↓
IR
    ↓
optimized IR
    ↓
machine code
```

### Specification engineering

```text
Human specification
       ↓
semantic model
       ↓
Specification IR / Graph
       ↓
implementation plan
       ↓
implementation
       ↓
verification evidence
       ↓
conformance
```

And that gives us something we don't get from a YAML representation alone:

**the same semantic model can drive both forward and backward reasoning.**

Forward:

```text
SPEC
 ↓
Ontology
 ↓
What must be built?
 ↓
Implementation Plan
```

Backward:

```text
Implementation
 ↓
Observed behavior / code / tests
 ↓
What obligations does this satisfy?
 ↓
Does it conform to the specification?
```

And potentially sideways:

```text
Decision D-08
      ↓
Which requirements/contracts/invariants does it affect?
      ↓
Which implementation components?
      ↓
Which tests?
      ↓
Which plans?
      ↓
What needs to be re-verified?
```

That is **much more powerful than "SPEC.md in YAML."**

---

## So I would build this incrementally

I wouldn't start by building the agent.

I'd first take your actual 499-line Monte Carlo `SPEC.md` and manually/semiautomatically construct:

**`spec.yaml` = one complete instance of SO-0.1.**

That exercise will almost certainly expose weaknesses in SO-0.1.

Then we'd have:

```text
SO-0.1 ontology
       +
real 499-line SPEC
       ↓
complete semantic instance
```

From that we can determine:

1. What concepts are missing?
2. Which concepts are redundant?
3. Which relationships are actually needed?
4. Which statements require an expression language?
5. Which semantics cannot be represented faithfully?
6. Which things require human judgment?
7. What should be inferred versus explicitly asserted?
8. What should be provenance-preserved from the original Markdown?

**Only after that would I build the Specification Compiler Agent.**

So, when I said **"compile all of it," my intended meaning was:**

> **Take the entire existing SPEC.md and construct a complete SO-0.1 semantic instance from it, probably serialized initially as YAML, while preserving provenance and making the semantic relationships explicit.**

The YAML is the **artifact**.  
The ontology is the **model**.  
The compiler is the **agent/tool that creates the model**.

And I think doing the first complete YAML instance from your Monte Carlo spec is the right next experiment, because it will be a very good **ontology validation exercise**, rather than designing SO-0.1 in the abstract.

---

If you want, I can:

- Detail Specification Compilation Steps
- Expand on Expression Language Design
- Illustrate Traceability Graph Construction
