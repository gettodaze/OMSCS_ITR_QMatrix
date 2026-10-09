# Sharing search results

Keep the database exports and derived record files private unless the applicable institutional license and content licenses explicitly permit public redistribution. Download access does not by itself establish redistribution rights.

The repository's former candidate CSV contains 836 records, including 835 abstracts, from multiple databases. Its seven derived CSVs reproduce those abstracts, and the example CSV also contains real abstracts. These should be treated as the same distribution issue, even after changing their column names or format.

## What the provider guidance establishes

- **Scopus:** published terms prohibit substantial or systematic redistribution of the service or parts of it, including derivative works. Public posting of the complete export is therefore a concern unless the applicable agreement grants permission. [Elsevier Scopus terms](https://www-prod.elsevier.com/legal/elsevier-website-terms-and-conditions/elsevier-scopus-terms-and-conditions).
- **PubMed:** NLM does not claim copyright in the abstracts, but publishers or authors may. Public availability through PubMed is not blanket permission to republish the abstract text. [NCBI policies](https://www.ncbi.nlm.nih.gov/home/about/policies/).
- **APA PsycInfo:** APA says appropriate usage depends on the license agreed with the institution. Obtain the applicable license rather than assuming export permission includes public sharing. [APA usage guidance](https://www.apa.org/pubs/librarians/policies/usage).
- **Other databases:** this review does not establish permission for every provider or record. Mixed exports need a rights assessment for their sources and content, not just a check that the download button is available.

This supports keeping the full mixed dataset private pending a license check; it is not a determination that every citation or abstract is prohibited from being shared. Ask the university library's electronic-resources/licensing team whether the subscription permits public redistribution of citation metadata, abstracts, index keywords, and derived review datasets, and whether uploading full records to Rayyan is permitted. These are separate uses. No institutional license was available for this review.

## Public repository content

Keep source code, search strings, search dates, aggregate counts, methodological documentation and synthetic examples in the repository. Share record-level citation lists only after checking the relevant permissions; removing abstracts alone may not satisfy database licensing restrictions.

Store downloaded records in `input/` and derived outputs in `output/`. Both directories, and the older root-level `input.csv` and `excel-example.csv` filenames, are ignored by Git. Ignoring a file prevents future additions; it does not remove files already present in commits.

Tests should use synthetic records. The existing local `input/input.csv` can still serve as an optional baseline for the export audit, without being published.

## History cleanup

Remove both historical locations of the candidate and example CSVs, together with the derived `output/` directory, from every published branch and tag. Keep local data copies and a local recovery bundle outside the repository before rewriting. Rewriting changes commit IDs, so collaborators should use a fresh clone rather than merging an old branch that could restore the data.

Replacing published branch history requires a force push. Use an explicit lease against the remote commit inspected before cleanup so concurrent remote changes are not overwritten.

A history rewrite prevents normal branch-history access but cannot retract existing clones, forks, downloads, or every cached commit view. GitHub documents those limitations; its sensitive-data cleanup support is not generally available for ordinary non-sensitive content. [GitHub history-removal guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
