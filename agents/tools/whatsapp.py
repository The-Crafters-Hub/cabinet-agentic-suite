"""
agents/tools/whatsapp.py
Send WhatsApp messages via Meta Cloud API.
Used by the Finance Sentinel for human-in-the-loop approval requests.

Public functions:
    send_whatsapp_message(to_phone, message) -> dict
    send_approval_request(match_data) -> str   (returns approval_id)
"""

import os
import uuid
import logging
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Meta API Config ───────────────────────────────────────────────────────────
_TOKEN    = os.getenv("META_PERMANENT_TOKEN") or os.getenv("META_ACCESS_TOKEN", "")
_PHONE_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
_API_VER  = "v20.0"
_BASE_URL = f"https://graph.facebook.com/{_API_VER}"

# Hosam's WhatsApp number — receives all Sentinel alerts
HOSAM_PHONE = os.getenv("HOSAM_ALERT_PHONE") or os.getenv("WHATSAPP_ALERT_RECIPIENT", "")


def send_whatsapp_message(to_phone: str, message: str) -> dict:
    """
    Send a plain text WhatsApp message via Meta Cloud API.

    Args:
        to_phone: Recipient phone number in international format (e.g. +201113776666)
        message:  Text message body (max 4096 chars)

    Returns:
        API response dict. Raises requests.HTTPError on failure.
    """
    if not _TOKEN:
        raise EnvironmentError("META_PERMANENT_TOKEN or META_ACCESS_TOKEN not set in .env")
    if not _PHONE_ID:
        raise EnvironmentError("WHATSAPP_PHONE_NUMBER_ID not set in .env")

    # Normalize phone number — remove spaces, ensure no leading +
    to_phone = to_phone.replace(" ", "").replace("-", "")
    if to_phone.startswith("+"):
        to_phone = to_phone[1:]

    url = f"{_BASE_URL}/{_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_phone,
        "type": "text",
        "text": {"preview_url": False, "body": message[:4096]},
    }

    response = requests.post(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()

    data = response.json()
    logger.info(f"WhatsApp sent to {to_phone}: message_id={data.get('messages', [{}])[0].get('id', 'unknown')}")
    return data


def send_approval_request(match_data: dict) -> str:
    """
    Format and send a Finance Sentinel approval request to Hosam via WhatsApp.

    Args:
        match_data: Dict with keys:
            - amount (float)
            - date (str)
            - description (str)
            - transaction_id (int)
            - db_description (str)
            - confidence_pct (int, 0-100)
            - source (str)

    Returns:
        approval_id (UUID string) for tracking the pending approval.

    Raises:
        ValueError: If HOSAM_ALERT_PHONE is not set.
    """
    if not HOSAM_PHONE:
        raise ValueError("HOSAM_ALERT_PHONE not set in .env — cannot send approval request")

    approval_id = str(uuid.uuid4())[:8].upper()  # Short 8-char ID for easy WhatsApp reply

    amount      = match_data.get("amount", 0)
    date        = match_data.get("date", "unknown date")
    description = match_data.get("description", "no description")
    tx_id       = match_data.get("transaction_id", "?")
    db_desc     = match_data.get("db_description", "no match found")
    confidence  = match_data.get("confidence_pct", 0)
    source      = match_data.get("source", "unknown")

    message = (
        f"🔍 *Finance Sentinel Alert*\n\n"
        f"📋 Unmatched Transaction Found:\n"
        f"• Amount: *{amount:,.2f} EGP*\n"
        f"• Date: {date}\n"
        f"• Description: {description}\n"
        f"• Source: {source}\n\n"
        f"🔗 Best Match in DB:\n"
        f"• ID #{tx_id}: {db_desc}\n"
        f"• Confidence: {confidence}%\n\n"
        f"Reply with:\n"
        f"✅ *APPROVE-{approval_id}* to confirm match\n"
        f"❌ *REJECT-{approval_id}* to skip\n\n"
        f"_Sent by The Cabinet Finance Sentinel_"
    )

    send_whatsapp_message(HOSAM_PHONE, message)
    logger.info(f"Approval request sent. ID: {approval_id}, TX: {tx_id}, Confidence: {confidence}%")
    return approval_id


def send_notification(message: str) -> dict:
    """
    Send a simple notification to Hosam (no approval required).
    Used for Sentinel run summaries.
    """
    if not HOSAM_PHONE:
        logger.warning("HOSAM_ALERT_PHONE not set — notification skipped")
        return {}
    return send_whatsapp_message(HOSAM_PHONE, message)
