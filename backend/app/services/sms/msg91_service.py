"""
KRISHIRAKSHA AI - MSG91 Indian SMS Gateway Service
Student Roll Number: 231FA04291

Strictly complies with Indian Telecom DLT (Distributed Ledger Technology) requirements.
Supports live MSG91 API submission and demo simulation for evaluation.
Never fakes success or delivery!
"""

import logging
import uuid
import datetime
import requests
from typing import Dict, Any, Optional, List
from backend.app.config import settings
from backend.app.services.language_service import language_service

logger = logging.getLogger("krishiraksha.sms")

class MSG91Service:
    def __init__(self):
        self.api_url = "https://control.msg91.com/api/v5/flow"
        self.status_url = "https://control.msg91.com/api/v5/report"
        self.auth_key = settings.MSG91_AUTH_KEY
        self.sender_id = settings.MSG91_SENDER_ID
        self.route = settings.MSG91_ROUTE
        self.mode = (settings.SMS_MODE or "demo").lower()

    def get_config_status(self) -> Dict[str, Any]:
        """
        Audits real MSG91 & DLT compliance status.
        Never falsely reports 'ready' if credentials or sender ID are missing.
        """
        has_auth = bool(self.auth_key and len(self.auth_key.strip()) > 8)
        has_sender = bool(self.sender_id and len(self.sender_id.strip()) >= 3)
        templates_status = language_service.get_all_templates_status()
        configured_templates = {k: v["is_configured"] for k, v in templates_status.items()}
        any_templates = any(configured_templates.values())

        if self.mode == "demo":
            gateway_status = "DEMO_MODE"
        elif has_auth and has_sender and any_templates:
            gateway_status = "READY"
        else:
            gateway_status = "NOT_CONFIGURED"

        return {
            "sms_mode": self.mode,
            "dlt_registered": has_sender and any_templates,
            "sender_id_configured": has_sender,
            "sender_id": self.sender_id if has_sender else None,
            "msg91_auth_configured": has_auth,
            "templates_configured": configured_templates,
            "gateway_status": gateway_status
        }

    def send_single_sms(
        self,
        mobile_number: str,
        language: str,
        state_name: str,
        district_name: str,
        period: str = "Next 24-48 Hours"
    ) -> Dict[str, Any]:
        """
        Dispatches single SMS according to active SMS_MODE.
        Enforces Requirement #47: Never fakes success if not configured.
        """
        template_id = language_service.get_template_id(language)
        rendered_text = language_service.render_sms_content(language, district_name, state_name, period)

        # 1. LIVE MODE
        if self.mode == "live":
            # Strict validation
            if not self.auth_key or not self.sender_id:
                logger.error("Live SMS requested but MSG91_AUTH_KEY or MSG91_SENDER_ID is missing")
                return {
                    "success": False,
                    "status": "FAILED",
                    "mode": "live",
                    "message": "Real SMS is not configured. Complete MSG91/DLT configuration.",
                    "provider": "MSG91",
                    "provider_message_id": None,
                    "failure_reason": "MSG91_AUTH_KEY or MSG91_SENDER_ID missing in environment"
                }

            if not template_id:
                logger.error(f"No DLT template ID configured for language: {language}")
                return {
                    "success": False,
                    "status": "FAILED",
                    "mode": "live",
                    "message": f"Real SMS is not configured for {language}. Complete MSG91/DLT configuration for MSG91_TEMPLATE_ID_{language.upper()[:2]}.",
                    "provider": "MSG91",
                    "provider_message_id": None,
                    "failure_reason": f"Missing DLT template for {language}"
                }

            # Submit to MSG91 flow API
            clean_mobile = mobile_number.replace("+", "").replace(" ", "").strip()
            headers = {
                "authkey": self.auth_key,
                "content-type": "application/json",
                "accept": "application/json"
            }
            payload = {
                "template_id": template_id,
                "short_url": "0",
                "recipients": [
                    {
                        "mobiles": clean_mobile,
                        "district": district_name,
                        "state": state_name,
                        "period": period
                    }
                ]
            }

            try:
                logger.info(f"Submitting LIVE SMS to MSG91 for {clean_mobile[-4:]} with template {template_id}")
                resp = requests.post(self.api_url, json=payload, headers=headers, timeout=12)
                resp_json = resp.json() if resp.status_code == 200 else {"raw": resp.text}

                if resp.status_code == 200 and resp_json.get("type") == "success":
                    req_id = resp_json.get("message", f"msg91_{uuid.uuid4().hex[:12]}")
                    return {
                        "success": True,
                        "status": "SUBMITTED", # Never mark DELIVERED until confirmed by webhook/status check
                        "mode": "live",
                        "message": f"SMS request submitted to MSG91 gateway (Request ID: {req_id}). Awaiting carrier delivery receipt.",
                        "provider": "MSG91",
                        "provider_message_id": str(req_id),
                        "provider_response": resp_json,
                        "template_id": template_id,
                        "rendered_text": rendered_text
                    }
                else:
                    return {
                        "success": False,
                        "status": "FAILED",
                        "mode": "live",
                        "message": f"MSG91 Gateway rejected dispatch: {resp_json.get('message', 'Unknown error')}",
                        "provider": "MSG91",
                        "provider_message_id": None,
                        "provider_response": resp_json,
                        "failure_reason": str(resp_json)
                    }
            except Exception as ex:
                logger.error(f"HTTP error communicating with MSG91: {ex}")
                return {
                    "success": False,
                    "status": "FAILED",
                    "mode": "live",
                    "message": f"Failed to connect to MSG91 gateway: {str(ex)}",
                    "provider": "MSG91",
                    "provider_message_id": None,
                    "failure_reason": str(ex)
                }

        # 2. DEMO MODE (Safe Simulation for College Evaluation)
        else:
            simulated_id = f"demo_msg91_{uuid.uuid4().hex[:10]}"
            logger.info(f"[DEMO MODE] Simulating SMS dispatch to {mobile_number[-4:]} in {language}")
            return {
                "success": True,
                "status": "SUBMITTED",
                "mode": "demo",
                "message": "[DEMO MODE] Simulated SMS generated successfully. In DEMO MODE, no real SMS is sent to avoid telecommunication carrier charges.",
                "provider": "MSG91_SIMULATOR",
                "provider_message_id": simulated_id,
                "template_id": template_id or f"DEMO_DLT_TMPL_{language.upper()[:2]}",
                "rendered_text": rendered_text,
                "provider_response": {
                    "type": "success",
                    "message": simulated_id,
                    "simulation": True,
                    "dlt_compliant_text": rendered_text
                }
            }

    def send_batch_sms(
        self,
        recipients_by_lang: Dict[str, List[Dict[str, Any]]],
        state_name: str,
        district_name: str,
        period: str = "Next 24-48 Hours"
    ) -> List[Dict[str, Any]]:
        """
        Dispatches bulk notifications grouped by language to avoid mixing templates.
        """
        dispatched_logs = []
        for lang, recipients in recipients_by_lang.items():
            for farmer_rec in recipients:
                res = self.send_single_sms(
                    mobile_number=farmer_rec["mobile_number"],
                    language=lang,
                    state_name=state_name,
                    district_name=district_name,
                    period=period
                )
                dispatched_logs.append({
                    "farmer_id": farmer_rec["id"],
                    "mobile_masked": f"+91******{farmer_rec['mobile_number'][-4:]}",
                    "language": lang,
                    "result": res
                })
        return dispatched_logs

msg91_service = MSG91Service()
