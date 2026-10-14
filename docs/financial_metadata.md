# Financial Data Metadata Documentation

## 1. Purpose

This document describes the financial data layer used in the Text-to-SQL over Financial Data project. It explains the source of the financial data, the selected financial concepts, the database structure, period handling, filing information, units and currency, and the data-cleaning approach.

## 2. Financial Data Source

The initial financial dataset is based on SEC XBRL Company Facts data. SEC Company Facts provides structured financial facts reported by companies through XBRL filings.

The project uses selected US-GAAP financial concepts and corresponding XBRL tags rather than using every available XBRL concept.

## 3. Current Dataset

- Companies: 3
- Financial concepts: 18
- Clean financial records: 909

### Companies
- Amazon.com Inc.
- Apple Inc.
- Microsoft Corporation

## 4. Financial Statement Types

- Balance Sheet: 471 records
- Income Statement: 234 records
- Cash Flow Statement: 204 records

The selected concepts cover three major financial statement categories: Income Statement, Balance Sheet, and Cash Flow Statement.

## 5. Financial Concept Catalog

The project maps user-facing financial concepts to selected SEC XBRL tags. The schema catalog contains descriptions, statement types, period types, expected units, query types, and search terms.

| Concept | XBRL Tag | Statement Type | Period Type | Query Type |
|---|---|---|---|---|
| Accounts Receivable | `AccountsReceivableNetCurrent` | Balance Sheet | instant | point_in_time |
| Cash and Cash Equivalents | `CashAndCashEquivalentsAtCarryingValue` | Balance Sheet | instant | point_in_time |
| Current Assets | `AssetsCurrent` | Balance Sheet | instant | point_in_time |
| Current Liabilities | `LiabilitiesCurrent` | Balance Sheet | instant | point_in_time |
| Inventory | `InventoryNet` | Balance Sheet | instant | point_in_time |
| Property Plant and Equipment | `PropertyPlantAndEquipmentNet` | Balance Sheet | instant | point_in_time |
| Stockholders Equity | `StockholdersEquity` | Balance Sheet | instant | point_in_time |
| Total Assets | `Assets` | Balance Sheet | instant | point_in_time |
| Total Liabilities | `Liabilities` | Balance Sheet | instant | point_in_time |
| Capital Expenditure | `PaymentsToAcquirePropertyPlantAndEquipment` | Cash Flow Statement | duration | period_value |
| Financing Cash Flow | `NetCashProvidedByUsedInFinancingActivities` | Cash Flow Statement | duration | period_value |
| Investing Cash Flow | `NetCashProvidedByUsedInInvestingActivities` | Cash Flow Statement | duration | period_value |
| Operating Cash Flow | `NetCashProvidedByUsedInOperatingActivities` | Cash Flow Statement | duration | period_value |
| Cost of Goods Sold | `CostOfGoodsAndServicesSold` | Income Statement | duration | period_value |
| Gross Profit | `GrossProfit` | Income Statement | duration | period_value |
| Net Income | `NetIncomeLoss` | Income Statement | duration | period_value |
| Operating Income | `OperatingIncomeLoss` | Income Statement | duration | period_value |
| Revenue | `RevenueFromContractWithCustomerExcludingAssessedTax` | Income Statement | duration | period_value |

## 6. Period and Fiscal Year Handling

Financial facts are stored using their actual reporting period start and end dates.

The fiscal year used in the cleaned dataset is normalized from the period end date so that the financial period is represented consistently.

Income Statement and Cash Flow Statement concepts are duration facts because they represent financial activity over a reporting period.

Balance Sheet concepts are instant facts because they represent financial position at a specific reporting date.

## 7. Data Cleaning and Duplicate Handling

The raw Company Facts data can contain multiple observations for the same financial period because filings may include historical comparative figures.

The cleaning process therefore:
1. Selects annual 10-K fiscal-year facts.
2. Keeps annual duration facts with an appropriate annual period length.
3. Keeps instantaneous facts for Balance Sheet concepts.
4. Uses the actual period dates to identify the financial year.
5. Removes duplicate observations for the same company, concept, and financial period.
6. Prefers the filing whose reported fiscal year matches the actual fiscal year represented by the period.

## 8. Units and Currency

Each financial fact stores its unit and currency information.

The current SEC dataset contains financial values represented in USD, with the unit and currency stored explicitly in the database.

## 9. Database Structure

The cleaned financial data is stored in an SQLite database.

### Companies
Stores company identity information such as company name and CIK.

### Financial Concepts
Stores the financial concept name, SEC XBRL tag, and statement type.

### Periods
Stores period start date, period end date, fiscal year, and fiscal period.

### Filings
Stores filing-level information such as accession number, filing date, and form.

### Financial Facts
Stores the actual financial value and connects the value to a company, financial concept, reporting period, and filing.

## 10. Financial Fact Relationship

A financial fact connects the following information:

Company + Financial Concept + Period + Filing + Value + Unit + Currency

This structure allows the system to retrieve a financial value while preserving its company, concept, reporting period, and filing context.

## 11. Financial Schema Search Support

The schema catalog contains alternative search terms for financial concepts. Entity mappings also connect common user terminology to the canonical database concepts.

Examples:
- sales → Revenue
- profit → Net Income
- assets → Total Assets
- capex → Capital Expenditure
- cash from operations → Operating Cash Flow

## 12. Current Validation

The current database has been tested using financial queries for Apple, Microsoft, and Amazon.

The database verification also confirmed that no duplicate records were found for company, financial concept, and fiscal year within the cleaned dataset.

## 13. Member 1 Data Layer Files

- `financial_data_clean.csv` — cleaned SEC financial data
- `financial_data.db` — SQLite financial database
- `financial_schema_catalog.csv` — financial concept metadata
- `entity_mappings.csv` — common user terms mapped to canonical financial concepts and companies
