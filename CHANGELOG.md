# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog] and this project adheres to
[Semantic Versioning].

Types of changes are:
* **Security** in case of vulnerabilities.
* **Deprecated** for soon-to-be removed features.
* **Added** for new features.
* **Changed** for changes in existing functionality.
* **Removed** for now removed features.
* **Fixed** for any bug fixes.

## [Unreleased]
### Added
* Added support for Amazon OpenSearch Service using AWS Signature v4 auth

### Changed
* Dropped dependency on `elasticsearch-py` to allow easy interoperability with OpenSearch

## [0.1.0] - 2022-04-02
### Added
* Project started :)
* Implemented support for (most) KQL queries

[Unreleased]: https://github.com/jacksmith15/elastic-log-cli/compare/0.1.0..HEAD
[0.1.0]: https://github.com/jacksmith15/elastic-log-cli/compare/initial..0.1.0

[Keep a Changelog]: http://keepachangelog.com/en/1.0.0/
[Semantic Versioning]: http://semver.org/spec/v2.0.0.html

[_release_link_format]: https://github.com/jacksmith15/elastic-log-cli/compare/{previous_tag}..{tag}
[_breaking_change_token]: BREAKING
