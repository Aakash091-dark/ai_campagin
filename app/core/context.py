# app/core/context.py
import contextvars

# Stores the Bearer token for the current request
request_token_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_token", default=None
)
