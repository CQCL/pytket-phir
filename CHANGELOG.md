# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0]

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
[unreleased]: https://github.com/CQCL/pytket-phir/compare/v0.2.0...HEAD

<!-- markdownlint-configure-file {"MD024": {"siblings_only" : true}, "MD034": false} -->
