"""Offline checks: python -m unittest test_search_databases -v."""

import os
import unittest
from unittest.mock import Mock, patch

from search_databases import CONCEPTS, SearchPlan, build_plans, run_search, search_page


class SearchTests(unittest.TestCase):
    def test_query_terms_and_ieee_splits(self):
        plans = {plan.database: plan for plan in build_plans()}
        self.assertEqual(len(plans), 7)
        for pair in CONCEPTS:
            for terms in pair:
                for term in terms:
                    self.assertIn(term, plans["Scopus"].queries[0])
                    self.assertTrue(any(term in query for query in plans["IEEE Xplore"].queries))
        self.assertIn("PUBYEAR > 2020 AND PUBYEAR < 2028", plans["Scopus"].queries[0])
        self.assertTrue(all(query.count("*") <= 2 for query in plans["IEEE Xplore"].queries))
        self.assertEqual(len(plans["ACM DL"].queries), 3)
        self.assertIn('"Q-matrices"', plans["ACM DL"].queries[0])

    def test_pagination_and_overlap_deduplication(self):
        plan = SearchPlan("IEEE Xplore", ("concept 1", "concept 2"))
        with patch("search_databases.search_page", side_effect=[
            ([{"article_number": "1"}, {"article_number": "2"}], 3),
            ([{"article_number": "3"}], 3),
            ([{"article_number": "2"}], 1),
        ]) as page:
            records = run_search(plan, Mock())
        self.assertEqual([r["article_number"] for r in records], ["1", "2", "3"])
        self.assertEqual([call.args[3] for call in page.call_args_list], [0, 2, 0])

    def test_empty_page_is_a_failure(self):
        with patch("search_databases.search_page", return_value=([], 10)):
            with self.assertRaisesRegex(RuntimeError, "empty page"):
                run_search(SearchPlan("Scopus", ("query",)), Mock())

    def test_scopus_empty_result_placeholder(self):
        client = Mock()
        client.get.return_value = {"search-results": {
            "opensearch:totalResults": "0", "entry": [{"error": "No results"}],
        }}
        with patch.dict(os.environ, {"SCOPUS_API_KEY": "test"}):
            self.assertEqual(search_page(client, "Scopus", "query", 0), ([], 0))

    def test_ebsco_restricts_provider_and_dates(self):
        client = Mock()
        client.get.return_value = {"SearchResult": {
            "Data": {"Records": []}, "Statistics": {"TotalHits": 0},
        }}
        with patch.dict(os.environ, {"EBSCO_ERIC_PROVIDER": "ERIC", "EBSCO_AUTH_TOKEN": "test",
                                    "EBSCO_SESSION_TOKEN": "test"}):
            search_page(client, "ERIC", "query", 100)
        params = client.get.call_args.args[1]
        self.assertEqual(params["pagenumber"], 2)
        self.assertEqual(params["facetfilter"], "1,ContentProvider:ERIC")
        self.assertEqual(params["limiter"], "DT1:2021-01/2027-12")

    def test_pubmed_fetches_xml_and_detects_truncation(self):
        client = Mock()
        client.get.side_effect = [{"esearchresult": {"idlist": ["1", "2"], "count": "2"}}, "<xml/>"]
        with patch.dict(os.environ, {"NCBI_EMAIL": "test@example.org"}):
            self.assertEqual(run_search(SearchPlan("PubMed", ("query",)), client),
                             [{"pmid": "1"}, {"pmid": "2"}])
            self.assertTrue(client.get.call_args.kwargs["xml"])
            client.get.side_effect = [{"esearchresult": {"idlist": ["1"], "count": "10001"}}]
            with self.assertRaisesRegex(RuntimeError, "incomplete"):
                run_search(SearchPlan("PubMed", ("query",)), client)

    def test_default_preview_makes_no_network_requests(self):
        from search_databases import main
        with patch("sys.argv", ["search_databases.py"]), patch("builtins.print"), \
                patch("requests.Session.get", side_effect=AssertionError("Network forbidden")):
            main()


if __name__ == "__main__":
    unittest.main()
