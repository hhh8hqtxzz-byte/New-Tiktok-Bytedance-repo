# ByteDance OTP Bot

## Authorized sandbox/custom provider mode

The bot includes a guarded sandbox provider for owned test infrastructure:

1. Run `/setapp sandbox_custom`.
2. Send `domain aid [app_name]`, for example `localhost:8000 1001 sandbox_app`.
3. Choose a type code or enter a custom type code.
4. When asked `Custom AID? Y or N`, choose `Y` to override the sandbox AID or `N` to keep the configured AID.

Custom provider domains are limited to localhost, private IPs, and reserved test/example domains (`.test`, `.example`, `.invalid`). Arbitrary public domains are rejected.
