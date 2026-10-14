import os
from pathlib import Path
from typing import Dict, Optional, Set
import pandas as pd

from retrieval.models import (
    ConceptMetadata,
    StatementType,
    PeriodType,
    QueryType,
)

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_DIR.parent
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"

DEFAULT_CATALOG_PATH = DEFAULT_DATA_DIR / "financial_schema_catalog.csv"
DEFAULT_MAPPINGS_PATH = DEFAULT_DATA_DIR / "entity_mappings.csv"

REQUIRED_CATALOG_COLUMNS: Set[str] = {
    "concept_id",
    "concept_name",
    "xbrl_tag",
    "statement_type",
    "description",
    "period_type",
    "expected_unit",
    "query_type",
    "search_terms",
}

REQUIRED_MAPPING_COLUMNS: Set[str] = {
    "entity_type",
    "user_term",
    "database_value",
}


class CatalogLoader:
    """Loads and validates the financial schema catalog and entity mappings."""

    def __init__(
        self,
        catalog_path: Optional[Path | str] = None,
        mappings_path: Optional[Path | str] = None,
    ) -> None:
        raw_catalog = catalog_path or os.getenv("FINANCIAL_CATALOG_PATH")
        self.catalog_path = Path(raw_catalog).resolve() if raw_catalog else DEFAULT_CATALOG_PATH

        raw_mappings = mappings_path or os.getenv("ENTITY_MAPPINGS_PATH")
        self.mappings_path = Path(raw_mappings).resolve() if raw_mappings else DEFAULT_MAPPINGS_PATH

        self._catalog_df: Optional[pd.DataFrame] = None
        self._mappings_df: Optional[pd.DataFrame] = None
        self._concepts_by_name: Dict[str, ConceptMetadata] = {}
        self._concepts_by_id: Dict[int, ConceptMetadata] = {}

        self.load()

    def load(self) -> None:
        """Loads both CSVs, validating existence and required columns."""
        self._load_catalog()
        self._load_mappings()

    def _load_catalog(self) -> None:
        if not self.catalog_path.is_file():
            raise FileNotFoundError(
                f"Financial schema catalog file not found at: {self.catalog_path}"
            )

        df = pd.read_csv(self.catalog_path)
        missing_cols = REQUIRED_CATALOG_COLUMNS - set(df.columns)
        if missing_cols:
            raise ValueError(
                f"Catalog CSV missing required columns: {sorted(missing_cols)} at {self.catalog_path}"
            )

        self._catalog_df = df
        self._concepts_by_name.clear()
        self._concepts_by_id.clear()

        for _, row in df.iterrows():
            metadata = ConceptMetadata(
                concept_id=int(row["concept_id"]),
                concept_name=str(row["concept_name"]),
                xbrl_tag=str(row["xbrl_tag"]),
                statement_type=StatementType(str(row["statement_type"])),
                description=str(row["description"]),
                period_type=PeriodType(str(row["period_type"])),
                expected_unit=str(row["expected_unit"]),
                query_type=QueryType(str(row["query_type"])),
                search_terms=str(row["search_terms"]),
            )
            self._concepts_by_name[metadata.concept_name] = metadata
            self._concepts_by_id[metadata.concept_id] = metadata

    def _load_mappings(self) -> None:
        if not self.mappings_path.is_file():
            raise FileNotFoundError(
                f"Entity mappings file not found at: {self.mappings_path}"
            )

        df = pd.read_csv(self.mappings_path)
        missing_cols = REQUIRED_MAPPING_COLUMNS - set(df.columns)
        if missing_cols:
            raise ValueError(
                f"Entity mappings CSV missing required columns: {sorted(missing_cols)} at {self.mappings_path}"
            )

        self._mappings_df = df

    @property
    def catalog_df(self) -> pd.DataFrame:
        if self._catalog_df is None:
            raise RuntimeError("Catalog data not loaded")
        return self._catalog_df

    @property
    def mappings_df(self) -> pd.DataFrame:
        if self._mappings_df is None:
            raise RuntimeError("Mappings data not loaded")
        return self._mappings_df

    def get_concept_by_name(self, concept_name: str) -> Optional[ConceptMetadata]:
        """Lookup catalog metadata by exact canonical concept name."""
        return self._concepts_by_name.get(concept_name)

    def get_concept_by_id(self, concept_id: int) -> Optional[ConceptMetadata]:
        """Lookup catalog metadata by concept ID."""
        return self._concepts_by_id.get(concept_id)

    def get_all_concepts(self) -> Dict[str, ConceptMetadata]:
        """Returns all loaded concept metadata keyed by canonical name."""
        return dict(self._concepts_by_name)
