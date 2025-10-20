import streamlit as st
import pandas as pd
import requests
import json
import io
from model import analyze_report
from utils import find_similar_companies

# Set the layout for the page
st.set_page_config(layout="wide")

# Utils
def format_number(val):
    try:
        val = float(val)
        return f"{int(val):,}" if val.is_integer() else f"{val:,.2f}"
    except Exception:
        return val

# Read definitions from definitions.json
with open("/Users/minhquan/Documents/SIIF/definitions.json", "r", encoding="utf-8") as f:
    definitions_data = json.load(f)
    # Create a dictionary mapping metric id, name, and aliases to definitions
    definitions = {}
    for metric in definitions_data["metrics"]:
        definitions[metric["id"]] = metric["definition"]
        definitions[metric["name"]] = metric["definition"]
        for alias in metric.get("aliases", []):
            definitions[alias] = metric["definition"]

# Paths to your combined data
DATA_DIR = "/Users/minhquan/Documents/SIIF/combined_data"
files = {
    "Financial Data": f"{DATA_DIR}/financial_data.csv",
    "Balance Sheet": f"{DATA_DIR}/balance_sheets.csv",
    "Cash Flow": f"{DATA_DIR}/cash_flow.csv",
    "Sector Means": f"{DATA_DIR}/sector_means.csv"
}

# Read the CSS design
css_path = "/Users/minhquan/Documents/SIIF/styles.css"
with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


with st.sidebar.expander("Navigation", expanded=True):
    page = st.radio("Go to", ["Financial Dashboard", "Report Analyst"], label_visibility="collapsed")

# Logic of the page
if page == "Financial Dashboard":
    st.title("Company Financial Dashboard")

    # Load Sector Means data and Ticker-to-Sector map
    sector_means_df = pd.DataFrame()
    ticker_to_sector = {}
    try:
        # Load Sector Means: Assuming the sector name is the index/key
        sector_means_path = files["Sector Means"]
        sector_means_df = pd.read_csv(sector_means_path)
        # Assuming the sector column is 'sector'
        if 'sector' in sector_means_df.columns:
            sector_means_df = sector_means_df.set_index('sector')
        else:
            # Fallback assumption if the sector is the first column and not named
            sector_means_df = sector_means_df.rename(columns={sector_means_df.columns[0]: 'sector'}).set_index('sector')

        # Load Ticker-Sector Map (assuming it's in financial_data.csv)
        financial_df = pd.read_csv(files["Financial Data"])
        if 'ticker' in financial_df.columns and 'sector' in financial_df.columns:
            ticker_to_sector = financial_df.set_index('ticker')['sector'].to_dict()
        del financial_df

    except Exception as e:
        st.error(f"Error loading data for Industry Average feature: {e}")

    ticker = st.text_input("Enter ASX Ticker (e.g., NAB, CBA, ANZ):").strip().upper()

    if ticker:
        # Determine the company's sector and corresponding sector average row
        company_sector = ticker_to_sector.get(ticker)
        sector_average_row = sector_means_df.loc[company_sector] if company_sector in sector_means_df.index else None

        for section, path in files.items():
            st.subheader(section)

            if section == "Sector Means":
                continue

            try:
                df = pd.read_csv(path)

                if ticker not in df['ticker'].values:
                    st.warning(f"{ticker} not found in {section}")
                    continue

                # Run find_similar_companies for this dataset
                similarity_results = find_similar_companies(df, threshold=0.1)

                row = df[df['ticker'] == ticker].iloc[0]
                # Drop 'ticker' and 'sector' (if present) before processing metrics
                cols_to_drop = ['ticker']
                if 'sector' in row.index:
                    cols_to_drop.append('sector')
                row = row.drop(cols_to_drop, errors='ignore').dropna()

                if row.empty:
                    st.info("No available data.")
                else:
                    industry_averages = []
                    for metric in row.index:
                        avg_value = "N/A"
                        if sector_average_row is not None and metric in sector_average_row.index:
                            avg_value = format_number(sector_average_row[metric])
                        industry_averages.append(avg_value)
        

                    clean_df = pd.DataFrame({
                        "Metric": row.index,
                        "Value": [format_number(v) for v in row.values],
                        "Similar Companies": [similarity_results.get(ticker, {}).get(metric, "N/A") for metric in row.index],
                        "Industry Average": industry_averages
                    })

                    # Create a table-like layout using columns with borders
                    with st.container():
                        # Header row
                        st.markdown('<div class="table-header">', unsafe_allow_html=True)
                        col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 3, 2])
                        with col1:
                            st.markdown('<div class="table-cell metric">Metric</div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown('<div class="table-cell value">Value</div>', unsafe_allow_html=True)
                        with col3:
                            st.markdown('<div class="table-cell notes">Notes</div>', unsafe_allow_html=True)
                        with col4:
                            st.markdown('<div class="table-cell similar">Similar Companies</div>', unsafe_allow_html=True)
                        with col5:
                            st.markdown('<div class="table-cell spacer">Industry Average</div>', unsafe_allow_html=True)
                        st.markdown('</div>', unsafe_allow_html=True)

                        # Data rows
                        for idx, row in clean_df.iterrows():
                            st.markdown('<div class="table-row">', unsafe_allow_html=True)
                           
                            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 3, 2])
                            with col1:
                                st.markdown(f'<div class="table-cell metric">{row["Metric"]}</div>', unsafe_allow_html=True)
                            with col2:
                                st.markdown(f'<div class="table-cell value">{row["Value"]}</div>', unsafe_allow_html=True)
                            with col3:
                                with st.popover("View"):
                                    definition = definitions.get(row["Metric"], "No definition available")
                                    st.markdown(definition)
                            with col4:
                                st.markdown(f'<div class="table-cell similar">{row["Similar Companies"]}</div>', unsafe_allow_html=True)
                            # --- NEW DATA COLUMN ---
                            with col5:
                                st.markdown(f'<div class="table-cell industry-avg">{row["Industry Average"]}</div>', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"Error loading {section}: {e}")

elif page == "Report Analyst":
    st.title("Report Analyst")

    colL, colR = st.columns([2, 1])
    with colL:
        uploaded = st.file_uploader("Upload financial report (.pdf or .txt)", type=["pdf", "txt"])
    with colR:
        ticker = st.text_input("Ticker (optional)", placeholder="e.g., CBA, NAB")
        user_note = st.text_area("Anything to focus on? (optional)", height=90)

    analyze = st.button("Analyze report", type="primary", disabled=uploaded is None)

    if analyze:
        with st.spinner("Analyzing…"):
            result = analyze_report(uploaded, ticker, user_note)
            st.markdown(result)
