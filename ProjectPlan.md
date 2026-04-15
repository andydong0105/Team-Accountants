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

The project will be completed in several stages corresponding to the data curation workflow required for the final deliverables. Tasks are scheduled so that each stage builds on the previous one while aligning with the official course milestones.

| Task | Description | Responsible | Target Completion |
|-----|-------------|-------------|------------------|
| Data Collection and Acquisition | Develop scripts to programmatically retrieve the Federal Funds Rate from FRED and S&P 500 data from Yahoo Finance. Document the acquisition process and verify that the datasets can be reproducibly retrieved. | Weimo Song | March 15, 2026 |
| Storage and Organization | Organize raw datasets within the repository and establish consistent folder structures and naming conventions for raw data, processed data, and outputs. | Weimo Song | March 22, 2026 |
| Data Integration | Integrate the two datasets using the shared `date` attribute and construct a unified time-series dataset. Document the integration logic and schema alignment. | Weimo Song | March 26, 2026 |
| Interim Status Report | Prepare and submit the interim project report summarizing the datasets, integration progress, and preliminary observations. | Weimo Song & Andy Dong | March 31, 2026 |
| Data Quality Profiling | Examine the integrated dataset to identify potential quality issues such as missing observations, inconsistent temporal coverage, or frequency mismatches between sources. | Weimo Song & Andy Dong | April 5, 2026 |
| Data Cleaning | Implement scripts to address identified data quality issues, standardize variable formats, and prepare the dataset for analysis. | Weimo Song & Andy Dong | April 12, 2026 |
| Data Analysis and Visualization | Conduct exploratory analysis of the integrated dataset and generate visualizations illustrating the relationship between the Federal Funds Rate and S&P 500 performance. | Andy Dong | April 19, 2026 |
| Metadata and Data Documentation | Prepare dataset documentation, including variable descriptions, data dictionary elements, and explanations of the integration and analysis workflow. | Andy Dong | April 26, 2026 |
| Final Report  | Compile the final project report, finalize visualizations and analysis outputs, and ensure the repository includes all required artifacts and reproducibility documentation. Publish the final GitHub release containing the report, datasets, scripts, and documentation required to reproduce the project workflow. | Weimo Song & Andy Dong | May 3, 2026 |

---

## Constraints

Several limitations and challenges may affect this project, particularly those related to differences in dataset structure, temporal coverage, and the nature of financial time-series data.

1. **Differences in temporal frequency between the datasets**

   - The Federal Funds Rate dataset from FRED includes observations for all calendar days, whereas the S&P 500 dataset from Yahoo Finance includes only **trading days** when financial markets are open. This discrepancy may lead to missing values or misaligned observations when integrating the datasets, requiring careful handling during the data integration and cleaning stages.

2. **Differences in temporal coverage**

   - The S&P 500 dataset from Yahoo Finance extends back to 1927, while the Federal Funds Rate series from FRED begins in 1954. As a result, the integrated dataset will necessarily be restricted to the overlapping time period beginning in 1954. This reduces the historical range available for analysis.

3. **Technical constraints related to programmatic data acquisition**

   - Both datasets are retrieved through external data services, and changes in API behavior, data formats, or access policies could affect the ability to automatically retrieve the data in the future. Ensuring that acquisition scripts remain robust and well documented will therefore be important for maintaining reproducibility.

4. **Limited variable scope**

   - The project currently focuses on two key variables—interest rates and stock market index values—which may not capture all factors influencing stock market movements. Macroeconomic variables such as inflation, unemployment, or economic growth may also affect market performance. Additionally, major events such as financial crises and geopolitical developments can also cause market volatility, although these effects are often difficult to quantify and systematically model. However, incorporating additional datasets is beyond the current scope of this project.

---

## Gaps

While the current project plan outlines the main workflow and datasets, several areas remain open for further refinement as the project progresses.

1. **Choice of analytical methods**

   - At this stage, the project primarily focuses on integrating datasets and performing exploratory analysis. Additional input may be needed to determine whether more advanced analytical approaches—such as correlation analysis, lagged comparisons, or trend analysis—should be used to better understand the relationship between interest rates and stock market performance.

2. **Potential need for additional economic indicators**

   - The current dataset includes only the Federal Funds Rate and the S&P 500 index. During the analysis stage, it may become necessary to incorporate additional macroeconomic variables (such as inflation, unemployment, or recession indicators) if the relationship between interest rates and market performance cannot be adequately interpreted using the existing variables.

3. **Representativeness of the S&P 500**

   - The project uses the S&P 500 index as a proxy for overall U.S. stock market performance. However, the S&P 500 primarily tracks large-cap publicly traded companies and may not fully represent the performance of small and medium-sized enterprises (SMEs) or the broader U.S. business landscape. Therefore, the observed relationship between interest rate changes and stock market movements may majorly reflect trends specific to large firms rather than the entire economy. In the analysis phase, we may need to include other indices, such as the S&P SmallCap 600 and the S&P MidCap 400 indices, to gain a more comprehensive understanding of the relationship between interest rates and stock market performance.

4. **Interpretation of economic relationships**

   - Financial markets are influenced by many interacting factors, and interpreting observed patterns between interest rates and stock market movements may require additional economic context. Further input from economic literature or domain knowledge may therefore be needed when interpreting the results of the analysis.
