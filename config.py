import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


load_dotenv(override=False)


class Settings(BaseModel):
    notion_api_key: str = Field(min_length=1)
    notion_database_id: str = Field(min_length=1)
    openai_api_key: str = Field(min_length=1)
    google_service_account_file: Optional[str] = None
    report_email_to: Optional[str] = None
    report_email_from: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True


try:
    settings = Settings(
        notion_api_key=os.getenv("NOTION_API_KEY", ""),
        notion_database_id=os.getenv("NOTION_DATABASE_ID", ""),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        google_service_account_file=os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE"),
        report_email_to=os.getenv("REPORT_EMAIL_TO"),
        report_email_from=os.getenv("REPORT_EMAIL_FROM"),
        smtp_host=os.getenv("SMTP_HOST"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME"),
        smtp_password=os.getenv("SMTP_PASSWORD"),
        smtp_use_tls=os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes"),
    )
except ValidationError as exc:
    raise RuntimeError(
        "Invalid configuration. Ensure NOTION_API_KEY, NOTION_DATABASE_ID, and OPENAI_API_KEY are set."
    ) from exc
