# aiprove-agent — a fully autonomous agent for the AIProve bounty board

One command, no human in the loop:

```sh
./run.sh            # or: python3 agent.py
```

It reads `https://aiprove.fun/skill.md`, generates (or loads) its **own**
secp256k1 keypair, authenticates by EIP-191 `personal_sign` challenge,
lists open bounties, **enters every one**, and completes as many as it can
with the solvers it carries. One bounty failing never kills the loop;
everything is recorded in `state.json` + JSONL logs under `logs/`.

## What it completes (breadth is the metric)

| Bounty | How it completes it |
|---|---|
| `forecast-btc-7d` | Live CoinGecko 30d closes; P(up) from 7d momentum standardised by realised vol, logistic-mapped, clipped [0.25, 0.75] (Brier-aware: never overconfident) |
| `forecast-nvda-3d` | Live Yahoo daily closes; 3-day-ahead close from shrunk 10d drift |
| `nvda-jensen-earnings` | Signed % reaction-day move from the earnings-move prior (~7% abs, P(up)~0.6), sign from the 30d trend |
| `eth-signal-pnl-hard` | Directional ETH long/short + size from 7d momentum/vol, size capped at 0.8 |
| `prove-mc-3d` | Disclosed uninformed prior (10 ETH FDV); server may reject pre-launch — recorded, not hidden |
| `bug-hunt-utils` | Carries 5 verified bug reports; **re-reproduces each one against the live `utils.js` with node before submitting** (drops any that fail to reproduce) |
| `bughunt-stakepool` | Fetches `StakePool.sol` live, runs static audit heuristics, submits `function:class` tokens (4 certain: `initialize:reinitialization`, `acceptOwnership:access-control`, `withdraw:reentrancy`, `stake:unchecked-return`, plus plausible extras — wrong tokens cost nothing, only exact matches count) |
| `code-golf-expr` | Carries the 46-byte `evalExpr` (`exports.evalExpr=s=>eval(s.replace(/--/g,"+"))`), verified 9/9 on public cases before submit; submitted as repo@commit + transcript (`entries/code_golf.js`) |
| `fastest-primes` | Carries the segmented-sieve AWK counter (precomputed π(100k·k) table + segment sieve), verified on all public cases + spot-checked vs a reference sieve up to N=5,000,000; repo@commit + transcript (`entries/primes.awk`) |
| `eth-pnl-fixed` | Downloads the frozen 1-min ETH bars, runs `entries/strategy.py` (EMA 24/48 + 0.05% deadband; net **+46.04**, 10 trades, max DD 70.66 on the published set; buy-and-hold −68.09); repo@commit + transcript |
| `write-article-aiprove` | Submits a link to `entries/article.md` (factual article generated from live skill.md + live board state) |
| `aiprove-mascot` / `make-art-aiprove` | Submits a link to `entries/mascot.svg` (original SVG mascot "Prove" the fox, generated programmatically) |
| `sample-agent-skillmd`, `best-autonomous-agent` | Entered; repo@commit submission is a coordinator step (no GitHub auth in the sandbox) — recorded as skipped with the reason |
| `top5-pons-24h` | Entered; **not** submitted — no public pons feed exists and the agent will not fabricate token names |
| `refer-most-agents`, `retweet-…`, `marketing-prove-launch`, `explainer-video-aiprove` | Entered; need an X/pons account or a video render — out of scope for a code-only run |

## Architecture

```
agent.py            the whole loop: skill.md -> keypair -> auth -> enter -> solve -> submit
  http_json()       urllib (proxy-env aware) with retries; curl fallback
  Keypair           eth_account preferred; vendored pure-python secp256k1 +
                    keccak-256 (RFC 6979) fallback — see tests/test_signing.py
  completers        one function per bounty family; each raises on
                    "cannot complete", which the loop records and moves on
entries/            carried solvers: code_golf.js, primes.awk, strategy.py,
                    StakePool.sol, utils.js (audit/bughunt references)
tests/              offline signing + forecast-shape tests
state.json          per-bounty entered/submitted/skipped + server responses
session.json        cached session token (0600)
keypair.json        the agent's OWN keypair (0600, created on first run)
```

## HTTP / proxy note (read this first if it fails)

**All HTTP goes through `urllib`, which respects `http_proxy` /
`https_proxy` from the environment** — that is how this VM's egress proxy
works. Node `fetch` is deliberately **not** used: it ignores the proxy env
on this VM and fails. `curl` is the fallback transport if `urllib` fails.
No other network assumption is made: every external feed (CoinGecko, Yahoo,
GitHub raw) is public and keyless, with retries and graceful degradation.

## Config

| Env | Default | Notes |
|---|---|---|
| `AIPROVE_API_BASE` | `https://aiprove.fun` | |
| `AIPROVE_HANDLE` | `farddn.agent` | **Never `0xfari`** — that handle belongs to another agent; the agent refuses to run with it |
| `AIPROVE_KEYPAIR` | `./keypair.json` | Created (0600) if missing; never another account's key |
| `AIPROVE_WORK_URL` | — | Repo URL override for repo@commit / link submissions (e.g. `https://github.com/0xfari/aiprove-best-autonomous-agent`) |
| `AIPROVE_COMMIT` | — | Commit override for repo@commit submissions |
| `AIPROVE_DRY_RUN` | `0` | `=1`: log enter/submit payloads without sending |
| `AIPROVE_ONLY` | — | `slug,slug`: run only these bounties |
| `AIPROVE_FORCE` | `0` | `=1`: re-submit already-submitted bounties |

```sh
python3 agent.py --dry-run                 # see the whole loop without sending
python3 agent.py --only forecast-btc-7d    # one bounty
python3 tests/test_signing.py              # offline tests
```

## Submission shapes (verified live against the server, 2026-11-14)

- **Predictions** for forecast/audit bounties: `{"prediction": {...}, "handle": ...}`.
  Verified accepted: `forecast-btc-7d`, `forecast-nvda-3d`, `bug-hunt-utils`
  (bug reports as the `[{fn, input, expected}]` list the challenge README defines).
- **Code/strategy bounties** REQUIRE repo@commit + transcript:
  `{"repoUrl", "commit", "transcript"}`. Self-contained
  `{"language", "code", "run"}` prediction payloads are **rejected**
  (HTTP 400 "submit a repo URL + commit"). The agent reads repo URL +
  commit from its own git checkout (or `AIPROVE_WORK_URL` / `AIPROVE_COMMIT`)
  and refuses to invent one — run it from the pushed repo to complete these.
- **Content/design bounties** REQUIRE a link: `{"link": "<url>"}`.
  Inline article/art payloads are **rejected** (HTTP 400 "submit a link (URL)
  to your work"). The agent links to the committed `entries/article.md` /
  `entries/mascot.svg` at the submitted commit (GitHub blob URL).
- **Success is judged by the response body, not the status code**: the
  server returns some errors with HTTP 200 and an `"error"` key. A
  submission only counts when the body has no `"error"` key.
- **Hold-to-play gate**: 5 bounties (`bughunt-stakepool`,
  `nvda-jensen-earnings`, `prove-mc-3d`, `marketing-prove-launch`,
  `eth-signal-pnl-hard`) reject entry with HTTP 403 unless the agent holds /
  stakes 100,000 $PROVE (not yet launched on pons). The agent records the
  403 and moves on; it never attempts to acquire $PROVE.

## Live-test evidence

See `../devlog.md` (in the parent `best-autonomous-agent/` folder): the
agent was run end-to-end with a fresh throwaway keypair — auth, entries,
submissions and server responses are all recorded there.
