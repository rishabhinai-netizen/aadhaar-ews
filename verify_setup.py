#!/usr/bin/env python3
"""
Setup Verification Script for Aadhaar EWS
Run this before starting the dashboard to verify everything is set up correctly
"""

import sys
from pathlib import Path
import importlib.util

def check_python_version():
    """Check if Python version is 3.9 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python version {version.major}.{version.minor} detected")
        print("   Requires Python 3.9 or higher")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def check_dependencies():
    """Check if all required packages are installed"""
    required = {
        'streamlit': 'Streamlit',
        'pandas': 'Pandas',
        'numpy': 'NumPy',
        'plotly': 'Plotly',
        'sklearn': 'Scikit-learn',
        'scipy': 'SciPy'
    }
    
    missing = []
    for package, name in required.items():
        spec = importlib.util.find_spec(package)
        if spec is None:
            print(f"❌ {name} not installed")
            missing.append(package if package != 'sklearn' else 'scikit-learn')
        else:
            print(f"✅ {name} installed")
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print(f"   Install with: pip install {' '.join(missing)}")
        return False
    
    return True

def check_directory_structure():
    """Check if all required directories and files exist"""
    current_dir = Path(__file__).parent
    
    required_files = [
        'app.py',
        'requirements.txt',
        'README.md',
        'data/ews_weekly_district_enhanced.csv',
        'data/district_forecasts.csv',
        'data/district_profiles.csv',
        'data/peer_benchmarks.csv',
        'data/geo_cleaning_summary.csv',
        'data/weight_justification.csv',
        'data/top_critical_districts.csv'
    ]
    
    missing = []
    for file_path in required_files:
        full_path = current_dir / file_path
        if not full_path.exists():
            print(f"❌ Missing: {file_path}")
            missing.append(file_path)
        else:
            # Check file size for CSV files
            if file_path.endswith('.csv'):
                size = full_path.stat().st_size
                size_mb = size / (1024 * 1024)
                if size_mb > 0.001:  # At least 1KB
                    print(f"✅ {file_path} ({size_mb:.2f} MB)")
                else:
                    print(f"⚠️  {file_path} exists but might be empty")
            else:
                print(f"✅ {file_path}")
    
    if missing:
        print(f"\n⚠️  Missing files/directories: {len(missing)}")
        return False
    
    return True

def check_data_files():
    """Verify data files can be loaded"""
    import pandas as pd
    
    current_dir = Path(__file__).parent
    data_path = current_dir / 'data'
    
    try:
        # Try loading main file
        main_file = data_path / 'ews_weekly_district_enhanced.csv'
        df = pd.read_csv(main_file)
        print(f"✅ Main data file loaded: {len(df):,} records")
        
        # Check expected columns
        expected_cols = ['week', 'state', 'district', 'risk_category', 'severity_score']
        missing_cols = [col for col in expected_cols if col not in df.columns]
        
        if missing_cols:
            print(f"⚠️  Missing columns in main data: {', '.join(missing_cols)}")
            return False
        
        print(f"✅ Data structure validated")
        return True
        
    except Exception as e:
        print(f"❌ Error loading data files: {e}")
        return False

def main():
    """Run all checks"""
    print("="*60)
    print("Aadhaar EWS - Setup Verification")
    print("="*60)
    print()
    
    print("1. Checking Python version...")
    python_ok = check_python_version()
    print()
    
    print("2. Checking dependencies...")
    deps_ok = check_dependencies()
    print()
    
    print("3. Checking directory structure...")
    dir_ok = check_directory_structure()
    print()
    
    print("4. Validating data files...")
    data_ok = check_data_files()
    print()
    
    print("="*60)
    if python_ok and deps_ok and dir_ok and data_ok:
        print("✅ ALL CHECKS PASSED!")
        print()
        print("You can now run the dashboard:")
        print("   streamlit run app.py")
        print()
        print("The dashboard will open in your browser at:")
        print("   http://localhost:8501")
    else:
        print("❌ SOME CHECKS FAILED")
        print()
        print("Please fix the issues above before running the dashboard.")
        print()
        if not deps_ok:
            print("To install dependencies:")
            print("   pip install -r requirements.txt")
    print("="*60)

if __name__ == "__main__":
    main()
