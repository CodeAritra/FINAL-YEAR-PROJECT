"""Unit tests for SecretDetector guardrail."""

from guardrails.secret_detector import SecretDetector


def test_secret_detection_openai_key():
    detector = SecretDetector()
    text = "Here is my secret API key: sk-abcdef1234567890abcdef1234567890 for OpenAI."
    matches = detector.scan(text)
    assert len(matches) >= 1
    assert matches[0].pattern_name == "OpenAI API Key"

    sanitized, _ = detector.redact(text)
    assert "sk-" not in sanitized
    assert "[REDACTED_OPENAI_API_KEY]" in sanitized


def test_secret_detection_password():
    detector = SecretDetector()
    text = "The database password = 'SuperSecretP@ssw0rd!' and username is admin."
    sanitized, matches = detector.redact(text)
    assert len(matches) >= 1
    assert "SuperSecretP@ssw0rd!" not in sanitized


def test_clean_text_no_secrets():
    detector = SecretDetector()
    text = "The quick brown fox jumps over the lazy dog. Today is a sunny day."
    matches = detector.scan(text)
    assert len(matches) == 0

