from powerdnsadmin.lib.password_login import otp_lock_minutes


def test_otp_lock_durations_stagger_and_then_double():
    assert [otp_lock_minutes(number) for number in range(1, 8)] == [
        5, 15, 30, 60, 120, 240, 480,
    ]
    assert otp_lock_minutes(8) == 960
    assert otp_lock_minutes(9) == 1920
    assert otp_lock_minutes(30) == 7 * 24 * 60
