Feature: Spec v1 schema validation
  Every .agentson file must validate against spec/v1.json (Draft 2020-12).
  NOTE: no CLI `validate` command exists yet; steps validate via jsonschema
  directly until one is added.

  Background:
    Given the schema "spec/v1.json" loads as valid JSON Schema Draft 2020-12

  Scenario: Every shipped example validates
    When I validate every file matching "examples/*.agentson"
    Then all files validate with zero errors

  Scenario: Dogfood session validates
    When I validate "examples/dogfood-session-2026-07-06.agentson"
    Then it validates with zero errors

  Scenario: Missing required session id is rejected
    Given a session document with the "id" field removed
    When I validate it against the schema
    Then validation fails mentioning "id"

  Scenario: Unknown entry type is rejected
    Given a session containing an entry of type "banana"
    When I validate it against the schema
    Then validation fails on the entry type enum

  Scenario: Known entry types are accepted
    Given a session containing one entry of each type:
      | user-query | context | querying | title | thought | action | answer | side-effect |
    When I validate it against the schema
    Then it validates with zero errors

  Scenario: Observation entry type status is pinned (ADR-014)
    Given a session whose only entry is the pinned "observation" type
    When I validate it against the schema
    Then the result matches the current ADR-014 decision
    # Today this FAILS (observation not in enum) while readers emit it.
    # This scenario exists to force the mismatch to stay visible until decided.

  Scenario: Empty entries array is handled per spec
    Given a session with an empty "entries" array
    When I validate it against the schema
    Then the result matches the documented minimum-entries rule

  Scenario: Additional unknown top-level properties
    Given a valid session with an extra top-level field "vendor_extra"
    When I validate it against the schema
    Then the result matches the spec's additionalProperties policy

  Scenario: Non-JSON file is rejected cleanly
    Given a file "not-json.agentson" containing "hello world"
    When I validate it
    Then validation fails with a parse error, not a crash

  Scenario: Provenance fields accept null and string
    Given a session with "parent_session_id" set to null
    And another with "parent_session_id" set to "abc-123"
    When I validate both
    Then both validate with zero errors
