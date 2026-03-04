"""Error response contracts for consistent API failures."""

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Single validation or domain error detail item."""

    field: str | None = Field(default=None, description="Field path related to the error.")
    message: str = Field(description="Human-readable error message.")


class ErrorResponse(BaseModel):
    """Standardized API error envelope."""

    error: str = Field(description="Machine-readable error code.")
    message: str = Field(description="Top-level error message.")
    details: list[ErrorDetail] | None = Field(
        default=None,
        description="Optional structured error details.",
    )
