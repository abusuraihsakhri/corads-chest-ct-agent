"""Tests for the optional legacy agent subsystem and compatibility CLI."""
import os

os.environ.setdefault("AUDIT_SECRET_KEY", "test-audit-secret-key-for-pytest-only")

import pytest

from agents.base import AuditLogger, AuditTrail, PHIGuard, SecurityException
from agents.models import SystemIntegrityStatus, SystemTaskPayload, UrgencyLevel
from agents.supervisor import SystemSupervisor
from agents.workers import InvariantQCWorker, ProtocolConformanceWorker, SafetyEscalationWorker
from corads_chest_ct_agent.cli import main


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient John Doe MRN-994827 blood culture positive for Staphylococcus")
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    assert InvariantQCWorker.evaluate(p1)[0].urgency == UrgencyLevel.ELEVATED
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    assert SafetyEscalationWorker.evaluate(p2)[0].urgency == UrgencyLevel.CRITICAL_STAT
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    assert len(ProtocolConformanceWorker.evaluate(p3)) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(task_id="TASK-PROD-01", target_identifier="KEY-PROD-01", primary_metric=12.0, secondary_metric=4.0, status_descriptor="NOMINAL")
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash
    assert AuditLogger.verify_integrity() is True


def test_audit_integrity_detects_signature_tampering():
    audit = AuditTrail(secret_key="unit-test-secret")
    entry = audit.log(actor="tester", actor_tier="test", event_type="CHECK", details={"status":"ok"})
    assert audit.verify_integrity() is True
    entry["actor"] = "tampered"
    assert audit.verify_integrity() is False


def test_cli_compatibility():
    assert main(["assess","--ggo","--peripheral","--bilateral","--multifocal"]) == 0
    assert main(["severity","--rum","3","--rmm","4","--rlm","5","--lum","3","--llm","4"]) == 0
    assert main(["info"]) == 0
