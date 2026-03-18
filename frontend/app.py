"""Frontend Streamlit dla Vehicle AI Agent."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = 20


st.set_page_config(
    page_title="Vehicle AI Agent",
    page_icon="🚘",
    layout="wide",
)


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=Space+Grotesk:wght@500;700&display=swap');

        :root {
            --ink: #17212b;
            --muted: #60707d;
            --surface: rgba(255, 250, 244, 0.88);
            --surface-strong: rgba(255, 255, 255, 0.96);
            --line: rgba(23, 33, 43, 0.09);
            --accent: #bd5f3c;
            --accent-strong: #934324;
            --accent-alt: #206b67;
            --success: #2f7d4a;
            --warning: #a76a1f;
            --danger: #b44b3d;
            --shadow: 0 24px 60px rgba(26, 37, 48, 0.08);
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(189, 95, 60, 0.15), transparent 28%),
                radial-gradient(circle at left 20%, rgba(32, 107, 103, 0.13), transparent 25%),
                linear-gradient(180deg, #f5efe7 0%, #f3f0ea 55%, #edf2ef 100%);
            color: var(--ink);
            font-family: "IBM Plex Sans", sans-serif;
        }

        .block-container {
            max-width: 1220px;
            padding-top: 2.25rem;
            padding-bottom: 3rem;
        }

        h1, h2, h3 {
            font-family: "Space Grotesk", sans-serif;
            letter-spacing: -0.03em;
            color: var(--ink);
        }

        h1 {
            font-size: 3rem;
            line-height: 1.02;
            margin-bottom: 0.5rem;
        }

        h2 {
            font-size: 1.45rem;
            margin-top: 0.2rem;
        }

        p, label, .stCaption {
            color: var(--muted);
        }

        .hero {
            background:
                linear-gradient(135deg, rgba(255, 251, 246, 0.95), rgba(247, 241, 231, 0.9)),
                linear-gradient(120deg, rgba(189, 95, 60, 0.08), rgba(32, 107, 103, 0.08));
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 28px;
            padding: 2rem 2.2rem;
            box-shadow: var(--shadow);
            margin-bottom: 1rem;
        }

        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.76rem;
            font-weight: 700;
            color: var(--accent-strong);
            margin-bottom: 0.65rem;
        }

        .hero-copy {
            max-width: 760px;
            font-size: 1.02rem;
            line-height: 1.6;
            color: #40505b;
        }

        .chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.65rem;
            margin-top: 1.15rem;
        }

        .chip {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.55rem 0.85rem;
            border-radius: 999px;
            border: 1px solid rgba(23, 33, 43, 0.08);
            background: rgba(255, 255, 255, 0.85);
            color: #31414d;
            font-size: 0.9rem;
            font-weight: 600;
        }

        .chip-ok { color: var(--success); }
        .chip-warn { color: var(--warning); }
        .chip-danger { color: var(--danger); }

        .section-note {
            background: rgba(255, 255, 255, 0.72);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            margin-bottom: 1rem;
        }

        .mini-title {
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--accent-alt);
            margin-bottom: 0.35rem;
        }

        .card-title {
            font-family: "Space Grotesk", sans-serif;
            font-weight: 700;
            font-size: 1.08rem;
            color: var(--ink);
            margin-bottom: 0.2rem;
        }

        div[data-testid="stMetric"] {
            background: var(--surface);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 0.75rem 0.9rem;
            box-shadow: 0 12px 32px rgba(26, 37, 48, 0.05);
        }

        div[data-testid="stMetricValue"] {
            font-family: "Space Grotesk", sans-serif;
            color: var(--ink);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            margin-top: 0.6rem;
        }

        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.55);
            border-radius: 999px;
            padding: 0.65rem 1rem;
            border: 1px solid transparent;
            font-weight: 700;
        }

        .stTabs [aria-selected="true"] {
            background: rgba(255, 255, 255, 0.92);
            border-color: rgba(23, 33, 43, 0.08);
        }

        .stTextInput > div > div,
        .stTextArea textarea,
        .stSelectbox [data-baseweb="select"] > div,
        .stFileUploader > div {
            background: rgba(255, 255, 255, 0.86);
            border-radius: 16px;
            border-color: rgba(23, 33, 43, 0.11);
        }

        .stButton > button {
            border-radius: 999px;
            border: 1px solid rgba(23, 33, 43, 0.08);
            background: rgba(255, 255, 255, 0.9);
            color: var(--ink);
            font-weight: 700;
            min-height: 2.8rem;
        }

        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #b85c39, #924426);
            color: white;
            border: none;
        }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 22px;
            border-color: rgba(23, 33, 43, 0.08);
            background: var(--surface);
            box-shadow: 0 18px 48px rgba(26, 37, 48, 0.05);
        }

        .result-shell {
            background: rgba(255, 255, 255, 0.74);
            border: 1px solid rgba(23, 33, 43, 0.08);
            border-radius: 22px;
            padding: 1rem 1.1rem;
        }

        .vehicle-meta {
            color: #4d5d69;
            font-size: 0.94rem;
            line-height: 1.55;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=15, show_spinner=False)
def _fetch_health() -> dict[str, Any] | None:
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@st.cache_data(ttl=15, show_spinner=False)
def _fetch_vehicles() -> list[dict[str, Any]]:
    response = requests.get(f"{API_URL}/api/vehicles", timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def _invalidate_cached_data() -> None:
    _fetch_health.clear()
    _fetch_vehicles.clear()


def _resolve_asset_url(image_reference: str | None) -> str | None:
    if not image_reference:
        return None
    if image_reference.startswith(("http://", "https://")):
        return image_reference
    return f"{API_URL}/assets/images/{Path(image_reference).name}"


def _format_price(value: Any) -> str:
    if value in {None, ""}:
        return "-"
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{amount:,.0f} PLN".replace(",", " ")


def _format_confidence(value: Any) -> str:
    if value is None:
        return "-"
    try:
        return f"{float(value):.1%}"
    except (TypeError, ValueError):
        return str(value)


def _status_chip(label: str, value: str, tone: str = "chip-ok") -> str:
    return f"<span class='chip {tone}'>{label}: {value}</span>"


def _render_hero(health: dict[str, Any] | None) -> None:
    if health:
        backend_state = "online"
        backend_tone = "chip-ok"
        provider = health.get("agent_provider") or health.get("agent_mode", "rule-based")
        model = health.get("llm_model") or "fallback only"
        classifier = "ready" if health.get("classifier_loaded") else "lazy-load"
    else:
        backend_state = "offline"
        backend_tone = "chip-danger"
        provider = "unreachable"
        model = "-"
        classifier = "-"

    st.markdown(
        f"""
        <section class="hero">
            <div class="eyebrow">Vehicle Intelligence Workbench</div>
            <h1>Lepszy frontend do demo agenta, bez devowego chaosu.</h1>
            <p class="hero-copy">
                Jedno miejsce do zadawania pytan po polsku, inspekcji wygenerowanego SQL,
                weryfikacji klasyfikacji obrazu i przegladu seeded danych. Ta wersja stawia na
                czytelny przeplyw i szybkie demo, a nie na surowy formularz.
            </p>
            <div class="chip-row">
                {_status_chip("Backend", backend_state, backend_tone)}
                {_status_chip("Provider", provider)}
                {_status_chip("Model", model)}
                {_status_chip("Classifier", classifier)}
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def _render_health_banner(health: dict[str, Any] | None) -> None:
    if health:
        return

    st.warning(
        "Backend nie odpowiada. Uruchom `make api` w katalogu repo i odswiez strone."
    )


def _render_examples() -> None:
    st.markdown(
        """
        <div class="section-note">
            <div class="mini-title">Suggested prompts</div>
            <div class="card-title">Szybkie wejscie do demo</div>
            <div class="vehicle-meta">
                Klikniecie przykladu podstawia pytanie do edytora.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    examples = [
        "co ma Kowalski?",
        "pokaz mi auta powyzej 100k",
        "co kupiono w 2020?",
        "do kogo poszlo BMW X5?",
        "jak szla Corolla - kto kupowal, kto sprzedawal?",
        "ile aut jest dostepnych?",
    ]
    cols = st.columns(2)
    for index, example in enumerate(examples):
        if cols[index % 2].button(example, key=f"example_{index}", width="stretch"):
            st.session_state["agent_question"] = example


def _submit_agent_question(question: str) -> None:
    try:
        response = requests.post(
            f"{API_URL}/api/ask",
            json={"question": question},
            timeout=REQUEST_TIMEOUT + 10,
        )
        payload = response.json()
    except requests.ConnectionError:
        st.session_state["agent_response"] = {
            "error": "Nie mozna polaczyc sie z backendem.",
            "sql_query": "",
            "rows": [],
            "columns": [],
            "explanation": "",
        }
        return
    except Exception as exc:
        st.session_state["agent_response"] = {
            "error": f"Blad komunikacji: {exc}",
            "sql_query": "",
            "rows": [],
            "columns": [],
            "explanation": "",
        }
        return

    if response.status_code != 200:
        st.session_state["agent_response"] = {
            "error": payload.get("detail", response.text),
            "sql_query": payload.get("sql_query", ""),
            "rows": payload.get("rows", []),
            "columns": payload.get("columns", []),
            "explanation": payload.get("explanation", ""),
        }
        return

    st.session_state["agent_response"] = payload


def _render_agent_results() -> None:
    payload = st.session_state.get("agent_response")
    if not payload:
        st.info("Wynik pojawi sie tutaj po uruchomieniu zapytania.")
        return

    if payload.get("error"):
        st.error(payload["error"])
        if payload.get("sql_query"):
            st.code(payload["sql_query"], language="sql")
        return

    rows = payload.get("rows", [])
    columns = payload.get("columns", [])
    classified_rows = [
        row for row in rows if row.get("classification_vehicle_type") or row.get("image_url")
    ]

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Rekordy", len(rows))
    metric_2.metric("Kolumny", len(columns))
    metric_3.metric("Rekordy z obrazem", len(classified_rows))

    left, right = st.columns([1.25, 0.75], gap="large")
    with left:
        st.markdown(
            """
            <div class="result-shell">
                <div class="mini-title">Generated SQL</div>
                <div class="card-title">Dokladnie to wykonal backend</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.code(payload.get("sql_query", ""), language="sql")
    with right:
        st.markdown(
            """
            <div class="result-shell">
                <div class="mini-title">Reasoning summary</div>
                <div class="card-title">Skrocone wyjasnienie</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write(payload.get("explanation", ""))

    if rows:
        st.subheader("Wynik tabelaryczny")
        st.dataframe(rows, width="stretch", hide_index=True)

        preview_rows = [
            row for row in rows if row.get("brand") and row.get("model")
        ][:3]
        if preview_rows:
            st.subheader("Szybki podglad pojazdow")
            columns_layout = st.columns(len(preview_rows))
            for column, row in zip(columns_layout, preview_rows, strict=False):
                with column:
                    with st.container(border=True):
                        image_url = _resolve_asset_url(row.get("image_url"))
                        if image_url:
                            st.image(image_url, width="stretch")
                        st.markdown(
                            f"""
                            <div class="mini-title">{row.get('brand', '')}</div>
                            <div class="card-title">{row.get('model', '')}</div>
                            <div class="vehicle-meta">
                                Rocznik: {row.get('year', '-')}<br/>
                                Cena: {_format_price(row.get('price'))}<br/>
                                Klasyfikacja:
                                {row.get('classification_vehicle_type', '-') or '-'}<br/>
                                Pewnosc: {_format_confidence(row.get('classification_confidence'))}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
        with st.expander("Surowy JSON"):
            st.json(payload)
    else:
        st.warning("Brak wynikow dla tego pytania.")


def _render_agent_tab() -> None:
    st.subheader("Query Studio")
    left, right = st.columns([1.35, 0.9], gap="large")

    with left:
        st.markdown(
            """
            <div class="section-note">
                <div class="mini-title">Natural language to SQL</div>
                <div class="card-title">Zadawaj pytania jak na review albo demo</div>
                <div class="vehicle-meta">
                    Backend zwroci wygenerowany SQL, rekordy i klasyfikacje obrazow dla pojazdow.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if "agent_question" not in st.session_state:
            st.session_state["agent_question"] = "co ma Kowalski?"

        question = st.text_area(
            "Pytanie do agenta",
            key="agent_question",
            height=128,
            placeholder="np. co ma Kowalski? / kto kupil X5? / auta powyzej 100k",
        )

        action_col_1, action_col_2 = st.columns([1, 1])
        with action_col_1:
            run_question = st.button(
                "Uruchom zapytanie",
                type="primary",
                width="stretch",
                disabled=not question.strip(),
            )
        with action_col_2:
            if st.button("Wyczysc odpowiedz", width="stretch"):
                st.session_state.pop("agent_response", None)
                st.rerun()

        if run_question and question.strip():
            with st.spinner("Agent analizuje pytanie i sklada SQL..."):
                _submit_agent_question(question.strip())

        _render_agent_results()

    with right:
        _render_examples()


def _show_classification(result: dict[str, Any]) -> None:
    if "detail" in result:
        st.error(result["detail"])
        return

    vehicle_type = result.get("vehicle_type", "?")
    confidence = result.get("confidence", 0)
    imagenet_class = result.get("imagenet_class", "?")
    is_vehicle = result.get("is_vehicle", False)

    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Typ", vehicle_type)
    metric_2.metric("Pewnosc", _format_confidence(confidence))
    metric_3.metric("ImageNet", imagenet_class)

    if is_vehicle:
        st.success("Model rozpoznal pojazd.")
    else:
        st.warning("Model nie rozpoznal pojazdu.")


def _submit_url_classification(image_url: str) -> None:
    try:
        response = requests.post(
            f"{API_URL}/api/classify",
            json={"image_url": image_url},
            timeout=REQUEST_TIMEOUT + 10,
        )
        st.session_state["classification_response"] = response.json()
        st.session_state["classification_preview"] = image_url
    except Exception as exc:
        st.session_state["classification_response"] = {"detail": str(exc)}
        st.session_state["classification_preview"] = image_url


def _submit_upload_classification(uploaded_file) -> None:
    try:
        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        response = requests.post(
            f"{API_URL}/api/classify/upload",
            files=files,
            timeout=REQUEST_TIMEOUT + 10,
        )
        st.session_state["classification_response"] = response.json()
        st.session_state["classification_preview"] = uploaded_file.getvalue()
    except Exception as exc:
        st.session_state["classification_response"] = {"detail": str(exc)}


def _render_classifier_samples(vehicles: list[dict[str, Any]]) -> None:
    st.markdown(
        """
        <div class="section-note">
            <div class="mini-title">Demo samples</div>
            <div class="card-title">Jednym kliknieciem odpal seeded obraz</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    sample_columns = st.columns(2)
    for index, vehicle in enumerate(vehicles[:4]):
        image_url = None
        if vehicle.get("images"):
            image_url = _resolve_asset_url(vehicle["images"][0]["image_url"])
        if not image_url:
            continue
        label = f"{vehicle['brand']} {vehicle['model']}"
        if sample_columns[index % 2].button(
            label,
            key=f"sample_{vehicle['vehicle_id']}",
            width="stretch",
        ):
            st.session_state["classify_url_value"] = image_url


def _render_classifier_tab(vehicles: list[dict[str, Any]]) -> None:
    st.subheader("Image Lab")
    top_left, top_right = st.columns([1.1, 0.9], gap="large")

    with top_left:
        st.markdown(
            """
            <div class="section-note">
                <div class="mini-title">Image classification</div>
                <div class="card-title">Sprawdz pojedynczy obraz niezaleznie od agenta</div>
                <div class="vehicle-meta">
                    Uzyj wlasnego pliku albo URL-a. To dobry sposob na pokazanie,
                    ze czesc vision dziala niezaleznie od toru NL to SQL.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        uploader_col, url_col = st.columns(2, gap="large")
        with uploader_col:
            uploaded_file = st.file_uploader(
                "Wgraj plik",
                type=["jpg", "jpeg", "png", "webp"],
                label_visibility="visible",
            )
            if uploaded_file and st.button("Klasyfikuj plik", width="stretch"):
                with st.spinner("Model analizuje plik..."):
                    _submit_upload_classification(uploaded_file)

        with url_col:
            if "classify_url_value" not in st.session_state:
                st.session_state["classify_url_value"] = ""
            image_url = st.text_input(
                "URL obrazu",
                key="classify_url_value",
                placeholder="https://example.com/car.jpg",
            )
            if image_url and st.button("Klasyfikuj URL", width="stretch"):
                with st.spinner("Model analizuje URL..."):
                    _submit_url_classification(image_url)

    with top_right:
        _render_classifier_samples(vehicles)

    payload = st.session_state.get("classification_response")
    preview = st.session_state.get("classification_preview")
    if payload:
        st.subheader("Wynik klasyfikacji")
        preview_col, result_col = st.columns([0.9, 1.1], gap="large")
        with preview_col:
            if preview:
                st.image(preview, width="stretch")
        with result_col:
            _show_classification(payload)


def _render_vehicle_card(vehicle: dict[str, Any]) -> None:
    image_url = None
    if vehicle.get("images"):
        image_url = _resolve_asset_url(vehicle["images"][0]["image_url"])

    with st.container(border=True):
        if image_url:
            st.image(image_url, width="stretch")
        availability = vehicle.get("availability", "-")
        tone = "chip-ok" if availability == "available" else "chip-warn"
        st.markdown(
            f"""
            <div class="mini-title">{vehicle.get('brand', '')}</div>
            <div class="card-title">{vehicle.get('model', '')}</div>
            <div class="chip-row" style="margin-top:0.6rem; margin-bottom:0.8rem;">
                {_status_chip("Status", availability, tone)}
                {_status_chip("Rok", str(vehicle.get('year', '-')))}
            </div>
            <div class="vehicle-meta">
                Cena katalogowa: {_format_price(vehicle.get('price'))}<br/>
                Vehicle ID: {vehicle.get('vehicle_id')}
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_catalog_tab() -> None:
    st.subheader("Fleet Index")
    refresh_col, spacer = st.columns([0.22, 0.78])
    with refresh_col:
        if st.button("Odswiez dane", width="stretch"):
            _invalidate_cached_data()
            st.rerun()

    try:
        vehicles = _fetch_vehicles()
    except requests.ConnectionError:
        st.warning("Backend nie jest dostepny.")
        return
    except Exception as exc:
        st.error(f"Blad pobierania pojazdow: {exc}")
        return

    available_count = sum(1 for vehicle in vehicles if vehicle.get("availability") == "available")
    sold_count = len(vehicles) - available_count
    metric_1, metric_2, metric_3 = st.columns(3)
    metric_1.metric("Pojazdy", len(vehicles))
    metric_2.metric("Dostepne", available_count)
    metric_3.metric("Sprzedane", sold_count)

    grid = st.columns(3, gap="large")
    for index, vehicle in enumerate(vehicles):
        with grid[index % 3]:
            _render_vehicle_card(vehicle)


_inject_styles()

health_payload = _fetch_health()
_render_hero(health_payload)
_render_health_banner(health_payload)

try:
    vehicles_payload = _fetch_vehicles()
except Exception:
    vehicles_payload = []

tab_agent, tab_classify, tab_catalog = st.tabs(
    ["Query Studio", "Image Lab", "Fleet Index"]
)

with tab_agent:
    _render_agent_tab()

with tab_classify:
    _render_classifier_tab(vehicles_payload)

with tab_catalog:
    _render_catalog_tab()
