# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-03-09

### Added
- **1-to-1 JavaScript SDK Parity**: `ReclaimProofRequest` now directly mirrors the capabilities and documentation of `@reclaimprotocol/js-sdk`.
- Complete set of callback URL endpoints parameters including `cancelCallbackUrl` and `cancelRedirectUrl`.
- Modal customization parameters via `set_modal_options` and `close_modal`.
- Claim creation type overrides via `set_claim_creation_type`.
- `set_json_context` alongside legacy `add_context`.
- Lifecycle methods `start_session`, `get_session_id`, `get_cancel_callback_url`, `get_json_proof_response`.
- Explicit `method` and `body` payload parameters added to `set_redirect_url` and `set_cancel_redirect_url`.
- Expanded JSON serialization compatibility preserving parity across TypeScript/Python JSON payloads using `to_json_string` and `from_json_string`.
- Implemented robust global signature validation checking the global test attestors pool automatically by fetching from the backend API.
- Fully mirrored JS documentation strings for all SDK functions enabling identical developer experience and rich IDE typing hinting.

### Changed
- Refactored `verify_proof` to rely on global dynamic attestors validation instead of solely local signature matching.
- **Breaking**: `Context` object schema unified with JS SDK handling (defaults to `"sample context"`).
- **Breaking**: Default export serialization variables matching structural expectations of the JavaScript backend payload processors.

### Deprecated
- `add_context(address, message)` has been deprecated in favor of `set_context(address, message)` which behaves equivalently. It will be removed in a future version.
- `set_callback_url(url)` has been marked as deprecated in favor of `set_app_callback_url`.

### Fixed
- Fixed URL constructor formatting omissions resulting in mismatched request template structures matching the iOS/Android apps constraints.
