from __future__ import annotations

DEPRECATION_MESSAGE = (
    "This project has been deprecated and the Notion update automation is disabled. "
    "No Notion or OpenAI calls will be made."
)


def run() -> None:
    print(DEPRECATION_MESSAGE)


if __name__ == "__main__":
    run()
