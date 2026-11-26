"""Operational alert delivery dispatcher across webhook, email, and audit log channels."""

import json
import logging
import smtplib
from collections.abc import Callable
from datetime import UTC, datetime
from email.message import EmailMessage
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request
from uuid import uuid4

from app.config import Settings, get_settings
from app.schemas.alert import (
    AlertActionRecord,
    AlertDeliveryRecord,
    DeliveryChannel,
    DeliveryStatus,
)

logger = logging.getLogger(__name__)


class AlertDeliveryDispatcher:
    """Dispatches operational alerts to configured channels and returns delivery records."""

    def __init__(
        self,
        settings: Settings | None = None,
        http_sender: Callable[[str, dict[str, Any], float], int] | None = None,
        smtp_sender: Callable[[str, int, str, list[str], str, str], None] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._http_sender = http_sender or self._default_http_post
        self._smtp_sender = smtp_sender or self._default_smtp_send

    @staticmethod
    def _default_http_post(url: str, payload: dict[str, Any], timeout_s: float) -> int:
        body = json.dumps(payload).encode("utf-8")
        req = urllib_request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=timeout_s) as resp:
            return int(resp.status)

    @staticmethod
    def _default_smtp_send(
        host: str,
        port: int,
        sender: str,
        recipients: list[str],
        subject: str,
        body: str,
    ) -> None:
        msg = EmailMessage()
        msg["From"] = sender
        msg["To"] = ", ".join(recipients)
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(host, port, timeout=5.0) as smtp:
            smtp.send_message(msg)

    @staticmethod
    def _build_payload(alert: AlertActionRecord) -> dict[str, Any]:
        return {
            "alert_id": alert.alert_id,
            "location_id": alert.location_id,
            "hazard_type": alert.hazard_type.value,
            "priority_level": alert.priority_level,
            "priority_score": alert.priority_score,
            "title": alert.title,
            "recommendation": alert.recommendation,
            "explanation": alert.explanation,
            "status": alert.status.value,
            "created_at": alert.created_at.isoformat(),
        }

    def _deliver_webhook(
        self,
        alert: AlertActionRecord,
        webhook_url: str,
    ) -> AlertDeliveryRecord:
        now = datetime.now(UTC)
        payload = self._build_payload(alert)
        try:
            code = self._http_sender(
                webhook_url, payload, self._settings.alert_webhook_timeout_seconds
            )
            ok = 200 <= code < 300
            return AlertDeliveryRecord(
                delivery_id=f"deliv-{uuid4().hex[:12]}",
                alert_id=alert.alert_id,
                channel=DeliveryChannel.WEBHOOK,
                target=webhook_url,
                status=DeliveryStatus.SENT if ok else DeliveryStatus.FAILED,
                attempts=1,
                response_code=code,
                last_error=None if ok else f"HTTP {code}",
                dispatched_at=now if ok else None,
                created_at=now,
            )
        except urllib_error.HTTPError as exc:
            return AlertDeliveryRecord(
                delivery_id=f"deliv-{uuid4().hex[:12]}",
                alert_id=alert.alert_id,
                channel=DeliveryChannel.WEBHOOK,
                target=webhook_url,
                status=DeliveryStatus.FAILED,
                attempts=1,
                response_code=exc.code,
                last_error=str(exc),
                dispatched_at=None,
                created_at=now,
            )
        except Exception as exc:
            return AlertDeliveryRecord(
                delivery_id=f"deliv-{uuid4().hex[:12]}",
                alert_id=alert.alert_id,
                channel=DeliveryChannel.WEBHOOK,
                target=webhook_url,
                status=DeliveryStatus.FAILED,
                attempts=1,
                response_code=None,
                last_error=str(exc),
                dispatched_at=None,
                created_at=now,
            )

    def _deliver_email(
        self,
        alert: AlertActionRecord,
        recipients: list[str],
    ) -> AlertDeliveryRecord:
        now = datetime.now(UTC)
        target = ", ".join(recipients)
        host = self._settings.alert_smtp_host
        sender = self._settings.alert_smtp_from or "alerts@himarakshak.local"
        if not host or not recipients:
            return AlertDeliveryRecord(
                delivery_id=f"deliv-{uuid4().hex[:12]}",
                alert_id=alert.alert_id,
                channel=DeliveryChannel.EMAIL,
                target=target or "unconfigured",
                status=DeliveryStatus.SKIPPED,
                attempts=1,
                last_error="SMTP host or recipients not configured.",
                dispatched_at=None,
                created_at=now,
            )

        body = (
            f"{alert.title}\n"
            f"Priority: {alert.priority_level} ({alert.priority_score:.2f})\n"
            f"Location: {alert.location_id} | Hazard: {alert.hazard_type.value}\n\n"
            f"Recommendation:\n{alert.recommendation}\n"
        )
        try:
            self._smtp_sender(
                host,
                self._settings.alert_smtp_port,
                sender,
                recipients,
                f"[HIMA-RAKSHAK] {alert.title}",
                body,
            )
            return AlertDeliveryRecord(
                delivery_id=f"deliv-{uuid4().hex[:12]}",
                alert_id=alert.alert_id,
                channel=DeliveryChannel.EMAIL,
                target=target,
                status=DeliveryStatus.SENT,
                attempts=1,
                dispatched_at=now,
                created_at=now,
            )
        except Exception as exc:
            return AlertDeliveryRecord(
                delivery_id=f"deliv-{uuid4().hex[:12]}",
                alert_id=alert.alert_id,
                channel=DeliveryChannel.EMAIL,
                target=target,
                status=DeliveryStatus.FAILED,
                attempts=1,
                last_error=str(exc),
                dispatched_at=None,
                created_at=now,
            )

    @staticmethod
    def _deliver_console(alert: AlertActionRecord) -> AlertDeliveryRecord:
        now = datetime.now(UTC)
        logger.warning(
            "OPERATIONAL_ALERT_DISPATCH alert_id=%s location=%s hazard=%s priority=%s title=%s",
            alert.alert_id,
            alert.location_id,
            alert.hazard_type.value,
            alert.priority_level,
            alert.title,
        )
        return AlertDeliveryRecord(
            delivery_id=f"deliv-{uuid4().hex[:12]}",
            alert_id=alert.alert_id,
            channel=DeliveryChannel.CONSOLE,
            target="operational-audit-log",
            status=DeliveryStatus.SENT,
            attempts=1,
            dispatched_at=now,
            created_at=now,
        )

    def dispatch(
        self,
        alert: AlertActionRecord,
        *,
        channels: list[DeliveryChannel] | None = None,
        webhook_url: str | None = None,
        email_recipients: list[str] | None = None,
    ) -> tuple[list[AlertDeliveryRecord], DeliveryStatus]:
        """Deliver an alert across configured or requested channels."""
        effective_webhook = webhook_url or self._settings.alert_webhook_url
        effective_recipients = email_recipients or [
            r.strip() for r in self._settings.alert_email_recipients.split(",") if r.strip()
        ]

        requested_channels = list(channels) if channels else []
        if not requested_channels:
            if effective_webhook:
                requested_channels.append(DeliveryChannel.WEBHOOK)
            if self._settings.alert_smtp_host and effective_recipients:
                requested_channels.append(DeliveryChannel.EMAIL)
            if not requested_channels:
                requested_channels.append(DeliveryChannel.CONSOLE)

        records: list[AlertDeliveryRecord] = []
        for ch in requested_channels:
            if ch == DeliveryChannel.WEBHOOK:
                if effective_webhook:
                    records.append(self._deliver_webhook(alert, effective_webhook))
                else:
                    now = datetime.now(UTC)
                    records.append(
                        AlertDeliveryRecord(
                            delivery_id=f"deliv-{uuid4().hex[:12]}",
                            alert_id=alert.alert_id,
                            channel=DeliveryChannel.WEBHOOK,
                            target="unconfigured",
                            status=DeliveryStatus.SKIPPED,
                            attempts=1,
                            last_error="Webhook URL not configured.",
                            created_at=now,
                        )
                    )
            elif ch == DeliveryChannel.EMAIL:
                records.append(self._deliver_email(alert, effective_recipients))
            elif ch == DeliveryChannel.CONSOLE:
                records.append(self._deliver_console(alert))

        if any(r.status == DeliveryStatus.SENT for r in records):
            overall = DeliveryStatus.SENT
        elif any(r.status == DeliveryStatus.FAILED for r in records):
            overall = DeliveryStatus.FAILED
        elif records and all(r.status == DeliveryStatus.SKIPPED for r in records):
            overall = DeliveryStatus.SKIPPED
        else:
            overall = DeliveryStatus.PENDING

        return records, overall
