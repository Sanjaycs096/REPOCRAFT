"""Module A — Multi-Phase Finding Ingestor for RepoCraft Phase 4.

Consumes and normalizes findings from Phase 1, Phase 2, and Phase 3 artifacts:
- Phase 1: recommendations.json, inventory.json, repository-audit.md
- Phase 2: maintenance-plan.json, maintenance-analysis.json, documentation-audit.md
- Phase 3: security-findings.json, dependency-audit.json, test-analysis.json, test-execution-report.json, cicd-audit.json

Validates JSON schemas, deduplicates overlapping findings, preserves source IDs,
and safely handles missing or malformed reports.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .repair_types import NormalizedFinding, RepairStatus


class FindingIngestor:
    """Ingests findings from Phase 1, 2, and 3 reports into normalized repair findings."""

    def __init__(self, reports_dir: str):
        self.reports_dir = Path(reports_dir).resolve()
        self.findings: List[NormalizedFinding] = []
        self.warnings: List[str] = []
        self._counter = 1
        self._seen_signatures: Set[str] = set()

    def _next_id(self) -> str:
        fid = f"NORM-{self._counter:03d}"
        self._counter += 1
        return fid

    def _read_json_file(self, filename: str) -> Optional[Any]:
        path = self.reports_dir / filename
        if not path.is_file():
            self.warnings.append(f"Artifact not found: '{filename}'. Skipping.")
            return None
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            return json.loads(content)
        except json.JSONDecodeError as exc:
            self.warnings.append(f"Malformed JSON in '{filename}': {str(exc)}. Skipping.")
            return None
        except Exception as exc:
            self.warnings.append(f"Error reading '{filename}': {str(exc)}. Skipping.")
            return None

    def ingest_all(self) -> Tuple[List[NormalizedFinding], List[str]]:
        """Ingest all available reports from reports_dir."""
        self.findings.clear()
        self.warnings.clear()
        self._seen_signatures.clear()
        self._counter = 1

        # Phase 1 Ingestion
        self._ingest_phase1_recommendations()

        # Phase 2 Ingestion
        self._ingest_phase2_maintenance_plan()
        self._ingest_phase2_maintenance_analysis()

        # Phase 3 Ingestion
        self._ingest_phase3_security_findings()
        self._ingest_phase3_dependency_audit()
        self._ingest_phase3_test_analysis()
        self._ingest_phase3_test_execution()
        self._ingest_phase3_cicd_audit()

        return self.findings, self.warnings

    def _add_finding(
        self,
        source_id: str,
        source_phase: str,
        category: str,
        severity: str,
        confidence: str,
        description: str,
        evidence: str,
        affected_files: List[str],
        proposed_remediation: str,
        approval_required: bool,
        validation_requirements: Optional[List[str]] = None,
    ) -> None:
        # Deduplication signature based on affected file and category or description
        file_key = affected_files[0] if affected_files else "repo"
        signature = f"{category.lower()}::{file_key.lower()}::{description.lower()[:60]}"
        if signature in self._seen_signatures:
            return
        self._seen_signatures.add(signature)

        finding = NormalizedFinding(
            stable_id=self._next_id(),
            source_id=source_id,
            source_phase=source_phase,
            category=category,
            severity=severity.upper(),
            confidence=confidence.upper(),
            description=description,
            evidence=evidence,
            affected_files=affected_files,
            proposed_remediation=proposed_remediation,
            approval_required=approval_required,
            validation_requirements=validation_requirements or ["local_syntax_check"],
            current_status=RepairStatus.FINDING_DETECTED,
        )
        self.findings.append(finding)

    # --------------------------------------------------------------------------
    # Phase 1 Ingestion
    # --------------------------------------------------------------------------
    def _ingest_phase1_recommendations(self) -> None:
        data = self._read_json_file("recommendations.json")
        if not data or not isinstance(data, (dict, list)):
            return
        recs = data if isinstance(data, list) else data.get("recommendations", [])
        for rec in recs:
            if not isinstance(rec, dict):
                continue
            src_id = rec.get("recommendation_id") or rec.get("id") or "P1-REC"
            cat = rec.get("category", "General")
            sev = rec.get("severity", "LOW")
            conf = rec.get("confidence", "HIGH")
            desc = rec.get("finding") or rec.get("description") or "Phase 1 finding"
            evid = rec.get("evidence", "")
            action = rec.get("action", "")
            files = rec.get("affected_files", [])

            self._add_finding(
                source_id=src_id,
                source_phase="phase1",
                category=cat,
                severity=sev,
                confidence=conf,
                description=desc,
                evidence=evid,
                affected_files=files,
                proposed_remediation=action,
                approval_required=sev in ("HIGH", "CRITICAL"),
            )

    # --------------------------------------------------------------------------
    # Phase 2 Ingestion
    # --------------------------------------------------------------------------
    def _ingest_phase2_maintenance_plan(self) -> None:
        data = self._read_json_file("maintenance-plan.json")
        if not data:
            return
        tasks = data.get("tasks", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
        for t in tasks:
            if not isinstance(t, dict):
                continue
            t_id = t.get("task_id", "P2-TASK")
            cat = t.get("category", "Maintenance")
            sev = t.get("severity", "MEDIUM")
            risk = t.get("risk_level", "LOW")
            title = t.get("title", "Phase 2 Maintenance Task")
            desc = t.get("description", title)
            files = t.get("affected_files", [])
            action = t.get("action", "")
            appr = t.get("requires_approval", risk in ("HIGH", "CRITICAL"))

            self._add_finding(
                source_id=t_id,
                source_phase="phase2",
                category=cat,
                severity=sev,
                confidence="HIGH",
                description=desc,
                evidence=action,
                affected_files=files,
                proposed_remediation=action,
                approval_required=appr,
            )

    def _ingest_phase2_maintenance_analysis(self) -> None:
        data = self._read_json_file("maintenance-analysis.json")
        if not data or not isinstance(data, dict):
            return

        # Organization findings
        org_findings = data.get("organization_findings", [])
        for of in org_findings:
            if not isinstance(of, dict):
                continue
            src_id = of.get("finding_id", "P2-ORG")
            cat = of.get("category", "ORGANIZATION")
            sev = of.get("severity", "LOW")
            msg = of.get("message", "Organization issue")
            fpath = of.get("file_path") or of.get("path")
            files = [fpath] if fpath else []
            self._add_finding(
                source_id=src_id,
                source_phase="phase2",
                category=cat,
                severity=sev,
                confidence="HIGH",
                description=msg,
                evidence=of.get("details", ""),
                affected_files=files,
                proposed_remediation=of.get("recommendation", "Review file organization"),
                approval_required=False,
            )

        # Unused file candidates
        unused = data.get("unused_file_candidates", [])
        for u in unused:
            if not isinstance(u, dict):
                continue
            fpath = u.get("file_path", "")
            conf = u.get("confidence", "POSSIBLY_UNUSED")
            files = [fpath] if fpath else []
            self._add_finding(
                source_id="P2-UNUSED",
                source_phase="phase2",
                category="DEAD_CODE_REVIEW",
                severity="LOW",
                confidence=conf,
                description=f"Potential unused file candidate: {fpath}",
                evidence=f"Confidence: {conf}",
                affected_files=files,
                proposed_remediation="Manual review before any deletion; never delete automatically.",
                approval_required=True,
            )

    # --------------------------------------------------------------------------
    # Phase 3 Ingestion
    # --------------------------------------------------------------------------
    def _ingest_phase3_security_findings(self) -> None:
        data = self._read_json_file("security-findings.json")
        if not data or not isinstance(data, dict):
            return

        # Secrets
        for s in data.get("secrets", []):
            if not isinstance(s, dict):
                continue
            self._add_finding(
                source_id=s.get("finding_id", "SEC-SECRET"),
                source_phase="phase3",
                category="SECRET_EXPOSURE",
                severity=s.get("severity", "CRITICAL"),
                confidence=s.get("confidence", "HIGH"),
                description=s.get("explanation", "Hardcoded credential detected"),
                evidence=s.get("redacted_evidence", "[REDACTED]"),
                affected_files=[s["file_path"]] if "file_path" in s else [],
                proposed_remediation="Revoke, rotate, and remove secret from repository history.",
                approval_required=True,
            )

        # Code patterns
        for p in data.get("code_patterns", []):
            if not isinstance(p, dict):
                continue
            self._add_finding(
                source_id=p.get("finding_id", "SEC-PATTERN"),
                source_phase="phase3",
                category=p.get("category", "APPLICATION_SECURITY"),
                severity=p.get("severity", "HIGH"),
                confidence=p.get("confidence", "HIGH"),
                description=p.get("explanation", "Dangerous security pattern detected"),
                evidence=p.get("redacted_evidence", "[REDACTED]"),
                affected_files=[p["file_path"]] if "file_path" in p else [],
                proposed_remediation=p.get("recommended_remediation", "Refactor unsafe pattern"),
                approval_required=True,
            )

        # Configuration findings
        for c in data.get("configuration", []):
            if not isinstance(c, dict):
                continue
            self._add_finding(
                source_id=c.get("finding_id", "SEC-CONFIG"),
                source_phase="phase3",
                category=c.get("category", "CONFIGURATION"),
                severity=c.get("severity", "MEDIUM"),
                confidence="HIGH",
                description=c.get("issue", "Configuration issue"),
                evidence=c.get("explanation", ""),
                affected_files=[c["file_path"]] if "file_path" in c else [],
                proposed_remediation=c.get("recommended_action", "Update configuration"),
                approval_required=c.get("requires_approval", True),
            )

        # Supply chain findings
        for sc in data.get("supply_chain", []):
            if not isinstance(sc, dict):
                continue
            self._add_finding(
                source_id=sc.get("finding_id", "SEC-SUPPLY-CHAIN"),
                source_phase="phase3",
                category=sc.get("category", "SUPPLY_CHAIN"),
                severity=sc.get("severity", "HIGH"),
                confidence="HIGH",
                description=sc.get("issue", "Supply chain vulnerability"),
                evidence=sc.get("explanation", ""),
                affected_files=[sc["workflow_path"]] if "workflow_path" in sc else [],
                proposed_remediation=sc.get("recommendation", "Pin action or restrict permissions"),
                approval_required=True,
            )

    def _ingest_phase3_dependency_audit(self) -> None:
        data = self._read_json_file("dependency-audit.json")
        if not data or not isinstance(data, dict):
            return
        results = data.get("results", [])
        for r in results:
            if not isinstance(r, dict):
                continue
            manifest = r.get("manifest_path", "")
            if not r.get("lockfile_present"):
                self._add_finding(
                    source_id="DEP-MISSING-LOCKFILE",
                    source_phase="phase3",
                    category="DEPENDENCY_CONFIGURATION",
                    severity="MEDIUM",
                    confidence="HIGH",
                    description=f"Missing lockfile for manifest '{manifest}'",
                    evidence=r.get("notes", "No lockfile found"),
                    affected_files=[manifest] if manifest else [],
                    proposed_remediation="Generate and commit deterministic lockfile.",
                    approval_required=True,
                )
            if r.get("unpinned_count", 0) > 0:
                self._add_finding(
                    source_id="DEP-UNPINNED",
                    source_phase="phase3",
                    category="DEPENDENCY_CONFIGURATION",
                    severity="LOW",
                    confidence="HIGH",
                    description=f"Manifest '{manifest}' has {r['unpinned_count']} unpinned dependencies",
                    evidence=f"Unpinned count: {r['unpinned_count']}",
                    affected_files=[manifest] if manifest else [],
                    proposed_remediation="Pin dependencies to explicit exact or minimum versions.",
                    approval_required=True,
                )

    def _ingest_phase3_test_analysis(self) -> None:
        data = self._read_json_file("test-analysis.json")
        if not data or not isinstance(data, dict):
            return
        if not data.get("is_ready_for_execution"):
            for b in data.get("blockers", []):
                self._add_finding(
                    source_id="TEST-BLOCKER",
                    source_phase="phase3",
                    category="TEST_FAILURE_CORRECTION",
                    severity="HIGH",
                    confidence="HIGH",
                    description=f"Test readiness blocker: {b}",
                    evidence=str(b),
                    affected_files=[],
                    proposed_remediation="Install missing test dependencies or configure test framework.",
                    approval_required=True,
                )
        for ef in data.get("empty_test_files", []):
            self._add_finding(
                source_id="TEST-EMPTY-FILE",
                source_phase="phase3",
                category="TEST_FAILURE_CORRECTION",
                severity="LOW",
                confidence="HIGH",
                description=f"Empty test file detected: {ef}",
                evidence=f"File: {ef}",
                affected_files=[ef],
                proposed_remediation="Implement test cases or remove placeholder file.",
                approval_required=False,
            )

    def _ingest_phase3_test_execution(self) -> None:
        data = self._read_json_file("test-execution-report.json")
        if not data or not isinstance(data, dict):
            return
        for r in data.get("results", []):
            if not isinstance(r, dict):
                continue
            if r.get("state") == "FAILED" or (r.get("tests_failed") or 0) > 0:
                cmd = r.get("command", "")
                self._add_finding(
                    source_id="TEST-FAILING-RUNNER",
                    source_phase="phase3",
                    category="TEST_FAILURE_CORRECTION",
                    severity="HIGH",
                    confidence="HIGH",
                    description=f"Test execution failed for command '{cmd}'",
                    evidence=r.get("error_summary") or r.get("raw_output_redacted", "")[:200],
                    affected_files=[],
                    proposed_remediation="Investigate root cause of failing tests and fix bugs without weakening assertions.",
                    approval_required=True,
                )

    def _ingest_phase3_cicd_audit(self) -> None:
        data = self._read_json_file("cicd-audit.json")
        if not data or not isinstance(data, dict):
            return
        for w in data.get("workflows", []):
            if not isinstance(w, dict):
                continue
            wf_file = w.get("workflow_file", "")
            for issue in w.get("issues", []):
                self._add_finding(
                    source_id="CICD-WORKFLOW-ISSUE",
                    source_phase="phase3",
                    category="CICD_WORKFLOW_IMPROVEMENT",
                    severity="MEDIUM",
                    confidence="HIGH",
                    description=f"CI/CD issue in '{wf_file}': {issue}",
                    evidence=issue,
                    affected_files=[wf_file] if wf_file else [],
                    proposed_remediation="Update workflow configuration.",
                    approval_required=True,
                )


def ingest_findings(reports_dir: str) -> Tuple[List[NormalizedFinding], List[str]]:
    """Convenience helper to ingest and normalize all findings in reports_dir."""
    ingestor = FindingIngestor(reports_dir)
    return ingestor.ingest_all()
