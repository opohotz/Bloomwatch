# Bloomwatch
NASA Space Apps Project - Chicago
Created: 10/04/2025

![Bloomwatch UI](https://github.com/opohotz/Bloomwatch/blob/main/Test%20Files/bloomwatch-UI.png)

🌸 BloomWatch

BloomWatch is a data analysis project that examines long-term plant bloom trends using large-scale NASA remote sensing data. By leveraging batch workflows and time-series analysis, this project surfaces shifts in seasonal bloom timing across regions—highlighting measurable climate-driven changes in plant behavior.

📌 Project Overview

BloomWatch processes multi-year vegetation datasets from NASA AppEEARS to analyze how plant bloom cycles have shifted over time. The project focuses on identifying seasonal patterns and regional differences in bloom onset, with an emphasis on detecting climate-related trends.

Key finding:
🌱 Northern regions show an average ~2-week earlier bloom onset over recent years, aligning with broader climate change patterns.

🧠 Key Objectives

Process large remote sensing datasets efficiently using batch workflows

Analyze seasonal and regional bloom timing across multiple years

Visualize trends to detect shifts in plant phenology

Correlate observed changes with known climate patterns

🛠️ Tech Stack

Python – core data processing and analysis

Pandas – data cleaning, aggregation, and time-series analysis

NASA AppEEARS – remote sensing data retrieval

📊 Methodology

Data Collection

Retrieved multi-year vegetation and phenology data from NASA AppEEARS

Used batch processing workflows to handle large datasets efficiently

Data Processing

Cleaned and normalized raw satellite data using Pandas

Aggregated bloom indicators by season, year, and geographic region

Analysis

Compared bloom onset timing across years and regions

Identified long-term trends and anomalies in northern vs. southern regions

📈 Results

Clear seasonal bloom patterns emerged across regions

Northern regions exhibited an average 2-week earlier bloom onset

Trends are consistent with existing climate change research on warming temperatures

🚀 How to Run
# Clone the repository
git clone https://github.com/opohotz/BloomWatch.git
cd BloomWatch

# Install dependencies
pip install -r requirements.txt

# Run analysis scripts
cd Backend
python app.py

🌍 Why This Matters

Understanding shifts in plant bloom timing is critical for:

Climate change research

Agriculture and ecosystem planning

Environmental monitoring and policy

BloomWatch demonstrates how satellite data and data science tools can be combined to extract real-world environmental insights.

📌 Future Improvements

Integrate temperature and precipitation datasets for deeper correlation analysis

Expand analysis to additional geographic regions

Automate AppEEARS data retrieval via API workflows
