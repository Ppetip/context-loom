# Context Loom

**Make context selection explainable before you spend an LLM call.**

A dependency-free context packer for RAG and agent builders. Supply candidate source variants, measured costs and priority values. Context Loom keeps mandatory material, chooses at most one variant per source and finds the maximum total priority under the supplied budget. A first-fit baseline shows what a naive selection would have included.

## Try it

Python 3.11+; no installation or API key required.

```sh
python app.py --input examples/demo.json
python -m unittest discover -s tests -v
python verify_demos.py
```

The authored synthetic demo has a 10-unit budget. Optimized selection retains the policy, brief history and ticket (value 13); first-fit retains the policy and long history (value 6). These numbers are arbitrary fixture priorities, not observed model accuracy or token savings.

## Input contract

`budget` is an integer from 0 to 10,000. `chunks` is an array of at most 100 objects. Each requires nonempty `id`, `source`, `text`, integer `units` from 1 to 10,000 and integer `value` from 0 to 1,000,000. Optional `required` is a boolean. IDs must be unique. Chunks sharing a source are mutually exclusive alternatives, such as a full document versus its summary. Assign different source IDs when both passages may be included.

All required chunks must fit and must have distinct sources; otherwise the complete request is rejected. The multiple-choice knapsack algorithm selects optional variants. Ties prefer lower cost, then sorted chunk IDs. Optimized selection is independent of input order; the first-fit baseline deliberately follows input order after required chunks.

## Output and boundaries

The JSON report contains selected blocks with original text, source IDs and content hashes, used units, total priority, omitted IDs and the baseline. It does not concatenate or send a prompt. Hashes detect text changes; they do not certify provenance or truth. Reports can contain private input text: keep them local and use only authorized files.

Units are supplied by you. Use a model-specific tokenizer externally and reserve room for instructions, framing and output; this tool does not measure actual provider tokens or enforce a provider limit. Priority is not calibrated relevance. Source labels and separation are not a prompt-injection defense.

The CLI reads one explicitly named UTF-8 JSON file, capped at 1 MiB. Duplicate JSON keys, nonfinite values, unsupported fields and malformed records fail with exit 2 and no report. Valid reports exit 0. There is no network access, model inference, persistence or tool execution.

## Evidence and next steps

9 local tests and 3 CLI contracts pass. Tests include 80 small generated problems checked against an independent exhaustive subset search, mandatory-source constraints, deterministic ties, strict JSON and input preservation. These are correctness tests, not a retrieval benchmark. All four Windows/Linux Python 3.11/3.13 jobs passed on GitHub Actions. [Hosted verification](https://github.com/Ppetip/context-loom/actions/runs/36965526002).

Next: an explicit tokenizer adapter, independently labeled retrieval cases and a quality comparison using held-out tasks. No paid provider integration is enabled.

Original code: GPL-3.0-only. See [LICENSE](LICENSE).
