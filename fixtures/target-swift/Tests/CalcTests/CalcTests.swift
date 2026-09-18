// CalcTests.swift — Swift Testing suite of the golden fixture (speccheck fixtures/target-swift).
import Testing

@testable import Calc

@Suite("Calc")
struct CalcTests {
    /// T-01, R-01: `add` returns the sum for integers and floats.
    @Test(arguments: [(1.0, 2.0, 3.0), (0.1, 0.2, 0.3)])
    func add(a: Double, b: Double, expected: Double) {
        #expect(Calc.add(a, b) == expected)
    }

    /// I-001: `add` commutes.
    @Test func addCommutes() {
        #expect(Calc.add(2, 5) == Calc.add(5, 2))
    }

    /// R-02: `subtract` returns a - b.
    @Test func subtract() {
        #expect(Calc.subtract(5, 2) == 3)
    }

    /// T-03, K-02: `subtract` of floats keeps two-decimal precision (planted FAILING).
    @Test func subtractPrecision() {
        #expect(Calc.subtract(1.0, 0.0) == 1.01)  // 1.0 != 1.01
    }

    /// T-02, C-01: divide by zero throws with the dividend in the error.
    @Test func divideByZero() {
        #expect(throws: CalcError.divideByZero(dividend: 7)) {
            try Calc.divide(7, 0)
        }
    }

    /// K-01: `divide` completes in under 1 ms (planted SKIPPED: disabled).
    @Test(.disabled("timing test not run in CI"))
    func divideFast() throws {
        _ = try Calc.divide(1, 3)
    }

    /// I-002: `scale` preserves the length (planted EXECUTES_ONLY: no assertion).
    @Test func scaleRuns() {
        _ = Calc.scale([1, 2, 3], by: 2)
    }

    @Suite struct Edges {
        /// E-02: an empty list scales to an empty list.
        @Test func scaleEmpty() {
            #expect(Calc.scale([], by: 3).isEmpty)
        }
    }

    /// E-01: negative inputs keep their sign (planted undelimited: no @Test, so file-level).
    func testScaleNegative() {
        _ = Calc.scale([-1], by: 2)
    }
}
