import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "creatorforge_worker.api:create_app",
        factory=True,
        host=os.environ.get("CF_HOST", "0.0.0.0"),
        port=int(os.environ.get("CF_PORT", "8765")),
    )


if __name__ == "__main__":
    main()
