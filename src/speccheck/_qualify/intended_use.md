Intended use of speccheck in a quality management system (v1.26)

Validated function: `speccheck check`, `speccheck verify` and `speccheck impact`, each run with
`--judge none` or `--judge mock`, together with `speccheck --self-check` and `speccheck qualify`.
For one specification, one set of source and test trees and one results file, `check` reports
which declared requirements are cited, tested and passing; identical inputs give byte-identical
reports. `verify` reports whether the files a manifest names are unchanged. `impact` lists what a
change to the specification might touch.

Outside validated use: `--judge llm`, `--jev-pre-triage` and `speccheck explain`. They may be
used. The judge can only lower a status, never raise one, but its output is advisory and is not
verification evidence.

speccheck does not run tests, does not decide whether a risk is acceptable, and does not sign or
approve records. The user's quality system owns test execution, risk acceptance, review, approval
and signatures, and the validation of speccheck for the user's own intended use.
