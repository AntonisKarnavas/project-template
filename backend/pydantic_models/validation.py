from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Union, Dict, Any
import re
from uuid import UUID


class CommonTypes:
    """Commonly used parameter types for validation"""

    # UUID validation
    UUID = UUID

    # Email validation
    Email = EmailStr

    # Integer with constraints
    PositiveInt = Field(gt=0)
    PageSize = Field(ge=1, le=100, default=20)
    PageNumber = Field(ge=1, default=1)


class WhitelistSchema(BaseModel):
    """
    Base schema for query parameter whitelisting.
    Endpoints should define their own schemas inheriting from this or BaseModel.
    """

    pass


class PaginationSchema(WhitelistSchema):
    page: int = CommonTypes.PageNumber
    size: int = CommonTypes.PageSize
    sort_by: Optional[str] = Field(None, pattern=r"^[a-zA-Z0-9_]+$")
    order: Optional[str] = Field("asc", pattern=r"^(asc|desc)$")


class SearchSchema(PaginationSchema):
    q: Optional[str] = Field(None, min_length=1, max_length=100)
    filters: Optional[Dict[str, Any]] = None


# Mapping of endpoint paths to their validation schemas
# This allows the middleware to lookup the correct schema for validation
ENDPOINT_SCHEMAS: Dict[str, Any] = {
    # Example mappings
    # "/users": SearchSchema,
    # "/items": PaginationSchema,
}
