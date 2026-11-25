# SOP-009: Local Dashboard Prototype

**Status:** Conceptual prototype; not suitable for production health monitoring.  
**Last reviewed:** 25 November 2026

## Purpose

Record the idea of displaying a local data summary on a dashboard. The earlier example used an unauthenticated HTTP endpoint and must not be deployed with real health data.

## Security boundary

- Do not display identifiable health information on a shared or public television or screen.
- Do not expose a Nightscout or database API directly to a browser on an untrusted network.
- Do not embed API secrets, tokens or credentials in client-side JavaScript.
- Do not use plain HTTP across an untrusted network.
- Do not treat a dashboard as an emergency alert or clinical monitoring system.

## Safe development approach

1. Use synthetic data only.
2. Build the dashboard against a local fixture file or a local test service.
3. If a future authenticated data service is required, place a server-side component between the browser and the source API.
4. Require authentication, TLS, access controls, logging and a defined retention policy before any real data is displayed.
5. Test stale-data, unavailable-network and malformed-response states. The UI must visibly indicate that data is stale or unavailable.

The earlier unauthenticated fetch example and public-screen deployment steps are withdrawn. No production dashboard integration is claimed.
