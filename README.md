# Coffee Bean

Coffee Bean is a Streamlit financial statement automation app. Upload a CSV or Excel file, review account classifications, and generate an income statement, balance sheet, financial ratios, charts, and an Excel report.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy with Streamlit Community Cloud

1. Create a GitHub repository and upload `app.py`, `requirements.txt`, `.streamlit/config.toml`, and `sample_financial_data.csv`.
2. Open [share.streamlit.io](https://share.streamlit.io).
3. Select the repository, branch, and `app.py` as the main file.
4. Deploy.

The app starts with a working demo dataset. Users can then upload their own CSV/XLS/XLSX files.

## Input format

The uploaded file must contain an account column such as `Account`, `Description`, or `Particulars`, and a numeric column such as `Amount`, `Balance`, or `Value`. A `Category` column is optional; if omitted, Coffee Bean classifies accounts automatically.
