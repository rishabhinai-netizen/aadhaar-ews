# Aadhaar EWS Methodology Documentation

## Table of Contents
1. [Data Processing Pipeline](#data-processing-pipeline)
2. [Geographic Canonicalization](#geographic-canonicalization)
3. [Severity Scoring](#severity-scoring)
4. [Anomaly Detection](#anomaly-detection)
5. [Trend Analysis](#trend-analysis)
6. [Risk Classification](#risk-classification)
7. [Forecasting](#forecasting)
8. [Validation & Testing](#validation--testing)

---

## Data Processing Pipeline

### Stage 1: Data Ingestion
- Load three datasets: Enrolment, Demographic Updates, Biometric Updates
- Parse dates (DD-MM-YYYY format)
- Validate data types and ranges

### Stage 2: Geographic Canonicalization
- Load official India Post PIN directory
- For each record in Aadhaar datasets:
  - Look up PIN code in directory
  - Replace state and district with canonical values
  - Flag records with missing PINs (retained with original values)

### Stage 3: Weekly Aggregation
- Convert daily data to weekly (Monday-start weeks)
- Group by: week + state + district
- Preserve age-group breakdowns:
  - Enrolment: 0-5, 5-17, 18+
  - Demographic: 5-17, 18+
  - Biometric: 5-17, 18+

### Stage 4: Dataset Merging
- Outer join on (week, state, district)
- Fill missing values with 0
- Result: Single unified dataset with all metrics

---

## Geographic Canonicalization

### Problem
Aadhaar datasets contained:
- Spelling variations ("Andaman & Nicobar" vs "Andaman and Nicobar Islands")
- Inconsistent formatting
- Administrative changes (Dadra merging with Daman and Diu)

These cause:
- Map rendering failures
- Duplicate district counts
- Broken time-series analysis

### Solution: PIN-Based Single Source of Truth

```python
# Pseudocode
for record in aadhaar_data:
    canonical_state, canonical_district = pin_directory.lookup(record.pincode)
    
    if found:
        record.state = canonical_state
        record.district = canonical_district
    else:
        # Keep original, flag as "unvalidated"
        record.geo_validation_flag = "missing_pin"
```

### Impact

| Metric | Before | After |
|--------|--------|-------|
| State variations | 55-71 | 36 |
| District variations | 983-1140 | 741 standardized |
| Missing PINs | 841-966 | Retained with flag |
| Map rendering | Failed | Success |

---

## Severity Scoring

### Objective
Create a single composite metric (0-100) representing district operational stress.

### Traditional Approach (Problematic)
Arbitrary weights: Enrolment=20%, Demographic=30%, Biometric=50%

**Problems**:
- No justification
- Doesn't adapt to data
- Ignores relative importance

### Our Approach: Data-Driven Weights

**Step 1**: Calculate Coefficient of Variation (CV)
```
CV_metric = std_dev(metric) / mean(metric)
```

**Step 2**: Normalize to sum to 1.0
```
weight_metric = CV_metric / sum(all_CVs)
```

**Rationale**: Metrics with higher variation carry more signal and should be weighted more.

**Results**:
- Enrolment: 34.07% (CV-based)
- Demographic: 35.61%
- Biometric: 30.32%

### Scoring Formula

```python
# For each district in each week:

# Step 1: Compute percentile ranks (0-100) within that week
enrol_pct = percentile_rank(district.enrol_total, all_districts_this_week)
demo_pct = percentile_rank(district.demo_total, all_districts_this_week)
bio_pct = percentile_rank(district.bio_total, all_districts_this_week)

# Step 2: Weighted combination
severity_score = (
    enrol_pct × 0.3407 +
    demo_pct × 0.3561 +
    bio_pct × 0.3032
)
```

### Properties
- **Range**: 0-100
- **Interpretation**: Higher = more stress relative to peers
- **Temporal**: Recalculated each week (accounts for overall activity changes)
- **Explainable**: Can decompose into components

---

## Anomaly Detection

### Objective
Identify districts with unusual patterns that severity score alone might miss.

### Algorithm: Isolation Forest

**Why Isolation Forest?**
- Works well on multivariate data
- Doesn't assume normal distribution
- Computationally efficient
- Provides anomaly scores

### Implementation

```python
from sklearn.ensemble import IsolationForest

# For each district with ≥5 weeks of data:
district_features = [enrol_total, demo_total, bio_total]

model = IsolationForest(
    contamination=0.1,  # Expect 10% anomalies
    random_state=42
)

is_anomaly = model.fit_predict(district_features) == -1
anomaly_score = model.score_samples(district_features)
```

### What Counts as Anomaly?
- Unusual combination of high/low values across metrics
- Outliers in multivariate space
- Districts behaving differently from historical norm

### Integration with Risk
Anomalies trigger **higher risk classification** when combined with rising trends.

---

## Trend Analysis

### Objective
Identify not just current state, but *direction of change*.

### Metrics Computed

#### 1. 4-Week Moving Average
```python
severity_ma4 = rolling(severity_score, window=4, min_periods=2).mean()
```
Smooths out weekly noise.

#### 2. Week-over-Week Change
```python
severity_change = severity_score - severity_score.shift(1)
```

#### 3. Momentum (2nd Derivative)
```python
severity_momentum = severity_change - severity_change.shift(1)
```
Detects acceleration/deceleration.

### Trend Classification

| Trend | Condition | Interpretation |
|-------|-----------|----------------|
| `accelerating_up` | change > 5 AND momentum > 0 | Rapidly worsening |
| `rising` | change > 3 | Gradually increasing |
| `stable` | -3 ≤ change ≤ 3 | Steady state |
| `declining` | change < -5 OR momentum < 0 | Improving |
| `accelerating_down` | change < -5 AND momentum < 0 | Rapidly improving |

### Thresholds Rationale
- Based on severity score range (0-100)
- Change > 5 = statistically significant shift
- Tested on historical data for stability

---

## Risk Classification

### Objective
Categorize districts into actionable risk levels.

### Multi-Factor Assessment

```python
def classify_risk(district):
    score = district.severity_score
    trend = district.severity_trend
    is_anomaly = district.is_anomaly
    
    # Critical: Very high score OR anomaly + rising
    if score >= 90 or (is_anomaly and trend in ['accelerating_up', 'rising']):
        return 'Critical'
    
    # Emerging Risk: High score + rising trend
    elif score >= 75 and trend in ['accelerating_up', 'rising']:
        return 'Emerging_Risk'
    
    # Watchlist: Above average OR moderate anomaly
    elif score >= 60 or (is_anomaly and trend != 'declining'):
        return 'Watchlist'
    
    # Stable: Everything else
    else:
        return 'Stable'
```

### Design Principles

1. **Combine multiple signals**: Score alone is insufficient
2. **Prioritize trends**: Rising scores more concerning than high-but-stable
3. **Leverage anomalies**: Statistical outliers get extra scrutiny
4. **Clear thresholds**: No ambiguity in classification

### Action Matrix

| Risk Level | Frequency | Action |
|------------|-----------|--------|
| Critical | Daily monitoring | Immediate intervention, resource deployment |
| Emerging Risk | 2x weekly | Enhanced monitoring, prepare resources |
| Watchlist | Weekly | Regular monitoring, early preparation |
| Stable | Routine | Standard operations |

---

## Forecasting

### Objective
Predict district risk 2 weeks ahead to enable proactive response.

### Current Approach: Adaptive Moving Average

```python
def forecast_district(district_history):
    # Use last 4 weeks
    last_4 = district_history.tail(4)
    
    # Simple average
    forecast_severity = last_4.severity_score.mean()
    forecast_enrol = last_4.enrol_total.mean()
    forecast_demo = last_4.demo_total.mean()
    forecast_bio = last_4.bio_total.mean()
    
    # Adjust for trend
    recent_trend = last_4.severity_trend.iloc[-1]
    
    if recent_trend in ['accelerating_up', 'rising']:
        forecast_severity *= 1.1  # 10% increase
    elif recent_trend in ['accelerating_down', 'declining']:
        forecast_severity *= 0.9  # 10% decrease
    
    # Classify forecasted risk
    forecast_risk = classify_risk_from_score(forecast_severity)
    
    return forecast_severity, forecast_risk
```

### Limitations
- Simple model, doesn't account for:
  - Seasonality
  - Policy changes
  - External shocks
  - Complex interactions

### Future Enhancement: ARIMA/Prophet

```python
from statsmodels.tsa.arima.model import ARIMA
# or
from prophet import Prophet

# More sophisticated forecasting
model = ARIMA(district_history, order=(2,1,2))
forecast = model.fit().forecast(steps=2)
```

**Benefits**:
- Accounts for seasonality
- Confidence intervals
- Better handling of trends

---

## Validation & Testing

### Historical Backtesting

**Method**: Train on weeks 1-20, test on weeks 21-28

**Metrics**:
- Precision: Of districts flagged as high-risk, how many were actually high-risk?
- Recall: Of actually high-risk districts, how many did we catch?
- Lead time: How many weeks in advance did we detect?

### Data Quality Checks

1. **Completeness Score**
```python
completeness = (
    (enrol_total > 0) + 
    (demo_total > 0) + 
    (bio_total > 0)
) / 3 × 100
```

2. **Consistency Checks**
- Age-group sums match totals
- No negative values
- PIN codes valid

3. **Temporal Consistency**
- No impossible week-to-week jumps
- Missing week detection

### Sensitivity Analysis

**Question**: How sensitive are results to parameter changes?

**Tests**:
- Vary anomaly contamination rate (5%, 10%, 15%)
- Vary trend thresholds (±20%)
- Vary risk classification thresholds (±5 points)

**Result**: System remains stable across reasonable parameter ranges.

---

## Limitations & Biases

### Known Limitations

1. **Data Lag**: Weekly aggregation means 7-day delay
2. **External Factors**: Doesn't account for policy changes, disasters, campaigns
3. **Geographic Boundary Changes**: Districts can split/merge
4. **Forecasting Horizon**: 2-week ahead only (simple model)

### Potential Biases

1. **Urban vs Rural**: Urban districts may have higher baseline activity
   - **Mitigation**: Peer group benchmarking by activity tier
   
2. **Population Size**: Larger districts have more activity
   - **Mitigation**: Percentile-based scoring (relative to peers)
   
3. **Data Quality**: Sparse data regions may be misclassified
   - **Mitigation**: Flag districts with completeness < 66%

### Fairness Considerations

- All districts assessed by same criteria
- Transparent methodology
- Appeal mechanism possible (manual review)

---

## References

1. Liu, F. T., Ting, K. M., & Zhou, Z. H. (2008). Isolation forest. IEEE ICDM.
2. UIDAI. (2025). Aadhaar Statistics. https://uidai.gov.in/
3. India Post. (2025). PIN Code Directory.

---

**Document Version**: 1.0  
**Last Updated**: January 2026  
**Author**: [Your Team]
