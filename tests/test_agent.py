from app.agent.sql_agent import get_agent


def test_agent_returns_current_owner_inventory(db_session):
    agent = get_agent()

    result = agent.ask("co ma Kowalski?", db_session)

    assert result.error is None
    assert "vehicle_id" in result.columns
    assert len(result.rows) == 1
    assert result.rows[0]["model"] == "CBR600RR"


def test_agent_returns_historical_owner_inventory(db_session):
    agent = get_agent()

    result = agent.ask(
        "Znajdz wszystkie samochody, ktorych wlascicielem byl Jan Kowalski.",
        db_session,
    )

    assert result.error is None
    assert {row["model"] for row in result.rows} == {"Corolla", "CBR600RR"}
    assert result.sql_query.lower().startswith("select")


def test_agent_filters_by_price(db_session):
    agent = get_agent()

    result = agent.ask("pokaz mi auta powyzej 100k", db_session)

    assert result.error is None
    assert {row["model"] for row in result.rows} == {"X5", "TGS"}
