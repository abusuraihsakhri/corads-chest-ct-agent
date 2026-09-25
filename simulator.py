"""Stress-test the optional legacy agent subsystem with synthetic records."""
import os
import random
import secrets
import sys
import time

os.environ.setdefault("AUDIT_SECRET_KEY", secrets.token_hex(32))

from agents.base import AuditLogger, PHIGuard, SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor


def run_simulation(iterations: int = 100) -> None:
    if iterations <= 0:
        raise ValueError("iterations must be greater than zero")
    print(f"Starting synthetic simulation ({iterations} tasks)...")
    supervisor = SystemSupervisor(model_provider="mock")
    start_time = time.time()
    nominal_count = elevated_count = critical_count = phi_blocked_count = 0
    for index in range(iterations):
        payload = SystemTaskPayload(task_id=f"SIM-{index + 1:04d}", target_identifier=f"SPECIMEN-{random.randint(100, 999)}", primary_metric=round(random.uniform(5.0, 40.0), 2), secondary_metric=round(random.uniform(1.0, 20.0), 2), status_descriptor=random.choice(["NOMINAL", "DISCORDANT_ANOMALY", "MUTANT_VARIANT", "OPTIMAL"]), is_critical_flag=random.random() < 0.15)
        dossier = supervisor.process_task(payload)
        if dossier.overall_urgency.value == "CRITICAL_STAT_PANIC": critical_count += 1
        elif dossier.overall_urgency.value == "ELEVATED_RISK": elevated_count += 1
        else: nominal_count += 1
        if (index + 1) % 25 == 0:
            try:
                PHIGuard.assert_no_phi(f"Patient John Doe MRN-{random.randint(100000, 999999)} test")
            except SecurityException:
                phi_blocked_count += 1
    elapsed = time.time() - start_time
    print(f"Total tasks: {iterations}")
    print(f"Elapsed: {elapsed:.3f} s")
    print(f"Routine: {nominal_count}")
    print(f"Elevated: {elevated_count}")
    print(f"Critical: {critical_count}")
    print(f"Identifier-pattern blocks: {phi_blocked_count}")
    print(f"Audit blocks: {len(AuditLogger.get_trail())}")
    print(f"Audit integrity: {AuditLogger.verify_integrity()}")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_simulation(count)
