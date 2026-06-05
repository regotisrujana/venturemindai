import os
import sys
import traceback

import uvicorn


def main() -> None:
    port = int(os.environ.get("PORT", "10000"))
    print(f"Starting VentureMind AI API on 0.0.0.0:{port}", flush=True)
    try:
        from app.main import app
        from app.core.database import Base, engine

        print("Imported FastAPI app successfully.", flush=True)
        try:
            Base.metadata.create_all(bind=engine)
            print("Database tables verified before server start.", flush=True)
        except Exception:
            print("Database table verification failed before server start:", flush=True)
            traceback.print_exc()
        if not any(getattr(route, "path", "") == "/api/health" for route in app.routes):
            @app.get("/api/health")
            def render_health():
                return {"status": "ok", "service": "VentureMind AI", "environment": os.environ.get("ENVIRONMENT", "production")}

        if not any(getattr(route, "path", "") == "/api/health/db" for route in app.routes):
            @app.get("/api/health/db")
            def render_database_health():
                from sqlalchemy import text

                from app.core.database import engine

                try:
                    with engine.connect() as connection:
                        connection.execute(text("SELECT 1"))
                    return {"status": "ok", "database": "postgresql"}
                except Exception as exc:
                    return {"status": "error", "database": "postgresql", "detail": str(exc)}

        print("Registered routes:", [getattr(route, "path", "") for route in app.routes], flush=True)
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
