# Usage and setup

Run with [uv](https://docs.astral.sh/uv/):

## Manual searches without API keys

Use the [manual search links and copyable queries](manual_search_links.md). PubMed links contain the query; IEEE links use a browser URL pattern that still needs validation. Scopus, Web of Science, EBSCO, and ACM have launch links with queries to paste and instructions for manual filters.

Regenerate the document without making database requests:

```bash
uv run --no-project --with-requirements requirements.txt python manual_search_links.py
```

Supply your library's access links with `--psycinfo-url 'https://…'` and `--eric-url 'https://…'` if the generic EBSCO launch page does not route to your institution. The generator does not open a browser or execute searches.

## API credentials

Start with PubMed: this runner only requires your email address for that database. The other automated databases need API credentials or institutional access. The runner has passed offline tests; live provider access and query compatibility remain unverified.

Credentials live in **`config.py`**, next to `search_databases.py`. On a fresh checkout, create it from the tracked template:

```bash
cp config.py.template config.py
```

If `config.py` already exists, edit it directly. Fill in only the settings for the databases you intend to run; leave unused settings and optional keys empty. `config.py` is ignored by Git; keep `config.py.template` free of real credentials. The runner imports this file and does not read credential environment variables or `.env` files. Query previews work without a config file.

| Database | How to obtain access | Runner configuration |
| --- | --- | --- |
| PubMed | No key required at the runner's request rate. For an optional key, sign in to My NCBI, open **Account settings → API Key Management → Create an API key**. [NLM instructions](https://support.nlm.nih.gov/knowledgebase/article/KA-05317/) | Set `NCBI_EMAIL`; optionally `NCBI_API_KEY`. |
| Scopus | Sign in to the [Elsevier Developer Portal](https://dev.elsevier.com/) and choose **I want an API Key**. A key alone does not grant data access: ask your university library to confirm Scopus API entitlement and whether campus network/VPN access or an institutional token is needed. | Set `SCOPUS_API_KEY`; optionally `SCOPUS_INST_TOKEN`. |
| Web of Science | Register an application in the [Clarivate Developer Portal](https://developer.clarivate.com/apis/wos) and request **Web of Science API Expanded**, with Core Collection access. Expanded requires a paid institutional license; ask your library whether it is available. The runner uses Expanded, not Starter. | Set `WOS_API_KEY`. |
| APA PsycInfo | Ask your library's EBSCO administrator for EDS API access to a profile that includes APA PsycInfo. This adapter uses authentication/session tokens rather than a permanent API key. See the EBSCO steps below. | Set `EBSCO_AUTH_TOKEN`, `EBSCO_SESSION_TOKEN`, and `EBSCO_PSYCINFO_PROVIDER`. |
| ERIC | Ask the EBSCO administrator for an EDS profile that includes ERIC. The current runner uses EBSCO to follow the working document; it does not implement ERIC's separate public API. | Set `EBSCO_AUTH_TOKEN`, `EBSCO_SESSION_TOKEN`, and `EBSCO_ERIC_PROVIDER`. |
| IEEE Xplore | [Register an IEEE developer account](https://developer.ieee.org/getting_started), confirm your email, and describe the application to request a metadata API key. IEEE reviews requests before issuing keys. | Set `IEEE_API_KEY`. |
| ACM DL | The runner has no verified ACM search API adapter. Use its three generated queries in the ACM interface, select the Full-Text Collection, metadata search, 2021–2027, and English, then export manually. | No credential is used; the runner reports `manual_required`. |

### EBSCO token setup

Follow EBSCO's [first-request workflow](https://developer.ebsco.com/eds-api/docs/making-your-first-request) using credentials and a profile supplied by your institution:

1. Call `POST /authservice/rest/UIDAuth` with the institution-issued `UserId`, `Password`, and `InterfaceId`. Save the returned `AuthToken` as `EBSCO_AUTH_TOKEN` in `config.py`.
2. Call `POST /edsapi/rest/CreateSession` for your institution's profile, with `x-authenticationToken` in the header. Save the returned `SessionToken` as `EBSCO_SESSION_TOKEN` in `config.py`.
3. Call `GET /edsapi/rest/info` with both token headers. Confirm the profile supports the runner's `TI`, `AB`, `KW`, and `LA` fields and `DT1` date limiter. These are profile-specific; the runner may need adjustment if they differ.
4. Use the exact `ContentProvider` facet values returned by a search for `EBSCO_PSYCINFO_PROVIDER` and `EBSCO_ERIC_PROVIDER`. Do not assume the profile's display labels match these values.

The runner consumes existing tokens; it does not create sessions or refresh expired tokens. Generate fresh tokens through the same workflow when needed. EBSCO's [search documentation](https://developer.ebsco.com/eds-api/docs/performing-a-search) describes the token headers and returned facets.

## Run the database extraction

Run commands from the repository root. Preview PubMed's query first; this makes no database requests:

```bash
uv run --no-project --with-requirements requirements.txt python search_databases.py --database "PubMed"
```

When ready to make live requests, set your email in `config.py`:

```python
NCBI_EMAIL = "your-email@example.edu"
NCBI_API_KEY = ""  # Optional.
```

Then add `--execute`:

```bash
uv run --no-project --with-requirements requirements.txt python search_databases.py --database "PubMed" --execute
```

For another database, fill in its settings from the table in `config.py` and select its name. For example, after setting `SCOPUS_API_KEY`:

```bash
uv run --no-project --with-requirements requirements.txt python search_databases.py --database "Scopus" --execute
```

Missing required settings are reported in `summary.csv` with the setting name and instructions to fill in `config.py`.

Repeat `--database` to select multiple databases. Omitting it selects all seven, including ACM's manual-export entry. IEEE currently uses 76 query partitions to respect its API wildcard limit; check your quota before selecting it.

Each live run creates `output/yyyymmdd_hhss/` containing:

- `queries.json`: the queries and database notes.
- A folder per database with raw `response_*.json` files and, on success, `records.json`.
- PubMed `response_*.xml` files with article metadata; its `records.json` contains PMIDs.
- `summary.csv`: database statuses, record counts, errors, and notes.

Check `summary.csv` after a run. `complete` means retrieval finished, `failed` means the database needs attention, and `manual_required` means ACM still needs manual export. Failed runs can leave raw responses but no complete `records.json`.

An HTTP 401/403 can indicate invalid credentials or missing entitlement; 429 indicates throttling or quota limits. EBSCO field/token errors need profile checks or refreshed tokens. The runner reports provider failures rather than silently treating them as zero results.

The extraction saves raw metadata. It does **not** convert those files into `input.csv` or the example CSV format, screen eligibility, or deduplicate across databases. Those steps remain separate. See the [database search documentation](database_search.md) for scope and the [CSV conversion documentation](csv_conversion.md) for the existing-input conversion workflow.
