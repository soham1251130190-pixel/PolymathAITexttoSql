from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class EntityType(str, Enum):
    COMPANY = "company"
    FINANCIAL_CONCEPT = "financial_concept"


class StatementType(str, Enum):
    BALANCE_SHEET = "Balance Sheet"
    INCOME_STATEMENT = "Income Statement"
    CASH_FLOW_STATEMENT = "Cash Flow Statement"


class PeriodType(str, Enum):
    INSTANT = "instant"
    DURATION = "duration"


class QueryType(str, Enum):
    POINT_IN_TIME = "point_in_time"
    PERIOD_VALUE = "period_value"


class ConceptMetadata(BaseModel):
    """Catalog metadata for a canonical financial concept."""
    model_config = ConfigDict(frozen=True)

    concept_id: int
    concept_name: str
    xbrl_tag: str
    statement_type: StatementType
    description: str
    period_type: PeriodType
    expected_unit: str
    query_type: QueryType
    search_terms: str


class CompanyMatch(BaseModel):
    """Resolved company entity."""
    model_config = ConfigDict(frozen=True)

    user_term: str
    canonical_name: str
    ticker: Optional[str] = None
    is_matched: bool = True


class ConceptMatch(BaseModel):
    """Resolved financial concept with catalog metadata."""
    model_config = ConfigDict(frozen=True)

    user_term: str
    canonical_name: str
    metadata: Optional[ConceptMetadata] = None
    is_matched: bool = True


class MappingResult(BaseModel):
    """Generic mapping result for single term resolution."""
    model_config = ConfigDict(frozen=True)

    raw_term: str
    normalized_term: str
    entity_type: Optional[EntityType] = None
    canonical_name: Optional[str] = None
    company_match: Optional[CompanyMatch] = None
    concept_match: Optional[ConceptMatch] = None
    is_matched: bool = False
    ambiguous: bool = False
    ambiguity_candidates: List[str] = Field(default_factory=list)


class ExtractedEntities(BaseModel):
    """Extracted company and concept entities from a user query or phrase."""
    raw_query: str
    companies: List[CompanyMatch] = Field(default_factory=list)
    concepts: List[ConceptMatch] = Field(default_factory=list)
    unmatched_terms: List[str] = Field(default_factory=list)
