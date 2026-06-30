"""Additional unit tests for utils/rdf.py (pure + mocked paths, offline)."""
from unittest.mock import MagicMock

from rdflib import URIRef

from utils import rdf


def test_extract_entities_from_valid_query():
    assert rdf.extract_entities("SELECT * WHERE { wd:Q567 ?p ?o }") == ["wd:Q567"]


def test_extract_entities_returns_empty_on_malformed_query():
    assert rdf.extract_entities("this is not sparql") == []


def test_extract_entities_recursive_handles_uri_and_prefix_dict():
    assert rdf.extract_entities_recursive(URIRef("http://example.org/x")) == ["http://example.org/x"]
    assert rdf.extract_entities_recursive({"prefix": "wd", "localname": "Q42"}) == ["wd:Q42"]
    assert rdf.extract_entities_recursive([URIRef("http://a"), URIRef("http://b")]) == ["http://a", "http://b"]


def test_get_wikidata_label_fixed_and_literal_paths():
    assert rdf.get_wikidata_label(None, "rdfs:label") == "label"
    assert rdf.get_wikidata_label(None, "xsd:integer") == "integer"  # in FIXED_LABELS
    assert rdf.get_wikidata_label(None, "xsd:foo") is None            # unknown xsd type
    assert rdf.get_wikidata_label(None, "Berlin") == "Berlin"          # plain literal


def test_execute_returns_json_on_200(monkeypatch):
    class _Resp:
        status_code = 200

        def json(self):
            return {"results": {"bindings": [{"x": 1}]}}

    monkeypatch.setattr(rdf.requests, "get", lambda url, params: _Resp())
    assert rdf.execute("SELECT * WHERE {}")["results"]["bindings"] == [{"x": 1}]


def test_execute_returns_none_on_error(monkeypatch):
    def _boom(url, params):
        raise RuntimeError("down")

    monkeypatch.setattr(rdf.requests, "get", _boom)
    assert rdf.execute("SELECT * WHERE {}") is None


def test_query_wikidata_returns_bindings(monkeypatch):
    monkeypatch.setattr(rdf, "execute", lambda q: {"results": {"bindings": [{"a": 1}]}})
    assert rdf.query_wikidata("SELECT * WHERE {}") == [{"a": 1}]


def test_query_wikidata_label_resolves_value(monkeypatch):
    monkeypatch.setattr(rdf, "query_wikidata", lambda q: [{"label": {"value": "Douglas Adams"}}])
    assert rdf.query_wikidata_label("wd:Q42") == "Douglas Adams"


def test_get_wikidata_label_cached_returns_cached(monkeypatch):
    cache = MagicMock()
    cache.wikidata_labels.find_one.return_value = {"uri": "Q42", "lang": "en", "label": "Cached"}
    assert rdf.get_wikidata_label_cached(cache, "Q42") == "Cached"


def test_get_wikidata_label_cached_queries_and_inserts(monkeypatch):
    cache = MagicMock()
    cache.wikidata_labels.find_one.return_value = None
    monkeypatch.setattr(rdf, "query_wikidata_label", lambda uri, lang: "Fresh")
    assert rdf.get_wikidata_label_cached(cache, "Q42") == "Fresh"
    cache.wikidata_labels.insert_one.assert_called_once()


def test_get_wikidata_label_resolves_via_cache(monkeypatch):
    cache = MagicMock()
    monkeypatch.setattr(rdf, "get_wikidata_label_cached", lambda c, w, lang="en": "Resolved")
    assert rdf.get_wikidata_label(cache, "wd:Q42") == "Resolved"
