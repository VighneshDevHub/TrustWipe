import os

import pytest

from src.wipers.clear import ClearWiper
from src.wipers.crypto_erase import CryptoEraseWiper
from src.wipers.purge import PurgeWiper


@pytest.fixture
def test_file(tmp_path):
    path = tmp_path / "test_volume.img"
    original_content = b"SENSITIVE-DATA-" * 1000  # 15,000 bytes of "data"
    path.write_bytes(original_content)
    return str(path), original_content


def test_clear_wiper_overwrites_all_content(test_file):
    path, original_content = test_file
    size = len(original_content)

    result = ClearWiper().wipe(path, size)

    assert result.passes == 1
    assert result.bytes_processed == size
    with open(path, "rb") as f:
        new_content = f.read()
    assert new_content != original_content
    assert len(new_content) == size


def test_purge_wiper_does_three_passes(test_file):
    path, original_content = test_file
    size = len(original_content)

    result = PurgeWiper().wipe(path, size)

    assert result.passes == 3
    with open(path, "rb") as f:
        new_content = f.read()
    # Final pass is all zeros
    assert new_content == b"\x00" * size


def test_crypto_erase_wiper_overwrites_content(test_file):
    path, original_content = test_file
    size = len(original_content)

    result = CryptoEraseWiper().wipe(path, size)

    assert result.bytes_processed == size
    with open(path, "rb") as f:
        new_content = f.read()
    assert new_content != original_content
