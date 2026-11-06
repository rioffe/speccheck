-- Minimal Lean fixture for T-99: three declarations, two tagged, one untagged.

/-- **R-01** discharges the sum contract. -/
theorem addSpec : True := trivial

/-- **R-02** discharges the difference contract. -/
theorem subtractSpec : True := trivial

def untaggedHelper : Nat := 0
