"""Application-internal routing; route_request is the only public entry point."""

import unittest
from dataclasses import dataclass

__all__ = ["route_request"]


@dataclass(frozen=True)
class _Request:
    tenant: str


def _normalize(payload):
    if not isinstance(payload, dict):
        raise ValueError("request must be a mapping")
    tenant = payload.get("tenant")
    if not isinstance(tenant, str) or not tenant.strip():
        raise ValueError("tenant must be nonempty text")
    return _Request(tenant=tenant.strip())


def _route(request):
    if request is None:
        return "/default"
    if isinstance(request, dict):
        request = _Request(tenant=request.get("tenant", "default"))
    return f"/{request.tenant}"


def route_request(payload):
    return _route(_normalize(payload))


class RouteTests(unittest.TestCase):
    def test_routes_normalized_tenant(self):
        self.assertEqual(route_request({"tenant": " blue "}), "/blue")

    def test_rejects_invalid_requests_at_boundary(self):
        for payload in (None, "blue", {}, {"tenant": None}, {"tenant": " "}):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                route_request(payload)


if __name__ == "__main__":
    unittest.main()
