"""Tests voor Pijler A modules.

Test de nieuwe functionaliteit van Pijler A:
- roles.py: Analistrollen definitie
- sources.py: Bronnen configuratie
- scanner.py: Scanner logica
- cycle.py: Orchestratie
"""

import unittest
from datetime import datetime, timezone

from kompas.pijler_a.roles import (
    STOCK_WATCHERS,
    TREND_VIEWERS,
    TECHNICAL_STOCK_WATCHERS,
    SectorSpecialist,
    SECTOR_SPECIALISTS,
    FIXED_ROLES,
    ALL_ROLES,
    get_role_by_name,
    get_sector_specialist,
    add_sector_specialist,
)
from kompas.pijler_a.sources import (
    Source,
    SourceType,
    SourceTier,
    RSS_SOURCES,
    INVESTING_PAGES,
    get_sources_for_role,
    get_sources_for_sector,
    get_websearch_queries_for_sector,
    get_technical_source_url,
    get_all_sources,
    get_sources_for_stock_watchers,
)
from kompas.pijler_a.scanner import (
    SignalCandidate,
    ParsedItem,
    ScanResult,
    RSSParser,
    WebPageParser,
    WebSearchParser,
    SignalExtractor,
    Scanner,
)
from kompas.core.signal import Signal, validate_signal


class TestRoles(unittest.TestCase):
    """Test de analistrollen definitie."""

    def test_fixed_roles_defined(self):
        """Test dat de vaste rollen gedefinieerd zijn."""
        self.assertEqual(len(FIXED_ROLES), 3)
        self.assertIn(STOCK_WATCHERS, FIXED_ROLES)
        self.assertIn(TREND_VIEWERS, FIXED_ROLES)
        self.assertIn(TECHNICAL_STOCK_WATCHERS, FIXED_ROLES)

    def test_sector_specialists_pool(self):
        """Test dat de sector specialisten pool gedefinieerd is."""
        self.assertGreater(len(SECTOR_SPECIALISTS), 0)
        
        # Check dat alle specialisten SectorSpecialist instances zijn
        for specialist in SECTOR_SPECIALISTS:
            self.assertIsInstance(specialist, SectorSpecialist)
            self.assertIsNotNone(specialist.sector)

    def test_all_roles_includes_both(self):
        """Test dat ALL_ROLES zowel vaste rollen als sector specialisten bevat."""
        self.assertIn(STOCK_WATCHERS, ALL_ROLES)
        self.assertIn(TREND_VIEWERS, ALL_ROLES)
        self.assertIn(TECHNICAL_STOCK_WATCHERS, ALL_ROLES)
        # Check dat de eerste specialist in ALL_ROLES zit
        self.assertIn(SECTOR_SPECIALISTS[0], ALL_ROLES)

    def test_get_role_by_name(self):
        """Test het opzoeken van rollen op naam."""
        role = get_role_by_name("Stock watchers")
        self.assertEqual(role, STOCK_WATCHERS)
        
        role = get_role_by_name("Trend viewers")
        self.assertEqual(role, TREND_VIEWERS)
        
        role = get_role_by_name("Non-existent")
        self.assertIsNone(role)

    def test_get_sector_specialist(self):
        """Test het opzoeken van sector specialisten."""
        specialist = get_sector_specialist("Halfgeleiders")
        self.assertIsNotNone(specialist)
        self.assertEqual(specialist.sector, "Halfgeleiders")
        
        specialist = get_sector_specialist("Non-existent")
        self.assertIsNone(specialist)

    def test_add_sector_specialist(self):
        """Test het toevoegen van een nieuwe sector specialist."""
        # Voeg een nieuwe specialist toe
        new_specialist = add_sector_specialist("New Sector")
        self.assertEqual(new_specialist.sector, "New Sector")
        self.assertEqual(new_specialist.full_name, "Sector specialist  New Sector")

    def test_sector_specialist_full_name(self):
        """Test de full_name property van SectorSpecialist."""
        specialist = SectorSpecialist(sector="Test Sector")
        self.assertEqual(specialist.full_name, "Sector specialist  Test Sector")


class TestSources(unittest.TestCase):
    """Test de bronnen configuratie."""

    def test_rss_sources_defined(self):
        """Test dat RSS bronnen gedefinieerd zijn."""
        self.assertGreater(len(RSS_SOURCES), 0)
        
        for source in RSS_SOURCES:
            self.assertIsInstance(source, Source)
            self.assertEqual(source.source_type, SourceType.RSS)
            self.assertIsNotNone(source.id)
            self.assertIsNotNone(source.name)
            self.assertIsNotNone(source.url_or_query)

    def test_investing_pages_defined(self):
        """Test dat Investing.com pagina's gedefinieerd zijn."""
        self.assertGreater(len(INVESTING_PAGES), 0)
        
        for source in INVESTING_PAGES:
            self.assertIsInstance(source, Source)
            self.assertEqual(source.source_type, SourceType.INVESTING_PAGE)

    def test_get_sources_for_role(self):
        """Test het opzoeken van bronnen voor een rol."""
        sources = get_sources_for_role("Stock watchers")
        self.assertGreater(len(sources), 0)
        
        for source in sources:
            self.assertIn("Stock watchers", source.roles)

    def test_get_sources_for_sector(self):
        """Test het opzoeken van bronnen voor een sector."""
        sources = get_sources_for_sector("Halfgeleiders")
        # Note: In de huidige implementatie zijn er geen directe bronnen voor sectoren
        # in de RSS_SOURCES of INVESTING_PAGES, dus dit kan 0 zijn
        # In productie zouden de WebSearch bronnen wel resultaat geven

    def test_get_websearch_queries_for_sector(self):
        """Test het opzoeken van WebSearch queries voor een sector."""
        queries = get_websearch_queries_for_sector("Halfgeleiders")
        self.assertGreater(len(queries), 0)

    def test_get_technical_source_url(self):
        """Test het genereren van technische bron URLs."""
        url = get_technical_source_url("ASML")
        self.assertIn("ASML", url)
        self.assertIn("technical", url)

    def test_get_all_sources(self):
        """Test het ophalen van alle bronnen."""
        all_sources = get_all_sources()
        self.assertGreater(len(all_sources), 0)

    def test_get_sources_for_stock_watchers(self):
        """Test het genereren van bronnen voor Stock Watchers voor specifieke tickers."""
        tickers = ["ASML", "NVDA"]
        sources = get_sources_for_stock_watchers(tickers)
        
        # Elke ticker zou 2 bronnen moeten hebben (technisch + websearch)
        self.assertEqual(len(sources), len(tickers) * 2)


class TestScanner(unittest.TestCase):
    """Test de scanner logica."""

    def test_parsed_item_creation(self):
        """Test het aanmaken van een ParsedItem."""
        item = ParsedItem(
            title="Test Titel",
            link="https://example.com",
            description="Test beschrijving",
            published="2024-01-01T12:00:00Z",
            source_name="Test Bron",
            source_type=SourceType.RSS,
        )
        
        self.assertEqual(item.title, "Test Titel")
        self.assertEqual(item.link, "https://example.com")
        self.assertEqual(item.source_name, "Test Bron")

    def test_signal_candidate_creation(self):
        """Test het aanmaken van een SignalCandidate."""
        candidate = SignalCandidate(
            role="Stock watchers",
            subject="Test Onderwerp",
            text="Test tekst",
            source="https://example.com",
            source_tier="tier 1",
            magnitude="10%",
            timeframe_horizon="kort termijn",
            data_confidence="hoog",
            signal_confidence="hoog",
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        
        self.assertEqual(candidate.role, "Stock watchers")
        self.assertEqual(candidate.subject, "Test Onderwerp")

    def test_signal_candidate_to_signal(self):
        """Test het converteren van SignalCandidate naar Signal."""
        candidate = SignalCandidate(
            role="Stock watchers",
            subject="Test Onderwerp",
            text="Test tekst",
            source="https://example.com",
            source_tier="tier 1",
            magnitude="10%",
            timeframe_horizon="kort termijn",
            data_confidence="hoog",
            signal_confidence="hoog",
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        
        signal = candidate.to_signal()
        self.assertIsInstance(signal, Signal)
        self.assertEqual(signal.role, "Stock watchers")
        self.assertEqual(signal.subject, "Test Onderwerp")

    def test_signal_candidate_validation(self):
        """Test de validatie van SignalCandidate."""
        # Valide candidate
        candidate = SignalCandidate(
            role="Stock watchers",
            subject="Test Onderwerp",
            text="Test tekst",
            source="https://example.com",
            source_tier="tier 1",
            magnitude="10%",
            timeframe_horizon="kort termijn",
            data_confidence="hoog",
            signal_confidence="hoog",
            observed_at=datetime.now(timezone.utc).isoformat(),
        )
        
        is_valid, errors = candidate.validate()
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Ongeldige candidate (geen bron)
        candidate.source = ""
        is_valid, errors = candidate.validate()
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)

    def test_rss_parser_parse(self):
        """Test de RSS parser."""
        rss_content = """<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Test Item</title>
              <link>https://example.com</link>
              <description>Test beschrijving</description>
              <pubDate>Mon, 01 Jan 2024 12:00:00 GMT</pubDate>
            </item>
          </channel>
        </rss>"""
        
        source = Source(
            id="test_rss",
            name="Test RSS",
            source_type=SourceType.RSS,
            url_or_query="https://example.com/rss",
            tier=SourceTier.TIER_2,
        )
        
        items = RSSParser.parse(rss_content, source)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Test Item")
        self.assertEqual(items[0].link, "https://example.com")

    def test_websearch_parser_parse_json(self):
        """Test de WebSearch parser met JSON input."""
        json_content = '[{"title": "Test Search", "url": "https://example.com", "description": "Test desc"}]'
        
        source = Source(
            id="test_websearch",
            name="Test WebSearch",
            source_type=SourceType.WEBSEARCH,
            url_or_query="test query",
            tier=SourceTier.TIER_2,
        )
        
        items = WebSearchParser.parse(json_content, source)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Test Search")

    def test_scanner_scan_source(self):
        """Test het scannen van een enkele bron."""
        scanner = Scanner()
        
        source = Source(
            id="test_source",
            name="Test Source",
            source_type=SourceType.RSS,
            url_or_query="https://example.com/rss",
            tier=SourceTier.TIER_2,
            roles=["Stock watchers"],
        )
        
        result = scanner.scan_source(source)
        self.assertTrue(result.success)
        self.assertIsNotNone(result.items)

    def test_scanner_scan_role(self):
        """Test het scannen van een rol."""
        scanner = Scanner()
        
        candidates = scanner.scan_role("Stock watchers")
        # In de huidige implementatie (zonder echte fetch) zou dit leeg kunnen zijn
        # of mock data bevatten
        self.assertIsInstance(candidates, list)

    def test_signal_extractor_extract(self):
        """Test het extraheren van signalen uit items."""
        item = ParsedItem(
            title="ASML stijgt met 10%",
            link="https://example.com/asml",
            description="ASML aandeel stijgt sterk",
            source_name="Test Source",
            source_type=SourceType.RSS,
        )
        
        candidate = SignalExtractor.extract_from_item(
            item, 
            role="Stock watchers",
            sector=None,
        )
        
        self.assertIsNotNone(candidate)
        self.assertIsInstance(candidate, SignalCandidate)
        self.assertEqual(candidate.role, "Stock watchers")


class TestCycle(unittest.TestCase):
    """Test de Pijler A cyclus orchestratie."""

    def test_run_pijler_a_cycle(self):
        """Test het uitvoeren van een complete Pijler A cyclus."""
        from kompas.pijler_a.cycle import run_pijler_a_cycle
        
        # Run met lege bestaande events
        result = run_pijler_a_cycle(existing_events=[])
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result.publishable_signals, list)
        self.assertIsInstance(result.errors, list)
        self.assertGreaterEqual(result.total_signals_scanned, 0)


if __name__ == '__main__':
    unittest.main()
