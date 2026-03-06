from fastapi.routing import APIRoute

from app.main import app
from app.security.api_key import require_api_key


def test_business_endpoints_have_api_key_dependency() -> None:
    protected_paths = {
        "/price/{symbol}",
        "/history/{symbol}",
        "/risk/{symbol}",
        "/risk-profile/{symbol}",
    }

    routes = [route for route in app.routes if isinstance(route, APIRoute)]

    for route in routes:
        if route.path not in protected_paths:
            continue

        dependency_calls = {dep.call for dep in route.dependant.dependencies}
        assert require_api_key in dependency_calls


def test_health_endpoint_is_not_protected() -> None:
    route = next(
        route
        for route in app.routes
        if isinstance(route, APIRoute) and route.path == "/health"
    )
    dependency_calls = {dep.call for dep in route.dependant.dependencies}

    assert require_api_key not in dependency_calls
