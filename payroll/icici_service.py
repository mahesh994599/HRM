"""
ICICI Connected Banking API Service

Handles fund transfer requests to ICICI Bank's API.
Supports NEFT, RTGS, IMPS modes.

API Documentation: ICICI Connected Banking / Composite API
"""

import hashlib
import json
import logging
import uuid
from datetime import datetime
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)


class ICICITransferError(Exception):
    """Raised when an ICICI API call fails."""
    pass


class ICICIBankService:
    """
    Service class for ICICI Bank Connected Banking API.

    Usage:
        config = ICICIBankConfig.objects.get(is_active=True)
        service = ICICIBankService(config)
        result = service.fund_transfer(
            amount=50000,
            beneficiary_account="1234567890",
            beneficiary_ifsc="HDFC0001234",
            beneficiary_name="John Doe",
            remarks="Salary May 2026",
        )
    """

    def __init__(self, config):
        self.config = config
        self.base_url = config.api_base_url.rstrip("/")
        self.headers = {
            "Content-Type": "application/json",
            "apikey": config.api_key,
            "client_id": config.client_id,
            "client_secret": config.client_secret,
        }

    def _generate_txn_ref(self):
        """Generate a unique transaction reference."""
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        uid = uuid.uuid4().hex[:8].upper()
        return f"SAL{ts}{uid}"

    def fund_transfer(
        self,
        amount,
        beneficiary_account,
        beneficiary_ifsc,
        beneficiary_name,
        transfer_mode=None,
        remarks="Salary Payment",
    ):
        """
        Initiate a fund transfer via ICICI API.

        Args:
            amount: Transfer amount (Decimal or float)
            beneficiary_account: Beneficiary bank account number
            beneficiary_ifsc: Beneficiary IFSC code
            beneficiary_name: Beneficiary name
            transfer_mode: NEFT/RTGS/IMPS (defaults to config default)
            remarks: Transaction remarks

        Returns:
            dict with keys: success, txn_ref, bank_ref, message
        """
        mode = transfer_mode or self.config.default_transfer_mode
        txn_ref = self._generate_txn_ref()

        payload = {
            "AGGRID": self.config.corp_id,
            "AGGRNAME": "HORILLA_HRM",
            "CORPID": self.config.corp_id,
            "USERID": self.config.corp_id,
            "URN": txn_ref,
            "DEBITACC": self.config.debit_account_no,
            "CREDITACC": beneficiary_account,
            "IFSC": beneficiary_ifsc or "",
            "TXNTYPE": mode,
            "AMOUNT": str(Decimal(str(amount)).quantize(Decimal("0.01"))),
            "PAYEENAME": beneficiary_name,
            "REMARKS": remarks,
            "UNIQUEID": txn_ref,
        }

        # In sandbox mode, simulate a successful transfer
        if self.config.is_sandbox:
            return self._sandbox_response(txn_ref, amount, beneficiary_name)

        try:
            url = f"{self.base_url}/composite-payment"
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("STATUS") == "SUCCESS" or data.get("response") == "SUCCESS":
                return {
                    "success": True,
                    "txn_ref": txn_ref,
                    "bank_ref": data.get("UTRNUMBER", data.get("bankReferenceNo", "")),
                    "message": data.get("MESSAGE", "Transfer successful"),
                }
            else:
                return {
                    "success": False,
                    "txn_ref": txn_ref,
                    "bank_ref": "",
                    "message": data.get("MESSAGE", data.get("message", "Transfer failed")),
                }

        except requests.exceptions.Timeout:
            logger.error(f"ICICI API timeout for txn {txn_ref}")
            return {
                "success": False,
                "txn_ref": txn_ref,
                "bank_ref": "",
                "message": "Request timed out. Please check transaction status.",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"ICICI API error for txn {txn_ref}: {e}")
            return {
                "success": False,
                "txn_ref": txn_ref,
                "bank_ref": "",
                "message": f"API error: {str(e)}",
            }

    def check_status(self, txn_ref):
        """
        Check the status of a previously initiated transaction.

        Returns:
            dict with keys: status, bank_ref, message
        """
        if self.config.is_sandbox:
            return {"status": "success", "bank_ref": f"SB{txn_ref}", "message": "Sandbox: completed"}

        try:
            url = f"{self.base_url}/transaction-inquiry"
            payload = {
                "AGGRID": self.config.corp_id,
                "CORPID": self.config.corp_id,
                "USERID": self.config.corp_id,
                "UNIQUEID": txn_ref,
            }
            response = requests.post(url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            status = data.get("STATUS", "").lower()
            if status in ("success", "completed"):
                return {"status": "success", "bank_ref": data.get("UTRNUMBER", ""), "message": "Completed"}
            elif status in ("pending", "in_progress", "sent_to_bank"):
                return {"status": "processing", "bank_ref": "", "message": "In progress"}
            else:
                return {"status": "failed", "bank_ref": "", "message": data.get("MESSAGE", "Failed")}

        except Exception as e:
            logger.error(f"ICICI status check error for {txn_ref}: {e}")
            return {"status": "pending", "bank_ref": "", "message": f"Status check error: {str(e)}"}

    def _sandbox_response(self, txn_ref, amount, beneficiary_name):
        """Simulate a successful transfer in sandbox mode."""
        logger.info(f"SANDBOX: Transfer {txn_ref} - {amount} to {beneficiary_name}")
        return {
            "success": True,
            "txn_ref": txn_ref,
            "bank_ref": f"SBREF{uuid.uuid4().hex[:10].upper()}",
            "message": f"[SANDBOX] Transfer of {amount} to {beneficiary_name} successful",
        }
