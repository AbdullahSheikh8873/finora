from pydantic import BaseModel, EmailStr, field_validator


class ProfileUpdateRequest(BaseModel):
    full_name: str
    email: EmailStr

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters long.")
        return v


class PreferencesUpdateRequest(BaseModel):
    currency: str
    date_format: str
    theme: str

    @field_validator("currency")
    @classmethod
    def valid_currency(cls, v: str) -> str:
        allowed = {"PKR", "USD", "EUR", "GBP"}
        if v not in allowed:
            raise ValueError(f"Currency must be one of {sorted(allowed)}.")
        return v

    @field_validator("theme")
    @classmethod
    def valid_theme(cls, v: str) -> str:
        if v not in {"light", "dark"}:
            raise ValueError("Theme must be 'light' or 'dark'.")
        return v
