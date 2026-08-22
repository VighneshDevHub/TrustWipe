from src.verifier import capture_pre_wipe_samples, verify_wipe
from src.wipers.clear import ClearWiper


def test_verify_wipe_passes_after_real_wipe(tmp_path):
    path = tmp_path / "vol.img"
    path.write_bytes(b"SECRET" * 500)
    size = path.stat().st_size

    samples = capture_pre_wipe_samples(str(path), size)
    ClearWiper().wipe(str(path), size)

    result = verify_wipe(str(path), samples)
    assert result.passed is True
    assert result.samples_changed == result.samples_checked


def test_verify_wipe_fails_if_nothing_was_actually_wiped(tmp_path):
    """The important negative test: if a 'wipe' is a no-op (e.g. a buggy
    wiper that didn't actually write anything), verification must catch
    it rather than blindly reporting success."""
    path = tmp_path / "vol.img"
    path.write_bytes(b"SECRET" * 500)
    size = path.stat().st_size

    samples = capture_pre_wipe_samples(str(path), size)
    # Deliberately skip the wipe step — content is untouched

    result = verify_wipe(str(path), samples)
    assert result.passed is False
    assert result.samples_changed == 0
