# Database searches

Preview the working document's final searches (no API calls):

```bash
uv run --no-project --with-requirements requirements.txt python search_databases.py
```

Add `--execute` to run; optionally select `--database "PubMed"` (repeatable).
Writes raw JSON/XML and `summary.csv` under `output/yyyymmdd_hhss/`.
Dates match the documented search filter, **2021–2027**; reruns can differ from the October 8 results.
These results require screening and cross-database deduplication before CSV conversion.

Credentials are Python string settings in `config.py`, next to the runner. For a fresh checkout:

```bash
cp config.py.template config.py
```

Edit an existing `config.py` directly. It is ignored by Git; the template is tracked and must contain only empty placeholders. Fill in settings for the databases you select; leave unused settings empty. Environment variables and `.env` files are not used for credentials. Query previews work without `config.py`.

For PubMed, fill in `NCBI_EMAIL` in `config.py`, then run:

```bash
uv run --no-project --with-requirements requirements.txt python search_databases.py --database "PubMed" --execute
```

| Database | Required config settings / access |
| --- | --- |
| Scopus | `SCOPUS_API_KEY`; optional `SCOPUS_INST_TOKEN`; institutional entitlement |
| Web of Science | `WOS_API_KEY` for **Expanded API**, including Core Collection |
| APA PsycInfo / ERIC | `EBSCO_AUTH_TOKEN`, `EBSCO_SESSION_TOKEN`; exact profile facet labels in `EBSCO_PSYCINFO_PROVIDER` / `EBSCO_ERIC_PROVIDER` |
| PubMed | `NCBI_EMAIL`; optional `NCBI_API_KEY` |
| IEEE Xplore | `IEEE_API_KEY` |
| ACM DL | Manual export; search API access has not been verified |

EBSCO needs institution-issued EDS tokens and a profile supporting `TI`, `AB`, `KW`, `LA`, and the `DT1` date limiter. Verify these with the API's Info endpoint before a live search. Renew expired tokens through your institution's EDS authentication flow.
Store refreshed tokens in `config.py`; the runner does not renew them automatically. See the [README](../README.md#api-credentials) for signup links and token setup.
IEEE API queries are split further to satisfy its two-wildcard limit; English eligibility requires screening. ACM queries are included in the preview and saved plan for manual use.
No live searches have been tested.

Offline checks:

```bash
uv run --no-project --with-requirements requirements.txt python -m unittest test_search_databases -v
```

API references: [Scopus](https://dev.elsevier.com/documentation/SCOPUSSearchAPI.wadl), [Web of Science Expanded](https://developer.clarivate.com/apis/wos), [EBSCO search](https://developer.ebsco.com/eds-api/docs/performing-a-search), [EBSCO dates](https://developer.ebsco.com/eds-api/docs/using-min-and-max-date-range-to-filter-results), [PubMed](https://www.ncbi.nlm.nih.gov/books/NBK25499/), [IEEE](https://developer.ieee.org/docs/read/Metadata_API_details).
