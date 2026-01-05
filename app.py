"""
Aadhaar Early Warning System (EWS)
UIDAI Data Hackathon 2026

A National Early Warning System for Aadhaar operations that detects emerging risk 
trends at the district level using privacy-preserving aggregated data.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# Add utils to path
sys.path.append(str(Path(__file__).parent / 'utils'))

# Page configuration
st.set_page_config(
    page_title="Aadhaar Early Warning System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .risk-critical {
        color: #d62728;
        font-weight: bold;
    }
    .risk-emerging {
        color: #ff7f0e;
        font-weight: bold;
    }
    .risk-watchlist {
        color: #bcbd22;
        font-weight: bold;
    }
    .risk-stable {
        color: #2ca02c;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Load data with caching
@st.cache_data
def load_data():
    """Load all EWS data files"""
    data_path = Path(__file__).parent / 'data'
    
    ews_data = pd.read_csv(data_path / 'ews_weekly_district_enhanced.csv')
    forecasts = pd.read_csv(data_path / 'district_forecasts.csv')
    profiles = pd.read_csv(data_path / 'district_profiles.csv')
    benchmarks = pd.read_csv(data_path / 'peer_benchmarks.csv')
    geo_summary = pd.read_csv(data_path / 'geo_cleaning_summary.csv')
    weights = pd.read_csv(data_path / 'weight_justification.csv')
    
    return ews_data, forecasts, profiles, benchmarks, geo_summary, weights

# Load data
try:
    ews_data, forecasts, profiles, benchmarks, geo_summary, weights = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar
st.sidebar.markdown("## 🚨 Aadhaar EWS")
st.sidebar.markdown("---")

# Navigation
page = st.sidebar.radio(
    "Navigation",
    ["🏠 National Overview", 
     "⚠️ Early Warning Signals", 
     "🗺️ Geospatial Risk Map",
     "📊 District Deep Dive",
     "🔮 Forecasts & Predictions",
     "🔬 Data Quality & Methodology",
     "📖 About & Ethics"]
)

st.sidebar.markdown("---")

# Global filters
st.sidebar.markdown("### Filters")

# Week filter
weeks = sorted(ews_data['week'].unique(), reverse=True)
selected_week = st.sidebar.selectbox("Select Week", weeks)

# State filter
states = ['All States'] + sorted(ews_data['state'].unique().tolist())
selected_state = st.sidebar.selectbox("Select State", states)

# Filter data
if selected_state != 'All States':
    filtered_data = ews_data[
        (ews_data['week'] == selected_week) & 
        (ews_data['state'] == selected_state)
    ]
else:
    filtered_data = ews_data[ews_data['week'] == selected_week]

st.sidebar.markdown("---")
st.sidebar.markdown("### System Info")
st.sidebar.info(f"""
**Data Coverage**  
Districts: {ews_data.groupby(['state', 'district']).ngroups:,}  
Weeks: {ews_data['week'].nunique()}  
Records: {len(ews_data):,}
""")

# ============================================================================
# PAGE 1: NATIONAL OVERVIEW
# ============================================================================
if page == "🏠 National Overview":
    st.markdown("<div class='main-header'>Aadhaar Early Warning System</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>National Dashboard - Week " + selected_week + "</div>", unsafe_allow_html=True)
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        critical_count = len(filtered_data[filtered_data['risk_category'] == 'Critical'])
        st.metric(
            "Critical Districts",
            f"{critical_count}",
            delta=None,
            delta_color="inverse"
        )
    
    with col2:
        emerging_count = len(filtered_data[filtered_data['risk_category'] == 'Emerging_Risk'])
        st.metric(
            "Emerging Risk",
            f"{emerging_count}",
            delta=None
        )
    
    with col3:
        watchlist_count = len(filtered_data[filtered_data['risk_category'] == 'Watchlist'])
        st.metric(
            "Watchlist",
            f"{watchlist_count}",
            delta=None
        )
    
    with col4:
        anomaly_count = filtered_data['is_anomaly'].sum()
        st.metric(
            "Anomalies Detected",
            f"{anomaly_count}",
            delta=None
        )
    
    st.markdown("---")
    
    # Risk distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Risk Category Distribution")
        risk_counts = filtered_data['risk_category'].value_counts()
        
        fig = px.pie(
            values=risk_counts.values,
            names=risk_counts.index,
            color=risk_counts.index,
            color_discrete_map={
                'Critical': '#d62728',
                'Emerging_Risk': '#ff7f0e',
                'Watchlist': '#bcbd22',
                'Stable': '#2ca02c'
            }
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Dominant Signal Analysis")
        signal_counts = filtered_data['dominant_signal'].value_counts()
        
        fig = px.bar(
            x=signal_counts.index,
            y=signal_counts.values,
            labels={'x': 'Signal Type', 'y': 'Number of Districts'},
            color=signal_counts.index,
            color_discrete_map={
                'Enrolment': '#1f77b4',
                'Demographic': '#ff7f0e',
                'Biometric': '#2ca02c'
            }
        )
        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Trend analysis over time
    st.markdown("### Risk Trends Over Time")
    
    trend_data = ews_data.groupby(['week', 'risk_category']).size().reset_index(name='count')
    
    fig = px.line(
        trend_data,
        x='week',
        y='count',
        color='risk_category',
        markers=True,
        color_discrete_map={
            'Critical': '#d62728',
            'Emerging_Risk': '#ff7f0e',
            'Watchlist': '#bcbd22',
            'Stable': '#2ca02c'
        }
    )
    fig.update_layout(
        xaxis_title="Week",
        yaxis_title="Number of Districts",
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Top critical districts
    st.markdown("### Top 10 Critical Districts")
    
    critical_districts = filtered_data[
        filtered_data['risk_category'] == 'Critical'
    ].sort_values('severity_score', ascending=False).head(10)
    
    if len(critical_districts) > 0:
        display_cols = ['state', 'district', 'severity_score', 'dominant_signal', 'severity_trend']
        st.dataframe(
            critical_districts[display_cols].style.format({
                'severity_score': '{:.1f}'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("No critical districts in the selected week!")

# ============================================================================
# PAGE 2: EARLY WARNING SIGNALS
# ============================================================================
elif page == "⚠️ Early Warning Signals":
    st.markdown("<div class='main-header'>Early Warning Signals</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Districts with Accelerating Risk Trends</div>", unsafe_allow_html=True)
    
    # Focus on accelerating trends
    accelerating = filtered_data[
        filtered_data['severity_trend'].isin(['accelerating_up', 'rising'])
    ].sort_values('severity_score', ascending=False)
    
    st.markdown(f"### ⚠️ {len(accelerating)} Districts Showing Upward Trends")
    
    if len(accelerating) > 0:
        # Severity distribution
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.scatter(
                accelerating,
                x='severity_score',
                y='state',
                size='severity_score',
                color='risk_category',
                hover_data=['district', 'dominant_signal'],
                color_discrete_map={
                    'Critical': '#d62728',
                    'Emerging_Risk': '#ff7f0e',
                    'Watchlist': '#bcbd22',
                    'Stable': '#2ca02c'
                }
            )
            fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Risk Breakdown")
            risk_dist = accelerating['risk_category'].value_counts()
            for risk, count in risk_dist.items():
                pct = count / len(accelerating) * 100
                st.markdown(f"**{risk}**: {count} ({pct:.1f}%)")
            
            st.markdown("#### Trend Breakdown")
            trend_dist = accelerating['severity_trend'].value_counts()
            for trend, count in trend_dist.items():
                st.markdown(f"**{trend}**: {count}")
        
        st.markdown("---")
        
        # Detailed table
        st.markdown("### Detailed Analysis")
        
        display_df = accelerating[[
            'state', 'district', 'risk_category', 'severity_score',
            'severity_trend', 'dominant_signal', 'data_quality_flag'
        ]].copy()
        
        st.dataframe(
            display_df.style.format({
                'severity_score': '{:.1f}'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ No districts showing accelerating risk trends in the selected week!")

# Continued in next part due to length...

# ============================================================================
# REMAINING PAGES (simplified for Part 1)
# ============================================================================
elif page == "🗺️ Geospatial Risk Map":
    st.markdown("<div class='main-header'>Geospatial Risk Map</div>", unsafe_allow_html=True)
    st.info("🚧 Geographic visualization requires india_districts.geojson - to be added")
    
    # State-level aggregation as alternative
    st.markdown("### State-Level Risk Summary")
    state_risk = filtered_data.groupby('state').agg({
        'severity_score': 'mean',
        'risk_category': lambda x: x.value_counts().index[0]
    }).reset_index()
    
    fig = px.bar(
        state_risk.sort_values('severity_score', ascending=True),
        y='state',
        x='severity_score',
        color='risk_category',
        orientation='h',
        color_discrete_map={
            'Critical': '#d62728',
            'Emerging_Risk': '#ff7f0e',
            'Watchlist': '#bcbd22',
            'Stable': '#2ca02c'
        }
    )
    fig.update_layout(height=800)
    st.plotly_chart(fig, use_container_width=True)

elif page == "📊 District Deep Dive":
    st.markdown("<div class='main-header'>District Deep Dive</div>", unsafe_allow_html=True)
    
    # District selector
    if selected_state != 'All States':
        available_districts = sorted(ews_data[ews_data['state'] == selected_state]['district'].unique())
    else:
        available_districts = sorted(ews_data['district'].unique())
    
    selected_district = st.selectbox("Select District", available_districts)
    
    # Get district data
    district_data = ews_data[
        (ews_data['state'] == selected_state if selected_state != 'All States' else True) &
        (ews_data['district'] == selected_district)
    ].sort_values('week')
    
    if len(district_data) > 0:
        # Metrics
        latest = district_data.iloc[-1]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Current Risk", latest['risk_category'])
        with col2:
            st.metric("Severity Score", f"{latest['severity_score']:.1f}")
        with col3:
            st.metric("Trend", latest['severity_trend'])
        with col4:
            st.metric("Dominant Signal", latest['dominant_signal'])
        
        st.markdown("---")
        
        # Severity trend over time
        st.markdown("### Severity Score Trend")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=district_data['week'],
            y=district_data['severity_score'],
            mode='lines+markers',
            name='Severity Score',
            line=dict(color='#1f77b4', width=2)
        ))
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Activity breakdown
        st.markdown("### Activity Breakdown")
        col1, col2 = st.columns(2)
        
        with col1:
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Enrolment', x=district_data['week'], y=district_data['enrol_total']))
            fig.add_trace(go.Bar(name='Demographic', x=district_data['week'], y=district_data['demo_total']))
            fig.add_trace(go.Bar(name='Biometric', x=district_data['week'], y=district_data['bio_total']))
            fig.update_layout(barmode='group', height=300)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Age group breakdown
            latest_age = latest[[
                'enrol_age_0_5', 'enrol_age_5_17', 'enrol_age_18_plus',
                'demo_age_5_17', 'demo_age_18_plus',
                'bio_age_5_17', 'bio_age_18_plus'
            ]]
            
            child_total = (latest['enrol_age_0_5'] + latest['enrol_age_5_17'] + 
                          latest['demo_age_5_17'] + latest['bio_age_5_17'])
            adult_total = (latest['enrol_age_18_plus'] + latest['demo_age_18_plus'] + 
                          latest['bio_age_18_plus'])
            
            fig = px.pie(
                values=[child_total, adult_total],
                names=['Children (0-17)', 'Adults (18+)'],
                title='Age Group Distribution'
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

elif page == "🔮 Forecasts & Predictions":
    st.markdown("<div class='main-header'>Forecasts & Predictions</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>2-Week Ahead Risk Forecasts</div>", unsafe_allow_html=True)
    
    # Filter forecasts
    if selected_state != 'All States':
        forecast_filtered = forecasts[forecasts['state'] == selected_state]
    else:
        forecast_filtered = forecasts
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        critical_forecast = len(forecast_filtered[forecast_filtered['forecast_risk_category'] == 'Critical'])
        st.metric("Forecasted Critical", critical_forecast)
    
    with col2:
        emerging_forecast = len(forecast_filtered[forecast_filtered['forecast_risk_category'] == 'Emerging_Risk'])
        st.metric("Forecasted Emerging Risk", emerging_forecast)
    
    with col3:
        watchlist_forecast = len(forecast_filtered[forecast_filtered['forecast_risk_category'] == 'Watchlist'])
        st.metric("Forecasted Watchlist", watchlist_forecast)
    
    st.markdown("---")
    
    # Top forecasted risks
    st.markdown("### Districts Forecasted as High Risk")
    
    high_risk_forecast = forecast_filtered[
        forecast_filtered['forecast_risk_category'].isin(['Critical', 'Emerging_Risk'])
    ].sort_values('forecast_severity_score', ascending=False)
    
    if len(high_risk_forecast) > 0:
        st.dataframe(
            high_risk_forecast[[
                'state', 'district', 'forecast_risk_category',
                'forecast_severity_score', 'current_trend'
            ]].style.format({
                'forecast_severity_score': '{:.1f}'
            }),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ No high-risk districts forecasted!")

elif page == "🔬 Data Quality & Methodology":
    st.markdown("<div class='main-header'>Data Quality & Methodology</div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Geo-Cleaning", "Severity Scoring", "Risk Classification"])
    
    with tab1:
        st.markdown("### Geographic Canonicalization Process")
        st.dataframe(geo_summary, use_container_width=True, hide_index=True)
        
        st.markdown("""
        #### Why PIN-Based Canonicalization?
        
        The Aadhaar datasets contain state and district names that vary in spelling and format.
        This creates problems for:
        - Geographic visualizations (maps won't render correctly)
        - Cross-dataset joins (names don't match)
        - Trend analysis (same location counted as different)
        
        **Solution**: Use PIN code as the single source of truth, mapping to official 
        postal directory for standardized state and district names.
        """)
    
    with tab2:
        st.markdown("### Severity Scoring Methodology")
        
        st.markdown("#### Data-Driven Weight Calculation")
        st.dataframe(weights, use_container_width=True, hide_index=True)
        
        st.markdown("""
        **Methodology**:
        1. Calculate coefficient of variation (CV) for each metric
        2. Normalize CVs to sum to 1.0
        3. Higher variation = higher weight (more signal)
        
        **Formula**:
        ```
        Severity Score = (Enrolment %ile × Weight₁) + 
                        (Demographic %ile × Weight₂) + 
                        (Biometric %ile × Weight₃)
        ```
        
        This approach is **data-driven** rather than arbitrary, ensuring weights reflect
        actual variation patterns in the data.
        """)
    
    with tab3:
        st.markdown("### Risk Classification Thresholds")
        
        threshold_df = pd.DataFrame([
            {
                'Risk Category': 'Critical',
                'Criteria': 'Severity ≥ 90 OR (Anomaly + Rising Trend)',
                'Action Required': 'Immediate intervention'
            },
            {
                'Risk Category': 'Emerging_Risk',
                'Criteria': 'Severity ≥ 75 AND Rising Trend',
                'Action Required': 'Monitor closely, prepare resources'
            },
            {
                'Risk Category': 'Watchlist',
                'Criteria': 'Severity ≥ 60 OR (Anomaly + Not Declining)',
                'Action Required': 'Regular monitoring'
            },
            {
                'Risk Category': 'Stable',
                'Criteria': 'All others',
                'Action Required': 'Routine operations'
            }
        ])
        
        st.dataframe(threshold_df, use_container_width=True, hide_index=True)
        
        st.markdown("### Trend Classification")
        
        trend_df = pd.DataFrame([
            {'Trend': 'accelerating_up', 'Definition': 'Change > 5 AND positive momentum'},
            {'Trend': 'rising', 'Definition': 'Change > 3'},
            {'Trend': 'stable', 'Definition': 'Change between -3 and 3'},
            {'Trend': 'declining', 'Definition': 'Change < -5 OR negative momentum'},
            {'Trend': 'accelerating_down', 'Definition': 'Change < -5 AND negative momentum'}
        ])
        
        st.dataframe(trend_df, use_container_width=True, hide_index=True)

elif page == "📖 About & Ethics":
    st.markdown("<div class='main-header'>About This System</div>", unsafe_allow_html=True)
    
    st.markdown("""
    ## Aadhaar Early Warning System (EWS)
    
    ### Purpose
    
    The Aadhaar EWS is designed to help UIDAI administrators identify districts that are
    quietly moving towards operational risk. Unlike simple threshold alerts, this system:
    
    - **Detects trends**, not just spikes
    - **Preserves privacy** through aggregation
    - **Provides context** via peer comparison
    - **Forecasts future risk** to enable proactive response
    
    ### Technical Approach
    
    #### 1. Data Processing
    - PIN-based geographic canonicalization
    - Weekly aggregation from daily data
    - Age-group preservation for policy insights
    
    #### 2. Analytics
    - Data-driven severity scoring (not arbitrary weights)
    - Statistical anomaly detection (Isolation Forest)
    - 4-week rolling trend analysis
    - 2-week ahead forecasting
    
    #### 3. Risk Classification
    - Explicit, documented thresholds
    - Multi-factor assessment (score + trend + anomaly)
    - Peer-based benchmarking
    
    ### Privacy & Ethics
    
    #### Privacy Protection
    - ✅ No individual records exposed
    - ✅ All data aggregated to district-week level
    - ✅ PIN codes not displayed in outputs
    - ✅ Minimum aggregation: district level (population in thousands)
    
    #### Ethical Considerations
    
    **Bias Prevention**: 
    - Data-driven weights avoid subjective bias
    - Peer comparison accounts for district characteristics
    - Multiple metrics prevent single-metric bias
    
    **Transparency**:
    - All thresholds explicitly documented
    - Methodology fully disclosed
    - Geo-cleaning process documented
    
    **Actionability**:
    - Clear risk categories tied to actions
    - Forecasts provide lead time
    - Dominant signal identification guides intervention
    
    ### Limitations
    
    1. **Forecasting Accuracy**: Simple moving average model; can be improved with ARIMA/Prophet
    2. **External Factors**: Does not account for policy changes, natural disasters, etc.
    3. **Data Quality**: Dependent on upstream data accuracy
    4. **Geographic Boundaries**: District boundaries may change; requires ongoing updates
    
    ### Data Sources
    
    - **Aadhaar Enrolment Dataset**: 1,006,029 records (March-December 2025)
    - **Aadhaar Demographic Update Dataset**: 2,071,700 records
    - **Aadhaar Biometric Update Dataset**: 1,861,108 records
    - **India Post PIN Directory**: 19,586 PIN codes, 741 districts, 36 states
    
    ### Team
    
    Submission for UIDAI Data Hackathon 2026
    
    ### Contact
    
    For questions about methodology or implementation, contact: [Your Contact]
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    Aadhaar Early Warning System | UIDAI Data Hackathon 2026<br>
    Built with Streamlit • Powered by Privacy-Preserving Analytics
</div>
""", unsafe_allow_html=True)
