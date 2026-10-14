import re
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd

from retrieval.catalog import CatalogLoader
from retrieval.models import (
    CompanyMatch,
    ConceptMatch,
    ConceptMetadata,
    EntityType,
    ExtractedEntities,
    MappingResult,
)

# Standard stock tickers for in-scope companies
TICKER_MAPPINGS: Dict[str, Tuple[str, str]] = {
    "aapl": ("Apple Inc.", "AAPL"),
    "msft": ("Microsoft Corporation", "MSFT"),
    "amzn": ("Amazon.com Inc.", "AMZN"),
}

# Supplementary company aliases (punctuation variations, common abbreviations)
SUPPLEMENTARY_COMPANY_ALIASES: Dict[str, Tuple[str, Optional[str]]] = {
    "apple": ("Apple Inc.", "AAPL"),
    "apple inc": ("Apple Inc.", "AAPL"),
    "apple inc.": ("Apple Inc.", "AAPL"),
    "apple computer": ("Apple Inc.", "AAPL"),
    "apple computer inc": ("Apple Inc.", "AAPL"),
    "apple computer inc.": ("Apple Inc.", "AAPL"),
    "microsoft": ("Microsoft Corporation", "MSFT"),
    "microsoft corporation": ("Microsoft Corporation", "MSFT"),
    "microsoft corp": ("Microsoft Corporation", "MSFT"),
    "microsoft corp.": ("Microsoft Corporation", "MSFT"),
    "amazon": ("Amazon.com Inc.", "AMZN"),
    "amazon.com": ("Amazon.com Inc.", "AMZN"),
    "amazon com": ("Amazon.com Inc.", "AMZN"),
    "amazon.com inc": ("Amazon.com Inc.", "AMZN"),
    "amazon.com inc.": ("Amazon.com Inc.", "AMZN"),
    "amazon com inc": ("Amazon.com Inc.", "AMZN"),
}


def normalize_term(term: str) -> str:
    """
    Normalizes a term for case, excess whitespace, and common punctuation variations.
    Preserves meaningful symbols like '&' in 'pp&e' and '.' in 'amazon.com'.
    """
    if not term:
        return ""

    # 1. Lowercase
    cleaned = term.lower().strip()

    # 2. Normalize hyphens and dashes to spaces
    cleaned = re.sub(r"[-–—]", " ", cleaned)

    # 3. Strip surrounding quotation marks, brackets, parentheses, colons, commas, question marks
    cleaned = re.sub(r"^[^\w&]+|[^\w&.]+$", "", cleaned)

    # 4. Collapse multiple whitespaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # 5. Normalize spacing around '&' (e.g., 'pp & e' -> 'pp&e')
    cleaned = re.sub(r"\s*&\s*", "&", cleaned)

    return cleaned


def strip_all_punctuation(term: str) -> str:
    """Strips all remaining periods and symbols for fallback matching."""
    cleaned = re.sub(r"[^\w\s&]", "", term)
    return re.sub(r"\s+", " ", cleaned).strip()


class FinancialEntityMapper:
    """
    Resolves colloquial user terms, stock tickers, and aliases into canonical
    database entities (companies and financial concepts) and enriches them
    with schema catalog metadata.
    """

    def __init__(self, catalog_loader: Optional[CatalogLoader] = None) -> None:
        self.catalog = catalog_loader or CatalogLoader()

        # Internal lookup dictionaries: normalized_term -> canonical_value
        self._company_mappings: Dict[str, Tuple[str, Optional[str]]] = {}
        self._concept_mappings: Dict[str, str] = {}

        # Distinct concepts and companies index
        self._known_companies: Set[str] = set()
        self._known_concepts: Set[str] = set()

        self._build_indices()

    def _build_indices(self) -> None:
        """Populates mapping indices from entity_mappings.csv, catalog, and built-ins."""
        df = self.catalog.mappings_df

        # 1. Ingest Member 1's entity_mappings.csv as primary source of truth
        for _, row in df.iterrows():
            etype = str(row["entity_type"]).strip()
            raw_term = str(row["user_term"])
            db_val = str(row["database_value"]).strip()

            norm = normalize_term(raw_term)
            norm_stripped = strip_all_punctuation(norm)

            if etype == "company":
                self._known_companies.add(db_val)
                self._company_mappings[norm] = (db_val, None)
                if norm_stripped and norm_stripped != norm:
                    self._company_mappings[norm_stripped] = (db_val, None)
            elif etype == "financial_concept":
                self._known_concepts.add(db_val)
                self._concept_mappings[norm] = db_val
                if norm_stripped and norm_stripped != norm:
                    self._concept_mappings[norm_stripped] = db_val

        # 2. Also ensure canonical concept names themselves are self-mapped
        for concept_name in self.catalog.get_all_concepts().keys():
            self._known_concepts.add(concept_name)
            norm = normalize_term(concept_name)
            self._concept_mappings[norm] = concept_name
            norm_stripped = strip_all_punctuation(norm)
            if norm_stripped:
                self._concept_mappings[norm_stripped] = concept_name

        # 3. Register standard tickers
        for ticker_key, (company_name, ticker_symbol) in TICKER_MAPPINGS.items():
            self._company_mappings[ticker_key] = (company_name, ticker_symbol)
            self._known_companies.add(company_name)

        # 4. Register supplementary aliases
        for alias_key, (company_name, ticker_symbol) in SUPPLEMENTARY_COMPANY_ALIASES.items():
            norm_alias = normalize_term(alias_key)
            self._company_mappings[norm_alias] = (company_name, ticker_symbol)
            norm_stripped = strip_all_punctuation(norm_alias)
            if norm_stripped:
                self._company_mappings[norm_stripped] = (company_name, ticker_symbol)

    def map_company(self, term: str) -> Optional[CompanyMatch]:
        """
        Resolves a term to a canonical company name, with ticker support.
        Returns None if unmatched.
        """
        norm = normalize_term(term)
        if not norm:
            return None

        # Check normalized key
        if norm in self._company_mappings:
            canonical, ticker = self._company_mappings[norm]
            return CompanyMatch(user_term=term, canonical_name=canonical, ticker=ticker, is_matched=True)

        # Check punctuation-stripped key
        stripped = strip_all_punctuation(norm)
        if stripped in self._company_mappings:
            canonical, ticker = self._company_mappings[stripped]
            return CompanyMatch(user_term=term, canonical_name=canonical, ticker=ticker, is_matched=True)

        return None

    def map_financial_concept(self, term: str) -> Optional[ConceptMatch]:
        """
        Resolves a term to a canonical financial concept and attaches catalog metadata.
        Returns None if unmatched.
        """
        norm = normalize_term(term)
        if not norm:
            return None

        canonical = self._concept_mappings.get(norm)
        if not canonical:
            stripped = strip_all_punctuation(norm)
            canonical = self._concept_mappings.get(stripped)

        if not canonical:
            return None

        metadata = self.catalog.get_concept_by_name(canonical)
        return ConceptMatch(
            user_term=term,
            canonical_name=canonical,
            metadata=metadata,
            is_matched=True,
        )

    def map_term(self, term: str, entity_type: Optional[EntityType] = None) -> MappingResult:
        """
        Unified resolver for an isolated term.
        If entity_type is provided, resolves only against that type.
        If not provided, attempts both and flags ambiguity if both match differently.
        """
        raw_term = term
        norm = normalize_term(term)

        if not norm:
            return MappingResult(
                raw_term=raw_term,
                normalized_term="",
                is_matched=False,
            )

        company_res = self.map_company(norm) if entity_type in (None, EntityType.COMPANY) else None
        concept_res = self.map_financial_concept(norm) if entity_type in (None, EntityType.FINANCIAL_CONCEPT) else None

        # Handle specific requested type
        if entity_type == EntityType.COMPANY:
            if company_res:
                return MappingResult(
                    raw_term=raw_term,
                    normalized_term=norm,
                    entity_type=EntityType.COMPANY,
                    canonical_name=company_res.canonical_name,
                    company_match=company_res,
                    is_matched=True,
                )
            return MappingResult(raw_term=raw_term, normalized_term=norm, is_matched=False)

        if entity_type == EntityType.FINANCIAL_CONCEPT:
            if concept_res:
                return MappingResult(
                    raw_term=raw_term,
                    normalized_term=norm,
                    entity_type=EntityType.FINANCIAL_CONCEPT,
                    canonical_name=concept_res.canonical_name,
                    concept_match=concept_res,
                    is_matched=True,
                )
            return MappingResult(raw_term=raw_term, normalized_term=norm, is_matched=False)

        # Untyped resolution: check for matches or ambiguity
        if company_res and concept_res:
            return MappingResult(
                raw_term=raw_term,
                normalized_term=norm,
                is_matched=False,
                ambiguous=True,
                ambiguity_candidates=[company_res.canonical_name, concept_res.canonical_name],
            )
        elif company_res:
            return MappingResult(
                raw_term=raw_term,
                normalized_term=norm,
                entity_type=EntityType.COMPANY,
                canonical_name=company_res.canonical_name,
                company_match=company_res,
                is_matched=True,
            )
        elif concept_res:
            return MappingResult(
                raw_term=raw_term,
                normalized_term=norm,
                entity_type=EntityType.FINANCIAL_CONCEPT,
                canonical_name=concept_res.canonical_name,
                concept_match=concept_res,
                is_matched=True,
            )

        return MappingResult(raw_term=raw_term, normalized_term=norm, is_matched=False)

    def extract_entities(self, query: str) -> ExtractedEntities:
        """
        Extracts company and financial concept entities from free-form query text.
        Guarantees longest-phrase matching first so specific terms like 'gross profit'
        are resolved before substrings like 'profit', and 'cash from operations' before 'cash'.
        """
        norm_query = normalize_term(query)
        if not norm_query:
            return ExtractedEntities(raw_query=query)

        # Collect all candidate phrases sorted by token count desc, then length desc
        # (Longest phrases match first)
        all_concept_terms = sorted(
            self._concept_mappings.keys(),
            key=lambda t: (len(t.split()), len(t)),
            reverse=True,
        )
        all_company_terms = sorted(
            self._company_mappings.keys(),
            key=lambda t: (len(t.split()), len(t)),
            reverse=True,
        )

        matched_companies: List[CompanyMatch] = []
        matched_concepts: List[ConceptMatch] = []

        # Keep track of matched spans to prevent overlap
        occupied_spans: List[Tuple[int, int]] = []

        def is_span_free(start: int, end: int) -> bool:
            for s, e in occupied_spans:
                if not (end <= s or start >= e):
                    return False
            return True

        # Phase 1: Match longest financial concepts
        for term_phrase in all_concept_terms:
            # Word-boundary matching
            pattern = r"(?<!\w)" + re.escape(term_phrase) + r"(?!\w)"
            for match in re.finditer(pattern, norm_query):
                s, e = match.span()
                if is_span_free(s, e):
                    match_obj = self.map_financial_concept(term_phrase)
                    if match_obj and match_obj not in matched_concepts:
                        matched_concepts.append(match_obj)
                        occupied_spans.append((s, e))

        # Phase 2: Match longest companies / tickers
        for term_phrase in all_company_terms:
            pattern = r"(?<!\w)" + re.escape(term_phrase) + r"(?!\w)"
            for match in re.finditer(pattern, norm_query):
                s, e = match.span()
                if is_span_free(s, e):
                    match_obj = self.map_company(term_phrase)
                    if match_obj and match_obj not in matched_companies:
                        matched_companies.append(match_obj)
                        occupied_spans.append((s, e))

        return ExtractedEntities(
            raw_query=query,
            companies=matched_companies,
            concepts=matched_concepts,
        )
