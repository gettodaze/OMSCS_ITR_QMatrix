# Database searches

For a workflow without API credentials, use the [manual search links and queries](manual_search_links.md). Generate them with `manual_search_links.py`; each entry states whether the link embeds the query or requires pasting it, and which filters remain manual.

## API searches

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

## How to obtain every config value

Put the values below into your local `config.py`. Start with PubMed, which needs only a contact email; request institutional access for the other providers in parallel.

### PubMed: `NCBI_EMAIL` and optional `NCBI_API_KEY`

1. Set `NCBI_EMAIL` to your own contact email address. This is a runner requirement, not a credential issued by NCBI.
2. Leave `NCBI_API_KEY = ""` to use the runner without a key.
3. For an optional key, sign in to [My NCBI](https://www.ncbi.nlm.nih.gov/account/), open **Account settings**, find **API Key Management**, and select **Create an API key**.
4. Copy that key into `NCBI_API_KEY`.

NCBI documents this process in its [API key instructions](https://support.nlm.nih.gov/knowledgebase/article/KA-05317/). The runner paces requests and does not require the higher request rate a key allows.

```python
NCBI_EMAIL = "your-email@example.edu"
NCBI_API_KEY = ""  # Optional.
```

### Scopus: `SCOPUS_API_KEY` and optional `SCOPUS_INST_TOKEN`

1. Sign in to the [Elsevier Developer Portal](https://dev.elsevier.com/) and select **I want an API Key**.
2. Register your application, describing this literature-search project, and copy the issued key into `SCOPUS_API_KEY`.
3. Ask your university library to confirm your institution's Scopus API entitlement and the supported network access method. Possessing a key alone does not grant access to Scopus data. [Elsevier access requirements](https://dev.elsevier.com/)
4. Leave `SCOPUS_INST_TOKEN = ""` if your approved access works through institutional IP authentication. If you need an institutional token, ask your library to coordinate with Elsevier's Research Product APIs Support Center; it is issued by Elsevier, not generated from your API key. Copy an approved token into `SCOPUS_INST_TOKEN`. [Institutional token instructions](https://dev.elsevier.com/tecdoc_api_authentication.html)

Ask the library: “Does our institution permit Scopus Search API access for this research project, and should I use an institutional IP address or request an institutional token?”

### Web of Science: `WOS_API_KEY`

1. Ask your library whether the institution licenses **Web of Science API Expanded** with Core Collection access. An ordinary browser subscription or a Starter API key does not establish access to the endpoint this runner uses.
2. Create an account in the [Clarivate Developer Portal](https://developer.clarivate.com/apis/wos), register an application, and request access to **Web of Science API Expanded**.
3. Follow the portal's subscription instructions: select the Standard plan, then have the access configured according to your institution's contract.
4. Once approved, copy the application's Expanded API key into `WOS_API_KEY`.

Expanded requires a paid license, and access/quotas depend on the institutional contract. [Clarivate subscription and access instructions](https://developer.clarivate.com/apis/wos)

### APA PsycInfo and ERIC: EBSCO tokens and provider labels

These settings come from an institution's **EBSCO Discovery Service (EDS) API** profile. Request API credentials, the interface ID, and a profile identifier from your library's EBSCO administrator. Ask for a profile with both databases enabled, plus the search fields and date limiter used by this runner.

Use the interactive API documentation in EBSCO's [first-request guide](https://developer.ebsco.com/eds-api/docs/making-your-first-request):

1. Call **UIDAuth** (`POST /authservice/rest/UIDAuth`) with the supplied `UserId`, `Password`, and `InterfaceId`. Copy the returned `AuthToken` into `EBSCO_AUTH_TOKEN`.
2. Call **CreateSession** (`POST /edsapi/rest/CreateSession`) with the profile identifier and the `x-authenticationToken` header. Copy the returned `SessionToken` into `EBSCO_SESSION_TOKEN`.
3. Call **Info** (`GET /edsapi/rest/info`) with both token headers. Check support for `TI`, `AB`, `KW`, `LA`, and `DT1`; profile differences may require runner changes.
4. Run a sample search with facets enabled. In the returned `ContentProvider` facet, copy the exact PsycInfo and ERIC values into `EBSCO_PSYCINFO_PROVIDER` and `EBSCO_ERIC_PROVIDER`. These are labels, not API keys or database IDs. If absent, ask the administrator to verify coverage. [EBSCO facets and search documentation](https://developer.ebsco.com/eds-api/docs/performing-a-search)

The runner uses the same token pair for both databases. If your institution requires separate profiles, configure and run each database separately with its matching session. Tokens expire; repeat authentication/session creation and update `config.py`. The runner does not refresh them.

### IEEE Xplore: `IEEE_API_KEY`

1. Open the [IEEE getting-started page](https://developer.ieee.org/getting_started) and select **Register**.
2. Complete registration and confirm your email.
3. Request a metadata API key, describing your application and providing your organization's website URL.
4. After IEEE reviews and approves the request, copy the issued key into `IEEE_API_KEY`.

Approval may take time. Use the developer portal's account/usage screens to review your quota before running the 76 IEEE query partitions. [IEEE registration and key instructions](https://developer.ieee.org/getting_started)

### ACM DL: no key used by this runner

There is no implemented ACM API adapter. Preview just its manual queries:

```bash
uv run --no-project --with-requirements requirements.txt python search_databases.py --database "ACM DL"
```

Run the three queries through your institution's ACM interface with the metadata fields, Full-Text Collection, English, and 2021–2027 filters specified in the plan, then export manually. Adding a key to `config.py` will not enable automated ACM extraction.

## After configuring access

Select one configured database first; `--execute` makes live requests:

```bash
uv run --no-project --with-requirements requirements.txt python search_databases.py --database "Scopus" --execute
```

Check the generated `summary.csv` for `complete` or an error. Missing settings are identified by name. HTTP 401/403 can indicate invalid credentials or missing entitlement; ask the provider or library to confirm access. HTTP 429 indicates throttling or quota limits. EBSCO failures can also require refreshed tokens or profile-specific query changes.

You do not need to fill every setting to run one database. The raw results still need screening, cross-database deduplication, and normalization before they can become input for `parse_records.py`.

## Verification and references

EBSCO needs institution-issued EDS tokens and a profile supporting `TI`, `AB`, `KW`, `LA`, and the `DT1` date limiter. Verify these with the API's Info endpoint before a live search. Renew expired tokens through your institution's EDS authentication flow.
Store refreshed tokens in `config.py`; the runner does not renew them automatically. See the [README](usage.md#api-credentials) for signup links and token setup.
IEEE API queries are split further to satisfy its two-wildcard limit; English eligibility requires screening. ACM queries are included in the preview and saved plan for manual use.
No live searches have been tested.

Offline checks:

```bash
uv run --no-project --with-requirements requirements.txt python -m unittest test_search_databases -v
```

API references: [Scopus](https://dev.elsevier.com/documentation/SCOPUSSearchAPI.wadl), [Web of Science Expanded](https://developer.clarivate.com/apis/wos), [EBSCO search](https://developer.ebsco.com/eds-api/docs/performing-a-search), [EBSCO dates](https://developer.ebsco.com/eds-api/docs/using-min-and-max-date-range-to-filter-results), [PubMed](https://www.ncbi.nlm.nih.gov/books/NBK25499/), [IEEE](https://developer.ieee.org/docs/read/Metadata_API_details).
