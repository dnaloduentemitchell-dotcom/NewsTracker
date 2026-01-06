from app.analysis.engine import analyze_item


def test_symbol_mapping_for_gold() -> None:
    analysis = analyze_item("Gold jumps on risk-off", "", "Risk-off tone boosts gold demand")
    assert "XAU/USD" in analysis.impacted_symbols


def test_impact_scoring_rules() -> None:
    analysis = analyze_item("Fed signals rate cut", "", "Dovish tone and rate cut discussions weigh on USD")
    assert analysis.direction in {"bearish", "bullish", "uncertain"}
    assert 0 <= analysis.confidence <= 100
