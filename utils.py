import pandas as pd
import numpy as np

def find_similar_companies(data, threshold=0.1, skip_cols=None, max_results=3):
    """
    For each company (row, indexed by Ticker) and each numeric metric column (excluding skipped columns),
    find other companies with values within a relative threshold.
    
    Parameters:
    - data: pandas DataFrame (companies in 'ticker' column, metrics in other columns)
    - threshold: relative difference to consider "similar" (default 10%)
    - skip_cols: list of column names to ignore (e.g., ['ticker']). Defaults to ['ticker']
    
    Returns:
    - dict: {company: {metric: "similar_str" or "N/A" or "None"}}
    """
    if skip_cols is None:
        skip_cols = ['ticker']
    
    # Set 'ticker' as index if it exists
    if 'ticker' not in data.columns:
        raise ValueError("Column 'ticker' not found in DataFrame")
    data = data.set_index('ticker')
    
    # Keep only numeric columns that are not in skip_cols
    numeric_cols = [
        col for col in data.columns
        if np.issubdtype(data[col].dtype, np.number) and col not in skip_cols
    ]
    
    companies = data.index.values
    result = {company: {} for company in companies}
    
    for company in companies:
        company_row = data.loc[company]
        
        for metric in numeric_cols:
            value = company_row[metric]
            
            # Handle missing / zero values
            if pd.isna(value) or value == 0:
                result[company][metric] = "N/A"
                continue
            
            similar = []
            for other in companies:
                if other == company:
                    continue
                oth_val = data.loc[other, metric]
                
                if pd.isna(oth_val) or oth_val == 0:
                    continue
                
                # Relative similarity check
                if abs(value - oth_val) / abs(value) <= threshold:
                    similar.append(f"{other} ({oth_val:.2f})")
            similar = similar[:max_results]
            result[company][metric] = "\n".join(similar) if similar else "None"
    
    return result