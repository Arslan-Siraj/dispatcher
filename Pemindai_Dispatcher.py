import csv
import datetime
import html
import os
import re
import threading
from glob import glob

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from app_helper import show_app_dev_info


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Pemindai Dispatcher",
    page_icon="📦",
    layout="centered",
)


show_app_dev_info()

# =========================================================
# SIDEBAR BRANDING + NAVIGATION DESIGN
# Compatible with Streamlit 1.28.1
# =========================================================
#
# IMPORTANT:
# In Streamlit 1.28.1 the icons shown in the built-in multipage
# navigation come from the page filenames. Therefore use:
#
# Main app:
#     📦_Pemindai_Dispatcher.py
#
# History page inside /pages:
#     1_📋_Riwayat_Pemindaian.py
#
# page_icon= controls the browser favicon, not the sidebar page icon.


st.markdown(
    """
<style>

/* ---------------------------------------------------------
   STREAMLIT 1.28.1 SIDEBAR
--------------------------------------------------------- */

section[data-testid="stSidebar"] > div {
    background:
        linear-gradient(
            180deg,
            rgba(15, 23, 42, 0.035) 0%,
            rgba(15, 23, 42, 0.012) 100%
        );
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.15rem;
}


/* ---------------------------------------------------------
   APP BRAND
--------------------------------------------------------- */

.dispatcher-sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;

    padding: 14px 14px;
    margin: 0 0 16px 0;

    border-radius: 16px;

    background:
        linear-gradient(
            135deg,
            rgba(34, 197, 94, 0.12),
            rgba(59, 130, 246, 0.08)
        );

    border:
        1px solid rgba(100, 116, 139, 0.18);
}

.dispatcher-brand-icon {
    display: flex;
    align-items: center;
    justify-content: center;

    width: 44px;
    height: 44px;

    border-radius: 13px;

    font-size: 1.55rem;
    line-height: 1;

    background: rgba(34, 197, 94, 0.13);
    border: 1px solid rgba(34, 197, 94, 0.22);
}

.dispatcher-brand-copy {
    min-width: 0;
}

.dispatcher-brand-title {
    font-size: 0.95rem;
    font-weight: 850;
    letter-spacing: 0.08em;
    line-height: 1.15;
}

.dispatcher-brand-subtitle {
    margin-top: 4px;

    font-size: 0.72rem;
    font-weight: 600;

    opacity: 0.58;
}

.dispatcher-sidebar-label {
    margin:
        2px 10px
        7px 10px;

    font-size: 0.67rem;
    font-weight: 800;

    letter-spacing: 0.11em;

    opacity: 0.46;
}


/* ---------------------------------------------------------
   BUILT-IN MULTIPAGE NAVIGATION
--------------------------------------------------------- */

/*
Streamlit 1.28.x renders the pages navigation in the sidebar.
These selectors only style that existing navigation; no newer
navigation API is required.
*/

section[data-testid="stSidebar"]
[data-testid="stSidebarNav"] {
    padding-top: 0;
}

section[data-testid="stSidebar"]
[data-testid="stSidebarNav"] ul {
    padding-left: 0;
}

section[data-testid="stSidebar"]
[data-testid="stSidebarNav"] li {
    margin-bottom: 5px;
}

section[data-testid="stSidebar"]
[data-testid="stSidebarNav"] a {
    border-radius: 11px;

    padding-top: 9px;
    padding-bottom: 9px;

    font-weight: 700;

    transition:
        background 0.12s ease,
        transform 0.12s ease;
}

section[data-testid="stSidebar"]
[data-testid="stSidebarNav"] a:hover {
    background: rgba(34, 197, 94, 0.08);
    transform: translateX(2px);
}


/* ---------------------------------------------------------
   SIDEBAR DIVIDER
--------------------------------------------------------- */

section[data-testid="stSidebar"] hr {
    margin-top: 1rem;
    margin-bottom: 1rem;

    opacity: 0.18;
}

</style>
""",
    unsafe_allow_html=True,
)


# =========================================================
# APPLICATION CONFIGURATION
# =========================================================

DATA_DIR = "data"

SHOPEE_PREFIX = "SPXID06"
SHOPEE_DIGITS = 10
SHOPEE_LENGTH = 17

JNT_PREFIX = "J"
JNT_REMAINING_CHARS = 11
JNT_LENGTH = 12

ANTERAJA_PREFIX = "1"
ANTERAJA_LENGTH = 14

# Bump when registry/loading/validation behavior changes so
# Streamlit does not reuse an older cached registry instance.
REGISTRY_CACHE_VERSION = "5.0.0"

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
   LARGE STICKY SCANNER INPUT
--------------------------------------------------------- */

div[data-testid="stTextInput"] {
    margin-top: 8px;
    margin-bottom: 16px;
}

div[data-testid="stTextInput"] input {
    font-size: 1.55rem !important;
    font-weight: 850 !important;

    text-align: center !important;
    letter-spacing: 0.045em !important;

    height: 104px !important;
    min-height: 104px !important;

    border-radius: 22px !important;

    border:
        3px solid rgba(34, 197, 94, 0.42) !important;

    background:
        rgba(34, 197, 94, 0.055) !important;

    transition:
        border 0.12s ease,
        box-shadow 0.12s ease,
        background 0.12s ease;
}

div[data-testid="stTextInput"] input::placeholder {
    font-size: 1.12rem !important;
    font-weight: 800 !important;
    letter-spacing: 0.025em !important;
    opacity: 0.68 !important;
}

div[data-testid="stTextInput"] input:hover {
    border:
        3px solid rgba(34, 197, 94, 0.70) !important;
}

div[data-testid="stTextInput"] input:focus {
    border:
        3px solid #22c55e !important;

    background:
        rgba(34, 197, 94, 0.09) !important;

    box-shadow:
        0 0 0 6px rgba(34, 197, 94, 0.12) !important;

    outline: none !important;
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
📦 Pemindai Dispatcher
</div>

<div class="dispatcher-subtitle">
Pemindaian paket cepat dengan perlindungan duplikat
</div>
""",
    unsafe_allow_html=True,
)


# =========================================================
# RECORDED SCANNER SOUND FEEDBACK
# =========================================================

SUCCESS_SOUND_FILE = os.path.join(
    "assets",
    "success.wav",
)

INVALID_SOUND_FILE = os.path.join(
    "assets",
    "invalid.wav",
)

DUPLICATE_SOUND_FILE = os.path.join(
    "assets",
    "duplicate.wav",
)

ERROR_SOUND_FILE = os.path.join(
    "assets",
    "error.wav",
)


try:
    import winsound

    WINDOWS_SOUND_AVAILABLE = True

except ImportError:
    WINDOWS_SOUND_AVAILABLE = False


def _play_fallback_beep(status):
    """
    Built-in fallback tones if a WAV file is missing
    or cannot be played.
    """

    if not WINDOWS_SOUND_AVAILABLE:
        return

    try:

        if status == "success":

            winsound.Beep(
                1500,
                120,
            )

            return


        if status == "invalid":

            winsound.Beep(
                850,
                300,
            )

            winsound.Beep(
                600,
                400,
            )

            winsound.Beep(
                850,
                450,
            )

            return


        winsound.Beep(
            1800,
            260,
        )

        winsound.Beep(
            900,
            320,
        )

        winsound.Beep(
            1800,
            380,
        )

    except Exception:
        pass


def _play_wav(sound_file, status):
    """
    Play a WAV file asynchronously.

    The barcode scanner remains ready for the next scan
    while the recording is playing.
    """

    if not WINDOWS_SOUND_AVAILABLE:
        return

    try:

        if os.path.exists(
            sound_file
        ):

            winsound.PlaySound(
                sound_file,
                winsound.SND_FILENAME
                | winsound.SND_ASYNC,
            )

        else:

            _play_fallback_beep(
                status
            )

    except Exception:

        _play_fallback_beep(
            status
        )


def play_sound(status):
    """
    Scanner audio mapping:

    success
        -> assets/success.wav

    invalid
        -> assets/invalid.wav

    duplicate
        -> assets/duplicate.wav

    save/system error
        -> assets/error.wav

    All WAV playback is asynchronous.
    """

    if not WINDOWS_SOUND_AVAILABLE:
        return

    try:

        if status == "success":

            _play_wav(
                SUCCESS_SOUND_FILE,
                "success",
            )

            return


        if status == "invalid":

            _play_wav(
                INVALID_SOUND_FILE,
                "invalid",
            )

            return


        if status == "duplicate":

            _play_wav(
                DUPLICATE_SOUND_FILE,
                "duplicate",
            )

            return


        _play_wav(
            ERROR_SOUND_FILE,
            "error",
        )

    except Exception:

        _play_fallback_beep(
            status
        )


# =========================================================
# BARCODE VALIDATION + COURIER DETECTION
# =========================================================

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
    Return the courier name for a supported barcode.

    Format yang didukung:

    Shopee SPX
        SPXID06 + exactly 10 digits
        Total length: 17

    J&T Express
        Starts with J
        12 characters total
        Remaining characters may be A-Z or 0-9

    AnterAja
        14 digits total, starting with 1
    """

    if barcode is None:
        return None

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

    return None


def is_valid_barcode(barcode):
    """
    True only for a supported courier barcode.
    """

    return (
        detect_courier(
            barcode
        )
        is not None
    )


# =========================================================
# SCANNER INPUT PARSER
# =========================================================

def parse_scanner_input(raw_input):
    """
    Parse one or more physical scanner reads.

    The USB scanner can occasionally place rapid scans
    together before Streamlit reruns. Because each courier
    has a known prefix and fixed length, the input can be
    safely split from left to right.

    Supported blocks:
        Shopee SPX : 17 chars, starts SPXID06
        J&T        : 12 chars, starts J, A-Z / 0-9
        AnterAja   : 14 digits, starts 1

    Any unknown character, incomplete block, or invalid
    barcode causes the complete scanner event to be rejected.
    """

    if raw_input is None:
        return []

    cleaned = re.sub(
        r"\s+",
        "",
        str(raw_input),
    ).upper()

    if not cleaned:
        return []

    barcodes = []
    position = 0
    input_length = len(
        cleaned
    )

    while position < input_length:

        remaining = cleaned[
            position:
        ]

        barcode = None


        # -------------------------------------------------
        # SHOPEE SPX
        # -------------------------------------------------

        if remaining.startswith(
            SHOPEE_PREFIX
        ):

            if len(
                remaining
            ) < SHOPEE_LENGTH:
                return []

            candidate = remaining[
                :SHOPEE_LENGTH
            ]

            if not SHOPEE_PATTERN.fullmatch(
                candidate
            ):
                return []

            barcode = candidate


        # -------------------------------------------------
        # J&T EXPRESS
        # -------------------------------------------------

        elif remaining.startswith(
            JNT_PREFIX
        ):

            if len(
                remaining
            ) < JNT_LENGTH:
                return []

            candidate = remaining[
                :JNT_LENGTH
            ]

            if not JNT_PATTERN.fullmatch(
                candidate
            ):
                return []

            barcode = candidate


        # -------------------------------------------------
        # ANTERAJA
        # -------------------------------------------------

        elif remaining.startswith(
            ANTERAJA_PREFIX
        ):

            if len(
                remaining
            ) < ANTERAJA_LENGTH:
                return []

            candidate = remaining[
                :ANTERAJA_LENGTH
            ]

            if not ANTERAJA_PATTERN.fullmatch(
                candidate
            ):
                return []

            barcode = candidate


        # -------------------------------------------------
        # UNKNOWN / UNSUPPORTED
        # -------------------------------------------------

        else:
            return []


        barcodes.append(
            barcode
        )

        position += len(
            barcode
        )


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
        ).upper()

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
SIAP MEMINDAI
</div>

<div class="ready-description">
Fokus pemindai dijaga aktif secara otomatis · Arahkan ke barcode paket lalu tekan pemicu
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
    "Input pemindai",
    key="barcode_input",
    placeholder="SIAP MEMINDAI — scanner focus active",
    on_change=barcode_submitted,
    label_visibility="collapsed",
)


# =========================================================
# STICKY SCANNER FOCUS
# =========================================================

components.html(
    """
<script>
(function () {

    const parentWindow = window.parent;
    const parentDocument = parentWindow.document;

    function getScannerInput() {
        const inputs = parentDocument.querySelectorAll(
            'div[data-testid="stTextInput"] input'
        );

        if (!inputs || inputs.length === 0) {
            return null;
        }

        // BarcodeScanner.py has one scanner text input.
        return inputs[0];
    }


    function focusScanner() {
        try {
            const scannerInput = getScannerInput();

            if (!scannerInput) {
                return;
            }

            scannerInput.setAttribute(
                "autocomplete",
                "off"
            );

            scannerInput.setAttribute(
                "autocapitalize",
                "off"
            );

            scannerInput.setAttribute(
                "spellcheck",
                "false"
            );

            scannerInput.focus({
                preventScroll: true
            });

        } catch (error) {
            console.log(
                "Dispatcher scanner focus unavailable."
            );
        }
    }


    // Remove handlers installed by the previous Streamlit
    // rerun before installing the new ones.
    if (parentWindow.__dispatcherScannerClickHandler) {
        parentDocument.removeEventListener(
            "click",
            parentWindow.__dispatcherScannerClickHandler,
            true
        );
    }

    if (parentWindow.__dispatcherScannerWindowFocusHandler) {
        parentWindow.removeEventListener(
            "focus",
            parentWindow.__dispatcherScannerWindowFocusHandler
        );
    }


    parentWindow.__dispatcherScannerClickHandler = function () {
        // Allow the clicked control (download button, sidebar,
        // etc.) to perform its action first, then return focus
        // to the barcode scanner.
        setTimeout(
            focusScanner,
            180
        );
    };


    parentWindow.__dispatcherScannerWindowFocusHandler = function () {
        // When the operator returns to this browser window,
        // make the scanner ready again.
        setTimeout(
            focusScanner,
            120
        );
    };


    parentDocument.addEventListener(
        "click",
        parentWindow.__dispatcherScannerClickHandler,
        true
    );

    parentWindow.addEventListener(
        "focus",
        parentWindow.__dispatcherScannerWindowFocusHandler
    );


    // Streamlit renders in stages, especially after on_change.
    // Multiple attempts make focus recovery reliable without
    // blocking the page.
    setTimeout(focusScanner, 50);
    setTimeout(focusScanner, 180);
    setTimeout(focusScanner, 450);
    setTimeout(focusScanner, 900);

})();
</script>
""",
    height=0,
)


# =========================================================
# STATUS PEMINDAIAN TERAKHIR
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
STATUS PEMINDAIAN TERAKHIR
</div>

<div class="status-title">
Menunggu barcode
</div>

<div class="status-info">
Hasil pemindaian berikutnya akan tampil di sini.
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

    courier = detect_courier(
        raw_barcode
    )

    safe_courier = html.escape(
        courier
        if courier
        else "Unknown"
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
STATUS PEMINDAIAN TERAKHIR
</div>

<div class="status-title">
✅ BERHASIL
</div>

<div class="status-barcode">
{safe_barcode}
</div>

<div class="status-info">
{safe_courier} · Berhasil disimpan · {scan_time}
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
STATUS PEMINDAIAN TERAKHIR
</div>

<div class="status-title">
🔁 DUPLIKAT TERDETEKSI
</div>

<div class="status-barcode">
{safe_barcode}
</div>

<div class="duplicate-record">

<div class="duplicate-record-title">
PEMINDAIAN BERHASIL PERTAMA
</div>

<div class="duplicate-row">
<span class="duplicate-key">Tanggal Pemindaian</span>
<span class="duplicate-value">{original_date}</span>
</div>

<div class="duplicate-row">
<span class="duplicate-key">Kurir</span>
<span class="duplicate-value">{safe_courier}</span>
</div>

<div class="duplicate-row">
<span class="duplicate-key">Waktu Pemindaian</span>
<span class="duplicate-value">{original_time}</span>
</div>

</div>

<div class="status-info">
⚠️ ID Dispatcher ini sudah pernah dipindai.<br>
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
STATUS PEMINDAIAN TERAKHIR
</div>

<div class="status-title">
⚠️ BARCODE TIDAK VALID
</div>

<div class="status-barcode">
{safe_invalid}
</div>

<div class="status-info">
Format yang didukung:<br>
Shopee SPX: SPXID06 + 10 digit<br>
J&amp;T: 12 karakter diawali J (huruf/angka)<br>
AnterAja: 14 digit diawali angka 1<br>
<strong>Tidak disimpan</strong>
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
                    "Tidak dapat menyimpan barcode.",
                )
            )
        )

        st.markdown(
            f"""
<div class="status-card status-error">

<div class="status-label">
STATUS PEMINDAIAN TERAKHIR
</div>

<div class="status-title">
❌ GAGAL MENYIMPAN
</div>

<div class="status-barcode">
{safe_barcode}
</div>

<div class="status-info">
{safe_message}<br>
<strong>Barcode tidak disimpan</strong>
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
⚡ {rapid_count} pemindaian cepat diproses satu per satu
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
        "Pemindaian hari ini",
        today_count,
    )


with metric_col2:

    st.metric(
        "Total pemindaian berhasil",
        total_successful,
    )


# =========================================================
# TODAY'S SCANS TABLE
# =========================================================

st.markdown(
    f"""
<div class="section-title">
Pemindaian Hari Ini — {today_str}
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


    df_today["Kurir"] = (
        df_today["Barcode_ID"]
        .map(
            detect_courier
        )
        .fillna(
            "Unknown"
        )
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
            "Kurir",
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
            "Kurir": "courier",
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
            18,
        )

        worksheet.set_column(
            "C:C",
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
        label="⬇️ Unduh File Pemindaian Hari Ini",
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
        f"Belum ada paket yang dipindai pada {today_str}."
    )