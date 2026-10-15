from fastapi import FastAPI

from app.auth.router import router as auth_router
from app.common.security import csrf_middleware, security_headers_middleware
from app.config import get_settings
from app.logs.router import router as logs_router
from app.nutrition.router import router as nutrition_router
from app.plans.router import router as plans_router
from app.profile.router import router as profile_router

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(title="FitPlan API", docs_url=None, redoc_url=None, openapi_url=None)

    # Order: the last registered middleware runs first, so headers are added to CSRF errors too.
    app.middleware("http")(csrf_middleware)
    app.middleware("http")(security_headers_middleware)

    @app.get("/api/health", include_in_schema=False)
    def health() -> dict[str, str]:
        # No DB access: used by the frontend to wake a sleeping free-tier instance cheaply.
        return {"status": "ok"}

    app.include_router(auth_router, prefix=API_PREFIX)
    app.include_router(profile_router, prefix=API_PREFIX)
    app.include_router(nutrition_router, prefix=API_PREFIX)
    app.include_router(plans_router, prefix=API_PREFIX)
    app.include_router(logs_router, prefix=API_PREFIX)
    if get_settings().feature_ai_meal_parsing:  # V2, disabled by default
        from app.ai.meal_parsing import router as ai_router

        app.include_router(ai_router, prefix=API_PREFIX)
    return app


app = create_app()
