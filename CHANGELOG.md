# Changelog

## [2.1.0](https://github.com/jefersondaniel/pydantic-mongo/compare/v2.0.3...v2.1.0) (2024-01-05)


### Features

* Create an empty py.typed file to add mypy type hint support  ([#61](https://github.com/jefersondaniel/pydantic-mongo/issues/61)) ([10e58de](https://github.com/jefersondaniel/pydantic-mongo/commit/10e58de6ac52e45a56b88cff586151359c219b43))


### Bug Fixes

* Fix README code snippets ([#65](https://github.com/jefersondaniel/pydantic-mongo/issues/65)) ([dac1347](https://github.com/jefersondaniel/pydantic-mongo/commit/dac1347229d876b9a3de525f8566bbfc0c0c62bd))

## [2.0.3](https://github.com/jefersondaniel/pydantic-mongo/compare/v2.0.2...v2.0.3) (2023-11-23)


### Bug Fixes

* Fix `save_many()` when there are no models to insert ([#43](https://github.com/jefersondaniel/pydantic-mongo/issues/43)) ([6b0912d](https://github.com/jefersondaniel/pydantic-mongo/commit/6b0912de3a429c28991a8f2ae30b3147d0285d5b))

## [2.0.2](https://github.com/jefersondaniel/pydantic-mongo/compare/v2.0.1...v2.0.2) (2023-09-13)


### Bug Fixes

* Use markdown for documentation ([1358799](https://github.com/jefersondaniel/pydantic-mongo/commit/1358799567cbb0473d588477b8b85405ae068246))

## [2.0.1](https://github.com/jefersondaniel/pydantic-mongo/compare/v2.0.0...v2.0.1) (2023-09-13)


### Bug Fixes

* Syntax error in documentation ([e32ad9d](https://github.com/jefersondaniel/pydantic-mongo/commit/e32ad9d8552160132929110be3b0227ff16afc97))

## [2.0.0](https://github.com/jefersondaniel/pydantic-mongo/compare/v1.0.1...v2.0.0) (2023-09-13)


### ⚠ BREAKING CHANGES

* Saving entities will upsert if the id is present
* **deps:** Moving to Pydantic V2
* **deps:** Python 3.7 will no longer be supported since it reached EOL

### Features

* Enhance existing repo with improved meta data ([#8](https://github.com/jefersondaniel/pydantic-mongo/issues/8)) ([9c234d1](https://github.com/jefersondaniel/pydantic-mongo/commit/9c234d1fee8006bd846621840ed8d1851b2ac00d))
* Implement save_many method in repositories ([8824622](https://github.com/jefersondaniel/pydantic-mongo/commit/8824622407d043905e76fae8107e172f91a919a2))


### Bug Fixes

* Uses upsert in save method ([1a89b5b](https://github.com/jefersondaniel/pydantic-mongo/commit/1a89b5b0bf8f64069b783818254893751991634b))


### Miscellaneous Chores

* **deps:** Deprecate python 3.7 ([#14](https://github.com/jefersondaniel/pydantic-mongo/issues/14)) ([d01bb52](https://github.com/jefersondaniel/pydantic-mongo/commit/d01bb521d2fcafc508662ad5605e94010d402a35))
* **deps:** Pydantic V2  ([#12](https://github.com/jefersondaniel/pydantic-mongo/issues/12)) ([561c122](https://github.com/jefersondaniel/pydantic-mongo/commit/561c12277f1771bdaef52d4a1ef66ea9c6721326))

## [1.0.1](https://github.com/jefersondaniel/pydantic-mongo/compare/v1.0.0...v1.0.1) (2023-01-24)


### Bug Fixes

* Use correct typing for find_one_by_id ([57210d6](https://github.com/jefersondaniel/pydantic-mongo/commit/57210d6a415ad79aec7e7c277f449f819da9b7e9))

## 1.0.0 (2023-01-19)


### Features

* Automate deployment pipeline ([735b5ad](https://github.com/jefersondaniel/pydantic-mongo/commit/735b5ad343237d16260279d9bf18d72d77c71250))


### Miscellaneous Chores

* release 1.0.0 ([abbad36](https://github.com/jefersondaniel/pydantic-mongo/commit/abbad36ce9ba083bb4d6c05090a8b833d8bb4e07))
