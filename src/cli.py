"""
Command-Line Interface (CLI) for Mental Health Continuity Handover System.
Allows generating Counsellor/Social Worker handovers, inspecting client records,
running simulations, and executing quantitative benchmarks directly from the terminal.
"""

import sys
import os
import argparse
import json

from src.models.data_models import ClientProfile, RoleEnum
from src.engine.summary_engine import SummaryEngine
from src.evaluation.benchmark import HandoverBenchmark, print_benchmark_report


DATA_PATH = os.path.join(
    os.path.dirname(__file__), "..", "data", "synthetic_clients.json"
)


def load_clients():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [ClientProfile(**item) for item in data]


def main():
    parser = argparse.ArgumentParser(
        description="Community Mental-Health Continuity & Handover System (CLI)"
    )
    parser.add_argument(
        "--client",
        type=str,
        default="MH-101",
        help="Client ID (e.g. MH-101, MH-102, MH-103, MH-104, MH-105)",
    )
    parser.add_argument(
        "--role",
        type=str,
        choices=["counsellor", "social_worker"],
        default="social_worker",
        help="Target receiving role for handover summary",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["prototype", "baseline", "benchmark", "compare"],
        default="prototype",
        help="Mode of operation: prototype (consent-aware), baseline (raw dump), compare, or benchmark",
    )

    args = parser.parse_args()

    if args.mode == "benchmark":
        print_benchmark_report()
        return

    clients = load_clients()
    matching = [c for c in clients if c.client_id.upper() == args.client.upper()]

    if not matching:
        print(f"Error: Client ID '{args.client}' not found in synthetic dataset.")
        print("Available Client IDs:", [c.client_id for c in clients])
        sys.exit(1)

    client = matching[0]
    target_role = RoleEnum.COUNSELLOR if args.role == "counsellor" else RoleEnum.SOCIAL_WORKER
    engine = SummaryEngine(client)

    if args.mode == "baseline":
        print("\n" + engine.generate_baseline_summary(target_role) + "\n")

    elif args.mode == "compare":
        print("\n" + "=" * 75)
        print(f" SIDE-BY-SIDE HANDOVER COMPARISON FOR {client.preferred_name} ({client.client_id}) ")
        print("=" * 75)
        print("\n--- [1] TRADITIONAL BASELINE (RAW UN-REDACTED DUMP) ---")
        print(engine.generate_baseline_summary(target_role))
        print("\n--- [2] PROTOTYPE (CONSENT-AWARE CONTINUITY HANDOVER) ---")
        summary = engine.generate_prototype_summary(target_role)
        print(summary.disclaimer_header)
        print(f"\nClient: {summary.client_name} ({summary.client_id}) | Target Role: {summary.target_role.value.upper()}")
        print("\n[Consented Notes]:")
        notes = summary.operational_support_notes if target_role == RoleEnum.SOCIAL_WORKER else summary.psychological_continuity_notes
        for n in notes:
            print(f"  • {n}")
        print("\n[Redacted / Privacy Scrubbed]:")
        for r in summary.redacted_sensitive_topics:
            print(f"  🚫 {r}")
        print("\n[Active Goals Preserved]:")
        for g in summary.active_goals:
            print(f"  🎯 [{g.priority.upper()}] {g.title} ({g.category}) - Status: {g.status}")
        print("\n[Pending Actions]:")
        for a in summary.pending_actions:
            print(f"  📌 Due {a.due_date}: {a.description}")
        if summary.uncertainty_flags:
            print("\n[⚠️ Uncertainty Flags]:")
            for f in summary.uncertainty_flags:
                print(f"  - [{f.issue_type}] {f.description}")
        print("=" * 75 + "\n")

    else:
        summary = engine.generate_prototype_summary(target_role)
        print("\n" + "=" * 75)
        print(summary.disclaimer_header)
        print("=" * 75)
        print(f"CLIENT: {summary.client_name} ({summary.client_id})")
        print(f"TARGET ROLE: {summary.target_role.value.upper()}\n")

        print("--- CONSENTED CONTINUITY NOTES ---")
        notes = summary.operational_support_notes if target_role == RoleEnum.SOCIAL_WORKER else summary.psychological_continuity_notes
        for n in notes:
            print(f"• {n}")

        if summary.redacted_sensitive_topics:
            print("\n--- PRIVACY REDACTION NOTICES ---")
            for r in summary.redacted_sensitive_topics:
                print(f"🚫 {r}")

        print("\n--- ACTIVE GOALS ---")
        for g in summary.active_goals:
            print(f"• [{g.priority.upper()}] {g.title} ({g.category}) - Status: {g.status}")

        print("\n--- PENDING ACTIONS ---")
        for a in summary.pending_actions:
            print(f"• Due {a.due_date or 'N/A'}: {a.description}")

        if summary.uncertainty_flags:
            print("\n--- ⚠️ UNCERTAINTY & QUALITY FLAGS ---")
            for f in summary.uncertainty_flags:
                print(f"• [{f.severity.upper()}] ({f.issue_type}): {f.description}")

        print("\n--- CONSENT AUDIT LOG ---")
        for audit in summary.audit_trail:
            print(f"  {audit}")
        print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
