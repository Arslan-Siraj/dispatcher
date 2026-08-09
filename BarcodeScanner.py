import csv
import datetime
import html
import os
import re
import threading
from glob import glob

import pandas as pd
import streamlit as st

from app_helper import show_app_dev_info


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Dispatcher Scanner",
    page_icon="📦",
    layout="centered",
)

show_app_dev_info()


# =========================================================
# APPLICATION CONFIGURATION
# =========================================================

DATA_DIR = "data"

VALID_PREFIX = "SPXID06"
BARCODE_DIGITS = 10
BARCODE_LENGTH = 17

# Change this whenever BarcodeRegistry is structurally changed.
REGISTRY_CACHE_VERSION = "4.0.0"

os.makedirs(DATA_DIR, exist_ok=True)


# =========================================================
# PAGE STYLE
# =========================================================

st.markdown(
    """
<style>

.block-container {
    max-width: 900px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

[data-testid="stHeader"] {
    background: transparent;
}


/* ---------------------------------------------------------
   HEADER
--------------------------------------------------------- */

.dispatcher-title {
    font-size: 2.15rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin-bottom: 0.15rem;
}

.dispatcher-subtitle {
    font-size: 0.95rem;
    opacity: 0.65;
    margin-bottom: 1.5rem;
}


/* ---------------------------------------------------------
   SCANNER READY
--------------------------------------------------------- */

.scanner-ready {
    display: flex;
    align-items: center;
    gap: 13px;

    border: 1px solid rgba(34, 197, 94, 0.30);
    background: rgba(34, 197, 94, 0.07);

    border-radius: 18px;

    padding: 16px 19px;
    margin-bottom: 10px;
}

.ready-dot {
    width: 12px;
    height: 12px;
    min-width: 12px;

    border-radius: 50%;

    background: #22c55e;

    box-shadow:
        0 0 0 5px rgba(34, 197, 94, 0.12);
}

.ready-title {
    font-size: 1rem;
    font-weight: 750;
}

.ready-description {
    font-size: 0.83rem;
    opacity: 0.65;
    margin-top: 2px;
}


/* ---------------------------------------------------------
   SCANNER INPUT
--------------------------------------------------------- */

div[data-testid="stTextInput"] {
    margin-bottom: 0.7rem;
}

div[data-testid="stTextInput"] input {
    font-size: 1.3rem !important;
    font-weight: 700 !important;

    text-align: center !important;
    letter-spacing: 0.035em !important;

    min-height: 60px !important;

    border-radius: 16px !important;

    border:
        2px solid rgba(100, 116, 139, 0.25) !important;

    transition:
        border 0.12s ease,
        box-shadow 0.12s ease;
}

div[data-testid="stTextInput"] input:focus {
    border:
        2px solid #22c55e !important;

    box-shadow:
        0 0 0 4px rgba(34, 197, 94, 0.10) !important;
}


/* ---------------------------------------------------------
   STATUS CARDS
--------------------------------------------------------- */

.status-card {
    width: 100%;
    box-sizing: border-box;

    border-radius: 20px;

    padding: 22px 24px;

    margin-top: 8px;
    margin-bottom: 20px;

    border: 1px solid transparent;
}

.status-success {
    background: rgba(34, 197, 94, 0.10);
    border-color: rgba(34, 197, 94, 0.32);
}

.status-duplicate {
    background: rgba(239, 68, 68, 0.10);
    border-color: rgba(239, 68, 68, 0.32);
}

.status-invalid {
    background: rgba(245, 158, 11, 0.11);
    border-color: rgba(245, 158, 11, 0.35);
}

.status-error {
    background: rgba(239, 68, 68, 0.10);
    border-color: rgba(239, 68, 68, 0.32);
}

.status-waiting {
    background: rgba(100, 116, 139, 0.07);
    border-color: rgba(100, 116, 139, 0.20);
}

.status-label {
    font-size: 0.75rem;
    font-weight: 750;

    letter-spacing: 0.09em;

    opacity: 0.60;

    margin-bottom: 8px;
}

.status-title {
    font-size: 1.4rem;
    font-weight: 850;

    margin-bottom: 7px;
}

.status-barcode {
    font-size: 1.65rem;
    font-weight: 850;

    letter-spacing: 0.025em;

    word-break: break-all;
}

.status-info {
    margin-top: 8px;

    font-size: 0.88rem;

    opacity: 0.70;
}


/* ---------------------------------------------------------
   DUPLICATE ORIGINAL RECORD
--------------------------------------------------------- */

.duplicate-record {
    margin-top: 16px;
    padding: 14px 16px;

    background: rgba(239, 68, 68, 0.06);
    border: 1px solid rgba(239, 68, 68, 0.20);

    border-radius: 13px;
}

.duplicate-record-title {
    font-size: 0.72rem;
    font-weight: 800;

    letter-spacing: 0.08em;

    opacity: 0.62;

    margin-bottom: 9px;
}

.duplicate-row {
    display: flex;
    justify-content: space-between;
    align-items: center;

    gap: 20px;

    padding: 5px 0;

    font-size: 0.90rem;
}

.duplicate-key {
    opacity: 0.64;
}

.duplicate-value {
    font-weight: 800;
    text-align: right;

    word-break: break-all;
}


/* ---------------------------------------------------------
   RAPID SCAN
--------------------------------------------------------- */

.rapid-pill {
    display: inline-block;

    padding: 5px 11px;

    border-radius: 999px;

    font-size: 0.78rem;
    font-weight: 650;

    background: rgba(59, 130, 246, 0.10);

    border:
        1px solid rgba(59, 130, 246, 0.22);

    margin-top: -7px;
    margin-bottom: 15px;
}


/* ---------------------------------------------------------
   SECTION
--------------------------------------------------------- */

.section-title {
    font-size: 1.15rem;
    font-weight: 800;

    margin-top: 1rem;
    margin-bottom: 0.65rem;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# PAGE HEADER
# =========================================================

st.markdown(
    """
<div class="dispatcher-title">
📦 Dispatcher Scanner
</div>

<div class="dispatcher-subtitle">
Fast parcel scanning with duplicate protection
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# LOUD NON-BLOCKING SOUND + INDONESIAN VOICE FEEDBACK
# =========================================================

try:
    import winsound

    WINDOWS_SOUND_AVAILABLE = True

except ImportError:
    WINDOWS_SOUND_AVAILABLE = False


try:
    import pyttsx3

    SPEECH_AVAILABLE = True

except ImportError:
    SPEECH_AVAILABLE = False


_sound_lock = threading.Lock()


def _speak_warning(message):
    """
    Speak an Indonesian warning message.

    This function runs inside the same background sound
    thread, so barcode processing is not blocked.
    """

    if not SPEECH_AVAILABLE:
        return

    try:

        engine = pyttsx3.init()

        # Slightly slower speech improves clarity in a
        # warehouse / dispatch environment.
        engine.setProperty(
            "rate",
            160,
        )

        # Maximum pyttsx3 output volume.
        engine.setProperty(
            "volume",
            1.0,
        )

        engine.say(
            message
        )

        engine.runAndWait()

        engine.stop()

    except Exception:
        # Audio feedback must never interrupt scanning.
        pass


def _run_sound_pattern(status):
    """
    Play warning beeps, then Indonesian voice feedback.

    The whole feedback sequence runs in a background thread,
    so the scanner callback can finish immediately.

    Actual loudness is controlled by the Windows output
    volume on the scanner workstation.
    """

    with _sound_lock:

        try:

            # -------------------------------------------------
            # SUCCESS
            # Short confirmation beep only.
            # -------------------------------------------------

            if status == "success":

                if WINDOWS_SOUND_AVAILABLE:

                    winsound.Beep(
                        1500,
                        90,
                    )

                return


            # -------------------------------------------------
            # DUPLICATE
            # Strong 3-tone alarm, then Indonesian warning.
            # -------------------------------------------------

            if status == "duplicate":

                if WINDOWS_SOUND_AVAILABLE:

                    winsound.Beep(
                        1900,
                        260,
                    )

                    winsound.Beep(
                        950,
                        320,
                    )

                    winsound.Beep(
                        1900,
                        360,
                    )


                _speak_warning(
                    "Barcode duplikat. "
                    "Sudah pernah dipindai."
                )

                return


            # -------------------------------------------------
            # INVALID
            # Strong 4-tone alarm, then Indonesian warning.
            # -------------------------------------------------

            if status == "invalid":

                if WINDOWS_SOUND_AVAILABLE:

                    winsound.Beep(
                        850,
                        360,
                    )

                    winsound.Beep(
                        600,
                        420,
                    )

                    winsound.Beep(
                        850,
                        360,
                    )

                    winsound.Beep(
                        600,
                        600,
                    )


                _speak_warning(
                    "Barcode tidak valid. "
                    "Silakan pindai ulang."
                )

                return


            # -------------------------------------------------
            # SAVE / SYSTEM ERROR
            # Distinct low alarm, then Indonesian warning.
            # -------------------------------------------------

            if WINDOWS_SOUND_AVAILABLE:

                winsound.Beep(
                    500,
                    450,
                )

                winsound.Beep(
                    380,
                    500,
                )

                winsound.Beep(
                    500,
                    650,
                )


            _speak_warning(
                "Terjadi kesalahan. "
                "Barcode tidak tersimpan."
            )

        except Exception:
            # Feedback failure must never stop barcode scanning.
            pass


def play_sound(status):
    """
    Start sound and voice feedback in the background.

    The scanner remains ready for the next barcode while
    warning audio is playing.
    """

    try:

        sound_thread = threading.Thread(
            target=_run_sound_pattern,
            args=(status,),
            daemon=True,
        )

        sound_thread.start()

    except Exception:
        pass


# =========================================================
# BARCODE VALIDATION
# =========================================================

BARCODE_PATTERN = re.compile(
    rf"^{re.escape(VALID_PREFIX)}"
    rf"\d{{{BARCODE_DIGITS}}}$"
)


def is_valid_barcode(barcode):
    """
    Required format:

        SPXID06 + exactly 10 digits

    Example:

        SPXID064644420698
    """

    if barcode is None:
        return False

    barcode = str(barcode).strip()

    if len(barcode) != BARCODE_LENGTH:
        return False

    return bool(
        BARCODE_PATTERN.fullmatch(barcode)
    )


# =========================================================
# SCANNER INPUT PARSER
# =========================================================

def parse_scanner_input(raw_input):
    """
    Supports normal and rapid merged scans.

    Example:

        SPXID064644420698SPXID064644420699

    becomes:

        [
            "SPXID064644420698",
            "SPXID064644420699"
        ]
    """

    if raw_input is None:
        return []

    cleaned = re.sub(
        r"\s+",
        "",
        str(raw_input),
    )

    if not cleaned:
        return []

    # Scanner data must consist entirely of complete
    # 17-character barcode blocks.
    if len(cleaned) % BARCODE_LENGTH != 0:
        return []

    barcodes = []

    for start in range(
        0,
        len(cleaned),
        BARCODE_LENGTH,
    ):

        barcode = cleaned[
            start:
            start + BARCODE_LENGTH
        ]

        if not is_valid_barcode(barcode):
            return []

        barcodes.append(barcode)

    return barcodes


# =========================================================
# BARCODE REGISTRY
# =========================================================

class BarcodeRegistry:
    """
    Fast shared registry.

    Duplicate lookup:
        O(1)

    Storage:
        daily CSV

    Duplicate IDs never reach CSV writing.
    """

    def __init__(self):

        self.lock = threading.RLock()

        # barcode -> first successful timestamp
        self.codes = {}

        self.current_day = (
            datetime.date.today()
            .isoformat()
        )

        # Successful records for today only.
        self.today_records = []

        self._load_existing_data()


    # =====================================================
    # LOAD EXISTING DATA
    # =====================================================

    def _load_existing_data(self):

        today = (
            datetime.date.today()
            .isoformat()
        )

        csv_files = sorted(
            glob(
                os.path.join(
                    DATA_DIR,
                    "*.csv",
                )
            )
        )

        for csv_file in csv_files:

            file_date = os.path.splitext(
                os.path.basename(csv_file)
            )[0]

            try:

                with open(
                    csv_file,
                    "r",
                    newline="",
                    encoding="utf-8",
                ) as file:

                    reader = csv.reader(file)

                    for row in reader:

                        if len(row) < 2:
                            continue

                        stored_value = str(
                            row[0]
                        ).strip()

                        timestamp = str(
                            row[1]
                        ).strip()

                        # Also understands older accidentally
                        # merged records.
                        parsed_barcodes = (
                            parse_scanner_input(
                                stored_value
                            )
                        )

                        if not parsed_barcodes:
                            continue

                        for barcode in parsed_barcodes:

                            # Keep first successful occurrence.
                            if barcode not in self.codes:

                                self.codes[
                                    barcode
                                ] = timestamp

                            if file_date == today:

                                self.today_records.append(
                                    (
                                        barcode,
                                        timestamp,
                                    )
                                )

            except Exception:
                continue


    # =====================================================
    # MIDNIGHT HANDLING
    # =====================================================

    def ensure_current_day(self):

        today = (
            datetime.date.today()
            .isoformat()
        )

        if self.current_day == today:
            return

        with self.lock:

            if self.current_day == today:
                return

            self.current_day = today
            self.today_records = []


    # =====================================================
    # PROCESS SCAN BATCH
    # =====================================================

    def process_batch(self, barcodes):
        """
        Process rapid scans under one lock.

        Duplicate checking happens BEFORE file writing.

        Therefore:
        - duplicates are never stored
        - invalid scans are never stored
        """

        self.ensure_current_day()

        results = []

        with self.lock:

            today = (
                datetime.date.today()
                .isoformat()
            )

            today_csv = os.path.join(
                DATA_DIR,
                f"{today}.csv",
            )

            rows_to_write = []

            new_records = []

            # IDs first seen inside this same scan event.
            batch_new_codes = {}


            # -------------------------------------------------
            # CLASSIFY
            # -------------------------------------------------

            for barcode in barcodes:

                # =============================================
                # PREVIOUSLY STORED DUPLICATE
                # =============================================

                if barcode in self.codes:

                    results.append(
                        {
                            "status": "duplicate",
                            "barcode": barcode,
                            "timestamp": self.codes[
                                barcode
                            ],
                        }
                    )

                    continue


                # =============================================
                # DUPLICATE WITHIN SAME RAPID BATCH
                # =============================================

                if barcode in batch_new_codes:

                    results.append(
                        {
                            "status": "pending_duplicate",
                            "barcode": barcode,
                            "timestamp": batch_new_codes[
                                barcode
                            ],
                        }
                    )

                    continue


                # =============================================
                # SUCCESS
                # =============================================

                timestamp = (
                    datetime.datetime.now()
                    .isoformat()
                )

                batch_new_codes[
                    barcode
                ] = timestamp

                rows_to_write.append(
                    [
                        barcode,
                        timestamp,
                    ]
                )

                new_records.append(
                    (
                        barcode,
                        timestamp,
                    )
                )

                results.append(
                    {
                        "status": "success",
                        "barcode": barcode,
                        "timestamp": timestamp,
                    }
                )


            # -------------------------------------------------
            # SAVE SUCCESSFUL IDS ONLY
            # -------------------------------------------------

            if rows_to_write:

                try:

                    with open(
                        today_csv,
                        "a",
                        newline="",
                        encoding="utf-8",
                    ) as csvfile:

                        writer = csv.writer(
                            csvfile
                        )

                        writer.writerows(
                            rows_to_write
                        )

                except Exception as exc:

                    for result in results:

                        if result[
                            "status"
                        ] in (
                            "success",
                            "pending_duplicate",
                        ):

                            result[
                                "status"
                            ] = "error"

                            result[
                                "message"
                            ] = str(exc)

                    return results


                # Memory is updated only AFTER disk write.
                for barcode, timestamp in new_records:

                    self.codes[
                        barcode
                    ] = timestamp

                    self.today_records.append(
                        (
                            barcode,
                            timestamp,
                        )
                    )


            # -------------------------------------------------
            # FINALIZE SAME-BATCH DUPLICATES
            # -------------------------------------------------

            for result in results:

                if (
                    result["status"]
                    == "pending_duplicate"
                ):

                    result[
                        "status"
                    ] = "duplicate"


        return results


    # =====================================================
    # TODAY'S SUCCESSFUL RECORDS
    # =====================================================

    def get_today_records(self):

        self.ensure_current_day()

        with self.lock:

            return list(
                self.today_records
            )


    # =====================================================
    # TOTAL SUCCESSFUL SCANS
    # =====================================================

    def get_total_successful_scans(self):
        """
        Number of successfully accepted barcode IDs
        across all loaded history.

        Since duplicates are not stored, each entry
        represents one successful scan.
        """

        with self.lock:

            return len(
                self.codes
            )


# =========================================================
# VERSIONED STREAMLIT CACHE
# =========================================================

@st.cache_resource(
    show_spinner=False
)
def get_barcode_registry(version):

    return BarcodeRegistry()


registry = get_barcode_registry(
    REGISTRY_CACHE_VERSION
)


# =========================================================
# SESSION STATE
# =========================================================

if "last_scan" not in st.session_state:

    st.session_state.last_scan = None


if "rapid_scan_count" not in st.session_state:

    st.session_state.rapid_scan_count = 0


# =========================================================
# DISPLAY TIME
# =========================================================

def format_timestamp(timestamp):

    try:

        value = pd.to_datetime(
            timestamp
        )

        return value.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    except Exception:

        return str(timestamp)


# =========================================================
# SCANNER CALLBACK
# =========================================================

def barcode_submitted():

    raw_input = st.session_state.get(
        "barcode_input",
        "",
    )

    # Clear immediately for next physical scan.
    st.session_state.barcode_input = ""

    if not raw_input:
        return


    # =====================================================
    # PARSE
    # =====================================================

    barcodes = parse_scanner_input(
        raw_input
    )


    # =====================================================
    # INVALID
    # =====================================================

    if not barcodes:

        cleaned = re.sub(
            r"\s+",
            "",
            str(raw_input),
        )

        st.session_state.last_scan = {
            "status": "invalid",
            "barcode": cleaned,
        }

        st.session_state.rapid_scan_count = 0

        play_sound(
            "invalid"
        )

        return


    # =====================================================
    # PROCESS
    # =====================================================

    results = registry.process_batch(
        barcodes
    )

    if not results:
        return

    # Last Scan Status represents the final barcode
    # physically received.
    last_result = results[-1]

    st.session_state.last_scan = (
        last_result
    )

    st.session_state.rapid_scan_count = (
        len(barcodes)
    )

    play_sound(
        last_result.get(
            "status",
            "error",
        )
    )


# =========================================================
# SCANNER READY PANEL
# =========================================================

st.markdown(
    """
<div class="scanner-ready">

<div class="ready-dot"></div>

<div>

<div class="ready-title">
Scanner ready
</div>

<div class="ready-description">
Point the scanner at a parcel barcode and press the trigger
</div>

</div>

</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# SCANNER INPUT
# =========================================================

st.text_input(
    "Scanner input",
    key="barcode_input",
    placeholder="Ready — scan barcode now",
    on_change=barcode_submitted,
    label_visibility="collapsed",
)


# =========================================================
# LAST SCAN STATUS
# =========================================================

last_scan = (
    st.session_state.last_scan
)


# ---------------------------------------------------------
# WAITING
# ---------------------------------------------------------

if last_scan is None:

    st.markdown(
        """
<div class="status-card status-waiting">

<div class="status-label">
LAST SCAN STATUS
</div>

<div class="status-title">
Waiting for barcode
</div>

<div class="status-info">
The next scan result will appear here.
</div>

</div>
""",
        unsafe_allow_html=True,
    )


else:

    status = last_scan.get(
        "status",
        "error",
    )

    raw_barcode = str(
        last_scan.get(
            "barcode",
            "",
        )
    )

    safe_barcode = html.escape(
        raw_barcode
    )


    # =====================================================
    # SUCCESS
    # =====================================================

    if status == "success":

        scan_time = format_timestamp(
            last_scan.get(
                "timestamp",
                "",
            )
        )

        st.markdown(
            f"""
<div class="status-card status-success">

<div class="status-label">
LAST SCAN STATUS
</div>

<div class="status-title">
✅ SUCCESS
</div>

<div class="status-barcode">
{safe_barcode}
</div>

<div class="status-info">
Saved successfully · {scan_time}
</div>

</div>
""",
            unsafe_allow_html=True,
        )


    # =====================================================
    # DUPLICATE
    # =====================================================

    elif status == "duplicate":

        original_timestamp = last_scan.get(
            "timestamp",
            "",
        )

        try:

            original_datetime = pd.to_datetime(
                original_timestamp
            )

            original_date = (
                original_datetime.strftime(
                    "%Y-%m-%d"
                )
            )

            original_time = (
                original_datetime.strftime(
                    "%H:%M:%S"
                )
            )

        except Exception:

            original_date = "-"
            original_time = html.escape(
                str(original_timestamp)
            )


        st.markdown(
            f"""
<div class="status-card status-duplicate">

<div class="status-label">
LAST SCAN STATUS
</div>

<div class="status-title">
🔁 DUPLICATE DETECTED
</div>

<div class="status-barcode">
{safe_barcode}
</div>

<div class="duplicate-record">

<div class="duplicate-record-title">
ORIGINAL SUCCESSFUL SCAN
</div>

<div class="duplicate-row">
<span class="duplicate-key">Scan Date</span>
<span class="duplicate-value">{original_date}</span>
</div>

<div class="duplicate-row">
<span class="duplicate-key">Scan Time</span>
<span class="duplicate-value">{original_time}</span>
</div>

</div>

<div class="status-info">
⚠️ This Dispatcher ID was already scanned.<br>
</div>

</div>
""",
            unsafe_allow_html=True,
        )


    # =====================================================
    # INVALID
    # =====================================================

    elif status == "invalid":

        display_value = raw_barcode

        if len(display_value) > 60:

            display_value = (
                display_value[:60]
                + "…"
            )

        safe_invalid = html.escape(
            display_value
        )

        st.markdown(
            f"""
<div class="status-card status-invalid">

<div class="status-label">
LAST SCAN STATUS
</div>

<div class="status-title">
⚠️ INVALID BARCODE
</div>

<div class="status-barcode">
{safe_invalid}
</div>

<div class="status-info">
Expected {VALID_PREFIX} + {BARCODE_DIGITS} digits<br>
<strong>Not stored</strong>
</div>

</div>
""",
            unsafe_allow_html=True,
        )


    # =====================================================
    # ERROR
    # =====================================================

    else:

        safe_message = html.escape(
            str(
                last_scan.get(
                    "message",
                    "Unable to save barcode.",
                )
            )
        )

        st.markdown(
            f"""
<div class="status-card status-error">

<div class="status-label">
LAST SCAN STATUS
</div>

<div class="status-title">
❌ SAVE ERROR
</div>

<div class="status-barcode">
{safe_barcode}
</div>

<div class="status-info">
{safe_message}<br>
<strong>Barcode was not stored</strong>
</div>

</div>
""",
            unsafe_allow_html=True,
        )


# =========================================================
# RAPID SCAN INDICATOR
# =========================================================

rapid_count = (
    st.session_state.rapid_scan_count
)


if rapid_count > 1:

    st.markdown(
        f"""
<div class="rapid-pill">
⚡ {rapid_count} rapid scans processed individually
</div>
""",
        unsafe_allow_html=True,
    )


# =========================================================
# TODAY'S DATA
# =========================================================

today = datetime.date.today()
today_str = today.isoformat()

records = registry.get_today_records()

today_count = len(records)

total_successful = (
    registry.get_total_successful_scans()
)


# =========================================================
# METRICS
# =========================================================

metric_col1, metric_col2 = st.columns(2)


with metric_col1:

    st.metric(
        "Today's scans",
        today_count,
    )


with metric_col2:

    st.metric(
        "Total successful scans",
        total_successful,
    )


# =========================================================
# TODAY'S SCANS TABLE
# =========================================================

st.markdown(
    f"""
<div class="section-title">
Today's Scans — {today_str}
</div>
""",
    unsafe_allow_html=True,
)


if records:

    # -----------------------------------------------------
    # CREATE TODAY DATAFRAME
    # -----------------------------------------------------

    df_today = pd.DataFrame(
        records,
        columns=[
            "Barcode_ID",
            "Timestamp",
        ],
    )


    df_today["Timestamp"] = pd.to_datetime(
        df_today["Timestamp"],
        errors="coerce",
    )


    df_today = df_today.dropna(
        subset=[
            "Timestamp"
        ]
    )


    df_today = df_today.sort_values(
        "Timestamp",
        ascending=False,
    )


    # -----------------------------------------------------
    # DISPLAY VERSION
    # -----------------------------------------------------

    display_df = df_today.copy()


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


    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


    # =====================================================
    # EXCEL DOWNLOAD
    # =====================================================

    import io


    # Create separate dataframe for downloaded Excel file.
    download_df = df_today[
        [
            "Barcode_ID",
            "Timestamp",
        ]
    ].copy()


    # Format timestamp
    download_df["Timestamp"] = (
        download_df["Timestamp"]
        .dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )


    # Required Excel column names
    download_df = download_df.rename(
        columns={
            "Barcode_ID": "dispatcher_id",
            "Timestamp": "date",
        }
    )


    # -----------------------------------------------------
    # CREATE EXCEL IN MEMORY
    # -----------------------------------------------------

    excel_buffer = io.BytesIO()


    with pd.ExcelWriter(
        excel_buffer,
        engine="xlsxwriter",
    ) as writer:

        download_df.to_excel(
            writer,
            index=False,
            sheet_name="Today_Scans",
        )


        workbook = writer.book

        worksheet = writer.sheets[
            "Today_Scans"
        ]


        # -----------------------------------------------
        # HEADER FORMAT
        # -----------------------------------------------

        header_format = workbook.add_format(
            {
                "bold": True,
                "border": 1,
                "align": "center",
                "valign": "vcenter",
            }
        )


        # Rewrite header with formatting
        for col_num, column_name in enumerate(
            download_df.columns
        ):

            worksheet.write(
                0,
                col_num,
                column_name,
                header_format,
            )


        # -----------------------------------------------
        # COLUMN WIDTHS
        # -----------------------------------------------

        worksheet.set_column(
            "A:A",
            24,
        )

        worksheet.set_column(
            "B:B",
            22,
        )


        # -----------------------------------------------
        # FREEZE HEADER
        # -----------------------------------------------

        worksheet.freeze_panes(
            1,
            0,
        )


        # -----------------------------------------------
        # FILTER
        # -----------------------------------------------

        worksheet.autofilter(
            0,
            0,
            len(download_df),
            len(download_df.columns) - 1,
        )


    excel_buffer.seek(0)


    # =====================================================
    # DOWNLOAD BUTTON
    # =====================================================

    st.markdown("---")


    st.download_button(
        label="⬇️ Download Today's Scan File",
        data=excel_buffer.getvalue(),
        file_name=(
            f"dispatcher_scans_"
            f"{today_str}.xlsx"
        ),
        mime=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        use_container_width=True,
    )


else:

    st.info(
        f"No parcels scanned on {today_str}."
    )