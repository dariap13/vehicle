"""Frontend Streamlit dla Vehicle AI Agent."""

from __future__ import annotations

import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Vehicle AI Agent",
    page_icon="🚗",
    layout="wide",
)

st.title("🚗 Vehicle AI Agent")
st.caption("Klasyfikacja pojazdow + agent NL→SQL")


def _show_classification(result: dict) -> None:
    if "detail" in result:
        st.error(result["detail"])
        return

    vehicle_type = result.get("vehicle_type", "?")
    confidence = result.get("confidence", 0)
    imagenet_class = result.get("imagenet_class", "?")
    is_vehicle = result.get("is_vehicle", False)

    if is_vehicle:
        st.success(f"{vehicle_type} (pewnosc: {confidence:.1%})")
    else:
        st.warning(f"Nie rozpoznano pojazdu: {imagenet_class} ({confidence:.1%})")

    st.caption(f"Klasa ImageNet: `{imagenet_class}`")


def _health_badge() -> None:
    try:
        response = requests.get(f"{API_URL}/api/health", timeout=5)
        response.raise_for_status()
        health = response.json()
        st.info(
            "Backend: OK | "
            f"agent: {health.get('agent_mode', 'unknown')} | "
            f"klasyfikator: {'gotowy' if health.get('classifier_loaded') else 'lazy-load'}"
        )
    except Exception:
        st.warning("Backend nie odpowiada. Uruchom `uvicorn app.main:app --port 8000`.")


_health_badge()

tab_agent, tab_classify, tab_vehicles = st.tabs(
    ["🤖 Agent AI", "📷 Klasyfikator", "📋 Lista pojazdow"]
)


with tab_agent:
    st.header("Zapytaj o pojazdy")
    examples = [
        "co ma Kowalski?",
        "pokaz mi auta powyzej 100k",
        "co kupiono w 2020?",
        "do kogo poszlo BMW X5?",
        "jak szla Corolla - kto kupowal, kto sprzedawal?",
        "ile aut jest dostepnych?",
    ]

    selected_example = st.selectbox("Przyklady", ["(wpisz wlasne)"] + examples)
    question = st.text_input(
        "Twoje pytanie",
        value=selected_example if selected_example != "(wpisz wlasne)" else "",
        placeholder="np. co ma Kowalski? / auta powyzej 100k / kto kupil X5?",
    )

    if st.button("Zapytaj", type="primary", disabled=not question):
        with st.spinner("Agent analizuje pytanie..."):
            try:
                response = requests.post(
                    f"{API_URL}/api/ask",
                    json={"question": question},
                    timeout=30,
                )
                payload = response.json()

                if response.status_code != 200:
                    st.error(payload.get("detail", response.text))
                elif payload.get("error"):
                    st.error(payload["error"])
                    if payload.get("sql_query"):
                        st.code(payload["sql_query"], language="sql")
                else:
                    st.subheader("Wygenerowane SQL")
                    st.code(payload["sql_query"], language="sql")
                    st.caption(payload["explanation"])

                    st.subheader(f"Wyniki ({len(payload['rows'])} rekordow)")
                    if payload["rows"]:
                        st.dataframe(payload["rows"], use_container_width=True)
                        with st.expander("Surowy JSON"):
                            st.json(payload)
                    else:
                        st.warning("Brak wynikow dla tego pytania.")
            except requests.ConnectionError:
                st.error("Nie mozna polaczyc sie z backendem.")
            except Exception as exc:
                st.error(f"Blad: {exc}")


with tab_classify:
    st.header("Klasyfikuj zdjecie pojazdu")
    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader("Wgraj plik", type=["jpg", "jpeg", "png", "webp"])
        if uploaded_file and st.button("Klasyfikuj plik", key="classify_file"):
            with st.spinner("Klasyfikuje..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
                    response = requests.post(
                        f"{API_URL}/api/classify/upload",
                        files=files,
                        timeout=30,
                    )
                    payload = response.json()
                    st.image(uploaded_file, width=320)
                    _show_classification(payload)
                except Exception as exc:
                    st.error(f"Blad: {exc}")

    with col2:
        image_url = st.text_input("URL obrazu", placeholder="https://example.com/car.jpg")
        if image_url and st.button("Klasyfikuj URL", key="classify_url"):
            with st.spinner("Klasyfikuje..."):
                try:
                    response = requests.post(
                        f"{API_URL}/api/classify",
                        json={"image_url": image_url},
                        timeout=30,
                    )
                    payload = response.json()
                    st.image(image_url, width=320)
                    _show_classification(payload)
                except Exception as exc:
                    st.error(f"Blad: {exc}")


with tab_vehicles:
    st.header("Pojazdy w bazie danych")
    if st.button("Odswiez", key="refresh_vehicles"):
        st.rerun()

    try:
        response = requests.get(f"{API_URL}/api/vehicles", timeout=10)
        response.raise_for_status()
        vehicles = response.json()

        if not vehicles:
            st.warning("Baza nie zawiera pojazdow.")
        else:
            st.dataframe(vehicles, use_container_width=True)
    except requests.ConnectionError:
        st.warning("Backend nie jest dostepny.")
    except Exception as exc:
        st.error(f"Blad: {exc}")
