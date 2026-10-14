import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
import pandas as pd

from retrieval.catalog import CatalogLoader, DEFAULT_CATALOG_PATH, DEFAULT_MAPPINGS_PATH
from retrieval.mapper import FinancialEntityMapper, normalize_term
from retrieval.models import (
    EntityType,
    PeriodType,
    QueryType,
    StatementType,
)


# ============================================================================
# 1. CATALOG LOADER & VALIDATION TESTS
# ============================================================================


def test_catalog_loader_default_paths():
    loader = CatalogLoader()
    assert loader.catalog_path == DEFAULT_CATALOG_PATH
    assert loader.mappings_path == DEFAULT_MAPPINGS_PATH
    assert len(loader.get_all_concepts()) == 18

    rev_meta = loader.get_concept_by_name("Revenue")
    assert rev_meta is not None
    assert rev_meta.concept_id == 17
    assert rev_meta.statement_type == StatementType.INCOME_STATEMENT
    assert rev_meta.period_type == PeriodType.DURATION
    assert rev_meta.query_type == QueryType.PERIOD_VALUE
    assert rev_meta.expected_unit == "USD"
    assert rev_meta.xbrl_tag == "RevenueFromContractWithCustomerExcludingAssessedTax"

    assets_meta = loader.get_concept_by_name("Total Assets")
    assert assets_meta is not None
    assert assets_meta.statement_type == StatementType.BALANCE_SHEET
    assert assets_meta.period_type == PeriodType.INSTANT
    assert assets_meta.query_type == QueryType.POINT_IN_TIME


def test_catalog_loader_missing_file(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist.csv"
    with pytest.raises(FileNotFoundError, match="Financial schema catalog file not found"):
        CatalogLoader(catalog_path=non_existent)


def test_catalog_loader_missing_columns(tmp_path: Path):
    bad_catalog = tmp_path / "bad_catalog.csv"
    # Create CSV missing xbrl_tag and period_type
    pd.DataFrame({
        "concept_id": [1],
        "concept_name": ["Revenue"],
        "statement_type": ["Income Statement"],
    }).to_csv(bad_catalog, index=False)

    with pytest.raises(ValueError, match="Catalog CSV missing required columns"):
        CatalogLoader(catalog_path=bad_catalog)


def test_mappings_loader_missing_columns(tmp_path: Path):
    bad_mappings = tmp_path / "bad_mappings.csv"
    pd.DataFrame({
        "user_term": ["apple"],
        "database_value": ["Apple Inc."],
    }).to_csv(bad_mappings, index=False)

    with pytest.raises(ValueError, match="Entity mappings CSV missing required columns"):
        CatalogLoader(mappings_path=bad_mappings)


# ============================================================================
# 2. EXACT MATCHING FROM SEED MAPPINGS
# ============================================================================


def test_exact_matches_from_csv():
    mapper = FinancialEntityMapper()

    # Company
    res_apple = mapper.map_company("apple")
    assert res_apple is not None
    assert res_apple.canonical_name == "Apple Inc."

    res_msft = mapper.map_company("microsoft")
    assert res_msft is not None
    assert res_msft.canonical_name == "Microsoft Corporation"

    # Concepts
    res_sales = mapper.map_financial_concept("sales")
    assert res_sales is not None
    assert res_sales.canonical_name == "Revenue"

    res_capex = mapper.map_financial_concept("capex")
    assert res_capex is not None
    assert res_capex.canonical_name == "Capital Expenditure"

    res_cogs = mapper.map_financial_concept("cogs")
    assert res_cogs is not None
    assert res_cogs.canonical_name == "Cost of Goods Sold"

    res_bottom_line = mapper.map_financial_concept("bottom line")
    assert res_bottom_line is not None
    assert res_bottom_line.canonical_name == "Net Income"


# ============================================================================
# 3. NORMALIZATION: CASE, WHITESPACE, PUNCTUATION
# ============================================================================


def test_normalization_variations():
    mapper = FinancialEntityMapper()

    # Case variations
    assert mapper.map_company("APPLE").canonical_name == "Apple Inc."
    assert mapper.map_financial_concept("REVENUE").canonical_name == "Revenue"

    # Whitespace variations
    assert mapper.map_company("   apple     inc   ").canonical_name == "Apple Inc."
    assert mapper.map_financial_concept("  cost   of   goods   sold  ").canonical_name == "Cost of Goods Sold"

    # Punctuation variations
    assert mapper.map_company("Apple, Inc.").canonical_name == "Apple Inc."
    assert mapper.map_company("apple inc.").canonical_name == "Apple Inc."
    assert mapper.map_company("amazon.com inc.").canonical_name == "Amazon.com Inc."
    assert mapper.map_company("amazon.com").canonical_name == "Amazon.com Inc."

    # PP&E variations
    assert mapper.map_financial_concept("pp&e").canonical_name == "Property Plant and Equipment"
    assert mapper.map_financial_concept("PP & E").canonical_name == "Property Plant and Equipment"
    assert mapper.map_financial_concept("ppe").canonical_name == "Property Plant and Equipment"

    # Parentheses and quotes
    assert mapper.map_financial_concept('"capex"').canonical_name == "Capital Expenditure"
    assert mapper.map_financial_concept("(operating income)").canonical_name == "Operating Income"


# ============================================================================
# 4. TICKER ALIASES
# ============================================================================


def test_ticker_aliases():
    mapper = FinancialEntityMapper()

    match_aapl = mapper.map_company("AAPL")
    assert match_aapl is not None
    assert match_aapl.canonical_name == "Apple Inc."
    assert match_aapl.ticker == "AAPL"

    match_msft = mapper.map_company("msft")
    assert match_msft is not None
    assert match_msft.canonical_name == "Microsoft Corporation"
    assert match_msft.ticker == "MSFT"

    match_amzn = mapper.map_company("  AMZN  ")
    assert match_amzn is not None
    assert match_amzn.canonical_name == "Amazon.com Inc."
    assert match_amzn.ticker == "AMZN"


# ============================================================================
# 5. LONGEST-PHRASE MATCHING & DISAMBIGUATION
# ============================================================================


def test_longest_phrase_matching_isolated():
    mapper = FinancialEntityMapper()

    # "gross profit" vs "profit"
    # In entity_mappings.csv: "profit" -> "Net Income", "gross profit" -> "Gross Profit"
    res_gross = mapper.map_financial_concept("gross profit")
    assert res_gross is not None
    assert res_gross.canonical_name == "Gross Profit"

    res_profit = mapper.map_financial_concept("profit")
    assert res_profit is not None
    assert res_profit.canonical_name == "Net Income"

    # "operating profit" vs "profit"
    res_op_profit = mapper.map_financial_concept("operating profit")
    assert res_op_profit is not None
    assert res_op_profit.canonical_name == "Operating Income"


def test_longest_phrase_matching_in_queries():
    mapper = FinancialEntityMapper()

    query1 = "What was Apple's gross profit in 2024?"
    extracted1 = mapper.extract_entities(query1)
    assert len(extracted1.companies) == 1
    assert extracted1.companies[0].canonical_name == "Apple Inc."
    assert len(extracted1.concepts) == 1
    assert extracted1.concepts[0].canonical_name == "Gross Profit"
    # Ensure "profit" was NOT also extracted as Net Income
    concept_names1 = [c.canonical_name for c in extracted1.concepts]
    assert "Net Income" not in concept_names1

    query2 = "Find operating cash flow and capex for MSFT in 2023"
    extracted2 = mapper.extract_entities(query2)
    assert len(extracted2.companies) == 1
    assert extracted2.companies[0].canonical_name == "Microsoft Corporation"
    concept_names2 = {c.canonical_name for c in extracted2.concepts}
    assert concept_names2 == {"Operating Cash Flow", "Capital Expenditure"}
    # Ensure "cash" was not greedily matched as Cash and Cash Equivalents
    assert "Cash and Cash Equivalents" not in concept_names2


# ============================================================================
# 6. CATALOG METADATA ATTACHMENT
# ============================================================================


def test_catalog_metadata_attachment():
    mapper = FinancialEntityMapper()

    res = mapper.map_financial_concept("sales")
    assert res is not None
    assert res.metadata is not None
    assert res.metadata.concept_name == "Revenue"
    assert res.metadata.statement_type == StatementType.INCOME_STATEMENT
    assert res.metadata.period_type == PeriodType.DURATION
    assert res.metadata.query_type == QueryType.PERIOD_VALUE
    assert res.metadata.expected_unit == "USD"
    assert res.metadata.xbrl_tag == "RevenueFromContractWithCustomerExcludingAssessedTax"

    res_bs = mapper.map_financial_concept("accounts receivable")
    assert res_bs is not None
    assert res_bs.metadata is not None
    assert res_bs.metadata.statement_type == StatementType.BALANCE_SHEET
    assert res_bs.metadata.period_type == PeriodType.INSTANT
    assert res_bs.metadata.query_type == QueryType.POINT_IN_TIME


# ============================================================================
# 7. UNKNOWN & AMBIGUOUS TERMS
# ============================================================================


def test_unknown_terms():
    mapper = FinancialEntityMapper()

    # Unknown financial concept
    assert mapper.map_financial_concept("ebitda") is None
    assert mapper.map_financial_concept("cryptocurrency") is None

    # Unknown company
    assert mapper.map_company("tesla") is None
    assert mapper.map_company("nvidia") is None

    # map_term behavior for unknown
    res = mapper.map_term("random_metric", entity_type=EntityType.FINANCIAL_CONCEPT)
    assert res.is_matched is False
    assert res.canonical_name is None

    # Empty inputs
    assert mapper.map_company("") is None
    assert mapper.map_financial_concept("   ") is None
    assert mapper.map_term("").is_matched is False


def test_untyped_resolution():
    mapper = FinancialEntityMapper()

    # Automatic company detection
    res_co = mapper.map_term("aapl")
    assert res_co.is_matched is True
    assert res_co.entity_type == EntityType.COMPANY
    assert res_co.canonical_name == "Apple Inc."

    # Automatic concept detection
    res_fc = mapper.map_term("capex")
    assert res_fc.is_matched is True
    assert res_fc.entity_type == EntityType.FINANCIAL_CONCEPT
    assert res_fc.canonical_name == "Capital Expenditure"
