import pytest
from backend.routes.ai_routes import detect_intent, tokenize

def test_tokenize():
    norm, tokens = tokenize("What's the profit for 2024?")
    assert "profit" in tokens
    assert "2024" in tokens

def test_detect_intent_profit():
    norm, tokens = tokenize("tell me about my profits")
    assert detect_intent(norm, tokens) == "profit"

def test_detect_intent_inventory():
    norm, tokens = tokenize("will I run out of stock?")
    assert detect_intent(norm, tokens) == "inventory"

def test_detect_intent_none():
    norm, tokens = tokenize("hello assistant")
    assert detect_intent(norm, tokens) is None

def test_detect_intent_alerts():
    norm, tokens = tokenize("show me any active alerts")
    assert detect_intent(norm, tokens) == "alerts"
