## 1. Overview

This Interim Status Report provides an update on the current progress of our project, focusing on both completed work and planned next steps. The primary purpose of this report is to document how the project has evolved since the initial project plan, particularly in response to instructor feedback, and to demonstrate progress through concrete artifacts stored in our repository.

To date, we have completed the data acquisition, storage and organization, and data integration stages, and have implemented a reproducible workflow supported by scripts and structured data outputs. We have also revised the project plan to better align with course concepts and methodological expectations.

This report includes a summary of revisions to the project plan, a detailed update on task progress with references to repository artifacts, a discussion of key challenges encountered, and individual contributions from each team member.
---
---
## 2. Revisions to the Project Plan

Based on the feedback received for Milestone 2, we made several targeted revisions to our project plan to improve conceptual clarity, methodological precision, and alignment with course terminology. Overall, the revised plan shifts from a high-level outline toward a more structured and theoretically grounded design.

---

### 2.1 [Constraints](ProjectPlan.md#constraints)

The original plan identified differences in temporal frequency between datasets but described them in general terms. Following instructor feedback, we reframed this issue explicitly as both a **schema heterogeneity problem** and a **data quality issue**, specifically a completeness problem.

We also refined our approach by moving from a vague notion of “aligning dates” to a clearly defined integration strategy. In particular, we now explicitly recognize that any integration decision requires trade-offs, such as the loss of certain observations when enforcing a consistent temporal unit.

This revision improves the plan by aligning it with course concepts and by making the implications of design choices transparent.

---

### 2.2 [Gaps](ProjectPlan.md#gaps)

The initial version of the Gaps section focused primarily on analytical uncertainties. Based on feedback, we revised this section to emphasize **dataset-level gaps** and areas requiring additional input.

We reframed gaps in terms of:
- completeness and representativeness of the integrated dataset  
- dependence on externally structured data sources  
- conceptual alignment between data and real-world phenomena  

We also introduced a **knowledge gap dimension**, acknowledging that parts of the workflow depend on course topics that have not yet been fully covered.

This revision improves the plan by shifting the focus from analysis to data curation, which better reflects the objectives of the project.

---

### 2.3 [Datasets](ProjectPlan.md#datasets)

The dataset descriptions were revised to incorporate course concepts related to data acquisition and representation. Both datasets are now explicitly framed as **secondary observational data**, highlighting that their structure and quality are inherited from external sources.

We also strengthened the schema-level description by conceptualizing each dataset as a **time-series relation** indexed by a temporal attribute. In addition, we clarified assumptions about what constitutes a valid observation (e.g., trading days versus calendar days).

These changes improve transparency and provide a clearer foundation for subsequent integration decisions.

---

### 2.4 [Dataset Integration](ProjectPlan.md#dataset-integration)

This section underwent the most substantial revision. The original version described integration at a high level, without clearly specifying how heterogeneity would be resolved.

In the revised plan, we outline a concrete integration strategy grounded in course concepts, including schema matching, schema mapping, and record-level integration. We also explicitly acknowledge the **temporal granularity mismatch** and its implications for completeness.

Rather than treating integration as a purely technical step, we now frame it as a design decision involving trade-offs between consistency and data retention. We also anticipate the need for derived attributes to support downstream analysis.

This revision strengthens the methodological rigor of the project and aligns it with the data integration framework presented in class.

---

### 2.5 [Updated Timeline](ProjectPlan.md#timeline)

The timeline was revised to better reflect actual progress and improve clarity. We introduced a **Status column** to distinguish between completed, in-progress, and not-started tasks, and updated target completion dates accordingly.

We also added a new task (“Project Plan Revision”) to explicitly capture work completed in response to instructor feedback.

These changes make the timeline more transparent and better aligned with the iterative nature of the project.

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
---


### 3.1 Completed Tasks

#### Data Collection and Acquisition

We implemented a reproducible data acquisition pipeline using Python, formalized in [`acquire_data.py`](acquire_data.py). This script programmatically retrieves the Federal Funds Rate from the FRED API and S&P 500 data from Yahoo Finance, and explicitly addresses the trade-off between reproducibility and timeliness.

In particular, we introduced a dual-mode design:
- a **frozen mode** (default), which fixes the observation end date at 2026-03-22 to ensure reproducibility  
- a **live mode**, which allows retrieval of the most recent data  

This design directly responds to course requirements around reproducibility and ensures that the dataset used for analysis can be consistently reconstructed.

The script also preserves both **source-native data** and **tabular representations**, producing the following artifacts in [`data/raw/`](data/raw/):

- [`fred_dff_raw.json`](data/raw/fred_dff_raw.json) (raw API response)

- [`fred_dff.csv`](data/raw/fred_dff.csv) (normalized tabular form)

- [`sp500_raw.csv`](data/raw/sp500_raw.csv)

To support data integrity, we compute SHA-256 checksums stored in [`CHECKSUMS.sha256`](data/raw/CHECKSUMS.sha256), enabling verification of data consistency across runs.

#### Storage and Organization

We formalized the storage layer using [`storage_and_organization.py`](storage_and_organization.py), which establishes a clear separation between raw, processed, and output data. This reflects best practices in data management and supports reproducibility and provenance tracking.

The repository now follows a structured layout:

- `data/raw/` for source-preserving data  

- `data/processed/` for transformed and integrated datasets  

- `data/output/` for downstream analysis results  

We also generated supporting documentation:

- [`docs/DATA_STRUCTURE.md`](docs/DATA_STRUCTURE.md), describing directory design and naming conventions  

- [`docs/file_inventory.csv`](docs/file_inventory.csv), listing all files and metadata  

This step ensures that all data artifacts are consistently organized and traceable throughout the workflow.

#### Data Integration

We implemented the integration pipeline in [`data_integration.py`](data_integration.py), explicitly addressing the **schema heterogeneity** and **temporal granularity mismatch** identified in the project plan.

Rather than performing a naive join, we defined a clear integration strategy:

- using S&P 500 trading days as the **reference relation**  

- performing schema matching between `date` and `Date`  

- restricting both datasets to the **overlapping temporal coverage (post-1954)**  

- applying a **left join** to construct one observation per trading day  

This design directly resolves the completeness issue by making an explicit trade-off: non-trading-day Federal Funds observations are excluded to maintain a consistent observation unit.

The resulting dataset is stored at:

- [`data/processed/integrated_fred_sp500.csv`](data/processed/integrated_fred_sp500.csv)

We also generate derived variables (e.g., daily returns, rate changes) to support future analysis.

To ensure transparency, we document the full integration process and its implications in:

- [`docs/INTEGRATION_SUMMARY.md`](docs/INTEGRATION_SUMMARY.md)

This file explicitly reports temporal coverage, row counts, and the impact of integration decisions on completeness.

#### Project Plan Revision

Following instructor feedback, we revised the project plan to improve both conceptual clarity and methodological precision. The updated plan is available at:

- [`ProjectPlan.md`](ProjectPlan.md)

Key revisions include:
- reframing temporal differences as **schema heterogeneity** and **data quality (completeness) issues**  
- specifying a concrete integration strategy rather than a generic “alignment” approach  
- explicitly discussing trade-offs such as observation loss  
- revising gaps to focus on dataset-level limitations and knowledge gaps  

These changes align the project more closely with course terminology and expectations.

#### Interim Status Report Preparation

We prepared this report (`StatusReport.md`) as part of Milestone 3 to consolidate progress and demonstrate alignment between planned and executed work.

The report integrates:
- updated project plan revisions  
- concrete implementation artifacts (scripts, datasets, documentation)  
- a structured evaluation of challenges and next steps  

As a version-controlled document in the repository, it serves both as a deliverable and as documentation of the project’s current state.

---

### 3.2 Remaining Tasks

#### Data Quality Profiling

We are currently in progress on data profiling. The next step is to systematically assess the integrated dataset using data quality dimensions such as completeness, consistency, and temporal coverage, and to quantify missingness introduced by the integration process.

#### Data Cleaning

Data cleaning has not yet been implemented. Based on profiling results, we will apply rule-based cleaning methods (error detection and repair) to address missing values, inconsistencies, and format standardization across variables.

#### Data Analysis and Visualization

Analytical work has not yet begun. We plan to conduct exploratory analysis, including computing trends and correlations, and generating visualizations to examine relationships between interest rates and market performance.

#### Metadata and Data Documentation

Comprehensive metadata has not yet been completed. We will develop a data dictionary and document variables, transformations, and workflow steps to support interpretability and reuse.

#### Final Report

The final report has not yet been started. Future work will focus on integrating all components—data, analysis, and documentation—into a fully reproducible and well-structured final deliverable.
---
---
## 4. Challenges and How We Are Addressing Them

Throughout the project, we have encountered several challenges related to data integration, data quality, and the evolving nature of the workflow. These challenges are closely tied to concepts discussed in the course, and we outline both their implications and our planned responses below.

### Temporal Granularity Mismatch and Completeness

The two datasets operate on different temporal granularities: the Federal Funds Rate includes calendar-day observations, while the S&P 500 dataset includes only trading days. This creates a **completeness issue** when integrating the datasets, as some observations cannot be directly aligned.

This affects the structure of the integrated dataset by forcing a choice of observation unit, which in turn determines which data points are retained or discarded.  
To address this, we define trading days as the reference relation and explicitly accept the resulting loss of non-trading-day observations. This decision is documented as a trade-off between completeness and analytical consistency.

### Differences in Temporal Coverage

The datasets differ in their historical coverage, with S&P 500 data starting in 1927 and Federal Funds Rate data starting in 1954. This creates a **population completeness constraint**, as only the overlapping time period can be used for integration.

This limitation reduces the number of usable observations and constrains the temporal scope of analysis.  
We address this by restricting the integrated dataset to the overlapping period and clearly documenting this decision, ensuring that downstream analysis is based on a consistent and well-defined population.

### Dependence on External Data Sources

Both datasets are acquired from external providers, making them **secondary observational data**. As a result, we inherit assumptions about data structure, definitions of observations, and potential inconsistencies.

This dependence introduces risks related to data quality, schema changes, and reproducibility over time.  
To mitigate these issues, we preserve raw data files, document acquisition methods, and use checksums to verify data integrity. These steps help ensure that the data pipeline remains transparent and reproducible.

### Knowledge Gap Across the Data Lifecycle

Some stages of the project, such as advanced data cleaning, workflow automation, and reproducibility practices, depend on course topics that have not yet been fully covered.

This creates uncertainty in how certain steps should be optimally implemented.  
We address this by treating the project as an iterative process, refining our methods as new concepts are introduced in the course. This approach allows us to progressively improve the workflow while aligning with best practices introduced later in the semester.
---
---
## 5. Team Member Contribution Summaries

### Weimo Song

Weimo Song was primarily responsible for the data pipeline development and early-stage workflow design. He implemented the data acquisition script (`acquire_data.py`) to retrieve data from FRED and Yahoo Finance, including reproducibility controls and integrity checks. He also developed the storage and organization structure (`storage_and_organization.py`) and created the data integration pipeline (`data_integration.py`). In addition, Weimo contributed the revision of the project plan by incorporating instructor feedback and aligning the methodology with course concepts.

### Andy Dong

Andy Dong contributed to the overall project design and documentation, with a focus on downstream analysis and interpretation. He collaborated on revising the project plan, particularly in refining the problem framing and integration logic. Andy is responsible for upcoming tasks including data analysis, visualization, and metadata documentation. He also contributed to structuring the interim report and ensuring clarity and consistency across written components.
