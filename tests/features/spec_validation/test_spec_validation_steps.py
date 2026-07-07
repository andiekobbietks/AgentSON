"""
Step definitions: spec_validation family.

No `agentson validate` CLI command exists yet, so these steps validate
directly via jsonschema against spec/v1.json. When a `validate` command
is added, replace direct jsonschema calls with subprocess calls to it.
"""
import glob
import json

import jsonschema
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

scenarios("../spec_validation/10-spec-validation.feature")

ENTRY_TYPES = [
    "user-query", "context", "querying", "title",
    "thought", "action", "answer", "side-effect",
]


@pytest.fixture
def ctx():
    return {}


@given(parsers.parse('the schema "{path}" loads as valid JSON Schema Draft 2020-12'))
def load_schema_ok(repo_root, path):
    data = json.loads((repo_root / path).read_text())
    jsonschema.Draft202012Validator.check_schema(data)


@when(parsers.parse('I validate every file matching "{pattern}"'))
def validate_glob(repo_root, schema, ctx, pattern):
    files = sorted(glob.glob(str(repo_root / pattern)))
    ctx["files"] = files
    ctx["errors"] = {}
    validator = jsonschema.Draft202012Validator(schema)
    for f in files:
        data = json.loads(open(f).read())
        errs = list(validator.iter_errors(data))
        if errs:
            ctx["errors"][f] = errs


@then("all files validate with zero errors")
def assert_all_valid(ctx):
    assert ctx["files"], "no files matched — fixture glob is wrong, not a pass"
    assert not ctx["errors"], f"validation errors: {ctx['errors']}"


@when(parsers.parse('I validate "{path}"'))
def validate_one(repo_root, schema, ctx, path):
    data = json.loads((repo_root / path).read_text())
    validator = jsonschema.Draft202012Validator(schema)
    ctx["errors"] = list(validator.iter_errors(data))


@then("it validates with zero errors")
def assert_zero_errors(ctx):
    assert not ctx["errors"], f"validation errors: {ctx['errors']}"


@given('a session document with the "id" field removed')
def session_missing_id(ctx):
    doc = {
        "entries": [{"type": "user-query", "text": "hi"}],
    }
    ctx["doc"] = doc


@when("I validate it against the schema")
def validate_doc(schema, ctx):
    validator = jsonschema.Draft202012Validator(schema)
    ctx["errors"] = list(validator.iter_errors(ctx["doc"]))


@then(parsers.parse('validation fails mentioning "{term}"'))
def assert_fails_mentioning(ctx, term):
    assert ctx["errors"], "expected validation errors, got none"
    assert any(term in str(e) for e in ctx["errors"]), ctx["errors"]


@given(parsers.parse('a session containing an entry of type "{etype}"'))
def session_with_entry_type(ctx, etype):
    ctx["doc"] = {
        "id": "test-session",
        "entries": [{"type": etype, "text": "x"}],
    }


@then("validation fails on the entry type enum")
def assert_fails_enum(ctx):
    assert ctx["errors"], "expected an enum validation failure, got none"


@given("a session containing one entry of each type:")
def session_all_types(ctx):
    ctx["doc"] = {
        "id": "test-session-all-types",
        "entries": [{"type": t, "text": "x"} for t in ENTRY_TYPES],
    }


@given(parsers.parse('a session containing an entry of type "observation"'))
def session_with_observation(ctx):
    ctx["doc"] = {
        "id": "test-session-observation",
        "entries": [{"type": "observation", "text": "x"}],
    }


@then("the result matches the current ADR-014 decision")
def check_adr014(ctx):
    # ADR-014 is Proposed, not Accepted, as of this session. Today the enum
    # does not include "observation", so this SHOULD fail. If it starts
    # passing, ADR-014 was accepted and the enum was updated — update this
    # step's expectation deliberately, don't just let it flip silently.
    assert ctx["errors"], (
        "observation now validates — if ADR-014 was accepted, update this "
        "step's assertion deliberately rather than leaving it stale"
    )


@given('a session with an empty "entries" array')
def session_empty_entries(ctx):
    ctx["doc"] = {"id": "test-empty", "entries": []}


@then("the result matches the documented minimum-entries rule")
def check_min_entries_documented(ctx, schema):
    # Whether empty entries[] is legal depends on the schema's minItems (if any).
    # We assert behavior matches whatever the schema actually declares —
    # not a guessed expectation — so this step is a consistency check, not
    # a pass/fail on a specific outcome.
    entries_schema = schema.get("properties", {}).get("entries", {})
    min_items = entries_schema.get("minItems")
    if min_items and min_items > 0:
        assert ctx["errors"], "schema declares minItems but empty array passed"
    else:
        assert not ctx["errors"], "schema has no minItems but empty array failed"


@given(parsers.parse('a valid session with an extra top-level field "{field}"'))
def session_extra_field(ctx, field):
    ctx["doc"] = {
        "id": "test-extra-field",
        "entries": [{"type": "user-query", "text": "x"}],
        field: "unexpected",
    }


@then("the result matches the spec's additionalProperties policy")
def check_additional_properties_policy(ctx, schema):
    allows_extra = schema.get("additionalProperties", True) is not False
    if allows_extra:
        assert not ctx["errors"], ctx["errors"]
    else:
        assert ctx["errors"], "schema forbids additionalProperties but extra field passed"


@given(parsers.parse('a file "{fname}" containing "{content}"'))
def write_bad_file(tmp_path, ctx, fname, content):
    p = tmp_path / fname
    p.write_text(content)
    ctx["bad_file"] = p


@when("I validate it")
def validate_bad_file(schema, ctx):
    try:
        data = json.loads(ctx["bad_file"].read_text())
        validator = jsonschema.Draft202012Validator(schema)
        ctx["errors"] = list(validator.iter_errors(data))
        ctx["parse_error"] = None
    except json.JSONDecodeError as e:
        ctx["parse_error"] = e
        ctx["errors"] = None


@then("validation fails with a parse error, not a crash")
def assert_parse_error_not_crash(ctx):
    assert ctx["parse_error"] is not None, "expected a JSONDecodeError, got none"


@given(parsers.parse('a session with "parent_session_id" set to null'))
def session_parent_null(ctx):
    ctx["doc_a"] = {
        "id": "a", "parent_session_id": None,
        "entries": [{"type": "user-query", "text": "x"}],
    }


@given(parsers.parse('another with "parent_session_id" set to "{val}"'))
def session_parent_string(ctx, val):
    ctx["doc_b"] = {
        "id": "b", "parent_session_id": val,
        "entries": [{"type": "user-query", "text": "x"}],
    }


@when("I validate both")
def validate_both(schema, ctx):
    validator = jsonschema.Draft202012Validator(schema)
    ctx["errors_a"] = list(validator.iter_errors(ctx["doc_a"]))
    ctx["errors_b"] = list(validator.iter_errors(ctx["doc_b"]))


@then("both validate with zero errors")
def assert_both_valid(ctx):
    assert not ctx["errors_a"], ctx["errors_a"]
    assert not ctx["errors_b"], ctx["errors_b"]
