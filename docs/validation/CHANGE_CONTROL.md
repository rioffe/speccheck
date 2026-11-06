# Change control — what a speccheck release obliges its users to do

> **Applies to:** speccheck 1.26.0 and later (`SPEC.md` v1.26, D-71).

## The rule

1. **Every tagged release gets a GitHub release** whose notes carry:
   - the `package_tree_sha256` of the tag, computed from `src/speccheck/` by
     `tools/validation_impact.py` (the value `speccheck qualify` prints the first 12 digits of);
   - a **Validation impact** section, produced by `uv run python tools/validation_impact.py <the
     previous release's tag>`, which lists:
     - every tool hazard whose controls changed: the ids `speccheck impact --against <the previous
       release's SPEC.md>` reports changed, joined with the CONTROLS markers of this `SPEC.md`;
     - every operational-qualification case whose packaged fixture, goldens or catalog changed;
   - the known anomalies added or fixed in the release.
2. **Users re-run `speccheck qualify` on every upgrade**, whatever the Validation impact section
   lists. It takes seconds and is the IQ/OQ of the new version (`IQ_OQ_PROTOCOL.md`).
3. **A non-empty Validation impact section tells the user's reviewer what to read**: the changed
   controls' rows in `SPEC.md` and the changed cases. Whether that triggers more than re-running
   `qualify` (for example, repeating performance qualification) is the user's decision under their
   own change-control procedure.

## Why a rule and not a list

A hand-kept list of "validation-critical contracts" goes stale: four of the controls the
readiness plan names (C-01, C-03, C-04 and R-15) changed between v1.18 and v1.25 with nothing
flagging it. The CONTROLS markers make the list part of the specification, and `impact` computes what
changed against it.

Note the one thing the computation does not see: a CONTROLS marker added to or removed from a row
is not a C-13 change (C-27), so it never appears as a changed control. Adding a control is a
strengthening; removing one shows up as `UNCONTROLLED` in speccheck's own build gate long before a
release.

## Known anomalies

`src/speccheck/_qualify/known_anomalies.json` is append-only. An anomaly is never renumbered or
removed; when fixed, its `fixed_in` is set to the version that fixes it and it stops being printed
in qualification records of that version and later.

## Versions

speccheck's version is `<spec major>.<spec minor>.<patch>`: `1.26.0` implements `SPEC.md` v1.26.
A patch release changes no spec row.
