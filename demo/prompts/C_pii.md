# C — PII → redact locally, then cloud on the clean text
# Expected: pii_redacted=true, placeholders for email/phone/account, then cloud

A customer emailed support. Draft a careful reply and list the next internal steps.

From: Priya Naidoo <priya.naidoo@example.net>
Phone: +27 82 555 0147
Account number: 88219403
South African ID: 9001014800088

Hi, I was charged twice for invoice INV-4412 last Tuesday. Please refund the duplicate
R1,280.00 to the card on file ending 4242 and confirm by email. My colleague
lerato.maseko@example.com is copied.

Do not include the raw email, phone, ID, or account number in any outbound draft.
