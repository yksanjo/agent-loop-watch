# agent-loop-watch

Spot repeated tool-call/result cycles at the end of an agent trace, without running the agent.

Python 3.10+, standard library, MIT. Offline review signal, not a kill switch or proof of a stuck agent.

## Try

```sh
python3 -m unittest -v
python3 demo.py
python3 loop_watch.py trace.json
```

The demo uses synthetic in-memory records. CLI exits 0 for no signal, 1 for a repeated suffix, 2 for invalid input. Output is JSON. Argument-parser errors also use exit 2 but print usage text to stderr.

A trace is a JSON array:

```json
[
  {"tool":"fixture_read","arguments":{"id":1},"result":{"status":"waiting"}},
  {"tool":"fixture_read","arguments":{"id":1},"result":{"status":"waiting"}},
  {"tool":"fixture_read","arguments":{"id":1},"result":{"status":"waiting"}}
]
```

Default: look for a suffix with period 1 through 8 records repeated at least 3 times. `--repeats` accepts 2..20, `--max-period` accepts 1..32. Reports the smallest matching period, its contiguous repetition count, zero-based start/end positions and SHA-256 fingerprints. It checks the full provided trace, up to 1,000 records.

Tool name, arguments and result all participate. Object-key order is ignored; array order and numeric representation are not. Records must contain exactly those three fields. Unknown fields fail rather than being silently ignored. Capture timestamps separately, not in results, if you want identical observations to match.

## Integration boundary

A trusted controller captures complete tool calls and results, then invokes this comparator. The controller decides whether a repeated suffix needs a person, a pause or no action. This program does not execute, stop, retry or authorize anything. It never connects to a server, updates a baseline or calls a model.

## Tests

15 tests cover simple/alternating cycles, thresholds, prefixes, changed arguments/results, key order, invalid records/settings, period limits and CLI exits. CLI regression cases include oversized files, invalid UTF-8, duplicate keys and parser-depth failure.

## Honest limits

- Identical polling can be healthy. This is exact repetition, not semantic progress detection. A changed timestamp can hide a real loop; identical output can still represent useful work.
- Only repeated suffixes within the configured period/threshold are detected. Earlier loops, longer cycles and incomplete traces can be missed.
- Hashes are fingerprints, not provenance. A compromised trace producer can hide or invent repetition. Raw trace data is not included in reports, but fingerprints and positions remain metadata.
- CLI accepts at most 1 MiB, 1,000 records and nesting depth 64. Limits are conservative, not general denial-of-service protection. Direct Python calls are trusted-input only.
- No live-agent reliability or cost-savings claim. No tool execution in tests or demo. Keep real traces private; they can contain secrets and personal data.
