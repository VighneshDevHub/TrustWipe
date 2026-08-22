from app.core.crypto import generate_keypair, sign_payload, verify_signature


def test_sign_and_verify_roundtrip():
    private_pem, public_pem = generate_keypair()
    payload = {"device_serial": "ABC123", "verification_passed": True}

    report_hash, signature = sign_payload(payload, private_pem)

    assert len(report_hash) == 64  # sha256 hex digest length
    assert verify_signature(payload, signature, public_pem) is True


def test_verify_fails_if_payload_altered_after_signing():
    private_pem, public_pem = generate_keypair()
    payload = {"device_serial": "ABC123", "verification_passed": True}

    _hash, signature = sign_payload(payload, private_pem)

    tampered_payload = {"device_serial": "ABC123", "verification_passed": False}
    assert verify_signature(tampered_payload, signature, public_pem) is False


def test_verify_fails_with_wrong_public_key():
    private_pem, _public_pem = generate_keypair()
    _other_private, other_public_pem = generate_keypair()
    payload = {"device_serial": "ABC123"}

    _hash, signature = sign_payload(payload, private_pem)

    assert verify_signature(payload, signature, other_public_pem) is False


def test_verify_fails_with_garbage_signature():
    _private_pem, public_pem = generate_keypair()
    payload = {"device_serial": "ABC123"}

    assert verify_signature(payload, "not-a-real-signature", public_pem) is False
