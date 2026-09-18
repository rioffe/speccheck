// LegacyTests.swift — XCTest half of the golden fixture (speccheck fixtures/target-swift).
import XCTest

@testable import Calc

final class LegacyTests: XCTestCase {
    /// R-01 through the legacy runner too.
    func testVersionString() {
        XCTAssertEqual(Calc.version, "1.0")
        XCTAssertEqual(Calc.add(1, 1), 2)
    }

    func helper() {}
}
