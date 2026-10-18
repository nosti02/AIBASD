import pytest

from booking import BookingSystem


def make_system(tmp_path):
    return BookingSystem(tmp_path / "booking_list.json", tmp_path / "waiting_list.json")


def test_capacity_and_ordered_waiting_list(tmp_path):
    system = make_system(tmp_path)

    for number in range(1, 11):
        assert system.book(f"user{number}") == "Confirmed: booking confirmed!"
    assert system.book("user11") == "Waitinglist: booking scheduled!"
    assert system.book("user12") == "Waitinglist: booking scheduled!"

    assert len(system.confirmed) == 10
    assert [entry["id"] for entry in system.waiting] == ["user11", "user12"]
    assert "Waitinglist: 2" in system.listing()
    assert "1   | user11\n2   | user12" in system.listing()


@pytest.mark.parametrize(
    "booking_count, duplicate_id",
    [(1, "user1"), (11, "user11")],
    ids=["confirmed", "waiting-list"],
)
def test_duplicate_booking_does_not_change_state(
    tmp_path, booking_count, duplicate_id
):
    system = make_system(tmp_path)
    for number in range(1, booking_count + 1):
        system.book(f"user{number}")
    before_confirmed = [entry.copy() for entry in system.confirmed]
    before_waiting = [entry.copy() for entry in system.waiting]

    assert system.book(duplicate_id).startswith("Duplicate:")
    assert system.confirmed == before_confirmed
    assert system.waiting == before_waiting


def test_registration_and_bookings_persist(tmp_path):
    system = make_system(tmp_path)
    assert system.register("ava") == "Success: user with ID: ava registered!"
    system.book("ava")

    loaded = make_system(tmp_path)
    assert "ava" in loaded.users
    assert [entry["id"] for entry in loaded.confirmed] == ["ava"]


def test_listing_includes_counts_and_both_lists(tmp_path):
    system = make_system(tmp_path)
    system.book("ava")
    for number in range(1, 11):
        system.book(f"user{number}")

    listing = system.listing()
    assert "Confirmed bookings: 10" in listing
    assert "Waitinglist: 1" in listing
    assert "1   | ava" in listing
    assert "1   | user10" in listing
