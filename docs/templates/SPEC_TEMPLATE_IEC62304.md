# SPECIFICATION — <Software item name> (<intended use in a few words>; <stack>)

<!--
SPEC.md profile for medical device software (IEC 62304:2006+A1:2015 / ISO 13485:2016).
Copy this file to your project's SPEC.md and replace every <...>. Sections 0–12 are the
spec-writing skill's template; the regulated additions are marked "62304". Delete these comments.
The ids below (R-01, C-01, ...) are examples: speccheck checks every bold id you declare.
-->

> - **Status:** v0.1 — draft for review
> - **Software safety class (62304 4.3):** **<A | B | C>** — <one sentence: the worst harm a
>   failure of this software could contribute to, after external risk control measures>.
>   Assigned in `<risk management file, document id and revision>`; approved by <role>, <date>.
>   <If items of this system differ in class: name each item, its class, and the segregation that
>   justifies the difference (62304 5.3.5).>
> - **Device and intended use:** <device name, model>; <intended use and user population, as in
>   the device's intended-use statement, document id>.
> - **Language / stack:** <language + version> | <frameworks> | <surfaces>
> - **Sources:** system requirements `<document id, revision>`; risk management file `<id,
>   revision>`; usability engineering file `<id>` (62304 5.2.2 h); <other design inputs>.
> - **Scope of this document:** the software requirements specification (62304 5.2) of
>   <software item>, its software system test specification (62304 5.7.1, §9), and its SOUP
>   (§10.1). Not in scope: <hardware, labelling, other software items>.
> - **Normative language:** MUST/MUST NOT/SHALL/SHALL NOT = normative; SHOULD = strong
>   recommendation; MAY = optional.
> - **Principle:** <the one design thesis that governs trade-offs>.
> - **Approval:** this document is a controlled design input (ISO 13485 4.2.4, 7.3.3). Its
>   approval record lives in `<eQMS reference>`, not in this file.

---

## 0. Intent and purpose

<Why this software exists, in the device's context. The deterministic/probabilistic or
trusted/untrusted boundaries, if any. Non-goals.>

**Intended use of this software item.** <What the software does for the device's intended use, and
what it explicitly does not do — the boundary the risk analysis relies on.>

## 1. Actors and goals

| Actor | Goals |
| ----- | ----- |
| **<User role>** (<training, environment>) | <what they need from the software> |
| **<Device hardware / other software item>** | <the interface contract it relies on> |

### 1.1 User needs (62304: trace to system requirements)

<!-- Labels in this table (UN-01) are not speccheck ids: they are cited in the Source column of §2
so the trace from need to requirement is visible. Keep them stable; never renumber. -->

| Need | Statement | Source |
| --- | --- | --- |
| UN-01 | <the user need, in the user's terms> | <user research or design-input reference> |

## 2. Requirements (62304 5.2.1, 5.2.2)

<!-- One row per software requirement. Cite the system requirement (SYS-..) or user need (UN-..)
it derives from in the Source column (62304 5.2.1). A requirement that is a risk control measure
names the hazards it controls with the CONTROLS marker right after its id (62304 5.2.3, 7.2.2);
speccheck rolls each hazard up to VERIFIED / NOT_VERIFIED / UNCONTROLLED. -->

| ID | Statement | Source |
| -- | --------- | ------ |
| **R-01** | <functional requirement, observable, in MUST language> | SYS-<nn>, UN-01 |
| **R-02** *(controls: HAZ-001)* | <a requirement that is a risk control measure: what the software MUST do to prevent or detect the hazardous situation> | SYS-<nn>; risk file `HAZ-001` |

The software requirements cover each content area of 62304 5.2.2 that applies; an area that does
not apply says so here in one line:

| 62304 5.2.2 area | Where specified |
| --- | --- |
| a) functional and capability requirements | §2, §4 |
| b) software system inputs and outputs | §4 (C-nn contracts), §5 |
| c) interfaces between the software system and other systems | §4, §5 |
| d) software-driven alarms, warnings and operator messages | §5 (messages and codes), §8 |
| e) security requirements | §2 (R rows), §6 (I rows) |
| f) user interface requirements implemented by software (usability) | §5, with the usability engineering file's references |
| g) data definition and database requirements | §4 |
| h) installation and acceptance requirements | §10 |
| i) operation and maintenance methods | §5, §10 |
| j) IT-network aspects | §2, §10 |
| k) user maintenance requirements | §10 |
| l) regulatory requirements | §2 (cite the regulation in Source) |

## 3. Behavior and state model

<Lifecycle and state machine; the main flow; durable artifacts. A `mermaid` diagram where it
helps; rows stay normative.>

## 4. Interfaces / contracts (62304 5.2.2 b, c, g)

### C-01 <Interface or data shape>

```text
<the pinned shape: fields, types, ranges, units, defaults, ordering, versioning>
```

## 5. Interface specification

<One subsection per surface: operations, inputs, outputs, error codes and operator messages
(62304 5.2.2 d), defaults.>

## 6. Invariants

| ID | Invariant |
| -- | --------- |
| **I-001** | <a property every valid implementation keeps> |

## 7. Constraints (precise and measurable)

| ID | Constraint |
| -- | ---------- |
| **K-01** | <timing, size, resource, accuracy limit, with units> |

## 8. Edge cases and failure semantics

| ID | Case | Semantics |
| -- | ---- | --------- |
| **E-01** | <malformed input, unavailable dependency, timeout, partial failure> | <the deterministic outcome, including the operator message> |

## 9. Software system test specification (62304 5.7.1)

<!-- Every R/C/I/K/E id has at least one T id. A T row states an unambiguous pass condition and
cites the ids it verifies. A risk control measure's tests verify the measure (62304 7.3.1). -->

### 9.1 <group: unit / integration / system>

| ID | Test |
| -- | ---- |
| **T-01** | <a concrete, reproducible check with its pass condition> (R-01) |
| **T-02** | <the test that shows the risk control measure works, including the hazardous condition it is meant to catch> (R-02) |

### 9.2 Acceptance criteria for release

- `speccheck check --strict --judge mock --risk-file <risk.json> --manifest` exits `0`: every
  in-scope id `PASSING`, no dangling or stale citation, no hazard `UNCONTROLLED`.
- <Class B/C: every hazard VERIFIED; any open anomaly evaluated in the verification report
  (62304 5.8.2).>

## 10. Dependencies and environment (62304 5.2.2 h, i, k)

<Runtime, platform, installation and acceptance, operation and maintenance.>

### 10.1 SOUP — software of unknown provenance (62304 5.3.3, 5.3.4, 7.1.2, 8.1.2)

<!-- One row per SOUP item, including runtime libraries, operating system components and
frameworks the software item depends on. Labels (SOUP-01) are not speccheck ids. For class B and C
software, every column is required. -->

| SOUP | Title | Manufacturer | Unique designator (version) | Purpose in this software | Functional and performance requirements on it (5.3.3) | Hardware and software it requires (5.3.4) | Published anomaly list, and its evaluation (7.1.2) | Requirements that rely on it |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SOUP-01 | <name> | <vendor or project> | <exact version, pinned in the lockfile> | <why it is used> | <what it MUST do for this software; the R/K ids that state it> | <OS, runtime, hardware> | <URL or document, date reviewed, conclusion> | R-<nn>, K-<nn> |

A SOUP item's version changes only through change control: the new version's anomaly list is
evaluated again and this row's designator and evaluation are updated in the same change.

## 11. Traceability matrix (id → where realized)

| Spec id | Where realized (component / module) | Verified by (tests / evidence) |
| ------- | ----------------------------------- | ------------------------------ |
| R-01 | <module> | T-01 |

<!-- For the release record, generate the full matrix from speccheck's output with
docs/templates/TRACEABILITY_MATRIX_TEMPLATE.md. -->

## 12. Open questions and decisions to confirm

| ID | Decision | Default taken | Alternatives | Affects | Owner / status |
| ----- | -------------- | ---------------- | ------------------ | ---------- | ------------ |
| D-01 | <a choice the sources did not settle> | <the default assumed> | <what else was reasonable> | <ids> | <named owner: clinical, risk, privacy...> / confirm |

## Revision history

| Version | Change |
| -- | -------------- |
| v0.1 | Initial draft from <sources>. |
