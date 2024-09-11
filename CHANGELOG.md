# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.1] - 2024-09-11

### Fixed

* Use a context manager for opening files in https://github.com/CQCL/pytket-phir/pull/219
* Emit nested binary expressions for classical ops in https://github.com/CQCL/pytket-phir/pull/224

## [0.8.0] - 2024-07-16

### Added

* Support for 64-bits while maintaining backward compatibility.

### Changed

* Abstract `WORDSIZE` to specify `maxwidth` on qasm conversion in https://github.com/CQCL/pytket-phir/pull/204 including
  * generate cvar with `data_type` dependent on `WORDSIZE`
  * Fail early on WASM calls with parameters using more than 32-bits
  * Require 64-bit version of PECOS, emit i32/i64 cvars for compatibility

## [0.7.3] - 2024-06-18

### Added

* Set maximum bit width for classical operations according to pytket support in https://github.com/CQCL/pytket-phir/pull/190
  * Fixes [#165: `UINTMAX` is hard-coded as `2^32 - 1`](https://github.com/CQCL/pytket-phir/issues/165)

## [0.7.2] - 2024-05-28

### Added

* feat(phirgen): add support for ZERO/ONE nullary ops by @qartik in https://github.com/CQCL/pytket-phir/pull/180

## [0.7.1] - 2024-04-12

### Fixed

* do nothing on Init gate instead of warning by @Asa-Kosto-QTM in https://github.com/CQCL/pytket-phir/pull/166

## [0.7.0] - 2024-04-10

### Added

* PHIR generation for `ExplicitPredicate`, `ExplicitModifier`, `MultiBitOp` in https://github.com/CQCL/pytket-phir/pull/162
  * Also fixes a bug with handling conditional ops

## [0.6.3] - 2024-04-02

### Fixed

* wasm/phirgen: correct arguments for conditional wasm functions in https://github.com/CQCL/pytket-phir/pull/157

## [0.6.2] - 2024-03-27

### Fixed

* phirgen: don't rely on args when qubits carries correct info in https://github.com/CQCL/pytket-phir/pull/155

## [0.6.1] - 2024-03-26

### Fixed

* Remove unneeded logic for comments for conditionals in https://github.com/CQCL/pytket-phir/pull/152
  * Fixes `make_comment_text` repeats the condition for conditional ops (https://github.com/CQCL/pytket-phir/issues/149)
* Invalid reordering of operations involving classical bits in https://github.com/CQCL/pytket-phir/pull/151
  * Fixes https://github.com/CQCL/pytket-phir/issues/150

## [0.6.0] - 2024-03-15

### Changed

* show approx transport time in PHIR in https://github.com/CQCL/pytket-phir/pull/147
  * **BREAKING CHANGE**: machine names `H1_1`/`H1-1` and `H1_2`/`H1-2` are now deprecated in favor of `H1`

## [0.5.1] - 2024-03-13

### Changed

* float not str for duration in https://github.com/CQCL/pytket-phir/pull/144

## [0.5.0] - 2024-03-06

### Added

* phirgen: add support for Sleep/Idle mop in https://github.com/CQCL/pytket-phir/pull/141
  * requires `phir>=0.3.1`

### Changed

* phirgen: better comments for classical expressions in PHIR output

## [0.4.4] - 2024-02-27

### Fixed

* support for nested bitwise ops in https://github.com/CQCL/pytket-phir/pull/135
* phirgen: emit "Skip" `"mop"` instead of raising error on global phase in https://github.com/CQCL/pytket-phir/pull/138

## [0.4.3] - 2024-02-15

### Removed

* An unnecessary ordering check exposed by an edge case in https://github.com/CQCL/pytket-phir/pull/125

## [0.4.2] - 2024-02-07

### Fixed

* Bugs in execution order of subcommands in https://github.com/CQCL/pytket-phir/pull/124

## [0.4.1] - 2024-02-02

### Added

* emit barrier instructions during phirgen in https://github.com/CQCL/pytket-phir/pull/118

### Fixed

* minor typing/linting issues in https://github.com/CQCL/pytket-phir/pull/116
* bug in sharding that assumed only one qreg declaration in https://github.com/CQCL/pytket-phir/pull/120

## [0.4.0] - 2024-01-26

### Removed

* `pytket-quantinuum` dependency in https://github.com/CQCL/pytket-phir/pull/107
  * **BREAKING**: Removes the `tket_optimization_level` argument to `pytket_to_phir`, i.e., input programs are expected to have any optimizations performed beforehand.

### Fixed

* A couple of bugs in parallel phirgen:
  * Prevent parallel blocks in 1-qubit circuits in https://github.com/CQCL/pytket-phir/pull/109
  * Stricter ordering checks in https://github.com/CQCL/pytket-phir/pull/112

## [0.3.0] - 2024-01-23

### Added

* Support for WASM files in https://github.com/CQCL/pytket-phir/pull/77
* Support for bitwise operations in https://github.com/CQCL/pytket-phir/pull/94

### Fixed

* sharder: issue with classical ordering in https://github.com/CQCL/pytket-phir/pull/96

## [0.2.1] - 2024-01-17

### Added

* Support for Python 3.12 in https://github.com/CQCL/pytket-phir/pull/89

### Fixed

* RZ/R1XY order swapping issue in https://github.com/CQCL/pytket-phir/pull/82
* Various phirgen bugs in https://github.com/CQCL/pytket-phir/pull/90:

  * `ClassicalExpBox` conversion is incomplete https://github.com/CQCL/pytket-phir/issues/86
  * `KeyError: 'name'` raised by `pytket_to_phir` with arithmetic operation https://github.com/CQCL/pytket-phir/issues/87
  * `TypeError: 'int' object is not subscriptable` raised by `pytket_to_phir` with arithmetic operation https://github.com/CQCL/pytket-phir/issues/88

## [0.2.0] - 2023-12-18

### Added

* Support for quantum parallel operations in https://github.com/CQCL/pytket-phir/pull/53
* Support for `CopyBits` op in https://github.com/CQCL/pytket-phir/pull/67

### Changed

* Minimum supported version of `phir` is now `v0.2.1` that supports `"qparallel"` blocks.
* Performance improvement via sharder rework in https://github.com/CQCL/pytket-phir/pull/64
* phirgen: metadata now includes pytket-phir version, see https://github.com/CQCL/pytket-phir/pull/65
* pytket-phir can now consume QASM strings as opposed to files alone by @neal-erickson in https://github.com/CQCL/pytket-phir/pull/69

### Fixed

* phirgen: R2XXYYZZ is a 2-qubit gate in https://github.com/CQCL/pytket-phir/pull/60
* phirgen: pass all bits in lhs of SetBitsOp in https://github.com/CQCL/pytket-phir/pull/63

## [0.1.2] - 2023-12-07

* build: add minimum pytket/pytket-quantinuum versions
* build: pin pecos to pre-release version
* chore: update dependencies

## [0.1.1] - 2023-11-17

* build: add missing dep, correct Python constraint in https://github.com/CQCL/pytket-phir/pull/37

## [0.1.0] - 2023-11-17

First release.

[0.1.0]: https://github.com/CQCL/pytket-phir/commits/v0.1.0
[0.1.1]: https://github.com/CQCL/pytket-phir/compare/v0.1.0...v0.1.1
[0.1.2]: https://github.com/CQCL/pytket-phir/compare/v0.1.1...v0.1.2
[0.2.0]: https://github.com/CQCL/pytket-phir/compare/v0.1.2...v0.2.0
[0.2.1]: https://github.com/CQCL/pytket-phir/compare/v0.2.0...v0.2.1
[0.3.0]: https://github.com/CQCL/pytket-phir/compare/v0.2.1...v0.3.0
[0.4.0]: https://github.com/CQCL/pytket-phir/compare/v0.3.0...v0.4.0
[0.4.1]: https://github.com/CQCL/pytket-phir/compare/v0.4.0...v0.4.1
[0.4.2]: https://github.com/CQCL/pytket-phir/compare/v0.4.1...v0.4.2
[0.4.3]: https://github.com/CQCL/pytket-phir/compare/v0.4.2...v0.4.3
[0.4.4]: https://github.com/CQCL/pytket-phir/compare/v0.4.3...v0.4.4
[0.5.0]: https://github.com/CQCL/pytket-phir/compare/v0.4.4...v0.5.0
[0.5.1]: https://github.com/CQCL/pytket-phir/compare/v0.5.0...v0.5.1
[0.6.0]: https://github.com/CQCL/pytket-phir/compare/v0.5.1...v0.6.0
[0.6.1]: https://github.com/CQCL/pytket-phir/compare/v0.6.0...v0.6.1
[0.6.2]: https://github.com/CQCL/pytket-phir/compare/v0.6.1...v0.6.2
[0.6.3]: https://github.com/CQCL/pytket-phir/compare/v0.6.2...v0.6.3
[0.7.0]: https://github.com/CQCL/pytket-phir/compare/v0.6.3...v0.7.0
[0.7.1]: https://github.com/CQCL/pytket-phir/compare/v0.7.0...v0.7.1
[0.7.2]: https://github.com/CQCL/pytket-phir/compare/v0.7.1...v0.7.2
[0.7.3]: https://github.com/CQCL/pytket-phir/compare/v0.7.2...v0.7.3
[0.8.0]: https://github.com/CQCL/pytket-phir/compare/v0.7.3...v0.8.0
[0.8.1]: https://github.com/CQCL/pytket-phir/compare/v0.8.0...v0.8.1
[unreleased]: https://github.com/CQCL/pytket-phir/compare/v0.8.1...HEAD

<!-- markdownlint-configure-file {"MD024": {"siblings_only" : true}, "MD034": false} -->
