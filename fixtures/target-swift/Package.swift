// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "Calc",
    platforms: [.macOS(.v14)],
    targets: [
        .target(name: "Calc"),
        .testTarget(name: "CalcTests", dependencies: ["Calc"]),
    ]
)
