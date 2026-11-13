"""Architecture analysis module for RepoCraft.

Extracts architecture dimensions based strictly on concrete evidence (imports, configurations, schemas).
Items without concrete evidence are labeled UNKNOWN.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Set

from .discovery import safe_read_text
from .types import ArchitectureObservation, EvidenceLevel, FileInventoryItem


class ArchitectureAnalyzer:
    """Analyzes architectural characteristics using verifiable file and configuration evidence."""

    def __init__(self, repo_root: Path, inventory: List[FileInventoryItem]):
        self.repo_root = repo_root
        self.inventory = inventory
        self.paths_set: Set[str] = {item.relative_path for item in inventory}

    def analyze(self) -> Dict[str, ArchitectureObservation]:
        observations: Dict[str, ArchitectureObservation] = {}

        observations["frontend"] = self._analyze_frontend()
        observations["backend"] = self._analyze_backend()
        observations["api_structure"] = self._analyze_api_structure()
        observations["database"] = self._analyze_database()
        observations["authentication"] = self._analyze_authentication()
        observations["state_management"] = self._analyze_state_management()
        observations["routing"] = self._analyze_routing()
        observations["shared_components"] = self._analyze_components()
        observations["utilities_services"] = self._analyze_utilities()
        observations["data_models_schemas"] = self._analyze_schemas()
        observations["external_integrations"] = self._analyze_integrations()
        observations["build_deployment"] = self._analyze_build_deployment()

        return observations

    def _analyze_frontend(self) -> ArchitectureObservation:
        evidence = []
        if any(p.startswith("app/") and p.endswith(("page.tsx", "page.jsx", "page.js")) for p in self.paths_set):
            evidence.append("Next.js App Router directory structure (app/page.*)")
            return ArchitectureObservation(
                dimension="Frontend Architecture",
                classification="Next.js App Router (React Server / Client Components)",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=evidence,
                details="Next.js App Router structure detected with route segments and layout hierarchy.",
            )

        if any(p.startswith("pages/") and p.endswith(("index.tsx", "index.jsx", "index.js")) for p in self.paths_set):
            evidence.append("Next.js Pages Router directory structure (pages/*)")
            return ArchitectureObservation(
                dimension="Frontend Architecture",
                classification="Next.js Pages Router",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=evidence,
                details="Next.js Pages Router detected using file-based routing in pages/.",
            )

        # React SPA check
        react_files = [p for p in self.paths_set if p in ("src/App.tsx", "src/App.jsx", "src/index.tsx", "src/index.jsx")]
        if react_files:
            evidence.extend(react_files)
            return ArchitectureObservation(
                dimension="Frontend Architecture",
                classification="Single Page Application (React SPA)",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=evidence,
                details="React root component and single-page mount point detected.",
            )

        # Vue SPA check
        vue_files = [p for p in self.paths_set if p in ("src/App.vue", "src/main.js", "src/main.ts") and p.endswith(".vue")]
        if vue_files or any(p.endswith(".vue") for p in self.paths_set):
            return ArchitectureObservation(
                dimension="Frontend Architecture",
                classification="Vue Component Application",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=[p for p in self.paths_set if p.endswith(".vue")][:5],
                details="Vue Single File Components detected.",
            )

        # Static HTML
        if "index.html" in self.paths_set:
            return ArchitectureObservation(
                dimension="Frontend Architecture",
                classification="Static HTML Web Interface",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=["index.html"],
                details="Standalone HTML entry document.",
            )

        return ArchitectureObservation(
            dimension="Frontend Architecture",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            evidence_sources=[],
            details="No frontend framework or UI entry point verified in repository.",
        )

    def _analyze_backend(self) -> ArchitectureObservation:
        evidence = []
        # FastAPI
        for p in self.paths_set:
            if p.endswith(".py"):
                txt = safe_read_text(self.repo_root / p, 2000)
                if "FastAPI(" in txt or "from fastapi import" in txt:
                    evidence.append(p)
                    return ArchitectureObservation(
                        dimension="Backend Architecture",
                        classification="FastAPI Async Microframework",
                        evidence_level=EvidenceLevel.VERIFIED,
                        evidence_sources=evidence[:3],
                        details="FastAPI application initialization found in Python source.",
                    )
                if "Flask(" in txt or "from flask import" in txt:
                    evidence.append(p)
                    return ArchitectureObservation(
                        dimension="Backend Architecture",
                        classification="Flask WSGI Application",
                        evidence_level=EvidenceLevel.VERIFIED,
                        evidence_sources=evidence[:3],
                        details="Flask application instance initialized.",
                    )

        # Express / Fastify / Nest
        for p in [p for p in self.paths_set if p.endswith((".ts", ".js"))]:
            txt = safe_read_text(self.repo_root / p, 2000)
            if "express()" in txt or 'require("express")' in txt or 'from "express"' in txt:
                return ArchitectureObservation(
                    dimension="Backend Architecture",
                    classification="Express HTTP Server",
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence_sources=[p],
                    details="Express server configuration detected.",
                )
            if "@nestjs/core" in txt or "@Controller" in txt:
                return ArchitectureObservation(
                    dimension="Backend Architecture",
                    classification="NestJS Modular Architecture",
                    evidence_level=EvidenceLevel.VERIFIED,
                    evidence_sources=[p],
                    details="NestJS controller/module decorators detected.",
                )

        # Spring Boot
        if any(p.endswith("Application.java") for p in self.paths_set):
            for p in [p for p in self.paths_set if p.endswith(".java")]:
                txt = safe_read_text(self.repo_root / p, 2000)
                if "@SpringBootApplication" in txt:
                    return ArchitectureObservation(
                        dimension="Backend Architecture",
                        classification="Spring Boot Application",
                        evidence_level=EvidenceLevel.VERIFIED,
                        evidence_sources=[p],
                        details="Spring Boot main application class with @SpringBootApplication.",
                    )

        return ArchitectureObservation(
            dimension="Backend Architecture",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            evidence_sources=[],
            details="No backend server framework or application entry verified in repository.",
        )

    def _analyze_api_structure(self) -> ArchitectureObservation:
        evidence = []
        if any(p in ("openapi.json", "openapi.yaml", "swagger.json", "swagger.yaml") for p in self.paths_set):
            spec_files = [p for p in self.paths_set if p in ("openapi.json", "openapi.yaml", "swagger.json", "swagger.yaml")]
            return ArchitectureObservation(
                dimension="API Structure",
                classification="OpenAPI / Swagger Contract-Driven API",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=spec_files,
                details="Formal OpenAPI / Swagger specification file discovered.",
            )

        api_routes = [p for p in self.paths_set if "/api/" in p or p.startswith("api/")]
        if api_routes:
            return ArchitectureObservation(
                dimension="API Structure",
                classification="File / Folder-Based REST Endpoints",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=api_routes[:5],
                details=f"Discovered {len(api_routes)} endpoint or API route file(s).",
            )

        # GraphQL check
        gql_files = [p for p in self.paths_set if p.endswith((".graphql", ".gql"))]
        if gql_files:
            return ArchitectureObservation(
                dimension="API Structure",
                classification="GraphQL Schema API",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=gql_files[:3],
                details="GraphQL schema definitions detected.",
            )

        return ArchitectureObservation(
            dimension="API Structure",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            details="No specific API endpoint or schema contract structure detected.",
        )

    def _analyze_database(self) -> ArchitectureObservation:
        evidence = []
        # Prisma
        if any(p.endswith("schema.prisma") for p in self.paths_set):
            return ArchitectureObservation(
                dimension="Database & ORM",
                classification="Prisma ORM with Declarative Schema",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=[p for p in self.paths_set if p.endswith("schema.prisma")],
                details="Prisma schema discovered.",
            )

        # Alembic / SQLAlchemy
        if "alembic.ini" in self.paths_set or any(p.startswith("alembic/") for p in self.paths_set):
            return ArchitectureObservation(
                dimension="Database & ORM",
                classification="SQLAlchemy with Alembic Migrations",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=[p for p in self.paths_set if "alembic" in p][:3],
                details="Alembic database migration configuration detected.",
            )

        # Django DB
        if any(p.endswith("models.py") for p in self.paths_set) and any(p.endswith("settings.py") for p in self.paths_set):
            return ArchitectureObservation(
                dimension="Database & ORM",
                classification="Django ORM",
                evidence_level=EvidenceLevel.LIKELY,
                evidence_sources=[p for p in self.paths_set if p.endswith(("models.py", "settings.py"))],
                details="Django models and settings detected.",
            )

        return ArchitectureObservation(
            dimension="Database & ORM",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            details="No database connection, migration scripts, or ORM schema verified.",
        )

    def _analyze_authentication(self) -> ArchitectureObservation:
        evidence = []
        for p in self.paths_set:
            if p.endswith((".ts", ".js", ".py")):
                txt = safe_read_text(self.repo_root / p, 2000)
                if "next-auth" in txt or "@auth/core" in txt:
                    return ArchitectureObservation(
                        dimension="Authentication Boundaries",
                        classification="Auth.js / NextAuth",
                        evidence_level=EvidenceLevel.VERIFIED,
                        evidence_sources=[p],
                        details="Auth.js / NextAuth integration verified in code.",
                    )
                if "passport.authenticate" in txt or 'from "passport"' in txt:
                    return ArchitectureObservation(
                        dimension="Authentication Boundaries",
                        classification="Passport.js Middleware",
                        evidence_level=EvidenceLevel.VERIFIED,
                        evidence_sources=[p],
                        details="Passport authentication middleware configured.",
                    )
                if "jwt.decode" in txt or "jwt.verify" in txt or "PyJWT" in txt:
                    evidence.append(p)

        if evidence:
            return ArchitectureObservation(
                dimension="Authentication Boundaries",
                classification="JWT Token-Based Authentication",
                evidence_level=EvidenceLevel.LIKELY,
                evidence_sources=evidence[:3],
                details="JWT verification/decoding routines found in source code.",
            )

        return ArchitectureObservation(
            dimension="Authentication Boundaries",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            details="No authentication or authorization boundaries identified from code inspection.",
        )

    def _analyze_state_management(self) -> ArchitectureObservation:
        for p in self.paths_set:
            if p.endswith((".ts", ".tsx", ".js", ".jsx")):
                txt = safe_read_text(self.repo_root / p, 1500)
                if "configureStore" in txt or "@reduxjs/toolkit" in txt:
                    return ArchitectureObservation(
                        dimension="State Management",
                        classification="Redux Toolkit",
                        evidence_level=EvidenceLevel.VERIFIED,
                        evidence_sources=[p],
                        details="Redux store configuration found in client code.",
                    )
                if "create(" in txt and "zustand" in txt:
                    return ArchitectureObservation(
                        dimension="State Management",
                        classification="Zustand Store",
                        evidence_level=EvidenceLevel.VERIFIED,
                        evidence_sources=[p],
                        details="Zustand state store hook verified.",
                    )

        return ArchitectureObservation(
            dimension="State Management",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            details="No centralized client-side state store detected.",
        )

    def _analyze_routing(self) -> ArchitectureObservation:
        if any("react-router" in safe_read_text(self.repo_root / p, 1500) for p in self.paths_set if p.endswith((".tsx", ".jsx", ".ts", ".js"))):
            return ArchitectureObservation(
                dimension="Routing Architecture",
                classification="React Router Client Routing",
                evidence_level=EvidenceLevel.VERIFIED,
                details="React Router provider and routes configured.",
            )
        if any(p.startswith("app/") and "page." in p for p in self.paths_set):
            return ArchitectureObservation(
                dimension="Routing Architecture",
                classification="Next.js App Router (File-System Based)",
                evidence_level=EvidenceLevel.VERIFIED,
                details="Next.js App router file-system route hierarchy.",
            )
        return ArchitectureObservation(
            dimension="Routing Architecture",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            details="No explicit client or server routing hierarchy confirmed.",
        )

    def _analyze_components(self) -> ArchitectureObservation:
        comp_dirs = [p for p in self.paths_set if p.startswith(("src/components/", "components/", "ui/"))]
        if comp_dirs:
            return ArchitectureObservation(
                dimension="Shared Components",
                classification="Modular Component Directory",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=comp_dirs[:5],
                details=f"Identified {len(comp_dirs)} component files in dedicated directories.",
            )
        return ArchitectureObservation(
            dimension="Shared Components",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            details="No dedicated UI component directory verified.",
        )

    def _analyze_utilities(self) -> ArchitectureObservation:
        util_files = [p for p in self.paths_set if any(part in ("utils", "lib", "services", "helpers") for part in p.split("/"))]
        if util_files:
            return ArchitectureObservation(
                dimension="Utilities & Services",
                classification="Structured Utility / Service Modules",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=util_files[:5],
                details=f"Discovered {len(util_files)} utility or service files.",
            )
        return ArchitectureObservation(
            dimension="Utilities & Services",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            details="No dedicated utility or service layer verified.",
        )

    def _analyze_schemas(self) -> ArchitectureObservation:
        schema_files = [p for p in self.paths_set if any(part in ("schemas", "models", "dto", "entities") for part in p.split("/"))]
        if schema_files:
            return ArchitectureObservation(
                dimension="Data Models & Schemas",
                classification="Dedicated Data Models / Schemas",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=schema_files[:5],
                details=f"Discovered {len(schema_files)} model/schema files.",
            )
        return ArchitectureObservation(
            dimension="Data Models & Schemas",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            details="No separate data model or schema directory verified.",
        )

    def _analyze_integrations(self) -> ArchitectureObservation:
        integrations = []
        for p in self.paths_set:
            if p.endswith((".ts", ".js", ".py", ".json")):
                txt = safe_read_text(self.repo_root / p, 2000)
                if "stripe" in txt:
                    integrations.append("Stripe (Payments)")
                if "boto3" in txt or "@aws-sdk" in txt:
                    integrations.append("AWS SDK (Cloud Infrastructure)")
                if "openai" in txt or "@google/generative-ai" in txt:
                    integrations.append("AI / LLM API")
                if "sendgrid" in txt:
                    integrations.append("SendGrid (Email)")
        if integrations:
            uniq = sorted(list(set(integrations)))
            return ArchitectureObservation(
                dimension="External Integrations",
                classification=", ".join(uniq),
                evidence_level=EvidenceLevel.VERIFIED,
                details=f"External third-party API SDK integrations detected: {', '.join(uniq)}.",
            )
        return ArchitectureObservation(
            dimension="External Integrations",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            details="No verified third-party cloud/service API integrations found in code.",
        )

    def _analyze_build_deployment(self) -> ArchitectureObservation:
        evidence = []
        if "Dockerfile" in self.paths_set:
            evidence.append("Dockerfile")
        if "docker-compose.yml" in self.paths_set or "docker-compose.yaml" in self.paths_set:
            evidence.append("docker-compose")
        if "vercel.json" in self.paths_set:
            evidence.append("Vercel configuration")
        if "netlify.toml" in self.paths_set:
            evidence.append("Netlify configuration")
        if any(p.endswith(".tf") for p in self.paths_set):
            evidence.append("Terraform IaC")

        if evidence:
            return ArchitectureObservation(
                dimension="Build & Deployment Structure",
                classification="Containerized / Cloud Configured",
                evidence_level=EvidenceLevel.VERIFIED,
                evidence_sources=evidence,
                details=f"Discovered build and deployment artifacts: {', '.join(evidence)}.",
            )
        return ArchitectureObservation(
            dimension="Build & Deployment Structure",
            classification="UNKNOWN",
            evidence_level=EvidenceLevel.UNKNOWN,
            details="No container or cloud deployment configuration files detected.",
        )

