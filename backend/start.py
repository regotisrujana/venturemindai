import os
import sys
import traceback

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "10000"))
    print(f"Starting VentureMind AI API on 0.0.0.0:{port}", flush=True)
    try:
        from app.main import app

        print("Imported FastAPI app successfully.", flush=True)
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            lifespan="off",
            log_level="debug",
            loop="asyncio",
            http="h11",
        )
    except BaseException:
        print("VentureMind API failed during Render startup:", flush=True)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
