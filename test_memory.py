from memory import automatic_ram_gb, maximum_manual_ram_gb, validate_ram_gb


def test_automatic_ram_policy():
    assert automatic_ram_gb(4) == 2
    assert automatic_ram_gb(8) == 4
    assert automatic_ram_gb(16) == 8
    assert automatic_ram_gb(32) == 10


def test_manual_ram_limit_keeps_host_reserve():
    assert maximum_manual_ram_gb(4) == 2
    assert maximum_manual_ram_gb(8) == 4
    assert maximum_manual_ram_gb(16) == 12
    assert maximum_manual_ram_gb(32) == 16


def test_manual_ram_validation():
    assert validate_ram_gb(2, 8)[0] is True
    assert validate_ram_gb(4, 8)[0] is True
    assert validate_ram_gb(6, 8)[0] is False
    assert validate_ram_gb(1, 16)[0] is False
    assert validate_ram_gb("not-a-number", 16)[0] is False


if __name__ == "__main__":
    test_automatic_ram_policy()
    test_manual_ram_limit_keeps_host_reserve()
    test_manual_ram_validation()
    print("RAM policy tests passed.")
