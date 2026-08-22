import pytest

from src.detectors.file_target import FileTargetDetector
from src.method_selector import select_wiper
from src.wipers.clear import ClearWiper
from src.wipers.crypto_erase import CryptoEraseWiper
from src.wipers.purge import PurgeWiper


def test_file_target_detector_reads_real_size(tmp_path):
    path = tmp_path / "vol.img"
    path.write_bytes(b"x" * 4096)

    device = FileTargetDetector().detect(str(path))

    assert device.device_type == "TEST_FILE"
    assert device.size_bytes == 4096
    assert device.serial.startswith("TESTFILE-")


def test_file_target_detector_raises_on_missing_file(tmp_path):
    missing = tmp_path / "does_not_exist.img"
    with pytest.raises(FileNotFoundError):
        FileTargetDetector().detect(str(missing))


def test_detector_is_stable_across_repeated_calls(tmp_path):
    """Same file path -> same fake serial, so repeated demo runs are
    predictable rather than generating a new random device each time."""
    path = tmp_path / "vol.img"
    path.write_bytes(b"x" * 100)

    device1 = FileTargetDetector().detect(str(path))
    device2 = FileTargetDetector().detect(str(path))

    assert device1.serial == device2.serial


@pytest.mark.parametrize(
    "device_type,supports_encryption,expected_wiper",
    [
        ("TEST_FILE", False, ClearWiper),
        ("SSD", True, CryptoEraseWiper),
        ("NVMe", True, CryptoEraseWiper),
        ("HDD", False, PurgeWiper),
        ("USB", False, ClearWiper),
    ],
)
def test_method_selector_maps_device_type_correctly(
    device_type, supports_encryption, expected_wiper
):
    wiper = select_wiper(device_type, supports_encryption)
    assert isinstance(wiper, expected_wiper)
