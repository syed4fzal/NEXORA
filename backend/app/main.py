"""
app/main.py
~~~~~~~~~~~
Application entrypoint. Creates and configures the FastAPI instance.

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI

app = FastAPI(title="Nexora API")


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    """Simple liveness check used by monitoring tools and load balancers."""
    return {"status": "healthy", "service": "Nexora API"}


@app.get("/", tags=["Root"])
def root() -> dict:
    """Basic root endpoint with a welcome message."""
    return {"message": "Welcome to Nexora API"}