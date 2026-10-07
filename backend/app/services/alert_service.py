"""
KRISHIRAKSHA AI - Alert Generation, Targeting, & Duplicate Protection Service
Student Roll Number: 231FA04291

Handles:
- District-specific geo-fencing (never broadcasts district alerts across all India)
- Duplicate alert fingerprinting & spam protection (FIXED: timestamped FP on force_send)
- Urgent alert upgrades (LOW -> HIGH, HIGH -> VERY_HIGH)
- Multi-language recipient grouping
- Background SMS batch creation
- State-wise broadcast to all eligible farmers in a state
"""

import hashlib
import json
import logging
import traceback
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.models.models import (
    Alert, SmsMessage, Farmer, District, State, RiskAssessment
)
from backend.app.services.language_service import language_service
from backend.app.services.sms.msg91_service import msg91_service

logger = logging.getLogger("krishiraksha.alert_service")


def _is_valid_mobile(mobile: str) -> bool:
    """
    Validates Indian mobile number.
    Accepts: +91XXXXXXXXXX, 91XXXXXXXXXX, XXXXXXXXXX (10-digit starting 6-9).
    """
    if not mobile:
        return False
    cleaned = re.sub(r"[\s\-\(\)]", "", mobile)
    # Strip +91 or 91 prefix
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    elif cleaned.startswith("91") and len(cleaned) == 12:
        cleaned = cleaned[2:]
    return bool(re.match(r"^[6-9]\d{9}$", cleaned))


def _safe_mask(mobile: str) -> str:
    """Returns last 4 digits masked — never logs full number."""
    if mobile and len(mobile) >= 4:
        return f"+91******{mobile[-4:]}"
    return "+91******XXXX"


class AlertService:

    @staticmethod
    def generate_fingerprint(
        state_id: int,
        district_id: int,
        risk_level: str,
        warning_level: str,
        forecast_period: str
    ) -> str:
        """
        Creates a deterministic fingerprint to prevent duplicate alerts within the same hazard window.
        """
        raw = f"{state_id}:{district_id}:{risk_level.upper()}:{warning_level.upper()}:{forecast_period}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_timestamped_fingerprint(
        state_id: int,
        district_id: int,
        risk_level: str,
        warning_level: str,
        forecast_period: str
    ) -> str:
        """
        Creates a unique fingerprint including UTC timestamp — used when force-resending
        to avoid UNIQUE constraint violation on the alerts table.

        ROOT CAUSE FIX: Previously, force_send=True bypassed the duplicate check but
        then tried to INSERT with the same deterministic fingerprint, causing:
        sqlalchemy.exc.IntegrityError: UNIQUE constraint failed: alerts.alert_fingerprint
        -> FastAPI 500 -> frontend: "Failed to generate alert"
        """
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        raw = f"{state_id}:{district_id}:{risk_level.upper()}:{warning_level.upper()}:{forecast_period}:{ts}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def evaluate_and_dispatch_alert(
        cls,
        db: Session,
        district_id: int,
        risk_level: str,       # HIGH or VERY_HIGH
        official_warning: str, # ORANGE or RED
        forecast_period: str = "Next 24-48 Hours",
        force_send: bool = False
    ) -> Dict[str, Any]:
        """
        Processes an elevated risk condition for a specific district:
        1. Checks for duplicate active alerts (fixed fingerprint collision on force_send)
        2. Detects alert upgrades (HIGH -> VERY_HIGH)
        3. Identifies eligible registered farmers in that district ONLY
        4. Groups recipients by language
        5. Queues and dispatches SMS via MSG91
        """
        try:
            district = db.query(District).filter(District.id == district_id).first()
            if not district:
                return {"status": "ERROR", "message": f"District ID {district_id} not found"}

            state = db.query(State).filter(State.id == district.state_id).first()
            state_name = state.name if state else "State"
            district_name = district.name

            # --- FINGERPRINT LOGIC (FIXED) ---
            # Standard deterministic fingerprint for dedup check
            base_fingerprint = cls.generate_fingerprint(
                state_id=district.state_id,
                district_id=district.id,
                risk_level=risk_level,
                warning_level=official_warning,
                forecast_period=forecast_period
            )

            # Duplicate protection check
            existing_alert = db.query(Alert).filter(
                Alert.alert_fingerprint == base_fingerprint,
                Alert.status == "ACTIVE"
            ).first()

            if existing_alert and not force_send:
                logger.info(
                    f"[ALERT DEDUP] Identical active alert already exists for {district_name} "
                    f"(Alert ID: {existing_alert.id}). Suppressed."
                )
                return {
                    "status": "SUPPRESSED_DUPLICATE",
                    "message": (
                        f"Identical active alert already exists for {district_name} "
                        f"(Alert ID: {existing_alert.id}). Duplicate transmission suppressed."
                    ),
                    "alert_id": existing_alert.id
                }

            # FIXED: When force_send=True and a duplicate exists, use a timestamped unique fingerprint
            # to avoid UNIQUE constraint violation on alerts.alert_fingerprint.
            if existing_alert and force_send:
                fingerprint = cls.generate_timestamped_fingerprint(
                    state_id=district.state_id,
                    district_id=district.id,
                    risk_level=risk_level,
                    warning_level=official_warning,
                    forecast_period=forecast_period
                )
                logger.info(
                    f"[ALERT FORCE-RESEND] Existing alert {existing_alert.id} found for {district_name}. "
                    f"Using timestamped fingerprint for new alert."
                )
            else:
                fingerprint = base_fingerprint

            # Check for upgrade from previous lower severity alert
            previous_active = db.query(Alert).filter(
                Alert.district_id == district.id,
                Alert.status == "ACTIVE"
            ).order_by(Alert.created_at.desc()).first()

            is_upgrade = False
            if previous_active:
                if previous_active.risk_level == "HIGH" and risk_level == "VERY_HIGH":
                    is_upgrade = True
                    previous_active.status = "UPGRADED"
                    db.add(previous_active)
                    logger.info(f"[ALERT UPGRADE] HIGH -> VERY_HIGH for {district_name}")

            # Create new Alert record
            headline = f"URGENT: {risk_level.replace('_', ' ')} WEATHER RISK in {district_name}"
            desc_en = (
                f"KRISHIRAKSHA AI Early Warning: Severe rainfall and flood/waterlogging risk "
                f"detected for {district_name}, {state_name}. Expected period: {forecast_period}. "
                f"Official Warning: {official_warning}. Protect standing crops and clear drainage channels."
            )

            new_alert = Alert(
                alert_fingerprint=fingerprint,
                state_id=district.state_id,
                district_id=district.id,
                risk_level=risk_level,
                official_warning=official_warning,
                forecast_period=forecast_period,
                headline=headline,
                description_en=desc_en,
                status="ACTIVE",
                created_at=datetime.utcnow()
            )
            db.add(new_alert)
            db.commit()
            db.refresh(new_alert)

        except IntegrityError as ie:
            db.rollback()
            logger.error(
                f"[ALERT SERVICE] IntegrityError creating alert for district_id={district_id}: "
                f"{type(ie).__name__} — check alert_fingerprint uniqueness.\n"
                f"{traceback.format_exc()}"
            )
            return {
                "status": "ERROR",
                "message": (
                    "Alert could not be created due to a database conflict "
                    "(duplicate fingerprint). Try again or use force_send=True."
                )
            }
        except Exception as exc:
            db.rollback()
            logger.error(
                f"[ALERT SERVICE] Unexpected error creating alert for district_id={district_id}: "
                f"{type(exc).__name__}: {exc}\n{traceback.format_exc()}"
            )
            return {
                "status": "ERROR",
                "message": f"Alert creation failed: {type(exc).__name__}. See server logs for details."
            }

        # STRICT TARGETING: Select registered farmers in THIS district ONLY
        targeted_farmers = db.query(Farmer).filter(
            Farmer.district_id == district.id,
            Farmer.is_active == True
        ).all()

        if not targeted_farmers:
            logger.info(f"[ALERT SERVICE] No active registered farmers in {district_name}.")
            return {
                "status": "ALERT_CREATED_NO_RECIPIENTS",
                "alert_id": new_alert.id,
                "message": f"Alert registered for {district_name}, but no active farmers registered in this district.",
                "affected_farmers_count": 0
            }

        # Group by farmer preferred language
        grouped_by_lang: Dict[str, List[Dict[str, Any]]] = {}
        for f in targeted_farmers:
            lang = language_service.resolve_language(f.preferred_language, state_name)
            if lang not in grouped_by_lang:
                grouped_by_lang[lang] = []
            grouped_by_lang[lang].append({
                "id": f.id,
                "mobile_number": f.mobile_number,
                "name": f.full_name
            })

        # Dispatch via MSG91 Service
        dispatched_results = msg91_service.send_batch_sms(
            recipients_by_lang=grouped_by_lang,
            state_name=state_name,
            district_name=district_name,
            period=forecast_period
        )

        # Save SMS logs
        total_queued = 0
        for item in dispatched_results:
            farmer_id = item["farmer_id"]
            mobile_masked = item["mobile_masked"]
            lang = item["language"]
            res = item["result"]

            sms_rec = SmsMessage(
                farmer_id=farmer_id,
                alert_id=new_alert.id,
                language=lang,
                template_id=res.get("template_id"),
                provider=res.get("provider", "MSG91"),
                provider_message_id=res.get("provider_message_id"),
                mobile_masked=mobile_masked,
                submitted_at=datetime.utcnow(),
                delivered_at=datetime.utcnow() if res.get("status") == "DELIVERED" else None,
                status=res.get("status", "QUEUED"),
                failure_reason=res.get("failure_reason"),
                payload_json=json.dumps(res.get("provider_response", {}))
            )
            db.add(sms_rec)
            total_queued += 1

        db.commit()

        return {
            "status": "SUCCESS",
            "alert_id": new_alert.id,
            "district": district_name,
            "state": state_name,
            "risk_level": risk_level,
            "is_upgrade": is_upgrade,
            "recipients_count": total_queued,
            "languages_used": list(grouped_by_lang.keys()),
            "sms_mode": msg91_service.mode
        }

    @classmethod
    def dispatch_state_broadcast(
        cls,
        db: Session,
        state_id: int,
        risk_level: str = "HIGH",
        official_warning: str = "ORANGE",
        forecast_period: str = "Next 24-48 Hours",
    ) -> Dict[str, Any]:
        """
        STATE-WISE BROADCAST: Sends a rain/flood alert SMS to ALL eligible active farmers
        in the given state (across all districts).

        Safety guarantees:
        - Validates mobile numbers before sending
        - Deduplicates by mobile number (one SMS per unique number per broadcast)
        - Skips inactive / opted-out farmers
        - Continues sending to remaining farmers if one fails
        - Never logs full phone numbers (masked in logs)
        - Never exposes credentials
        - Returns per-farmer tracking + overall summary statistics
        """
        state = db.query(State).filter(State.id == state_id).first()
        if not state:
            return {"status": "ERROR", "message": f"State ID {state_id} not found"}

        state_name = state.name
        logger.info(f"[STATE BROADCAST] Starting broadcast for state: {state_name} (ID={state_id})")

        # Fetch all active farmers in this state
        all_farmers = db.query(Farmer).filter(
            Farmer.state_id == state_id,
            Farmer.is_active == True
        ).all()

        total_farmers = len(all_farmers)
        logger.info(f"[STATE BROADCAST] {state_name}: {total_farmers} total active farmers found")

        # Use state's first district as anchor for the alert record
        anchor_district = db.query(District).filter(District.state_id == state_id).first()
        if not anchor_district:
            return {
                "status": "ERROR",
                "message": f"No districts configured for {state_name}. Please seed district data."
            }

        # Generate unique timestamped fingerprint for this broadcast
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
        raw_fp = f"STATE_BROADCAST:{state_id}:{risk_level.upper()}:{official_warning.upper()}:{ts}"
        fingerprint = hashlib.sha256(raw_fp.encode("utf-8")).hexdigest()

        headline = f"STATE ALERT: {risk_level.replace('_', ' ')} WEATHER RISK — {state_name}"
        desc_en = (
            f"KRISHIRAKSHA AI State-Wide Early Warning: Severe rainfall and flood/waterlogging risk "
            f"detected across {state_name}. Expected period: {forecast_period}. "
            f"Official Warning: {official_warning}. Protect standing crops and clear drainage channels."
        )

        try:
            broadcast_alert = Alert(
                alert_fingerprint=fingerprint,
                state_id=state_id,
                district_id=anchor_district.id,
                risk_level=risk_level,
                official_warning=official_warning,
                forecast_period=forecast_period,
                headline=headline,
                description_en=desc_en,
                status="ACTIVE",
                created_at=datetime.utcnow()
            )
            db.add(broadcast_alert)
            db.commit()
            db.refresh(broadcast_alert)
        except IntegrityError as ie:
            db.rollback()
            logger.error(f"[STATE BROADCAST] IntegrityError creating broadcast alert: {ie}")
            return {"status": "ERROR", "message": "Database conflict creating broadcast alert. Please retry."}
        except Exception as exc:
            db.rollback()
            logger.error(
                f"[STATE BROADCAST] Error creating alert: {type(exc).__name__}: {exc}\n"
                f"{traceback.format_exc()}"
            )
            return {"status": "ERROR", "message": f"Failed to create broadcast alert: {type(exc).__name__}"}

        # --- Eligibility filtering & deduplication ---
        eligible_farmers = []
        skipped_no_mobile = 0
        skipped_duplicate = 0
        seen_mobiles: Set[str] = set()

        for f in all_farmers:
            # Skip if no valid mobile number
            if not f.mobile_number or not _is_valid_mobile(f.mobile_number):
                skipped_no_mobile += 1
                logger.warning(
                    f"[STATE BROADCAST] Farmer ID {f.id} skipped — invalid or missing mobile number"
                )
                continue

            # Normalize for dedup: strip non-digits
            normalized_mobile = re.sub(r"\D", "", f.mobile_number)
            if normalized_mobile in seen_mobiles:
                skipped_duplicate += 1
                logger.info(
                    f"[STATE BROADCAST] Farmer ID {f.id} skipped — duplicate mobile ****{f.mobile_number[-4:]}"
                )
                continue
            seen_mobiles.add(normalized_mobile)
            eligible_farmers.append(f)

        eligible_count = len(eligible_farmers)
        logger.info(
            f"[STATE BROADCAST] {state_name}: {eligible_count} eligible out of {total_farmers} "
            f"(skipped: {skipped_no_mobile} no/invalid mobile, {skipped_duplicate} duplicates)"
        )

        if eligible_count == 0:
            return {
                "status": "NO_ELIGIBLE_FARMERS",
                "alert_id": broadcast_alert.id,
                "state_name": state_name,
                "total_farmers": total_farmers,
                "eligible_farmers": 0,
                "sms_sent": 0,
                "sms_failed": 0,
                "message": f"No eligible farmers found in {state_name} with valid mobile numbers.",
                "skipped_no_mobile": skipped_no_mobile,
                "skipped_duplicate": skipped_duplicate,
                "farmer_results": [],
                "failed_details": [],
            }

        # --- SMS Dispatch: one at a time, never stop on individual failure ---
        sms_sent = 0
        sms_failed = 0
        farmer_results = []

        # Pre-load all districts for name lookup (avoids N+1 queries)
        district_map: Dict[int, str] = {
            d.id: d.name for d in db.query(District).filter(District.state_id == state_id).all()
        }

        for f in eligible_farmers:
            district_name = district_map.get(f.district_id, state_name)
            lang = language_service.resolve_language(f.preferred_language, state_name)

            try:
                result = msg91_service.send_single_sms(
                    mobile_number=f.mobile_number,
                    language=lang,
                    state_name=state_name,
                    district_name=district_name,
                    period=forecast_period
                )
                sms_status = result.get("status", "UNKNOWN")
                failure_reason = result.get("failure_reason")

                if sms_status in ("SUBMITTED", "DELIVERED"):
                    sms_sent += 1
                else:
                    sms_failed += 1

                # Record individual SMS log
                sms_rec = SmsMessage(
                    farmer_id=f.id,
                    alert_id=broadcast_alert.id,
                    language=lang,
                    template_id=result.get("template_id"),
                    provider=result.get("provider", "MSG91"),
                    provider_message_id=result.get("provider_message_id"),
                    mobile_masked=_safe_mask(f.mobile_number),
                    submitted_at=datetime.utcnow(),
                    delivered_at=datetime.utcnow() if sms_status == "DELIVERED" else None,
                    status=sms_status,
                    failure_reason=failure_reason,
                    payload_json=json.dumps(result.get("provider_response", {}))
                )
                db.add(sms_rec)

                farmer_results.append({
                    "farmer_id": f.id,
                    "farmer_name": f.full_name,
                    "mobile_masked": _safe_mask(f.mobile_number),
                    "district": district_name,
                    "language": lang,
                    "status": sms_status,
                    "failure_reason": failure_reason,
                })

            except Exception as exc:
                sms_failed += 1
                logger.error(
                    f"[STATE BROADCAST] Error dispatching SMS for farmer_id={f.id}: "
                    f"{type(exc).__name__}: {exc}"
                )
                farmer_results.append({
                    "farmer_id": f.id,
                    "farmer_name": f.full_name,
                    "mobile_masked": _safe_mask(f.mobile_number),
                    "district": district_name,
                    "language": lang,
                    "status": "FAILED",
                    "failure_reason": f"{type(exc).__name__}: {str(exc)[:120]}",
                })

        # Commit all SMS records
        try:
            db.commit()
        except Exception as exc:
            logger.error(f"[STATE BROADCAST] Error committing SMS records: {exc}")
            db.rollback()

        logger.info(
            f"[STATE BROADCAST] {state_name} COMPLETE: "
            f"sent={sms_sent}, failed={sms_failed}, eligible={eligible_count}"
        )

        failed_details = [r for r in farmer_results if r["status"] not in ("SUBMITTED", "DELIVERED")]

        return {
            "status": "BROADCAST_COMPLETE",
            "alert_id": broadcast_alert.id,
            "state_name": state_name,
            "total_farmers": total_farmers,
            "eligible_farmers": eligible_count,
            "sms_sent": sms_sent,
            "sms_failed": sms_failed,
            "skipped_no_mobile": skipped_no_mobile,
            "skipped_duplicate": skipped_duplicate,
            "sms_mode": msg91_service.mode,
            "languages_used": list({r["language"] for r in farmer_results}),
            "farmer_results": farmer_results,
            "failed_details": failed_details,
            "message": (
                f"State-wide broadcast to {state_name} complete. "
                f"SMS Sent: {sms_sent}, Failed: {sms_failed} "
                f"out of {eligible_count} eligible farmers."
            )
        }


alert_service = AlertService()
