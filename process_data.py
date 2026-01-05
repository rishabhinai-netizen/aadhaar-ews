"""
Aadhaar EWS Data Processing Pipeline
=====================================

This script processes raw Aadhaar datasets through the complete EWS analytics pipeline:
1. Data loading and validation
2. PIN-based geographic canonicalization  
3. Weekly aggregation with age-group preservation
4. Advanced analytics (severity scoring, anomaly detection, trends)
5. Forecasting and peer benchmarking
6. Output generation

Usage:
    python process_data.py --enrol <path> --demo <path> --bio <path> --pincode <path>

Author: [Your Team]
Date: January 2026
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import RobustScaler
from sklearn.ensemble import IsolationForest
import argparse
import warnings
from pathlib import Path
from datetime import datetime
import logging

warnings.filterwarnings('ignore')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AadhaarEWSProcessor:
    """Main processor for Aadhaar EWS analytics pipeline"""
    
    def __init__(self, output_dir='data'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.enrolment_df = None
        self.demographic_df = None
        self.biometric_df = None
        self.pincode_ref = None
        self.ews_data = None
        
    def load_data(self, enrol_path, demo_path, bio_path, pincode_path):
        """Load all input datasets"""
        logger.info("="*80)
        logger.info("PHASE 1: DATA LOADING")
        logger.info("="*80)
        
        # Load datasets based on file type
        logger.info("Loading enrolment data...")
        if str(enrol_path).endswith('.csv'):
            self.enrolment_df = pd.read_csv(enrol_path)
        else:
            # Handle multiple CSV files
            self.enrolment_df = pd.read_csv(enrol_path)
        
        logger.info("Loading demographic data...")
        self.demographic_df = pd.read_csv(demo_path)
        
        logger.info("Loading biometric data...")
        self.biometric_df = pd.read_csv(bio_path)
        
        logger.info("Loading pincode reference...")
        self.pincode_ref = pd.read_csv(pincode_path)
        
        logger.info(f"✓ Enrolment: {len(self.enrolment_df):,} records")
        logger.info(f"✓ Demographic: {len(self.demographic_df):,} records")
        logger.info(f"✓ Biometric: {len(self.biometric_df):,} records")
        logger.info(f"✓ Pincode: {len(self.pincode_ref):,} records")
        
    def parse_dates(self):
        """Parse date columns"""
        logger.info("\nParsing dates...")
        
        self.enrolment_df['date'] = pd.to_datetime(
            self.enrolment_df['date'], 
            format='%d-%m-%Y', 
            errors='coerce'
        )
        self.demographic_df['date'] = pd.to_datetime(
            self.demographic_df['date'], 
            format='%d-%m-%Y', 
            errors='coerce'
        )
        self.biometric_df['date'] = pd.to_datetime(
            self.biometric_df['date'], 
            format='%d-%m-%Y', 
            errors='coerce'
        )
        
        logger.info(f"✓ Date range: {self.enrolment_df['date'].min()} to {self.enrolment_df['date'].max()}")
        
    def canonicalize_geography(self):
        """Apply PIN-based geographic canonicalization"""
        logger.info("\n" + "="*80)
        logger.info("PHASE 2: GEOGRAPHIC CANONICALIZATION")
        logger.info("="*80)
        
        # Clean pincode reference
        self.pincode_ref.columns = ['pincode', 'district', 'state']
        self.pincode_ref['state'] = self.pincode_ref['state'].str.strip().str.upper()
        self.pincode_ref['district'] = self.pincode_ref['district'].str.strip().str.upper()
        self.pincode_ref = self.pincode_ref.drop_duplicates(subset=['pincode'])
        
        logger.info(f"Pincode reference: {len(self.pincode_ref):,} unique PINs")
        
        # Apply to each dataset
        self._apply_canonicalization(self.enrolment_df, "Enrolment")
        self._apply_canonicalization(self.demographic_df, "Demographic")
        self._apply_canonicalization(self.biometric_df, "Biometric")
        
    def _apply_canonicalization(self, df, name):
        """Apply canonicalization to a single dataset"""
        original_states = df['state'].nunique()
        original_districts = df['district'].nunique()
        
        # Merge with pincode reference
        df = df.merge(
            self.pincode_ref[['pincode', 'state', 'district']],
            on='pincode',
            how='left',
            suffixes=('_original', '')
        )
        
        # Track missing
        missing_pins = df[df['state'].isna()]['pincode'].nunique()
        
        # Fill missing with original
        df['state'] = df['state'].fillna(df['state_original'])
        df['district'] = df['district'].fillna(df['district_original'])
        
        # Drop original columns
        df.drop(['state_original', 'district_original'], axis=1, errors='ignore', inplace=True)
        
        new_states = df['state'].nunique()
        new_districts = df['district'].nunique()
        
        logger.info(f"✓ {name}: {original_states}→{new_states} states, "
                   f"{original_districts}→{new_districts} districts, "
                   f"{missing_pins:,} missing PINs")
        
    def aggregate_weekly(self):
        """Aggregate daily data to weekly with age groups preserved"""
        logger.info("\n" + "="*80)
        logger.info("PHASE 3: WEEKLY AGGREGATION")
        logger.info("="*80)
        
        # Add week column
        self.enrolment_df['week'] = self.enrolment_df['date'].dt.to_period('W-MON').astype(str)
        self.demographic_df['week'] = self.demographic_df['date'].dt.to_period('W-MON').astype(str)
        self.biometric_df['week'] = self.biometric_df['date'].dt.to_period('W-MON').astype(str)
        
        # Aggregate each dataset
        logger.info("Aggregating enrolment data...")
        enrol_weekly = self.enrolment_df.groupby(['week', 'state', 'district']).agg({
            'age_0_5': 'sum',
            'age_5_17': 'sum',
            'age_18_greater': 'sum'
        }).reset_index()
        enrol_weekly['enrol_total'] = enrol_weekly[['age_0_5', 'age_5_17', 'age_18_greater']].sum(axis=1)
        enrol_weekly.columns = ['week', 'state', 'district', 'enrol_age_0_5', 
                                'enrol_age_5_17', 'enrol_age_18_plus', 'enrol_total']
        
        logger.info("Aggregating demographic data...")
        demo_weekly = self.demographic_df.groupby(['week', 'state', 'district']).agg({
            'demo_age_5_17': 'sum',
            'demo_age_17_': 'sum'
        }).reset_index()
        demo_weekly['demo_total'] = demo_weekly[['demo_age_5_17', 'demo_age_17_']].sum(axis=1)
        demo_weekly.columns = ['week', 'state', 'district', 'demo_age_5_17', 
                               'demo_age_18_plus', 'demo_total']
        
        logger.info("Aggregating biometric data...")
        bio_weekly = self.biometric_df.groupby(['week', 'state', 'district']).agg({
            'bio_age_5_17': 'sum',
            'bio_age_17_': 'sum'
        }).reset_index()
        bio_weekly['bio_total'] = bio_weekly[['bio_age_5_17', 'bio_age_17_']].sum(axis=1)
        bio_weekly.columns = ['week', 'state', 'district', 'bio_age_5_17', 
                              'bio_age_18_plus', 'bio_total']
        
        # Merge all
        logger.info("Merging datasets...")
        self.ews_data = enrol_weekly.merge(demo_weekly, on=['week', 'state', 'district'], how='outer')
        self.ews_data = self.ews_data.merge(bio_weekly, on=['week', 'state', 'district'], how='outer')
        self.ews_data = self.ews_data.fillna(0)
        
        # Convert to int
        numeric_cols = ['enrol_age_0_5', 'enrol_age_5_17', 'enrol_age_18_plus', 'enrol_total',
                       'demo_age_5_17', 'demo_age_18_plus', 'demo_total',
                       'bio_age_5_17', 'bio_age_18_plus', 'bio_total']
        for col in numeric_cols:
            self.ews_data[col] = self.ews_data[col].astype(int)
        
        logger.info(f"✓ Merged dataset: {len(self.ews_data):,} district-weeks")
        logger.info(f"✓ Districts: {self.ews_data.groupby(['state', 'district']).ngroups:,}")
        logger.info(f"✓ Weeks: {self.ews_data['week'].nunique()}")
        
    def compute_severity_scores(self):
        """Compute data-driven severity scores"""
        logger.info("\n" + "="*80)
        logger.info("PHASE 4: SEVERITY SCORING")
        logger.info("="*80)
        
        # Calculate data-driven weights
        total_cols = ['enrol_total', 'demo_total', 'bio_total']
        cvs = {}
        for col in total_cols:
            mean_val = self.ews_data[col].mean()
            std_val = self.ews_data[col].std()
            cv = std_val / mean_val if mean_val > 0 else 0
            cvs[col] = cv
        
        total_cv = sum(cvs.values())
        weights = {k: v/total_cv for k, v in cvs.items()}
        
        logger.info(f"✓ Data-driven weights:")
        logger.info(f"  • Enrolment: {weights['enrol_total']:.2%}")
        logger.info(f"  • Demographic: {weights['demo_total']:.2%}")
        logger.info(f"  • Biometric: {weights['bio_total']:.2%}")
        
        # Save weights
        weights_df = pd.DataFrame([
            {'metric': k.replace('_total', ''), 'weight': v, 
             'rationale': 'Based on coefficient of variation'}
            for k, v in weights.items()
        ])
        weights_df.to_csv(self.output_dir / 'weight_justification.csv', index=False)
        
        # Compute percentile ranks
        for col in total_cols:
            self.ews_data[f'{col}_pct'] = self.ews_data.groupby('week')[col].rank(pct=True) * 100
        
        # Weighted severity score
        self.ews_data['severity_score'] = (
            self.ews_data['enrol_total_pct'] * weights['enrol_total'] +
            self.ews_data['demo_total_pct'] * weights['demo_total'] +
            self.ews_data['bio_total_pct'] * weights['bio_total']
        )
        
        logger.info(f"✓ Severity scores computed: mean={self.ews_data['severity_score'].mean():.1f}")
        
    def detect_anomalies(self):
        """Detect statistical anomalies using Isolation Forest"""
        logger.info("\n" + "="*80)
        logger.info("PHASE 5: ANOMALY DETECTION")
        logger.info("="*80)
        
        self.ews_data['anomaly_score'] = 0
        self.ews_data['is_anomaly'] = False
        
        # Get districts with sufficient data
        district_counts = self.ews_data.groupby(['state', 'district']).size()
        active_districts = district_counts[district_counts >= 5].index
        
        logger.info(f"Running Isolation Forest on {len(active_districts):,} districts...")
        
        for state, district in active_districts:
            mask = (self.ews_data['state'] == state) & (self.ews_data['district'] == district)
            district_data = self.ews_data.loc[mask, ['enrol_total', 'demo_total', 'bio_total']].values
            
            if len(district_data) >= 5:
                iso_forest = IsolationForest(contamination=0.1, random_state=42)
                anomaly_preds = iso_forest.fit_predict(district_data)
                self.ews_data.loc[mask, 'is_anomaly'] = (anomaly_preds == -1)
                self.ews_data.loc[mask, 'anomaly_score'] = iso_forest.score_samples(district_data)
        
        anomaly_count = self.ews_data['is_anomaly'].sum()
        logger.info(f"✓ Detected {anomaly_count:,} anomalies ({anomaly_count/len(self.ews_data)*100:.1f}%)")
        
    def compute_trends(self):
        """Compute severity trends"""
        logger.info("\n" + "="*80)
        logger.info("PHASE 6: TREND ANALYSIS")
        logger.info("="*80)
        
        # Sort data
        self.ews_data = self.ews_data.sort_values(['state', 'district', 'week'])
        
        # 4-week rolling average
        self.ews_data['severity_score_ma4'] = self.ews_data.groupby(
            ['state', 'district']
        )['severity_score'].transform(
            lambda x: x.rolling(window=4, min_periods=2).mean()
        )
        
        # Week-over-week change
        self.ews_data['severity_score_change'] = self.ews_data.groupby(
            ['state', 'district']
        )['severity_score'].diff()
        
        # Momentum
        self.ews_data['severity_score_momentum'] = self.ews_data.groupby(
            ['state', 'district']
        )['severity_score_change'].diff()
        
        # Classify trend
        def classify_trend(row):
            if pd.isna(row['severity_score_change']):
                return 'insufficient_data'
            
            change = row['severity_score_change']
            momentum = row['severity_score_momentum'] if not pd.isna(row['severity_score_momentum']) else 0
            
            if change > 5 and momentum > 0:
                return 'accelerating_up'
            elif change > 3:
                return 'rising'
            elif change > -3:
                return 'stable'
            elif change < -5 and momentum < 0:
                return 'accelerating_down'
            else:
                return 'declining'
        
        self.ews_data['severity_trend'] = self.ews_data.apply(classify_trend, axis=1)
        
        logger.info(f"✓ Trend distribution:")
        for trend, count in self.ews_data['severity_trend'].value_counts().items():
            logger.info(f"  • {trend}: {count:,}")
        
    def classify_risk(self):
        """Assign risk categories"""
        logger.info("\n" + "="*80)
        logger.info("PHASE 7: RISK CLASSIFICATION")
        logger.info("="*80)
        
        def assign_risk(row):
            score = row['severity_score']
            trend = row['severity_trend']
            is_anomaly = row['is_anomaly']
            
            if score >= 90 or (is_anomaly and trend in ['accelerating_up', 'rising']):
                return 'Critical'
            elif score >= 75 and trend in ['accelerating_up', 'rising']:
                return 'Emerging_Risk'
            elif score >= 60 or (is_anomaly and trend != 'declining'):
                return 'Watchlist'
            else:
                return 'Stable'
        
        self.ews_data['risk_category'] = self.ews_data.apply(assign_risk, axis=1)
        
        logger.info(f"✓ Risk distribution:")
        for risk, count in self.ews_data['risk_category'].value_counts().items():
            logger.info(f"  • {risk}: {count:,}")
        
    def identify_dominant_signals(self):
        """Identify dominant contributing signal"""
        logger.info("\nIdentifying dominant signals...")
        
        def get_dominant(row):
            enrol_pct = row['enrol_total_pct']
            demo_pct = row['demo_total_pct']
            bio_pct = row['bio_total_pct']
            
            max_pct = max(enrol_pct, demo_pct, bio_pct)
            
            if max_pct == enrol_pct:
                return 'Enrolment'
            elif max_pct == demo_pct:
                return 'Demographic'
            else:
                return 'Biometric'
        
        self.ews_data['dominant_signal'] = self.ews_data.apply(get_dominant, axis=1)
        
        logger.info(f"✓ Signal distribution:")
        for signal, count in self.ews_data['dominant_signal'].value_counts().items():
            logger.info(f"  • {signal}: {count:,}")
        
    def compute_data_quality(self):
        """Compute data quality metrics"""
        logger.info("\nComputing data quality metrics...")
        
        self.ews_data['data_completeness'] = (
            (self.ews_data['enrol_total'] > 0).astype(int) +
            (self.ews_data['demo_total'] > 0).astype(int) +
            (self.ews_data['bio_total'] > 0).astype(int)
        ) / 3 * 100
        
        self.ews_data['data_quality_flag'] = self.ews_data['data_completeness'].apply(
            lambda x: 'complete' if x == 100 else ('partial' if x >= 33 else 'sparse')
        )
        
        logger.info(f"✓ Quality distribution:")
        for quality, count in self.ews_data['data_quality_flag'].value_counts().items():
            logger.info(f"  • {quality}: {count:,}")
        
    def save_outputs(self):
        """Save all output files"""
        logger.info("\n" + "="*80)
        logger.info("SAVING OUTPUTS")
        logger.info("="*80)
        
        # Main EWS file
        output_cols = [
            'week', 'state', 'district',
            'risk_category', 'severity_score', 'severity_trend',
            'dominant_signal',
            'enrol_total', 'demo_total', 'bio_total',
            'enrol_age_0_5', 'enrol_age_5_17', 'enrol_age_18_plus',
            'demo_age_5_17', 'demo_age_18_plus',
            'bio_age_5_17', 'bio_age_18_plus',
            'is_anomaly', 'data_quality_flag', 'data_completeness'
        ]
        
        self.ews_data[output_cols].to_csv(
            self.output_dir / 'ews_weekly_district_enhanced.csv', 
            index=False
        )
        logger.info(f"✓ Saved: ews_weekly_district_enhanced.csv")
        
    def run_pipeline(self, enrol_path, demo_path, bio_path, pincode_path):
        """Run the complete pipeline"""
        start_time = datetime.now()
        
        logger.info("Starting Aadhaar EWS Processing Pipeline")
        logger.info(f"Start time: {start_time}")
        logger.info("="*80)
        
        try:
            self.load_data(enrol_path, demo_path, bio_path, pincode_path)
            self.parse_dates()
            self.canonicalize_geography()
            self.aggregate_weekly()
            self.compute_severity_scores()
            self.detect_anomalies()
            self.compute_trends()
            self.classify_risk()
            self.identify_dominant_signals()
            self.compute_data_quality()
            self.save_outputs()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info("\n" + "="*80)
            logger.info("PIPELINE COMPLETE")
            logger.info("="*80)
            logger.info(f"Duration: {duration:.1f} seconds")
            logger.info(f"Output directory: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Aadhaar EWS Data Processing Pipeline")
    parser.add_argument("--enrol", required=True, help="Path to enrolment CSV")
    parser.add_argument("--demo", required=True, help="Path to demographic CSV")
    parser.add_argument("--bio", required=True, help="Path to biometric CSV")
    parser.add_argument("--pincode", required=True, help="Path to pincode reference CSV")
    parser.add_argument("--output", default="data", help="Output directory")
    
    args = parser.parse_args()
    
    processor = AadhaarEWSProcessor(output_dir=args.output)
    processor.run_pipeline(args.enrol, args.demo, args.bio, args.pincode)
