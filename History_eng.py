import datetime
import html
import io
import os
import re

import pandas as pd
import streamlit as st

from app_helper import show_app_dev_info


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Scan History",
    page_icon="📋",
    layout="wide",
)

show_app_dev_info()


# =========================================================
# CONFIGURATION
# =========================================================

DATA_DIR = "data"

SHOPEE_PREFIX = "SPXID06"
SHOPEE_DIGITS = 10

JNT_PREFIX = "J"
JNT_REMAINING_CHARS = 11

ANTERAJA_PREFIX = "1"
ANTERAJA_LENGTH = 14

COURIER_OPTIONS = [
    "All",
    "Shopee SPX",
    "J&T Express",
    "AnterAja",
]

SHOPEE_PATTERN = re.compile(
    rf"^{re.escape(SHOPEE_PREFIX)}"
    rf"\d{{{SHOPEE_DIGITS}}}$"
)

JNT_PATTERN = re.compile(
    rf"^{re.escape(JNT_PREFIX)}"
    rf"[A-Z0-9]{{{JNT_REMAINING_CHARS}}}$"
)

ANTERAJA_PATTERN = re.compile(
    rf"^{re.escape(ANTERAJA_PREFIX)}"
    rf"\d{{{ANTERAJA_LENGTH - 1}}}$"
)


def detect_courier(barcode):
    """
    Detect courier from Dispatcher ID.

    Shopee SPX:
        SPXID06 + 10 digits

    J&T Express:
        12 characters total
        starts with J
        remaining characters A-Z / 0-9

    AnterAja:
        14 digits total
        starts with 1
    """

    if barcode is None:
        return "Unknown"

    barcode = (
        str(barcode)
        .strip()
        .upper()
    )

    if SHOPEE_PATTERN.fullmatch(
        barcode
    ):
        return "Shopee SPX"

    if JNT_PATTERN.fullmatch(
        barcode
    ):
        return "J&T Express"

    if ANTERAJA_PATTERN.fullmatch(
        barcode
    ):
        return "AnterAja"

    return "Unknown"


os.makedirs(
    DATA_DIR,
    exist_ok=True,
)


# =========================================================
# PAGE STYLE
# =========================================================

st.markdown(
    """
<style>

/* ---------------------------------------------------------
   MAIN PAGE
--------------------------------------------------------- */

.block-container {
    max-width: 1200px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

[data-testid="stHeader"] {
    background: transparent;
}


/* ---------------------------------------------------------
   HEADER
--------------------------------------------------------- */

.page-title {
    font-size: 2.15rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin-bottom: 0.15rem;
}

.page-subtitle {
    font-size: 0.95rem;
    opacity: 0.65;
    margin-bottom: 1.4rem;
}


/* ---------------------------------------------------------
   TABS
--------------------------------------------------------- */

button[data-baseweb="tab"] {
    font-size: 0.95rem;
    font-weight: 700;
}

div[data-baseweb="tab-list"] {
    gap: 8px;
}


/* ---------------------------------------------------------
   SECTION TITLES
--------------------------------------------------------- */

.section-title {
    font-size: 1.2rem;
    font-weight: 800;
    margin-top: 1.2rem;
    margin-bottom: 0.15rem;
}

.section-subtitle {
    font-size: 0.87rem;
    opacity: 0.60;
    margin-bottom: 1rem;
}


/* ---------------------------------------------------------
   INPUT LABEL
--------------------------------------------------------- */

.input-label {
    font-size: 0.76rem;
    font-weight: 750;
    letter-spacing: 0.08em;
    opacity: 0.60;
    margin-top: 1rem;
    margin-bottom: 5px;
}


/* ---------------------------------------------------------
   SEARCH INPUT
--------------------------------------------------------- */

div[data-testid="stTextInput"] input {
    min-height: 52px !important;
    border-radius: 14px !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}


/* ---------------------------------------------------------
   EMPTY STATE
--------------------------------------------------------- */

.empty-card {
    border: 1px dashed rgba(100, 116, 139, 0.30);
    background: rgba(100, 116, 139, 0.04);
    border-radius: 20px;
    padding: 42px 24px;
    text-align: center;
    margin-top: 18px;
}

.empty-icon {
    font-size: 2.3rem;
    margin-bottom: 10px;
}

.empty-title {
    font-size: 1.18rem;
    font-weight: 800;
    margin-bottom: 5px;
}

.empty-text {
    font-size: 0.9rem;
    opacity: 0.65;
}


/* ---------------------------------------------------------
   EXACT MATCH CARD
--------------------------------------------------------- */

.match-card {
    border: 1px solid rgba(34, 197, 94, 0.25);
    background: rgba(34, 197, 94, 0.07);
    border-radius: 18px;
    padding: 18px 20px;
    margin-top: 18px;
    margin-bottom: 8px;
}

.match-label {
    font-size: 0.75rem;
    font-weight: 750;
    letter-spacing: 0.08em;
    opacity: 0.60;
}

.match-id {
    font-size: 1.25rem;
    font-weight: 800;
    margin-top: 5px;
}


/* ---------------------------------------------------------
   DOWNLOAD
--------------------------------------------------------- */

.download-title {
    font-size: 1rem;
    font-weight: 750;
    margin-top: 1.2rem;
    margin-bottom: 0.3rem;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
<div class="page-title">
📋 Scan History
</div>

<div class="page-subtitle">
Browse successful scans by date or search for a Dispatcher ID
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# DATA HELPERS
# =========================================================

@st.cache_data(
    show_spinner=False
)
def load_scan_file(
    file_path,
    modified_time,
):
    """
    Load one daily CSV.

    modified_time is included in the cache key so Streamlit
    automatically reloads the file after new scans are added.
    """

    return pd.read_csv(
        file_path,
        names=[
            "Barcode_ID",
            "Timestamp",
        ],
        dtype=str,
    )


def read_scan_file(file_path):
    """
    Safely load and clean a daily scan file.
    """

    if not os.path.exists(
        file_path
    ):
        return pd.DataFrame(
            columns=[
                "Barcode_ID",
                "Timestamp",
            ]
        )

    try:

        modified_time = os.path.getmtime(
            file_path
        )

        df = load_scan_file(
            file_path,
            modified_time,
        ).copy()

    except Exception:

        return pd.DataFrame(
            columns=[
                "Barcode_ID",
                "Timestamp",
            ]
        )

    if df.empty:
        return df

    df["Barcode_ID"] = (
        df["Barcode_ID"]
        .astype(str)
        .str.strip()
    )

    df["Courier"] = (
        df["Barcode_ID"]
        .map(
            detect_courier
        )
    )

    df["Timestamp"] = pd.to_datetime(
        df["Timestamp"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "Timestamp",
        ]
    )

    df = df[
        df["Barcode_ID"] != ""
    ]

    return df.reset_index(
        drop=True
    )


# =========================================================
# EXCEL CREATOR
# =========================================================

def create_excel_file(
    dataframe,
    sheet_name,
):
    """
    Create an Excel file with:

        dispatcher_id
        courier
        date
    """

    download_df = dataframe[
        [
            "Barcode_ID",
            "Courier",
            "Timestamp",
        ]
    ].copy()

    download_df["Timestamp"] = (
        download_df["Timestamp"]
        .dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    download_df = download_df.rename(
        columns={
            "Barcode_ID": "dispatcher_id",
            "Courier": "courier",
            "Timestamp": "date",
        }
    )

    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(
        excel_buffer,
        engine="xlsxwriter",
    ) as writer:

        download_df.to_excel(
            writer,
            index=False,
            sheet_name=sheet_name,
        )

        workbook = writer.book

        worksheet = writer.sheets[
            sheet_name
        ]

        header_format = workbook.add_format(
            {
                "bold": True,
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )

        for column_number, column_name in enumerate(
            download_df.columns
        ):

            worksheet.write(
                0,
                column_number,
                column_name,
                header_format,
            )

        worksheet.set_column(
            "A:A",
            25,
        )

        worksheet.set_column(
            "B:B",
            18,
        )

        worksheet.set_column(
            "C:C",
            22,
        )

        worksheet.freeze_panes(
            1,
            0,
        )

        if len(download_df) > 0:

            worksheet.autofilter(
                0,
                0,
                len(download_df),
                len(download_df.columns) - 1,
            )

    excel_buffer.seek(0)

    return excel_buffer.getvalue()


# =========================================================
# TABS
# =========================================================

date_tab, barcode_tab = st.tabs(
    [
        "📅 History by Date",
        "🔎 Search by Barcode ID",
    ]
)


# =========================================================
# TAB 1 — HISTORY BY DATE
# =========================================================

with date_tab:

    st.markdown(
        """
<div class="input-label">
SELECT SCAN DATE
</div>
""",
        unsafe_allow_html=True,
    )

    date_col, courier_col = st.columns(
        [2, 1]
    )

    with date_col:

        selected_date = st.date_input(
            "Select scan date",
            value=datetime.date.today(),
            max_value=datetime.date.today(),
            key="history_selected_date",
            label_visibility="collapsed",
        )

    with courier_col:

        selected_courier = st.selectbox(
            "Courier",
            COURIER_OPTIONS,
            index=0,
            key="history_courier_filter",
            label_visibility="collapsed",
        )

    selected_date_str = (
        selected_date.isoformat()
    )

    selected_file = os.path.join(
        DATA_DIR,
        f"{selected_date_str}.csv",
    )


    # =====================================================
    # NO FILE
    # =====================================================

    if not os.path.exists(
        selected_file
    ):

        st.markdown(
            f"""
<div class="empty-card">

<div class="empty-icon">
📭
</div>

<div class="empty-title">
No scans found
</div>

<div class="empty-text">
There are no successful scans recorded for
<strong>{selected_date_str}</strong>.
</div>

</div>
""",
            unsafe_allow_html=True,
        )


    else:

        # =================================================
        # LOAD
        # =================================================

        df_date = read_scan_file(
            selected_file
        )

        if (
            selected_courier
            != "All"
        ):

            df_date = (
                df_date[
                    df_date["Courier"]
                    == selected_courier
                ]
                .reset_index(
                    drop=True
                )
            )


        # =================================================
        # EMPTY
        # =================================================

        if df_date.empty:

            st.markdown(
                f"""
<div class="empty-card">

<div class="empty-icon">
📭
</div>

<div class="empty-title">
No valid scans found
</div>

<div class="empty-text">
The scan file for <strong>{selected_date_str}</strong>
does not contain any valid records.
</div>

</div>
""",
                unsafe_allow_html=True,
            )


        else:

            # =================================================
            # SORT
            # =================================================

            df_date = (
                df_date.sort_values(
                    "Timestamp",
                    ascending=False,
                )
                .reset_index(
                    drop=True
                )
            )


            # =================================================
            # SUMMARY
            # =================================================

            total_scans = len(
                df_date
            )

            first_scan = (
                df_date["Timestamp"]
                .min()
                .strftime(
                    "%H:%M:%S"
                )
            )

            latest_scan = (
                df_date["Timestamp"]
                .max()
                .strftime(
                    "%H:%M:%S"
                )
            )


            st.markdown(
                f"""
<div class="section-title">
Daily Summary
</div>

<div class="section-subtitle">
Successful scans recorded on {selected_date_str} · Courier: {selected_courier}
</div>
""",
                unsafe_allow_html=True,
            )


            metric1, metric2, metric3 = (
                st.columns(3)
            )


            with metric1:

                st.metric(
                    "Successful scans",
                    f"{total_scans:,}",
                )


            with metric2:

                st.metric(
                    "First scan",
                    first_scan,
                )


            with metric3:

                st.metric(
                    "Latest scan",
                    latest_scan,
                )


            # =================================================
            # TABLE
            # =================================================

            st.markdown(
                f"""
<div class="section-title">
Scans — {selected_date_str}
</div>

<div class="section-subtitle">
All successful Dispatcher IDs for the selected date
</div>
""",
                unsafe_allow_html=True,
            )


            display_df = (
                df_date.copy()
            )


            display_df.insert(
                0,
                "No.",
                range(
                    1,
                    len(display_df) + 1,
                ),
            )


            display_df["Timestamp"] = (
                display_df["Timestamp"]
                .dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )


            display_df = (
                display_df.rename(
                    columns={
                        "Barcode_ID":
                            "Dispatcher ID",
                        "Timestamp":
                            "Date",
                    }
                )
            )


            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "No.": (
                        st.column_config.NumberColumn(
                            "No.",
                            width="small",
                        )
                    ),
                    "Dispatcher ID": (
                        st.column_config.TextColumn(
                            "Dispatcher ID",
                            width="large",
                        )
                    ),
                    "Courier": (
                        st.column_config.TextColumn(
                            "Courier",
                            width="medium",
                        )
                    ),
                    "Date": (
                        st.column_config.TextColumn(
                            "Date",
                            width="medium",
                        )
                    ),
                },
            )


            # =================================================
            # EXCEL DOWNLOAD
            # =================================================

            excel_data = (
                create_excel_file(
                    df_date,
                    "Scan_History",
                )
            )


            st.markdown(
                """
<div class="download-title">
Export scan history
</div>
""",
                unsafe_allow_html=True,
            )


            st.download_button(
                label=(
                    f"⬇️ Download "
                    f"{selected_date_str} "
                    f"Scan History"
                ),
                data=excel_data,
                file_name=(
                    f"dispatcher_scans_"
                    f"{selected_date_str}.xlsx"
                ),
                mime=(
                    "application/"
                    "vnd.openxmlformats-"
                    "officedocument."
                    "spreadsheetml.sheet"
                ),
                use_container_width=True,
                key="date_history_download",
            )


# =========================================================
# TAB 2 — SEARCH BY BARCODE
# =========================================================

with barcode_tab:

    st.markdown(
        """
<div class="input-label">
SEARCH DISPATCHER ID
</div>
""",
        unsafe_allow_html=True,
    )


    with st.form(
        "barcode_search_form",
        clear_on_submit=False,
    ):

        search_col, search_courier_col = st.columns(
            [2, 1]
        )

        with search_col:

            barcode_query = st.text_input(
                "Search Dispatcher ID",
                placeholder=(
                    "Enter full or partial ID — "
                    "Shopee, J&T, or AnterAja"
                ),
                key="barcode_history_search",
                label_visibility="collapsed",
            )

        with search_courier_col:

            search_courier = st.selectbox(
                "Courier",
                COURIER_OPTIONS,
                index=0,
                key="barcode_courier_filter",
                label_visibility="collapsed",
            )

        search_submitted = st.form_submit_button(
            "🔎 Search",
            use_container_width=True,
        )


    barcode_query = (
        barcode_query
        .strip()
        .upper()
    )


    # =====================================================
    # WAITING
    # =====================================================

    if (
        not search_submitted
        or not barcode_query
    ):

        st.markdown(
            """
<div class="empty-card">

<div class="empty-icon">
🔎
</div>

<div class="empty-title">
Search scan history
</div>

<div class="empty-text">
Enter a full or partial Dispatcher ID, choose a courier if needed, then press Search.
</div>

</div>
""",
            unsafe_allow_html=True,
        )


    else:

        # =================================================
        # SEARCH ALL DAILY FILES
        # =================================================

        matching_records = []


        try:

            data_files = [
                entry
                for entry
                in os.scandir(DATA_DIR)
                if (
                    entry.is_file()
                    and entry.name.lower()
                    .endswith(".csv")
                )
            ]

        except Exception as exc:

            st.error(
                f"Could not access scan data: {exc}"
            )

            data_files = []


        for entry in data_files:

            file_path = (
                entry.path
            )

            file_date = (
                os.path.splitext(
                    entry.name
                )[0]
            )


            df_file = read_scan_file(
                file_path
            )


            if df_file.empty:
                continue

            if (
                search_courier
                != "All"
            ):

                df_file = df_file[
                    df_file["Courier"]
                    == search_courier
                ].copy()

                if df_file.empty:
                    continue


            matching = df_file[
                df_file[
                    "Barcode_ID"
                ]
                .str.contains(
                    barcode_query,
                    case=False,
                    na=False,
                    regex=False,
                )
            ].copy()


            if matching.empty:
                continue


            matching[
                "Scan_Date"
            ] = file_date


            matching_records.append(
                matching
            )


        # =================================================
        # NO RESULTS
        # =================================================

        if not matching_records:

            safe_query = html.escape(
                barcode_query
            )


            st.markdown(
                f"""
<div class="empty-card">

<div class="empty-icon">
🔍
</div>

<div class="empty-title">
No matching scans
</div>

<div class="empty-text">
No scan history was found for
<strong>{safe_query}</strong>.
</div>

</div>
""",
                unsafe_allow_html=True,
            )


        else:

            # =================================================
            # COMBINE RESULTS
            # =================================================

            result = pd.concat(
                matching_records,
                ignore_index=True,
            )


            result = (
                result.sort_values(
                    "Timestamp",
                    ascending=False,
                )
                .reset_index(
                    drop=True
                )
            )


            # =================================================
            # METRICS
            # =================================================

            matching_count = len(
                result
            )

            unique_ids = (
                result["Barcode_ID"]
                .nunique()
            )


            st.markdown(
                f"""
<div class="section-title">
Search Results
</div>

<div class="section-subtitle">
Matching successful scans across all dates · Courier: {search_courier}
</div>
""",
                unsafe_allow_html=True,
            )


            search_metric1, search_metric2 = (
                st.columns(2)
            )


            with search_metric1:

                st.metric(
                    "Matching records",
                    matching_count,
                )


            with search_metric2:

                st.metric(
                    "Matching Dispatcher IDs",
                    unique_ids,
                )


            # =================================================
            # RESULTS TABLE
            # =================================================

            display_result = (
                result.copy()
            )


            display_result.insert(
                0,
                "No.",
                range(
                    1,
                    len(display_result) + 1,
                ),
            )


            display_result[
                "Timestamp"
            ] = (
                display_result[
                    "Timestamp"
                ]
                .dt.strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )


            display_result = (
                display_result.rename(
                    columns={
                        "Barcode_ID":
                            "Dispatcher ID",
                        "Timestamp":
                            "Date",
                        "Scan_Date":
                            "File Date",
                    }
                )
            )


            st.dataframe(
                display_result[
                    [
                        "No.",
                        "Dispatcher ID",
                        "Courier",
                        "Date",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "No.": (
                        st.column_config.NumberColumn(
                            "No.",
                            width="small",
                        )
                    ),
                    "Dispatcher ID": (
                        st.column_config.TextColumn(
                            "Dispatcher ID",
                            width="large",
                        )
                    ),
                    "Courier": (
                        st.column_config.TextColumn(
                            "Courier",
                            width="medium",
                        )
                    ),
                    "Date": (
                        st.column_config.TextColumn(
                            "Date",
                            width="medium",
                        )
                    ),
                },
            )


            # =================================================
            # EXACT MATCH INFORMATION
            # =================================================

            exact_matches = result[
                result["Barcode_ID"]
                .str.casefold()
                == barcode_query.casefold()
            ]


            if not exact_matches.empty:

                first_scan = (
                    exact_matches[
                        "Timestamp"
                    ]
                    .min()
                    .strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )


                latest_scan = (
                    exact_matches[
                        "Timestamp"
                    ]
                    .max()
                    .strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )


                safe_exact_id = html.escape(
                    barcode_query
                )

                exact_courier = (
                    exact_matches["Courier"]
                    .iloc[0]
                )

                safe_exact_courier = html.escape(
                    str(
                        exact_courier
                    )
                )


                st.markdown(
                    f"""
<div class="match-card">

<div class="match-label">
EXACT DISPATCHER ID FOUND
</div>

<div class="match-id">
✅ {safe_exact_id}
</div>

<div class="section-subtitle">
Courier: {safe_exact_courier}
</div>

</div>
""",
                    unsafe_allow_html=True,
                )


                exact_col1, exact_col2 = (
                    st.columns(2)
                )


                with exact_col1:

                    st.metric(
                        "First scanned",
                        first_scan,
                    )


                with exact_col2:

                    st.metric(
                        "Latest scanned",
                        latest_scan,
                    )