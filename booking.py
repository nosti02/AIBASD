import json
from pathlib import Path
from typing import TypedDict


CAPACITY = 10
DATA_DIRECTORY = Path(__file__).parent
BOOKING_FILE = DATA_DIRECTORY / "booking_list.json"
WAITING_FILE = DATA_DIRECTORY / "waiting_list.json"


class BookingEntry(TypedDict):
    number: int
    id: str


def _load_json(path: Path) -> object:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def _booking_entries(value: object, key: str) -> list[BookingEntry]:
    if isinstance(value, list):
        entries = value
    elif isinstance(value, dict):
        entries = value.get(key, [])
    else:
        raise ValueError(f"Expected a JSON list or object containing '{key}'.")

    if not isinstance(entries, list):
        raise ValueError(f"Expected '{key}' to be a JSON list.")

    result: list[BookingEntry] = []
    for index, entry in enumerate(entries):
        if isinstance(entry, str):
            participant_id = entry
        elif isinstance(entry, dict) and isinstance(entry.get("id"), str):
            participant_id = entry["id"]
        else:
            raise ValueError(f"Invalid entry at position {index} in '{key}'.")
        result.append({"number": index, "id": participant_id})
    return result


class BookingSystem:
    def __init__(
        self,
        booking_file: Path = BOOKING_FILE,
        waiting_file: Path = WAITING_FILE,
    ) -> None:
        self.booking_file = booking_file
        self.waiting_file = waiting_file

        booking_data = _load_json(booking_file)
        waiting_data = _load_json(waiting_file)
        self.confirmed: list[BookingEntry] = _booking_entries(
            booking_data, "confirmed_bookings"
        )
        self.waiting: list[BookingEntry] = _booking_entries(
            waiting_data, "waiting_list"
        )

        if isinstance(booking_data, dict):
            users = booking_data.get("users", [])
        else:
            users = []
        if not isinstance(users, list) or not all(
            isinstance(user, str) for user in users
        ):
            raise ValueError(
                "Expected 'users' in booking_list.json to be a list of IDs."
            )

        self.users: set[str] = set(users)
        self.users.update(item["id"] for item in self.confirmed)
        self.users.update(item["id"] for item in self.waiting)

    def save(self) -> None:
        booking_data = {
            "users": sorted(self.users),
            "confirmed_bookings": self.confirmed,
        }
        waiting_data = {"waiting_list": self.waiting}
        with self.booking_file.open("w", encoding="utf-8") as file:
            json.dump(booking_data, file, indent=2)
            file.write("\n")
        with self.waiting_file.open("w", encoding="utf-8") as file:
            json.dump(waiting_data, file, indent=2)
            file.write("\n")

    def register(self, participant_id: str) -> str:
        if participant_id in self.users:
            return f"Error: user with ID: {participant_id} already exists!"
        self.users.add(participant_id)
        self.save()
        return f"Success: user with ID: {participant_id} registered!"

    def book(self, participant_id: str) -> str:
        booked_ids = {item["id"] for item in self.confirmed + self.waiting}
        if participant_id in booked_ids:
            return "Duplicate: this user is already booked or is in the waitinglist!"

        if len(self.confirmed) < CAPACITY:
            self.confirmed.append(
                {"number": len(self.confirmed), "id": participant_id}
            )
            self.save()
            return "Confirmed: booking confirmed!"

        self.waiting.append({"number": len(self.waiting), "id": participant_id})
        self.save()
        return "Waitinglist: booking scheduled!"

    def listing(self) -> str:
        lines = [
            f"Confirmed bookings: {len(self.confirmed)}",
            "Nr. | ID",
            "-----------------------------------",
        ]
        lines.extend(
            f"{index + 1}   | {entry['id']}"
            for index, entry in enumerate(self.confirmed)
        )
        lines.extend(
            [
                "",
                f"Waitinglist: {len(self.waiting)}",
                "Nr. | ID",
                "-----------------------------------",
            ]
        )
        lines.extend(
            f"{index + 1}   | {entry['id']}"
            for index, entry in enumerate(self.waiting)
        )
        return "\n".join(lines)


def print_help() -> None:
    print(
        "Following actions are supported:\n"
        "- help: Lists available actions.\n"
        "- register [ID]: Registers an account.\n"
        "- login [ID]: Logs in a registered user.\n"
        "- logout: Logs out the current user.\n"
        "- book: Books a place for the active user.\n"
        "- list: Displays bookings, waiting list, and their counts.\n"
        "- exit: Terminates the program."
    )


def main() -> int:
    try:
        system = BookingSystem()
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Error: could not load booking data: {error}")
        return 1

    active_user = None
    print("Welcome to booking cli for our workshop!")
    print("Type help to see possible actions")

    while True:
        try:
            command = input("> ").strip().split()
        except EOFError:
            print()
            return 0
        if not command:
            continue

        action, *arguments = command
        if action == "help":
            print_help()
        elif action == "register":
            if active_user is not None:
                print("Error: someone is already logged in! Please logout first!")
            elif len(arguments) != 1:
                print("Error: please provide a user ID!")
            else:
                try:
                    print(system.register(arguments[0]))
                except OSError as error:
                    print(f"Error: could not save booking data: {error}")
                    return 1
        elif action == "login":
            if active_user is not None:
                print("Error: someone is already logged in!")
            elif len(arguments) != 1 or arguments[0] not in system.users:
                print("Error: user not found!")
            else:
                active_user = arguments[0]
                print(f"Success: user with ID: {active_user} active!")
        elif action == "logout":
            if active_user is None:
                print("Error: no active user! Please login first!")
            else:
                print(f"Success: user with ID: {active_user} logged out!")
                active_user = None
        elif action == "book":
            if active_user is None:
                print("Error: no active user! Please login first!")
            else:
                try:
                    print(system.book(active_user))
                except OSError as error:
                    print(f"Error: could not save booking data: {error}")
                    return 1
        elif action == "list":
            print(system.listing())
        elif action == "exit":
            return 0
        else:
            print("Error: unknown action!")


if __name__ == "__main__":
    raise SystemExit(main())
