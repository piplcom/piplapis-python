# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [Released]
## 5.2.0v - 2019-08-18
### Fixed
- allow for search by US address - can pass a house number in street (API-1202)
- send 'url' in a parameter based search (API-1369)
- allow to send a valid query that has a mix of bad and good data (API-1293)
- allow searching by street (API-1394)

### Added
- Package key HTTP headers to be exposed in Code Libraries - added to Python only and should be add to all code libraries (java, ruby, python, c#, php) (API-1341)
- Option to use top_match in API request
- Option to use zip_code in API request
- Option to use response_class instead of the generic SearchAPIResponse

### Changed
- Allow HTTPS only

### Removed
