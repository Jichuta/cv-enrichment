"""Entry point — start the FastAPI server with uvicorn."""

import uvicorn

if __name__ == "__main__":
    # Import here so the .env is loaded before settings are read
    from app.core.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_DEBUG,
        log_level="debug" if settings.APP_DEBUG else "info",
    )
