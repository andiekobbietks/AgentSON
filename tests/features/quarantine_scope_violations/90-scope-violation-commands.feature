Feature: finetune, push, pull (QUARANTINED — ADR-013)
  These commands violate the core litmus test ("using AgentSON, not
  defining it"). Scenarios pin CURRENT behavior only so that moving them
  to downstream packages is provably behavior-preserving. Delete this file
  when ADR-013 is resolved.

  Scenario: finetune produces unsloth output from a real session
    When I run "agentson finetune examples/dogfood-session-2026-07-06.agentson --format unsloth --output /tmp/ft"
    Then the command exits 0 and an output file exists

  Scenario: finetune --no-thoughts excludes thought entries
    Given a session containing thought entries
    When I run finetune with "--no-thoughts"
    Then the training output contains no thought-derived records

  Scenario: push without Supabase credentials fails cleanly
    Given no Supabase credentials in the environment
    When I run "agentson push examples/mcp_demo.agentson"
    Then the command exits nonzero without a traceback and without hanging

  Scenario: pull without credentials fails cleanly
    Given no Supabase credentials in the environment
    When I run "agentson pull --limit 1"
    Then the command exits nonzero without a traceback and without hanging
