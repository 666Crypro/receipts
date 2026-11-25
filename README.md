# Receipts

**Call it now. Prove it later.** Receipts is a Gno.land realm for sealed predictions: publish a hash of your call today, reveal the exact words when the time comes, and let the chain prove when you said it.

Built for the Gnome Tavern hackathon. Live on the Gno.land testnet (Onyx, `onyx-1`).

| | |
|---|---|
| Live app (gnoweb) | https://onyx.testnets.gno.land/r/nym-receipts001/receipts |
| Realm path | `gno.land/r/nym-receipts001/receipts` |
| Offline sealer | https://666crypro.github.io/receipts/ |
| Demo video | [`docs/demo.mp4`](docs/demo.mp4) |

## Why

"I called it" is cheap to say after the fact. Posting a hash first fixes that, but plain hash commitments have a known hole: you can seal ten guesses and only ever reveal the one that landed.

Receipts closes that hole. Every call carries a **reveal deadline its author chose**. A call that is still sealed after its deadline is publicly marked **ducked** and counts against the author's track record. Revealing late is allowed, but it stays marked **late**. So an author's page shows not just the calls they got right, but whether they keep their word.

## How it works

1. **Write a call** and pick a random **salt** (8 to 64 characters).
2. **Commit off-chain:** `commitment = hex(sha256(salt + "|" + call))`. Use the [offline sealer](https://666crypro.github.io/receipts/) (WebCrypto, nothing leaves the page) or `printf '%s|%s' "$SALT" "$CALL" | sha256sum`.
3. **Seal** on-chain with a public topic and a reveal deadline in days. The realm records the block height and time.
4. **Reveal** the exact call and salt. The realm re-hashes them and only accepts an exact match.
5. **Verdicts.** Once a call is revealed, any other account can mark it **held** or **missed** (one verdict per account, changeable).

| Status | Meaning |
|---|---|
| sealed | hash public, call hidden, deadline not passed |
| revealed | opened on or before the deadline and verified |
| revealed late | opened after the deadline: verified, but not counted as kept word |
| ducked | deadline passed and still not revealed: counts against the author |

Track records rank authors by calls the crowd says **held**, then **kept word** (share of due calls revealed on time), then fewest **ducked**.

## Use it

### In the browser (gnoweb + Adena)

Open the [live app](https://onyx.testnets.gno.land/r/nym-receipts001/receipts). The home page has a **Seal a call** form, each call page (`:call/<id>`) has a **Reveal** form while sealed and a **Verdict** form once revealed, and every form submits through your wallet (or shows the matching `gnokey` command).

Pages: home, `:call/<id>`, `:u/<address>` (track record), `:board` (track records), `:how`.

### From the command line

[`scripts/receipts.sh`](scripts/receipts.sh) wraps `gnokey`. It generates the salt, keeps the call and salt in a private local receipt file, and sends the transaction:

```bash
export KEY=mykey            # a gnokey key funded from https://faucet.gno.land
scripts/receipts.sh seal "BTC close on Dec 31, 2026" "BTC closes 2026 above \$150k" 37
scripts/receipts.sh show                       # home page as markdown
scripts/receipts.sh reveal 3 ~/.receipts/receipt-1a2b3c4d.txt
scripts/receipts.sh verdict 3 held             # from another account
scripts/receipts.sh show board
```

### Raw gnokey

```bash
gnokey maketx call -pkgpath gno.land/r/nym-receipts001/receipts -func Seal \
  -args "BTC close on Dec 31, 2026" -args <commitment> -args 37 \
  -gas-fee 100000ugnot -gas-wanted 30000000 -broadcast -chainid onyx-1 \
  -remote https://rpc.onyx.testnets.gno.land:443 mykey
```

## Realm API

Transactions (crossing functions; the caller is `cur.Previous().Address()`):

| Function | What it does |
|---|---|
| `Seal(topic, commitment string, revealByDays int) int` | Publish a commitment. Topic up to 120 bytes, commitment 64 hex chars, deadline 1 to 3650 days. Returns the call ID. |
| `Reveal(id int, prediction, salt string)` | Author only. Checks `sha256(salt + "\|" + prediction)` against the sealed commitment. |
| `Verdict(id int, verdict string)` | `"held"` or `"missed"`. Revealed calls only, not by the author, one per account (re-calling changes it). |

Read helpers for clients (`vm/qeval`): `Commit(prediction, salt)`, `GetCall(id)`, `StatusOf(id)`, `TrackRecord(addr)`, `Leaderboard(n)`, `Count()`.

Events: `Sealed`, `Revealed`, `Verdict`.

```bash
gnokey query vm/qeval -remote https://rpc.onyx.testnets.gno.land:443 \
  -data 'gno.land/r/nym-receipts001/receipts.StatusOf(1)'
```

## Design notes

- **State:** calls live in an `avl.Tree` keyed by `seqid` (ordered, paginated rendering); each author has an index of their call IDs. Verdicts are an `avl.Tree` per call, so a vote can be changed without double counting.
- **Time:** deadlines use block time (`time.Now()` in Gno is the block timestamp), so "ducked" flips on its own with no keeper transaction.
- **Rendering:** routes go through `p/nt/mux`. Every user-supplied string (topic, call, salt) passes through `p/nt/markdown/sanitize/v0` before it reaches markdown, and `$` is escaped so user text cannot render as math. Forms use `<gno-form exec>` so the whole lifecycle works from gnoweb.
- **No coins:** the realm never holds or moves funds. Nothing to drain.
- **Privacy:** the call never touches the chain before reveal. `Commit()` exists as a read helper for clients, but querying it sends the text to an RPC node, so the sealer page and CLI hash locally instead.
- **Limits, honestly:** verdicts are one-account-one-vote and therefore sybil-able; they are social signal, not an oracle. Short calls with weak salts could be brute-forced, which is why reveal requires an 8+ byte salt and the tools generate 16 random characters.

## Testnet evidence

TESTNET_EVIDENCE

## Develop

Requires the Gno toolchain matching Onyx (`v1.8.0-rc.1`).

```bash
cd realm/receipts
gno test -v .        # unit tests: lifecycle, validation, ducked/late, rendering
gno lint .
gnodev local .       # local node + gnoweb at http://127.0.0.1:8888
```

## Repository layout

```
realm/receipts/        the realm: receipts.gno (logic), render.gno (gnoweb pages), receipts_test.gno
docs/index.html        offline sealer and receipt checker (GitHub Pages)
docs/demo.mp4          demo video
scripts/receipts.sh    CLI wrapper around gnokey
```

## Credits and license

Uses Gno.land packages `p/nt/avl`, `p/nt/seqid`, `p/nt/mux`, `p/nt/markdown/sanitize` (and `p/nt/uassert`, `p/nt/testutils` in tests). Built with the Gno docs and the gnomcp skill references. MIT licensed.
