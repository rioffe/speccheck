# speccheck:ignore-file — line 1 is dropped by tests/test_16_namespaces.py (F-713)
# Spec (T-108)

| ID | Statement |
| -- | --------- |
| **R-01** | names platform:R-02 only |
| **R-02** | names platform:R-03 and bare R-03 |
| **R-03** | plain |
| **R-04** | plain |
| **R-05** | ranges platform:R-01..R-04 |

| ID | Decision | Affects |
| -- | -------- | ------- |
| D-01 | x | platform:R-01, R-02 |
