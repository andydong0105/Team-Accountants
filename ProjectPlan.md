# 💵Team Accountants Project Plan💵

---

## Overview

The goal of this project is to examine the relationship between U.S. monetary policy and stock market performance by integrating macroeconomic and financial market data from multiple sources. In particular, we aim to investigate how changes in the **Federal Funds Rate**, a key policy interest rate set by the Federal Reserve, relate to movements in the **S&P 500 index**, one of the most widely used indicators of U.S. equity market performance.

To address this question, we will construct an integrated dataset by combining two independent data sources: interest rate data obtained from the [Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/) database and historical market data retrieved from [Yahoo Finance](https://finance.yahoo.com/). These datasets share a common temporal attribute (date), which allows them to be linked and analyzed together. By integrating these sources, we will create a unified time-series dataset that captures both macroeconomic policy signals and financial market outcomes over multiple decades.

The project will follow a reproducible data curation workflow that includes **programmatic data acquisition, schema alignment, data integration, and quality assessment**. Scripts will be developed to retrieve data through web APIs, verify dataset integrity, and transform the raw data into a consistent structure suitable for analysis. Additional steps will include identifying and addressing potential data quality issues such as inconsistent temporal coverage, missing observations, and differences in data frequency between the two sources.

After preparing the integrated dataset, we will perform exploratory analysis and generate visualizations to examine patterns between interest rate changes and stock market performance. The final deliverable will include documented scripts, cleaned datasets, and visualizations, along with a reproducible workflow that allows others to recreate the entire pipeline from data acquisition to final results.

---

## Team

This project is completed collaboratively by two team members with clearly defined responsibilities across different stages of the data workflow.

* **Weimo Song** will primarily focus on the early stages of the project, including **data collection and acquisition**, **storage and organization**, **data integration**, and **data quality assessment and cleaning**. This includes developing scripts to programmatically retrieve datasets, organizing the raw and processed data within the project repository, integrating multiple datasets based on shared attributes, and identifying potential data quality issues.

* **Andy Dong** will focus on the later stages of the project, including **data cleaning, analysis and visualization**, as well as **metadata and data documentation**. Responsibilities include conducting exploratory analysis of the integrated dataset, producing visualizations to support findings, and preparing documentation such as data descriptions, codebooks, and reproducibility instructions required for the final project report.

---

## Research or Business Questions

The primary objective of this project is to explore the relationship between U.S. monetary policy and stock market performance by integrating macroeconomic data with financial market data. In particular, we focus on how changes in the **Federal Funds Rate**, the Federal Reserve’s primary policy interest rate, relate to movements in the **S&P 500 index**, a widely used indicator of overall equity market performance.

The main research question guiding this project is:

### How are changes in the Federal Funds Rate associated with movements in the S&P 500 index over time?

To further explore this relationship, we will consider several additional analytical questions that may be investigated depending on the scope and results of the initial analysis:

* **Do increases or decreases in the Federal Funds Rate correspond with observable short-term changes in stock market returns?**

* **Are there identifiable patterns between major shifts in interest rate policy and longer-term trends in the S&P 500 index?**

* **How does the relationship between interest rates and market performance vary across different economic periods?**

These questions will be addressed by integrating interest rate data from FRED with historical S&P 500 market data from Yahoo Finance using the shared temporal attribute (**date**). The resulting dataset will enable time-series exploration of the interaction between monetary policy signals and equity market behavior.

---

## Datasets

This project integrates two independent datasets that capture different aspects of the U.S. economic system. From a data management perspective, these are **secondary observational datasets**, meaning we inherit the structure, schema design, and data quality decisions made by the original providers. This has implications for how the data can be interpreted, transformed, and reused. 
The datasets represent two conceptual entities:
- monetary policy conditions (interest rates)
- stock market performance (equity index values)

Both datasets are structured as **time-series relations**, where each row represents an observation at a given time and each column represents an attribute. The shared temporal attribute enables them to be linked at the schema level.

### Dataset 1: Federal Funds Rate (FRED)

The first dataset contains historical values of the Federal Funds Effective Rate from the [Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/) database.

Key characteristics:

* **Source:** FRED (Federal Reserve Bank of St. Louis)  
* **Type:** Secondary observational data (API-based acquisition)  
* **Series:** DFF  
* **Temporal coverage:** July 1954 – present  
* **Frequency:** Daily (calendar-day observations)  
* **Primary attributes:**
  * `date` – observation date  
  * `value` – federal funds rate  

From a schema perspective, this dataset follows a simple relational structure with a single primary measurement (`value`) indexed by time. The dataset reflects how monetary policy is operationalized and recorded, but also embeds assumptions about what constitutes a valid observation (e.g., one rate per day, including non-trading days).

### Dataset 2: S&P 500 Market Data (Yahoo Finance)

The second dataset contains historical S&P 500 index data from [Yahoo Finance](https://finance.yahoo.com/).

Key characteristics:

* **Source:** Yahoo Finance  
* **Type:** Secondary observational data (downloaded via API/library)  
* **Index:** S&P 500 (^GSPC)  
* **Temporal coverage:** December 1927 – present  
* **Frequency:** Daily (trading-day observations only)  
* **Primary attributes:**
  * `Date` – trading date  
  * `Close`, `Open`, `High`, `Low` – price attributes  
  * `Volume` – trading volume  

This dataset is more complex at the schema level, containing multiple attributes describing each trading-day observation. It reflects the structure of financial market data, where observations exist only when markets are open. As a result, the notion of a “day” differs conceptually from the FRED dataset.

For this project, we focus on the `Close` attribute, as it represents the final aggregated market value for each trading session and is commonly used as a standardized measure in financial analysis.

### Dataset Integration

The two datasets will be integrated at the **schema level** and **record level** using the temporal attribute as the linkage key. While both datasets contain a date field, they exhibit **schema heterogeneity** and **temporal granularity mismatch**, requiring explicit alignment decisions rather than a direct join.

We define the S&P 500 dataset (trading-day observations) as the **reference relation**, and perform a **left join** by mapping Federal Funds Rate observations onto trading dates. This establishes a consistent observation unit: one record per trading day.

Our integration workflow follows standard data integration steps:  

- **Schema matching:** align `date` (FRED) with `Date` (Yahoo) and standardize formats 

- **Schema mapping:** define the integrated schema with selected attributes (`date`, `close`, `value`)  

- **Transformation:** convert both datasets into a common tidy structure  

- **Record-level integration:** join on date after preprocessing and cleaning :contentReference[oaicite:0]{index=0}  

To address the temporal mismatch, we will apply a **rule-based data fusion strategy**:
- For each trading day, assign the corresponding Federal Funds Rate observed on that date  
- Non-trading-day observations (weekends/holidays) will be excluded, creating a controlled **completeness reduction**

We also restrict the integrated dataset to the **overlapping temporal coverage (post-1954)** to ensure population consistency.

This approach introduces trade-offs:

- We lose some temporal completeness (dropped observations)

- We impose a market-centric definition of time

- We simplify the relationship between policy rates and market responses

However, this design produces a dataset that is **fit for use** for analyzing market behavior. Additional derived attributes (e.g., daily returns, rate changes) may be constructed to support downstream analysis, though these transformations may introduce further assumptions that will be documented.

---

## Timeline

The project follows a structured data curation workflow aligned with course concepts such as data acquisition, schema-level integration, data quality assessment, and reproducibility.

| Task | Description | Responsible | Target Completion | Status |
|-----|-------------|-------------|------------------|--------|
| Data Collection and Acquisition | Implement API-based data acquisition pipelines for FRED and Yahoo Finance; document source constraints, schema assumptions, and ensure reproducible retrieval. | Weimo Song | March 22, 2026 | Completed |
| Storage and Organization | Establish repository structure for raw and processed data; enforce consistent naming conventions and data organization to support downstream reproducibility. | Weimo Song | March 22, 2026 | Completed |
| Data Integration | Perform schema matching and mapping; construct an integrated time-series dataset through record-level integration on the temporal attribute. | Weimo Song | April 5, 2026 | Completed |
| Project Plan Revision | Revise project plan based on instructor feedback, refining terminology (e.g., schema heterogeneity, completeness) and specifying integration and data quality strategies. | Weimo Song & Andy Dong | April 12, 2026 | Completed |
| Interim Status Report | Document project progress, integration design decisions, and updates to the project plan based on feedback. | Weimo Song & Andy Dong | April 14, 2026 | Completed |
| Data Quality Profiling | Conduct data profiling to assess completeness, consistency, and temporal coverage; identify quality issues across integrated sources. | Weimo Song & Andy Dong | April 19, 2026 | In Progress |
| Data Cleaning | Apply rule-based data cleaning (error detection and repair) to address missingness, inconsistencies, and format standardization. | Weimo Song & Andy Dong | April 19, 2026 | Not Started |
| Data Analysis and Visualization | Perform exploratory data analysis and generate visualizations to examine relationships between variables. | Andy Dong | April 26, 2026 | Not Started |
| Metadata and Data Documentation | Develop metadata, data dictionary, and workflow documentation to support interpretability and reuse. | Andy Dong | May 3, 2026 | Not Started |
| Final Report | Finalize analysis, compile report, and publish reproducible project artifacts (data, scripts, documentation) via GitHub release. | Weimo Song & Andy Dong | May 3, 2026 | Not Started |

---

## Constraints

This project faces several constraints related to **schema heterogeneity**, **data quality**, and **data acquisition assumptions**, which directly affect the fitness-for-use of the integrated dataset.

### 1. Temporal Granularity Mismatch and Completeness

- The FRED dataset contains **calendar-day observations**, while the S&P 500 dataset contains only **trading-day observations**. This represents both **schema heterogeneity** (different temporal representations) and a **completeness issue** in the integrated dataset.

- **Our handling approach:**
  - We will adopt the S&P 500 trading calendar as the reference schema and perform a **schema-level alignment** by mapping Federal Funds Rate observations onto trading days.
  - We will conduct **data profiling** to quantify temporal completeness (e.g., number of dropped observations).

- **Impact:**
  - We will lose non-trading-day observations (weekends/holidays), reducing **population completeness**, but gain a dataset aligned with market activity, improving analytical validity.
  - This reflects the course principle that **“no neutral integration exists”**—we trade completeness for consistency.

### 2. Differences in Temporal Coverage

- The datasets have different historical coverage (1927 vs. 1954), creating a **temporal completeness constraint**.

- **Our handling approach:**
  - Restrict the integrated dataset to the overlapping period (post-1954).
  - Explicitly document this as a **population completeness reduction** and justify it based on analytical needs.

- **Impact:**
  - We lose earlier S&P 500 observations, limiting long-term analysis but ensuring consistent joint observations.

### 3. Data Acquisition and Source Assumptions

- Both datasets are **secondary observational data**, meaning we inherit structural and quality assumptions from external providers.

- **Our handling approach:**
  - Document API behavior, schema, and update frequency.
  - Preserve raw data snapshots to ensure **reproducibility and integrity**.

- **Impact:**
  - Reduces risk of future schema drift and improves transparency in data provenance.

### 4. Limited Variable Scope and Analytical Validity

- The dataset includes only two variables, which may limit explanatory power.

- **Our handling approach:**
  - Frame the dataset explicitly as **fit-for-purpose** for exploratory analysis rather than causal inference.
  - Use documentation to clarify scope limitations.

- **Impact:**
  - Ensures correct interpretation of results while maintaining project feasibility.

## Gaps

While the project plan establishes a clear workflow, several higher-level gaps remain that relate to the datasets, their interpretation, and our evolving understanding of the data lifecycle.

### 1. Dataset-level completeness and representativeness  

   - Although we identified temporal coverage differences, we have not fully assessed whether the integrated dataset adequately represents the underlying economic phenomena. In particular, limiting the data to overlapping periods and trading days may introduce systematic bias in what is observed versus omitted.  

   - **Plan:** we will evaluate dataset coverage using data quality dimensions such as population and temporal completeness, and document how integration choices shape what the dataset ultimately represents.

### 2. Dependence on externally structured data  

   - Both datasets are secondary data sources, meaning we inherit modeling decisions (e.g., how rates and prices are recorded, what counts as an observation) that may not fully align with our analytical goals.  

   - **Plan:** we will critically examine source assumptions and document how these affect schema design, integration choices, and interpretation.

### 3. Conceptual alignment between data and real-world phenomena  

   - The mapping between variables (interest rates and market index values) and the real-world concepts they represent is not fully specified. This creates a gap between the conceptual model and the data model.  

   - **Plan:** we will refine our conceptual understanding of entities, attributes, and relationships to ensure that the integrated dataset supports meaningful interpretation.

### 4. Knowledge gap across the full data lifecycle  

   - Some stages of the project (e.g., advanced integration methods, workflow automation, reproducibility, metadata) rely on concepts not yet covered in the course.  

   - **Plan:** we will iteratively refine our approach as new topics are introduced, allowing the project to evolve alongside our technical understanding.
