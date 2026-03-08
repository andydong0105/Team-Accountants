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

This project integrates two independent datasets that capture different aspects of the U.S. economic and financial system. One dataset represents **monetary policy conditions**, while the other represents **stock market performance**. Together, they provide complementary information that enables the analysis of relationships between interest rate policy and equity market behavior.

The two datasets can be meaningfully integrated because they share a common **temporal attribute (date)**, allowing them to be linked into a unified time-series dataset.

### Dataset 1: Federal Funds Rate (FRED)

The first dataset contains historical values of the **Federal Funds Effective Rate**, obtained from the [Federal Reserve Economic Data (FRED)](https://fred.stlouisfed.org/) database maintained by the Federal Reserve Bank of St. Louis. The Federal Funds Rate is the interest rate at which depository institutions lend reserve balances to other institutions overnight and is widely regarded as the central policy rate used by the Federal Reserve to influence economic activity.

Key characteristics of this dataset include:

* **Source:** Federal Reserve Economic Data (FRED)
* **Series name:** Federal Funds Effective Rate (DFF)
* **Temporal coverage:** July 1954 – present
* **Frequency:** Daily observations
* **Primary variables:**
  * `date` – observation date
  * `value` – federal funds effective rate (percentage)

This dataset represents the **monetary policy environment** and provides a long historical record of interest rate movements. Because it is distributed through the FRED API, it can be programmatically retrieved, ensuring reproducibility and allowing the dataset to be updated automatically when new observations are released.

### Dataset 2: S&P 500 Market Data (Yahoo Finance)

The second dataset contains historical data for the **S&P 500 index**, retrieved from [Yahoo Finance](https://finance.yahoo.com/), a widely used public source for financial market data*. The S&P 500 index tracks the performance of 500 large publicly traded U.S. companies and is commonly used as a benchmark for overall stock market performance.

Key characteristics of this dataset include:

* **Source:** Yahoo Finance  
* **Index:** S&P 500 (^GSPC)  
* **Temporal coverage:** December 1927 – present  
* **Frequency:** Daily trading-day observations  
* **Primary variables:**
  * `Date` – trading date
  * `Close` – closing value of the index
  * `Open` – opening value of the index
  * `High` – highest value reached during the trading day
  * `Low` – lowest value reached during the trading day
  * `Volume` – total trading volume for the day

For this project, we focus primarily on the **closing index value** because it reflects the final market consensus after a full trading session. Closing prices are widely used in financial analysis and economic research since they incorporate all intraday information and are the standard reference for computing daily returns and long-term market trends.

*Compared to the Federal Funds Rate series from FRED used in HW1, which only covers data for the last 10 years due to restrictions imposed by FRED's agreement with S&P Dow Jones Indices LLC, Yahoo offers a much broader timeframe, starting from December 1927.

### Dataset Integration

The two datasets are integrated using their shared **date attribute**, allowing them to be aligned as a single time-series dataset. Because the Federal Funds Rate dataset includes observations for all calendar days while the stock market dataset includes only trading days, the integration process will involve aligning dates and handling differences in temporal frequency. The resulting integrated dataset will allow us to analyze how changes in interest rates correspond to movements in stock market values over time.

---

# Timeline

# Constraints

# Gaps

# Conclusion
