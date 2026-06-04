import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "10000"))
    print(f"Starting VentureMind AI API on 0.0.0.0:{port}", flush=True)
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        lifespan="off",
        log_level="debug",
        loop="asyncio",
        http="h11",
    )


if __name__ == "__main__":
    main()
