"""
agents/sentinel_agent.py
Finance Sentinel Agent — ADK 2.7.1
Scans production finance_transactions for unmatched/anomalous entries.
Sends WhatsApp approval requests to Hosam. NEVER auto-writes to finance DB.
READ-ONLY on Cabinet tables. WRITE-ONLY to sentinel_log (new table, safe).

Usage (from main.py):
    run_sentinel_agent(days_back=7)
"""

import os
import sys
import logging
import asyncio
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from agents.tools.whatsapp import send_approval_request, send_notification

logger = logging.getLogger(__name__)


# ── Tool functions ─────────────────────────────────────────────────────────────

def tool_scan_unmatched_transactions(days_back: int = 7) -> dict:
    """
    Scan finance_transactions for unmatched or anomalous entries.
    READ-ONLY — never modifies Cabinet finance data.

    Args:
        days_back: Number of days to look back (default 7).

    Returns:
        dict with 'transactions' list and 'total_unmatched' count.
    """
    from db.connection import get_connection

    # Unmatched income: rows where registration_id is NULL and there is income amount
    sql = """
        SELECT
            ft.id,
            COALESCE(NULLIF(ft.income_receivable,0), NULLIF(ft.income_cash,0), NULLIF(ft.income_bank,0), 0) AS amount,
            ft.transaction_date::text AS date,
            ft.description,
            ft.category,
            ft.flow_direction,
            ft.notes
        FROM finance_transactions ft
        WHERE
            ft.transaction_date >= NOW() - INTERVAL '1 day' * %(days_back)s
            AND ft.registration_id IS NULL
            AND ft.flow_direction = 'IN'
            AND COALESCE(NULLIF(ft.income_receivable,0), NULLIF(ft.income_cash,0), NULLIF(ft.income_bank,0), 0) > 0
        ORDER BY ft.transaction_date DESC
        LIMIT 20
    """

    transactions = []
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {"days_back": int(days_back)})
                rows = cur.fetchall()
                for row in rows:
                    transactions.append({
                        "id":          row[0],
                        "amount":      float(row[1]) if row[1] else 0,
                        "date":        row[2],
                        "description": row[3] or "",
                        "source":      row[4] or "",
                        "type":        row[5] or "",
                        "notes":       row[6] or "",
                    })
    except Exception as e:
        logger.error(f"scan_unmatched_transactions error: {e}")
        return {"transactions": [], "total_unmatched": 0, "error": str(e)}

    return {
        "transactions":     transactions,
        "total_unmatched":  len(transactions),
        "days_scanned":     days_back,
    }


def tool_find_best_student_match(transaction_id: int, amount: float, description: str) -> dict:
    """
    Find the best matching student record for an unmatched transaction.
    READ-ONLY search across students and registrations.

    Args:
        transaction_id: ID of the transaction to match.
        amount:         Transaction amount in EGP.
        description:    Transaction description text.

    Returns:
        dict with 'match_found' (bool), 'student_id', 'student_name',
        'service_id', 'amount_paid', 'confidence_pct'.
    """
    from db.connection import get_connection

    # Find student registrations where amount_paid is close to the transaction amount
    sql = """
        SELECT
            s.id          AS student_id,
            s.full_name   AS student_name,
            r.service_id  AS service_id,
            r.amount_paid AS amount_paid,
            r.status      AS status,
            ABS(r.amount_paid - %(amount)s) AS delta
        FROM students s
        JOIN registrations r ON r.student_id = s.id
        WHERE
            ABS(r.amount_paid - %(amount)s) < 500
            AND (r.status IN ('CONFIRMED', 'confirmed', 'PENDING', 'pending', 'active', 'CREATED') OR r.status IS NULL)
        ORDER BY delta ASC
        LIMIT 1
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {"amount": amount})
                row = cur.fetchone()

                if row:
                    delta           = float(row[5])
                    confidence_pct  = max(0, int(100 - (delta / max(amount, 1)) * 100))
                    return {
                        "match_found":     True,
                        "student_id":      row[0],
                        "student_name":    row[1],
                        "course_name":     f"Service #{row[2]}",
                        "expected_amount": float(row[3]),
                        "confidence_pct":  confidence_pct,
                        "transaction_id":  transaction_id,
                        "db_description":  f"{row[1]} — Service #{row[2]}",
                    }
    except Exception as e:
        logger.error(f"find_best_student_match error: {e}")
        return {"match_found": False, "error": str(e)}

    return {"match_found": False, "transaction_id": transaction_id}



def tool_request_hosam_approval(match_data_json: str) -> dict:
    """
    Send a WhatsApp approval request to Hosam for a proposed transaction match.
    Hosam must reply APPROVE-{id} or REJECT-{id}.
    This tool NEVER modifies any database record.

    Args:
        match_data_json: JSON string of match data dict containing:
            amount, date, description, transaction_id, db_description,
            confidence_pct, source.

    Returns:
        dict with 'approval_id' (str) and 'sent' (bool).
    """
    try:
        match_data = json.loads(match_data_json)
    except json.JSONDecodeError:
        return {"sent": False, "error": "Invalid JSON in match_data_json"}

    try:
        approval_id = send_approval_request(match_data)
        return {"approval_id": approval_id, "sent": True}
    except Exception as e:
        logger.error(f"WhatsApp send failed: {e}")
        return {"sent": False, "error": str(e)}


def tool_send_sentinel_summary(total_scanned: int, sent_for_approval: int, skipped: int) -> dict:
    """
    Send a summary notification to Hosam when the sentinel run completes.

    Args:
        total_scanned:      Total unmatched transactions found.
        sent_for_approval:  How many were sent for Hosam's review.
        skipped:            How many had no match and were skipped.

    Returns:
        dict with 'sent' (bool).
    """
    message = (
        f"✅ *Finance Sentinel Run Complete*\n\n"
        f"📊 Summary:\n"
        f"• Unmatched transactions scanned: {total_scanned}\n"
        f"• Sent for your approval: {sent_for_approval}\n"
        f"• No match found (skipped): {skipped}\n\n"
        f"_Reply APPROVE-{{id}} or REJECT-{{id}} to each pending request._\n"
        f"_Sent by The Cabinet Finance Sentinel_"
    )
    try:
        send_notification(message)
        return {"sent": True}
    except Exception as e:
        return {"sent": False, "error": str(e)}


# ── ADK Agent definition ───────────────────────────────────────────────────────

SENTINEL_AGENT = Agent(
    name="finance_sentinel_agent",
    model=os.getenv("GEMINI_MODEL", "gemini-3.6-flash"),
    description=(
        "Monitors The Crafters Hub finance transactions for unmatched payments. "
        "Sends WhatsApp approval requests to Hosam. Never auto-modifies finance data."
    ),
    instruction="""You are the Finance Sentinel Agent for The Crafters Hub — a woodworking school in Cairo, Egypt.

Your mission: find unmatched income transactions and ask Hosam to approve matches via WhatsApp.

CRITICAL RULES — read before doing anything:
- You are READ-ONLY on all Cabinet finance tables.
- You NEVER modify, update, or delete any database record.
- You NEVER approve a match yourself — only Hosam approves via WhatsApp reply.
- tool_request_hosam_approval must be called for EVERY high-confidence match (>= 60%).

Workflow:
1. Call tool_scan_unmatched_transactions with days_back.
2. For each transaction in the results:
   a. Call tool_find_best_student_match with its id, amount, and description.
   b. If match_found=True and confidence_pct >= 60:
      - Build match_data as JSON string with all required fields.
      - Call tool_request_hosam_approval with that JSON.
      - Count this as "sent_for_approval".
   c. If match_found=False or confidence_pct < 60:
      - Count as "skipped". Do not send an approval request.
3. After processing ALL transactions, call tool_send_sentinel_summary.
4. Report a concise summary to the user.

Do NOT call tool_request_hosam_approval more than once per transaction.
Do NOT invent match data — use only what the tools return.""",
    tools=[
        FunctionTool(tool_scan_unmatched_transactions),
        FunctionTool(tool_find_best_student_match),
        FunctionTool(tool_request_hosam_approval),
        FunctionTool(tool_send_sentinel_summary),
    ],
)


# ── Public runner function ─────────────────────────────────────────────────────

def run_sentinel_agent(days_back: int = 7) -> str:
    """
    Run the Finance Sentinel Agent.

    Args:
        days_back: How many days of transactions to scan.

    Returns:
        Agent's final summary as a string.
    """
    from dotenv import load_dotenv
    load_dotenv()

    session_service = InMemorySessionService()
    runner = Runner(
        agent=SENTINEL_AGENT,
        app_name="tch_sentinel",
        session_service=session_service,
    )

    async def _run():
        session = await session_service.create_session(
            app_name="tch_sentinel",
            user_id="hosam",
        )
        message = genai_types.Content(
            role="user",
            parts=[genai_types.Part(
                text=f"Run the finance sentinel scan for the last {days_back} days."
            )]
        )
        final_response = ""
        async for event in runner.run_async(
            user_id="hosam",
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_response += part.text
        return final_response

    return asyncio.run(_run())
