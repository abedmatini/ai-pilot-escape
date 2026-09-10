from demo.pii import redact


def test_redacts_email_phone_and_sa_id():
    text = (
        "Call +27 82 555 0147 or email ada@example.com. "
        "ID 9001014800088 account number 88219403."
    )
    result = redact(text)
    assert result.has_pii
    assert "ada@example.com" not in result.redacted
    assert "9001014800088" not in result.redacted
    assert "+27 82 555 0147" not in result.redacted
    assert "88219403" not in result.redacted
    assert "[EMAIL_1]" in result.redacted
    assert "[PHONE_1]" in result.redacted
    assert "[SA_ID_1]" in result.redacted
    assert "[ACCOUNT_1]" in result.redacted


def test_same_email_reuses_placeholder():
    result = redact("ada@example.com wrote to ada@example.com")
    assert result.redacted.count("[EMAIL_1]") == 2
    assert "[EMAIL_2]" not in result.redacted


def test_luhn_card_redacted_random_digits_kept():
    # Visa test PAN 4111111111111111 passes Luhn.
    text = "card 4111111111111111 vs order 123456789012"
    result = redact(text)
    assert "4111111111111111" not in result.redacted
    assert "[CC_1]" in result.redacted
    assert "123456789012" in result.redacted


def test_no_pii_unchanged():
    text = "Summarize standup: move it to 10:30."
    result = redact(text)
    assert not result.has_pii
    assert result.redacted == text


def test_api_key_shape_redacted():
    result = redact("key AIzaSyA-demo-key-that-is-long-enough")
    assert result.has_pii
    assert "AIza" not in result.redacted
