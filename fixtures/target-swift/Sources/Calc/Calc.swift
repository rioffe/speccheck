// Calc.swift — the golden fixture's four functions (speccheck fixtures/target-swift).

public enum CalcError: Error, Equatable {
    case divideByZero(dividend: Double)  // C-01: the message names the dividend
}

/// R-01: the arithmetic sum, rounded per K-02.
public func add(_ a: Double, _ b: Double) -> Double {
    round2(a + b)  // I-001 holds because + commutes
}

/// R-02: a - b, rounded per K-02.
public func subtract(_ a: Double, _ b: Double) -> Double {
    round2(a - b)
}

/// C-01: throws `divideByZero(dividend:)` when b == 0.
public func divide(_ a: Double, _ b: Double) throws -> Double {
    guard b != 0 else { throw CalcError.divideByZero(dividend: a) }
    return round2(a / b)
}

/// C-02: returns a new array and never mutates its input; E-02: an empty input yields [].
public func scale(_ values: [Double], by factor: Double) -> [Double] {
    values.map { round2($0 * factor) }
}

/// K-02: every result is rounded to two decimal places.
func round2(_ x: Double) -> Double {
    (x * 100).rounded() / 100
}

public let version = "1.0"
