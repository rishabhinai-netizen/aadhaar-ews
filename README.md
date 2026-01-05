# 🚨 Aadhaar Early Warning System (EWS)

**UIDAI Data Hackathon 2026 Submission**

A National Early Warning System for Aadhaar operations that detects emerging risk trends at the district level using privacy-preserving, aggregated data analytics.

---

## 🎯 Problem Statement

UIDAI needs to identify districts that are **quietly moving towards operational risk** - not just those with obvious spikes, but those showing concerning trends that require proactive intervention.

Traditional threshold-based alerts miss:
- Gradual deterioration patterns
- Districts moving from stable to at-risk
- Combinations of moderate issues across multiple metrics
- Seasonal and geographic context

## 💡 Our Solution

The Aadhaar EWS is a **comprehensive risk monitoring system** that:

✅ **Detects trends**, not just spikes (4-week rolling analysis)  
✅ **Preserves privacy** (district-level aggregation only)  
✅ **Provides forecasts** (2-week ahead predictions)  
✅ **Enables comparison** (peer benchmarking by activity tier)  
✅ **Explains decisions** (transparent methodology and thresholds)  

---

## 🏗️ Architecture

```
Raw Data (Daily, PIN-level)
         ↓
PIN-Based Geographic Canonicalization
         ↓
Weekly District Aggregation (Age-Groups Preserved)
         ↓
Advanced Analytics Pipeline
         ├── Data-Driven Severity Scoring
         ├── Statistical Anomaly Detection
         ├── Trend Analysis (4-week rolling)
         ├── Risk Classification
         └── Forecasting (2-week ahead)
         ↓
Interactive Streamlit Dashboard
```

---

## 📊 Key Features

### 1. **Data-Driven Severity Scoring**
Instead of arbitrary weights (20-30-50), we compute weights based on **coefficient of variation**:
- Enrolment: 34.07%
- Demographic: 35.61%
- Biometric: 30.32%

**Why?** Metrics with higher variation carry more signal and should be weighted more.

### 2. **Statistical Anomaly Detection**
Uses **Isolation Forest** algorithm to detect unusual patterns that simple thresholds miss.

### 3. **Trend-Based Early Warning**
Analyzes 4-week trends to identify:
- `accelerating_up` - Rapid worsening
- `rising` - Gradual increase
- `stable` - Steady state
- `declining` - Improving
- `accelerating_down` - Rapid improvement

### 4. **Explicit Risk Categories**

| Category | Criteria | Action |
|----------|----------|--------|
| **Critical** | Severity ≥ 90 OR (Anomaly + Rising) | Immediate intervention |
| **Emerging Risk** | Severity ≥ 75 AND Rising | Monitor closely |
| **Watchlist** | Severity ≥ 60 OR Anomaly | Regular monitoring |
| **Stable** | All others | Routine operations |

### 5. **Peer Benchmarking**
Districts grouped by:
- **Activity Tier**: Low/Medium-Low/Medium-High/High
- **Demographic Profile**: Child-focused vs Adult-focused

### 6. **Age-Group Granularity**
Unlike approaches that lose age detail, we preserve:
- Enrolment: 0-5, 5-17, 18+ years
- Demographic Updates: 5-17, 18+ years
- Biometric Updates: 5-17, 18+ years

---

## 🗂️ Repository Structure

```
aadhaar-ews/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
│
├── data/                           # Generated analytics (privacy-safe)
│   ├── ews_weekly_district_enhanced.csv
│   ├── district_forecasts.csv
│   ├── district_profiles.csv
│   ├── peer_benchmarks.csv
│   ├── geo_cleaning_summary.csv
│   ├── weight_justification.csv
│   └── top_critical_districts.csv
│
├── utils/                          # Helper modules (to be added)
│   ├── data_processing.py
│   ├── analytics.py
│   └── visualization.py
│
├── docs/                           # Documentation
│   └── methodology.md
│
└── notebooks/                      # Analysis notebooks
    ├── 01_data_exploration.ipynb
    ├── 02_analytics_development.ipynb
    └── 03_validation.ipynb
```

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/[your-username]/aadhaar-ews.git
cd aadhaar-ews

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

---

## 📈 Dashboard Pages

### 1. 🏠 National Overview
- Key metrics (Critical/Emerging/Watchlist districts)
- Risk distribution visualization
- Dominant signal analysis
- Historical trends

### 2. ⚠️ Early Warning Signals
- Districts with accelerating risk trends
- State-wise breakdown
- Detailed district list

### 3. 🗺️ Geospatial Risk Map
- State-level risk summary
- *Note: Full district choropleth requires india_districts.geojson*

### 4. 📊 District Deep Dive
- Individual district analysis
- Severity trend over time
- Activity breakdown by type
- Age-group distribution

### 5. 🔮 Forecasts & Predictions
- 2-week ahead risk forecasts
- Districts likely to become high-risk
- Proactive intervention planning

### 6. 🔬 Data Quality & Methodology
- Geographic canonicalization documentation
- Severity scoring explanation
- Risk classification thresholds
- Complete transparency

### 7. 📖 About & Ethics
- Privacy protections
- Ethical considerations
- Limitations and biases
- Contact information

---

## 🔬 Methodology

### Geographic Canonicalization

**Challenge**: Aadhaar datasets had inconsistent state/district names:
- "Andaman & Nicobar Islands" vs "Andaman and Nicobar Islands"
- "Dadra & Nagar Haveli" vs "Dadra and Nagar Haveli and Daman and Diu"

**Solution**: Use **PIN code as single source of truth**
- Merge with official India Post PIN directory
- Override Aadhaar text fields with canonical names
- Document all changes in `geo_cleaning_summary.csv`

**Impact**:
- Reduced state variations from 55-71 → 36 standardized states
- Enabled accurate map rendering
- Prevented duplicate districts in analytics

### Severity Scoring

```python
# Data-driven weights (not arbitrary)
weights = coefficient_of_variation / sum(coefficients)

# Percentile-based scoring (within-week comparison)
severity_score = (
    enrol_percentile × weight_enrol +
    demo_percentile × weight_demo +
    bio_percentile × weight_bio
)
```

### Anomaly Detection

Uses `sklearn.ensemble.IsolationForest`:
- Contamination rate: 10%
- Applied only to districts with ≥5 weeks of data
- Flags unusual patterns for investigation

### Trend Analysis

```python
# 4-week rolling average
severity_ma4 = rolling(severity_score, window=4).mean()

# Week-over-week change
severity_change = severity_score.diff()

# Momentum (2nd derivative)
severity_momentum = severity_change.diff()
```

### Forecasting

Simple moving average with trend adjustment:
```python
forecast = mean(last_4_weeks)

if trend == 'rising':
    forecast *= 1.1  # 10% increase
elif trend == 'declining':
    forecast *= 0.9  # 10% decrease
```

*Note: Can be enhanced with ARIMA/Prophet for production*

---

## 🔒 Privacy & Ethics

### Privacy Protections

✅ **No Individual Records**: All data aggregated to district-week level  
✅ **No PIN Exposure**: PIN codes not shown in outputs or visualizations  
✅ **Minimum Aggregation**: District level (populations in thousands)  
✅ **Anonymization**: Cannot reverse-engineer individual transactions  

### Ethical Considerations

**Bias Prevention**:
- Data-driven weights avoid subjective bias
- Peer comparison accounts for district characteristics
- Multi-metric approach prevents single-dimension focus

**Transparency**:
- All thresholds documented
- Complete methodology disclosed
- Geo-cleaning process explained

**Fairness**:
- Districts compared to similar peers
- Activity level considered in benchmarking
- Context-aware risk assessment

---

## 📊 Data Coverage

| Dataset | Records | Districts | Weeks | Date Range |
|---------|---------|-----------|-------|------------|
| Enrolment | 1,006,029 | 1,084 | 27 | Mar-Dec 2025 |
| Demographic | 2,071,700 | 1,140 | 21 | Mar-Dec 2025 |
| Biometric | 1,861,108 | 1,132 | 21 | Mar-Dec 2025 |
| **Combined** | **4,938,837** | **1,181** | **28** | **Mar-Dec 2025** |

---

## 🎓 Key Insights

### Current Status (Latest Week)

- **1,181 districts** monitored
- **2,318 districts** in Critical category (9.3%)
- **1,148 districts** in Emerging Risk (4.6%)
- **3,131 anomalies** detected (12.6% of all district-weeks)

### Dominant Signals

- **Enrolment**: 36.6% of districts
- **Demographic**: 33.3% of districts
- **Biometric**: 30.1% of districts

### Age Demographics

- **High child-focus districts**: 546 (46.2%)
- Districts with child ratio > 35%

---

## 🛠️ Technical Stack

- **Python 3.9+**
- **Streamlit** - Interactive dashboard
- **Pandas & NumPy** - Data processing
- **Plotly** - Visualizations
- **Scikit-learn** - Anomaly detection
- **SciPy** - Statistical analysis

---

## 🚧 Future Enhancements

### Short Term
1. Add district-level choropleth map (requires geojson)
2. Implement ARIMA forecasting for better predictions
3. Add export functionality (PDF reports)

### Medium Term
1. Real-time data ingestion pipeline
2. Alert notification system
3. Resource allocation optimizer
4. Mobile app for field officers

### Long Term
1. Machine learning risk prediction
2. Root cause analysis (correlation with external factors)
3. Intervention impact tracking
4. API for integration with existing UIDAI systems

---

## 🏆 Competitive Advantages

| Feature | Traditional Approaches | Our EWS |
|---------|----------------------|---------|
| Detection | Threshold-based spikes | Trend-based early warning |
| Context | None | Peer benchmarking |
| Transparency | Black box | Fully explainable |
| Forecasting | Reactive | 2-week ahead predictions |
| Age Insights | Lost in aggregation | Preserved granularity |
| Privacy | Often compromised | Privacy-by-design |
| Weights | Arbitrary (20-30-50) | Data-driven (34-36-30) |

---

## 📝 Citation

If you use this work, please cite:

```
Aadhaar Early Warning System (EWS)
UIDAI Data Hackathon 2026
[Your Team Name]
https://github.com/[your-username]/aadhaar-ews
```

---

## 📞 Contact

**Team Lead**: [Your Name]  
**Email**: [Your Email]  
**Institution**: [Your Institution]  

For queries about methodology or collaboration opportunities.

---

## 📄 License

This project is submitted for the UIDAI Data Hackathon 2026. 

The code is open-source under MIT License, but the data remains property of UIDAI and should not be redistributed.

---

## 🙏 Acknowledgments

- **UIDAI** for providing anonymized datasets
- **NIC & MeitY** for organizing the hackathon
- **India Post** for PIN directory
- Open-source community for tools (Streamlit, Plotly, scikit-learn)

---

**Built with ❤️ for better governance and citizen services**
