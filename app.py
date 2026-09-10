import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from io import BytesIO
from PIL import Image
import re

# OCR is optional
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Coffee Bean | Financial Statements",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>
    :root {
        --bg: #f7f0e8;
        --panel: #fffdfb;
        --card: #fffaf3;
        --primary: #5d3b2e;
        --primary-dark: #3d281f;
        --accent: #d29a58;
        --accent-soft: #f7e4c5;
        --success: #2e7d5d;
        --text: #2d1e1a;
        --muted: #6f5c56;
        --line: rgba(93,59,46,0.12);
    }

    .stApp {
        background: linear-gradient(180deg, #f8f3ed 0%, #f3eee9 100%);
        color: var(--text);
    }

    .main {
        padding-top: 1rem;
    }

    h1, h2, h3 {
        font-weight: 700;
        color: var(--primary-dark);
    }

    .brand-row {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 0.5rem;
    }

    .brand-logo {
        width: 82px;
        height: 82px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: linear-gradient(135deg, var(--primary) 0%, var(--accent) 100%);
        border-radius: 22px;
        box-shadow: 0 12px 28px rgba(93,59,46,0.18);
        padding: 8px;
    }

    .brand-logo svg {
        width: 100%;
        height: 100%;
    }

    .brand-tag {
        letter-spacing: 0.14em;
        text-transform: uppercase;
        font-size: 0.7rem;
        color: var(--accent);
        font-weight: 700;
        margin-bottom: 4px;
    }

    .metric-card {
        padding: 15px;
        border-radius: 14px;
        border: 1px solid var(--line);
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.82) 0%, rgba(255, 243, 228, 0.9) 100%);
        box-shadow: 0 8px 18px rgba(61, 40, 31, 0.06);
    }

    .stDataFrame, .stTable {
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
    }

    .stMetric {
        background: linear-gradient(180deg, #fffdfb 0%, #fff7ee 100%);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 16px;
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fffaf5 0%, #f4eee8 100%);
        border-right: 1px solid rgba(93, 59, 46, 0.08);
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--primary) 0%, #7a4f39 100%);
        color: white;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.7rem 1rem;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #4a3128 0%, #5d3b2e 100%);
    }

    .sidebar-logo {
        padding: 16px 10px 8px;
        display: flex;
        justify-content: center;
    }

    .sidebar-logo svg {
        width: 110px;
        height: 110px;
    }

</style>
""", unsafe_allow_html=True)


def brand_logo_svg():
    return """
    <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Coffee Bean Financial Logo">
      <defs>
        <linearGradient id="beanGlow" x1="0" x2="1">
          <stop offset="0%" stop-color="#f4d3a2"/>
          <stop offset="100%" stop-color="#d7984a"/>
        </linearGradient>
      </defs>
      <rect x="8" y="8" width="104" height="104" rx="26" fill="#5d3b2e"/>
      <path d="M63 23c-12 0-22 9-22 22 0 10 6 18 13 25 6 6 8 12 8 18 0 8-5 14-13 14-6 0-11-4-13-9-2-5-6-8-12-8-10 0-17 9-17 19 0 16 14 29 31 29 21 0 38-16 38-38 0-10-4-19-12-26-7-7-11-14-11-22 0-6 4-12 11-12 7 0 12 5 12 12 0 6-5 11-11 11h-2v8h2c13 0 22-10 22-22 0-14-11-25-25-25z" fill="url(#beanGlow)" opacity="0.96"/>
      <path d="M77 39c9 4 15 13 15 23 0 12-8 22-20 27" fill="none" stroke="#fff8ee" stroke-width="6" stroke-linecap="round" opacity="0.9"/>
      <path d="M36 80h48" stroke="#fff8ee" stroke-width="6" stroke-linecap="round" opacity="0.8"/>
      <path d="M37 91l9-12 12 9 14-17 16 20" fill="none" stroke="#fff2d7" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
    """


def render_brand_header():
    st.markdown(
        f"""
        <div class="brand-row">
            <div class="brand-logo">{brand_logo_svg()}</div>
            <div>
                <div class="brand-tag">Financial intelligence</div>
                <h1 style="margin: 0; font-size: 2.3rem;">Coffee Bean</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_number(value):
    """
    Convert financial values such as:
    ₹1,20,000
    $50,000
    (25,000)
    10,000
    into numeric values.
    """

    if pd.isna(value):
        return 0.0

    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip()

    if text == "":
        return 0.0

    negative = False

    # Accounting format: (50,000)
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]

    # Remove currency symbols and commas
    text = re.sub(r"[₹$€£,\s]", "", text)

    # Remove other non-numeric characters except . and -
    text = re.sub(r"[^0-9.\-]", "", text)

    try:
        number = float(text)

        if negative:
            number = -abs(number)

        return number

    except:
        return 0.0


def normalize_text(value):
    if pd.isna(value):
        return ""

    return str(value).strip().lower()


def detect_column(df, possible_names):

    normalized_columns = {
        str(col).strip().lower(): col
        for col in df.columns
    }

    for name in possible_names:
        if name.lower() in normalized_columns:
            return normalized_columns[name.lower()]

    return None


def categorize_account(account):

    """
    Automatically classify common financial accounts.
    """

    account = normalize_text(account)

    # Revenue
    if any(x in account for x in [
        "revenue",
        "sales",
        "income from sales",
        "service income",
        "turnover"
    ]):
        return "Revenue"

    # COGS
    if any(x in account for x in [
        "cost of goods",
        "cogs",
        "cost of sales",
        "raw material",
        "purchases"
    ]):
        return "COGS"

    # Operating expenses
    if any(x in account for x in [
        "salary",
        "salaries",
        "wages",
        "rent",
        "advertising",
        "marketing",
        "insurance",
        "office expense",
        "administrative",
        "utilities",
        "travel",
        "selling expense"
    ]):
        return "Operating Expense"

    # Depreciation
    if "depreciation" in account:
        return "Depreciation"

    # Interest
    if any(x in account for x in [
        "interest expense",
        "finance cost",
        "interest payable"
    ]):
        return "Interest"

    # Tax
    if any(x in account for x in [
        "income tax",
        "tax expense",
        "tax payable"
    ]):
        return "Tax"

    # Cash
    if any(x in account for x in [
        "cash",
        "bank balance",
        "cash equivalents"
    ]):
        return "Asset"

    # Other assets
    if any(x in account for x in [
        "receivable",
        "inventory",
        "stock",
        "property",
        "plant",
        "equipment",
        "ppe",
        "investment",
        "prepaid",
        "goodwill"
    ]):
        return "Asset"

    # Liabilities
    if any(x in account for x in [
        "loan",
        "borrowings",
        "payable",
        "creditor",
        "debt",
        "provision",
        "liability"
    ]):
        return "Liability"

    # Equity
    if any(x in account for x in [
        "share capital",
        "capital",
        "retained earnings",
        "reserves",
        "equity"
    ]):
        return "Equity"

    return "Unclassified"


def get_sample_financial_data():
    return pd.DataFrame({
        "Account": [
            "Revenue",
            "Cost of Goods Sold",
            "Salaries",
            "Rent",
            "Marketing",
            "Depreciation",
            "Interest Expense",
            "Cash",
            "Accounts Receivable",
            "Inventory",
            "Bank Loan",
            "Share Capital",
            "Retained Earnings"
        ],
        "Amount": [
            1200000,
            700000,
            180000,
            60000,
            35000,
            20000,
            15000,
            400000,
            200000,
            180000,
            250000,
            500000,
            100000
        ]
    })


def prepare_data(df):

    df = df.copy()

    # Remove completely empty rows
    df = df.dropna(how="all")

    if df.empty:
        raise ValueError("The uploaded file contains no usable data.")

    # Find account column
    account_col = detect_column(
        df,
        [
            "Account",
            "Account Name",
            "Description",
            "Particulars",
            "Ledger",
            "Item",
            "Name"
        ]
    )

    # Find amount column
    amount_col = detect_column(
        df,
        [
            "Amount",
            "Balance",
            "Value",
            "Debit",
            "Credit",
            "Amount (₹)",
            "Amount INR"
        ]
    )

    # Find category column
    category_col = detect_column(
        df,
        [
            "Category",
            "Type",
            "Account Type",
            "Classification"
        ]
    )

    if account_col is None:
        raise ValueError(
            "Could not find an Account/Description/Particulars column."
        )

    if amount_col is None:
        raise ValueError(
            "Could not find an Amount/Balance/Value column."
        )

    # Rename
    df = df.rename(
        columns={
            account_col: "Account",
            amount_col: "Amount"
        }
    )

    # Clean amounts
    df["Amount"] = df["Amount"].apply(clean_number)

    # Category
    if category_col is not None:

        df = df.rename(
            columns={category_col: "Category"}
        )

        df["Category"] = (
            df["Category"]
            .astype(str)
            .str.strip()
        )

    else:

        df["Category"] = df["Account"].apply(
            categorize_account
        )

    return df


# ============================================================
# FINANCIAL CALCULATIONS
# ============================================================

def calculate_financials(df):

    categories = (
        df["Category"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    def total(category):
        return df.loc[
            categories == category.lower(),
            "Amount"
        ].sum()

    revenue = total("Revenue")
    cogs = total("COGS")
    opex = total("Operating Expense")
    depreciation = total("Depreciation")
    interest = total("Interest")
    tax = total("Tax")

    assets = total("Asset")
    liabilities = total("Liability")
    equity = total("Equity")

    gross_profit = revenue - cogs

    operating_income = (
        gross_profit
        - opex
        - depreciation
    )

    profit_before_tax = (
        operating_income
        - interest
    )

    net_income = (
        profit_before_tax
        - tax
    )

    balance_difference = (
        assets - liabilities - equity
    )

    return {
        "revenue": revenue,
        "cogs": cogs,
        "opex": opex,
        "depreciation": depreciation,
        "interest": interest,
        "tax": tax,
        "assets": assets,
        "liabilities": liabilities,
        "equity": equity,
        "gross_profit": gross_profit,
        "operating_income": operating_income,
        "profit_before_tax": profit_before_tax,
        "net_income": net_income,
        "balance_difference": balance_difference
    }


# ============================================================
# INCOME STATEMENT
# ============================================================

def create_income_statement(fin):

    return pd.DataFrame({

        "Particulars": [
            "Revenue",
            "Cost of Goods Sold",
            "Gross Profit",
            "Operating Expenses",
            "Depreciation",
            "Operating Income",
            "Interest Expense",
            "Profit Before Tax",
            "Tax",
            "Net Income"
        ],

        "Amount": [
            fin["revenue"],
            -fin["cogs"],
            fin["gross_profit"],
            -fin["opex"],
            -fin["depreciation"],
            fin["operating_income"],
            -fin["interest"],
            fin["profit_before_tax"],
            -fin["tax"],
            fin["net_income"]
        ]
    })


# ============================================================
# BALANCE SHEET
# ============================================================

def create_balance_sheet(fin):

    total_liabilities_equity = (
        fin["liabilities"] +
        fin["equity"]
    )

    return pd.DataFrame({

        "Particulars": [
            "Total Assets",
            "Total Liabilities",
            "Total Equity",
            "Liabilities + Equity",
            "Balance Difference"
        ],

        "Amount": [
            fin["assets"],
            fin["liabilities"],
            fin["equity"],
            total_liabilities_equity,
            fin["balance_difference"]
        ]
    })


# ============================================================
# RATIOS
# ============================================================

def create_ratios(fin):

    revenue = fin["revenue"]

    gross_margin = (
        fin["gross_profit"] / revenue
        if revenue != 0 else 0
    )

    operating_margin = (
        fin["operating_income"] / revenue
        if revenue != 0 else 0
    )

    net_margin = (
        fin["net_income"] / revenue
        if revenue != 0 else 0
    )

    debt_equity = (
        fin["liabilities"] / fin["equity"]
        if fin["equity"] != 0 else 0
    )

    return pd.DataFrame({

        "Ratio": [
            "Gross Profit Margin",
            "Operating Margin",
            "Net Profit Margin",
            "Debt-to-Equity"
        ],

        "Value": [
            f"{gross_margin:.2%}",
            f"{operating_margin:.2%}",
            f"{net_margin:.2%}",
            f"{debt_equity:.2f}x"
        ]
    })


# ============================================================
# EXCEL EXPORT
# ============================================================

def create_excel(df, income, balance, ratios):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            sheet_name="Processed Data",
            index=False
        )

        income.to_excel(
            writer,
            sheet_name="Income Statement",
            index=False
        )

        balance.to_excel(
            writer,
            sheet_name="Balance Sheet",
            index=False
        )

        ratios.to_excel(
            writer,
            sheet_name="Ratios",
            index=False
        )

    return output.getvalue()


# ============================================================
# HEADER
# ============================================================

render_brand_header()

st.markdown(
    """
    <div style="margin-top: 0.25rem; margin-bottom: 1rem; color: #6f5c56; font-size: 1.05rem;">
        Turn raw accounting data into polished financial statements, insights, and export-ready reports.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-logo">{}</div>
        """.format(brand_logo_svg()),
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="text-align:center; font-weight:700; font-size:1.2rem; color:#3d281f; margin-bottom: 0.5rem;">Coffee Bean</div>
        """,
        unsafe_allow_html=True,
    )

    st.header("⚙️ Settings")

    currency = st.selectbox(
        "Currency",
        ["₹", "$", "€", "£"]
    )

    st.divider()

    st.subheader("OCR Settings")

    if OCR_AVAILABLE:

        tesseract_path = st.text_input(
            "Tesseract path (optional)",
            placeholder="C:\\Program Files\\Tesseract-OCR\\tesseract.exe"
        )

        if tesseract_path:
            try:
                pytesseract.pytesseract.tesseract_cmd = (
                    tesseract_path
                )
            except Exception:
                pass

    else:

        st.warning(
            "pytesseract is not installed. "
            "Run: pip install pytesseract"
        )


# ============================================================
# INPUT METHODS
# ============================================================

st.subheader("📥 Import Financial Data")

tab1, tab2, tab3 = st.tabs([
    "📁 File Upload",
    "📷 Camera",
    "🖼️ Picture Upload"
])


uploaded_file = None
uploaded_image = None


# ------------------------------------------------------------
# FILE UPLOAD
# ------------------------------------------------------------

with tab1:

    uploaded_file = st.file_uploader(
        "Upload Excel or CSV",
        type=[
            "xlsx",
            "xls",
            "csv"
        ],
        key="financial_file"
    )


# ------------------------------------------------------------
# CAMERA
# ------------------------------------------------------------

with tab2:

    camera_image = st.camera_input(
        "Take a picture of your financial statement"
    )

    if camera_image is not None:

        uploaded_image = camera_image

        image = Image.open(camera_image)

        st.image(
            image,
            caption="Captured financial statement",
            use_container_width=True
        )


# ------------------------------------------------------------
# IMAGE UPLOAD
# ------------------------------------------------------------

with tab3:

    picture = st.file_uploader(
        "Upload a financial statement picture",
        type=[
            "png",
            "jpg",
            "jpeg",
            "webp"
        ],
        key="financial_image"
    )

    if picture is not None:

        uploaded_image = picture

        image = Image.open(picture)

        st.image(
            image,
            caption="Uploaded financial statement",
            use_container_width=True
        )


# ============================================================
# OCR PROCESSING
# ============================================================

if uploaded_image is not None:

    st.subheader("🔎 Extract Data From Image")

    if not OCR_AVAILABLE:

        st.error(
            "OCR is unavailable because pytesseract is not installed."
        )

    else:

        if st.button(
            "🔍 Extract Financial Data",
            type="primary"
        ):

            try:

                image = Image.open(
                    uploaded_image
                )

                with st.spinner(
                    "Reading financial statement..."
                ):

                    extracted_text = pytesseract.image_to_string(
                        image
                    )

                if extracted_text.strip():

                    st.success(
                        "Text extracted successfully."
                    )

                    st.text_area(
                        "Extracted text",
                        extracted_text,
                        height=300
                    )

                    st.info(
                        "OCR extracts text from the image. "
                        "For automatic statement generation, "
                        "Excel/CSV data is more reliable."
                    )

                else:

                    st.warning(
                        "No readable text was detected. "
                        "Try a clearer image."
                    )

            except Exception as e:

                st.error(
                    f"OCR error: {e}"
                )


def process_dataframe(df_raw, source_name, currency):
    df = prepare_data(df_raw)

    st.success(
        f"Financial data imported successfully from {source_name}."
    )

    st.subheader("🧠 Account Classification")
    st.write(
        "Review or modify the automatically assigned categories."
    )

    categories_available = [
        "Revenue",
        "COGS",
        "Operating Expense",
        "Depreciation",
        "Interest",
        "Tax",
        "Asset",
        "Liability",
        "Equity",
        "Unclassified"
    ]

    edited_df = st.data_editor(
        df,
        column_config={
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=categories_available,
                required=True
            ),
            "Amount": st.column_config.NumberColumn(
                "Amount",
                format="%.2f"
            )
        },
        num_rows="dynamic",
        use_container_width=True
    )

    df = edited_df
    fin = calculate_financials(df)
    income_statement = create_income_statement(fin)
    balance_sheet = create_balance_sheet(fin)
    ratios = create_ratios(fin)

    st.divider()
    st.header("📈 Financial Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Revenue", f"{currency}{fin['revenue']:,.0f}")
    col2.metric("Gross Profit", f"{currency}{fin['gross_profit']:,.0f}")
    col3.metric("Operating Income", f"{currency}{fin['operating_income']:,.0f}")
    col4.metric("Net Income", f"{currency}{fin['net_income']:,.0f}")

    st.header("📑 Income Statement")
    income_display = income_statement.copy()
    income_display["Amount"] = income_display["Amount"].apply(
        lambda x: f"{currency}{x:,.2f}"
    )
    st.dataframe(income_display, use_container_width=True, hide_index=True)

    st.header("🏦 Balance Sheet")
    balance_display = balance_sheet.copy()
    balance_display["Amount"] = balance_display["Amount"].apply(
        lambda x: f"{currency}{x:,.2f}"
    )
    st.dataframe(balance_display, use_container_width=True, hide_index=True)

    difference = abs(fin["balance_difference"])
    if difference < 0.01:
        st.success("✅ Balance Sheet checks: Assets = Liabilities + Equity")
    else:
        st.warning(
            f"⚠️ Balance Sheet does not balance. Difference = {currency}{fin['balance_difference']:,.2f}"
        )

    st.header("📊 Financial Ratios")
    st.dataframe(ratios, use_container_width=True, hide_index=True)

    chart_data = pd.DataFrame({
        "Metric": ["Revenue", "Gross Profit", "Operating Income", "Net Income"],
        "Amount": [
            fin["revenue"],
            fin["gross_profit"],
            fin["operating_income"],
            fin["net_income"]
        ]
    })

    st.header("📊 Profitability Analysis")
    fig = px.bar(chart_data, x="Metric", y="Amount", title="Profitability Overview")
    st.plotly_chart(fig, use_container_width=True)

    st.header("🔍 Account Breakdown")
    category_summary = df.groupby("Category")["Amount"].sum().reset_index()
    fig2 = px.pie(
        category_summary,
        names="Category",
        values="Amount",
        title="Financial Category Distribution"
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.header("📥 Export")
    excel_data = create_excel(df, income_statement, balance_sheet, ratios)
    st.download_button(
        label="📥 Download Complete Excel Report",
        data=excel_data,
        file_name="Automated_Financial_Statements.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )


# ============================================================
# FILE PROCESSING
# ============================================================

sample_data = None

demo_data = st.button("Load demo financial data", type="primary")
if demo_data:
    sample_data = get_sample_financial_data()

if uploaded_file is not None:

    try:
        if uploaded_file.name.lower().endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file)
        else:
            df_raw = pd.read_excel(uploaded_file)

        process_dataframe(df_raw, "uploaded file", currency)

    except Exception as e:

        st.error("⚠️ The application could not process this file.")
        st.exception(e)
        st.info(
            """
            Try checking that your file contains:

            • Account / Description / Particulars
            • Amount / Balance / Value

            Example:

            Account | Amount
            Revenue | 100000
            Salaries | 25000
            Cash | 50000
            Bank Loan | 30000
            Share Capital | 20000
            """
        )

elif sample_data is not None:
    process_dataframe(sample_data, "demo dataset", currency)


# ============================================================
# EMPTY STATE
# ============================================================

if uploaded_file is None and uploaded_image is None and sample_data is None:

    st.info(
        """
        👆 Choose an input method above or use the demo data.

        📁 Excel/CSV → Best option for accurate automation

        📷 Camera → Photograph a financial statement

        🖼️ Picture → Upload a screenshot/photo

        🧪 Demo data → Load a working sample to see the app report immediately

        The application will then clean, classify and analyze
        the financial data.
        """
    )