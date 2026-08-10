from datetime import date, datetime

from app.core.time_utils import utcnow

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models.application_assignment import ApplicationAssignment
from app.db.models.area import Area
from app.db.models.catalog_device import CatalogDevice
from app.db.models.architecture import ArchitectureElement, ArchitectureModel, ArchitectureRelationship
from app.db.models.audit import Audit
from app.db.models.compliance import ClientControlStatus, ComplianceControl, ComplianceFramework
from app.db.models.hardening import HardeningRule
from app.db.models.netdoctor import NetdoctorIssue
from app.db.models.risk import Risk, RiskAsset, Threat, Vulnerability
from app.db.models.client import Client
from app.db.models.client_profile import ClientProfile
from app.db.models.collaborator_profile import CollaboratorProfile
from app.db.models.doc_type import DocType
from app.db.models.enums import (
    AssignmentType,
    ClientStatus,
    DocScope,
    JobApplicationStatus,
    ProjectStatus,
    RoleCode,
    SkillStatus,
    UserStatus,
)
from app.db.models.organization import Organization
from app.db.models.product import Product
from app.db.models.project import Project
from app.db.models.project_member import ProjectMember
from app.db.models.project_requirement import ProjectRequirement
from app.db.models.project_type import ProjectType
from app.db.models.role import Role
from app.db.models.service import Service
from app.db.models.skill import Skill
from app.db.models.user import User
from app.db.models.integration import Integration
from app.db.models.job_application import JobApplication
from app.db.models.report import Report
from app.db.models.user_skill import UserSkill


def apply_inline_migrations(db: Session) -> None:
    """ALTER TABLE inline para columnas agregadas post-creación.

    Idempotente (IF NOT EXISTS). Se ejecuta antes del seed para garantizar
    que las nuevas columnas existan aunque la tabla `devices` haya sido
    creada en una versión anterior del esquema.
    """
    statements = [
        # Devices — ISO 27001 A.8 / NIST CSF ID.AM (P1)
        "ALTER TABLE devices ADD COLUMN IF NOT EXISTS criticality VARCHAR(20)",
        "ALTER TABLE devices ADD COLUMN IF NOT EXISTS data_classification VARCHAR(20)",
        "ALTER TABLE devices ADD COLUMN IF NOT EXISTS responsible_user_id INTEGER REFERENCES users(id)",
    ]
    for stmt in statements:
        db.execute(text(stmt))
    db.commit()


def seed_initial_data(db: Session) -> None:
    apply_inline_migrations(db)

    organization = db.scalar(
        select(Organization).where(Organization.slug == "ninjasec-internal")
    )
    if not organization:
        organization = Organization(
            name="NinjaSec Internal",
            slug="ninjasec-internal",
            plan="enterprise",
            status="active",
        )
        db.add(organization)
        db.commit()
        db.refresh(organization)

    role_map: dict[str, str] = {
        RoleCode.SUPER_ADMIN.value: "Super Admin",
        RoleCode.ADMIN.value: "Admin",
        RoleCode.COLLABORATOR.value: "Collaborator",
        RoleCode.CLIENT.value: "Client",
    }
    for code, name in role_map.items():
        role = db.scalar(select(Role).where(Role.code == code))
        if not role:
            db.add(Role(code=code, name=name, description=f"System role: {name}"))
    db.commit()

    roles = {role.code: role for role in db.scalars(select(Role)).all()}

    project_type_seed = [
        ("Implementacion", "implementation"),
        ("Consultoria", "consulting"),
        ("Soporte", "support"),
    ]
    for name, slug in project_type_seed:
        if not db.scalar(select(ProjectType).where(ProjectType.slug == slug)):
            db.add(ProjectType(name=name, slug=slug, is_active=True))
    db.commit()

    area_seed = [
        ("Redes", "network"),
        ("Seguridad de redes", "network-security"),
        ("Ciberseguridad", "cybersecurity"),
        ("Desarrollo", "development"),
        ("DevOps", "devops"),
        ("Gestion TI", "it-management"),
        ("Consultoria", "consulting"),
        ("Datos y analitica", "data-analytics"),
        ("Compliance / GRC", "compliance-grc"),
    ]
    for name, slug in area_seed:
        if not db.scalar(select(Area).where(Area.slug == slug)):
            db.add(Area(name=name, slug=slug, is_active=True))
    db.commit()

    doc_types_seed = [
        ("Implementacion tecnica", DocScope.PUBLIC),
        ("Manual de uso", DocScope.PUBLIC),
        ("Reporte ejecutivo", DocScope.PUBLIC),
        ("Runbook operativo", DocScope.PRIVATE),
        ("Acta de proyecto", DocScope.PRIVATE),
        ("Contrato y anexos", DocScope.PRIVATE),
        ("Procedimientos internos", DocScope.PRIVATE),
        ("SLA", DocScope.BOTH),
    ]

    for name, scope in doc_types_seed:
        if not db.scalar(select(DocType).where(DocType.name == name)):
            db.add(DocType(name=name, scope=scope, is_active=True))
    db.commit()

    def upsert_user(
        email: str, full_name: str, role_code: RoleCode, password: str, job_title: str
    ) -> User:
        user = db.scalar(select(User).where(User.email == email))
        if not user:
            user = User(
                organization_id=organization.id,
                role_id=roles[role_code.value].id,
                role_code=role_code,
                full_name=full_name,
                email=email,
                password_hash=hash_password(password),
                status=UserStatus.ACTIVE,
                job_title=job_title,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user

    admin = upsert_user(
        "admin@ninjasec.local",
        "Ruben Mark Salazar Tocas",
        RoleCode.SUPER_ADMIN,
        "change-me",
        "Founder",
    )
    admin_ops = upsert_user(
        "ops@ninjasec.local",
        "Paola Rojas",
        RoleCode.ADMIN,
        "admin123",
        "Operations Manager",
    )
    collaborator = upsert_user(
        "collab@ninjasec.local",
        "Demo Collaborator",
        RoleCode.COLLABORATOR,
        "temp123",
        "SOC Analyst",
    )
    collaborator_2 = upsert_user(
        "maria@ninjasec.local",
        "Maria Torres",
        RoleCode.COLLABORATOR,
        "temp123",
        "Network Engineer",
    )
    collaborator_3 = upsert_user(
        "luis@ninjasec.local",
        "Luis Arce",
        RoleCode.COLLABORATOR,
        "temp123",
        "Security Analyst",
    )
    collaborator_4 = upsert_user(
        "carla@ninjasec.local",
        "Carla Paredes",
        RoleCode.COLLABORATOR,
        "temp123",
        "DevOps Engineer",
    )
    collaborator_5 = upsert_user(
        "diego@ninjasec.local",
        "Diego Castillo",
        RoleCode.COLLABORATOR,
        "temp123",
        "Cloud Engineer",
    )
    collaborator_6 = upsert_user(
        "sofia@ninjasec.local",
        "Sofia Vargas",
        RoleCode.COLLABORATOR,
        "temp123",
        "Threat Analyst",
    )
    client_user = upsert_user(
        "client@ninjasec.local",
        "Ana Torres",
        RoleCode.CLIENT,
        "client123",
        "Operations Lead",
    )
    client_user_2 = upsert_user(
        "client2@ninjasec.local",
        "Ricardo Nunez",
        RoleCode.CLIENT,
        "client123",
        "IT Manager",
    )
    client_user_3 = upsert_user(
        "client3@ninjasec.local",
        "Valeria Soto",
        RoleCode.CLIENT,
        "client123",
        "Security Lead",
    )

    def upsert_collaborator_profile(
        user: User,
        position_title: str,
        seniority: str,
        availability_status: str,
        bio: str | None = None,
    ) -> None:
        if not db.scalar(
            select(CollaboratorProfile).where(CollaboratorProfile.user_id == user.id)
        ):
            db.add(
                CollaboratorProfile(
                    user_id=user.id,
                    position_title=position_title,
                    seniority=seniority,
                    availability_status=availability_status,
                    bio=bio,
                )
            )

    upsert_collaborator_profile(
        collaborator,
        "SOC Analyst",
        "Mid",
        "available",
        "Monitorea alertas y coordina respuesta inicial.",
    )
    upsert_collaborator_profile(
        collaborator_2,
        "Network Engineer",
        "Senior",
        "available",
        "Especialista en redes y despliegues en campo.",
    )
    upsert_collaborator_profile(
        collaborator_3,
        "Security Analyst",
        "Mid",
        "busy",
        "Analiza incidentes y prepara reportes ejecutivos.",
    )
    upsert_collaborator_profile(
        collaborator_4,
        "DevOps Engineer",
        "Senior",
        "available",
        "Automatiza despliegues y pipelines de seguridad.",
    )
    upsert_collaborator_profile(
        collaborator_5,
        "Cloud Engineer",
        "Mid",
        "available",
        "Gestiona entornos cloud y observabilidad.",
    )
    upsert_collaborator_profile(
        collaborator_6,
        "Threat Analyst",
        "Senior",
        "available",
        "Analisis avanzado de amenazas y hunting.",
    )

    client = db.scalar(select(Client).where(Client.company_name == "Blue Shield Tech"))
    if not client:
        client = Client(
            organization_id=organization.id,
            company_name="Blue Shield Tech",
            commercial_status=ClientStatus.ACTIVE,
            sector="Cybersecurity",
            size="SMB",
            notes="Initial demo client",
        )
        db.add(client)
        db.commit()
        db.refresh(client)

    if not db.scalar(select(Client).where(Client.company_name == "Orion Logistics")):
        db.add(
            Client(
                organization_id=organization.id,
                company_name="Orion Logistics",
                commercial_status=ClientStatus.ACTIVE,
                sector="Logistics",
                size="Enterprise",
                notes="Expansion client",
            )
        )

    if not db.scalar(select(Client).where(Client.company_name == "Nova Retail")):
        db.add(
            Client(
                organization_id=organization.id,
                company_name="Nova Retail",
                commercial_status=ClientStatus.ACTIVE,
                sector="Retail",
                size="Mid",
                notes="Retail pilot",
            )
        )

    def upsert_client_profile(user: User, client_ref: Client, title: str) -> None:
        if not db.scalar(select(ClientProfile).where(ClientProfile.user_id == user.id)):
            db.add(
                ClientProfile(
                    client_id=client_ref.id,
                    user_id=user.id,
                    position_title=title,
                    access_level="standard",
                )
            )

    upsert_client_profile(client_user, client, "Operations Lead")
    orion_client = db.scalar(
        select(Client).where(Client.company_name == "Orion Logistics")
    )
    if orion_client:
        upsert_client_profile(client_user_2, orion_client, "IT Manager")
    nova_client = db.scalar(select(Client).where(Client.company_name == "Nova Retail"))
    if nova_client:
        upsert_client_profile(client_user_3, nova_client, "Security Lead")

    if not db.scalar(select(Service).where(Service.slug == "api-reporting")):
        cybersecurity = db.scalar(select(Area).where(Area.slug == "cybersecurity"))
        implementation = db.scalar(
            select(ProjectType).where(ProjectType.slug == "implementation")
        )
        db.add(
            Service(
                organization_id=organization.id,
                area_id=cybersecurity.id if cybersecurity else None,
                project_type_id=implementation.id if implementation else None,
                title="API Reporting",
                slug="api-reporting",
                category="core",
                summary="Automated reporting from infrastructure APIs",
                description="Connect devices and systems such as pfSense and FortiGate to generate automated reports.",
                is_public=True,
                active=True,
            )
        )

    if not db.scalar(select(Service).where(Service.slug == "soc-dashboard")):
        cybersecurity = db.scalar(select(Area).where(Area.slug == "cybersecurity"))
        consulting = db.scalar(
            select(ProjectType).where(ProjectType.slug == "consulting")
        )
        db.add(
            Service(
                organization_id=organization.id,
                area_id=cybersecurity.id if cybersecurity else None,
                project_type_id=consulting.id if consulting else None,
                title="SOC Dashboard",
                slug="soc-dashboard",
                category="security",
                summary="Security operations dashboard",
                description="Operational visibility for SOC teams.",
                is_public=True,
                active=True,
            )
        )

    if not db.scalar(select(Service).where(Service.slug == "network-monitoring")):
        network = db.scalar(select(Area).where(Area.slug == "network"))
        implementation = db.scalar(
            select(ProjectType).where(ProjectType.slug == "implementation")
        )
        db.add(
            Service(
                organization_id=organization.id,
                area_id=network.id if network else None,
                project_type_id=implementation.id if implementation else None,
                title="Network Monitoring",
                slug="network-monitoring",
                category="network",
                summary="Network visibility and alerts",
                description="Monitoring and observability for network operations.",
                is_public=True,
                active=True,
            )
        )

    if not db.scalar(select(Service).where(Service.slug == "compliance-baseline")):
        compliance = db.scalar(select(Area).where(Area.slug == "compliance-grc"))
        consulting = db.scalar(
            select(ProjectType).where(ProjectType.slug == "consulting")
        )
        db.add(
            Service(
                organization_id=organization.id,
                area_id=compliance.id if compliance else None,
                project_type_id=consulting.id if consulting else None,
                title="Compliance Baseline",
                slug="compliance-baseline",
                category="compliance",
                summary="Baseline compliance assessment",
                description="Compliance assessment and remediation plan.",
                is_public=True,
                active=True,
            )
        )

    if not db.scalar(select(Product).where(Product.slug == "ninjasec-core")):
        cybersecurity = db.scalar(select(Area).where(Area.slug == "cybersecurity"))
        db.add(
            Product(
                organization_id=organization.id,
                area_id=cybersecurity.id if cybersecurity else None,
                name="NinjaSec Core",
                slug="ninjasec-core",
                summary="Core platform for automated reporting",
                is_active=True,
            )
        )

    if not db.scalar(select(Product).where(Product.slug == "ninjasec-observability")):
        network = db.scalar(select(Area).where(Area.slug == "network"))
        db.add(
            Product(
                organization_id=organization.id,
                area_id=network.id if network else None,
                name="NinjaSec Observability",
                slug="ninjasec-observability",
                summary="Network observability suite",
                is_active=True,
            )
        )

    if not db.scalar(
        select(Integration).where(Integration.name == "pfSense Main Edge")
    ):
        db.add(
            Integration(
                organization_id=organization.id,
                client_id=client.id,
                connector_type="pfSense",
                name="pfSense Main Edge",
                base_url="https://pfsense.local/api",
                auth_type="token",
                config_json='{"environment":"demo","site":"hq"}',
                status="pending",
            )
        )

    if not db.scalar(
        select(Integration).where(Integration.name == "FortiGate Branch 01")
    ):
        db.add(
            Integration(
                organization_id=organization.id,
                client_id=client.id,
                connector_type="FortiGate",
                name="FortiGate Branch 01",
                base_url="https://fortigate.local/api",
                auth_type="token",
                config_json='{"environment":"demo","site":"branch-01"}',
                status="pending",
            )
        )

    db.commit()

    skill_seed = [
        "Redes",
        "FortiGate",
        "Seguridad de redes",
        "Ciberseguridad",
        "SOC",
        "Threat Hunting",
        "DevOps",
        "Automatizacion",
        "CI/CD",
        "Python",
        "SIEM",
        "AWS",
        "Azure",
        "Kubernetes",
        "Incident Response",
    ]
    for name in skill_seed:
        if not db.scalar(select(Skill).where(Skill.name == name)):
            db.add(Skill(name=name, category="core", is_active=True))
    db.commit()

    def upsert_skill(user: User, skill_name: str, level: str) -> None:
        skill = db.scalar(select(Skill).where(Skill.name == skill_name))
        if not skill:
            return
        existing = db.scalar(
            select(UserSkill).where(
                UserSkill.user_id == user.id, UserSkill.skill_id == skill.id
            )
        )
        if not existing:
            db.add(
                UserSkill(
                    user_id=user.id,
                    skill_id=skill.id,
                    level=level,
                    status=SkillStatus.APPROVED,
                )
            )

    upsert_skill(collaborator_2, "Redes", "Senior")
    upsert_skill(collaborator_2, "FortiGate", "Mid")
    upsert_skill(collaborator_2, "Seguridad de redes", "Mid")
    upsert_skill(collaborator_3, "Ciberseguridad", "Senior")
    upsert_skill(collaborator_3, "SOC", "Mid")
    upsert_skill(collaborator_3, "Threat Hunting", "Mid")
    upsert_skill(collaborator_4, "DevOps", "Senior")
    upsert_skill(collaborator_4, "Automatizacion", "Mid")
    upsert_skill(collaborator_4, "CI/CD", "Mid")
    upsert_skill(collaborator_5, "AWS", "Senior")
    upsert_skill(collaborator_5, "Kubernetes", "Mid")
    upsert_skill(collaborator_5, "DevOps", "Mid")
    upsert_skill(collaborator_6, "Threat Hunting", "Senior")
    upsert_skill(collaborator_6, "SIEM", "Senior")
    upsert_skill(collaborator_6, "Incident Response", "Mid")
    db.commit()

    api_reporting = db.scalar(select(Service).where(Service.slug == "api-reporting"))
    soc_dashboard = db.scalar(select(Service).where(Service.slug == "soc-dashboard"))
    network_monitoring = db.scalar(
        select(Service).where(Service.slug == "network-monitoring")
    )
    compliance_baseline = db.scalar(
        select(Service).where(Service.slug == "compliance-baseline")
    )
    core_product = db.scalar(select(Product).where(Product.slug == "ninjasec-core"))
    observability_product = db.scalar(
        select(Product).where(Product.slug == "ninjasec-observability")
    )
    implementation = db.scalar(
        select(ProjectType).where(ProjectType.slug == "implementation")
    )
    consulting = db.scalar(select(ProjectType).where(ProjectType.slug == "consulting"))
    support = db.scalar(select(ProjectType).where(ProjectType.slug == "support"))

    def upsert_project(
        name: str,
        client_ref: Client,
        project_type: ProjectType | None,
        service: Service | None,
        product: Product | None,
        status: ProjectStatus,
        description: str,
    ) -> Project:
        project = db.scalar(select(Project).where(Project.name == name))
        if not project:
            area_id = None
            if service:
                area_id = service.area_id
            if not area_id and product:
                area_id = product.area_id
            project = Project(
                organization_id=organization.id,
                client_id=client_ref.id,
                project_type_id=project_type.id if project_type else None,
                area_id=area_id,
                service_id=service.id if service else None,
                product_id=product.id if product else None,
                name=name,
                description=description,
                status=status,
                start_date=date.today(),
            )
            db.add(project)
            db.commit()
            db.refresh(project)
        return project

    project_1 = upsert_project(
        "API Reporting - Blue Shield",
        client,
        implementation,
        api_reporting,
        None,
        ProjectStatus.ACTIVE,
        "Implementacion de reporting automatizado y dashboards ejecutivos.",
    )
    project_2 = upsert_project(
        "SOC Dashboard - Blue Shield",
        client,
        consulting,
        soc_dashboard,
        None,
        ProjectStatus.PLANNING,
        "Definicion de requerimientos para SOC y tablero operativo.",
    )
    if orion_client:
        project_3 = upsert_project(
            "Network Monitoring - Orion",
            orion_client,
            implementation,
            network_monitoring,
            None,
            ProjectStatus.ACTIVE,
            "Despliegue de monitoreo y alertas de red en multiples sedes.",
        )
    else:
        project_3 = None
    if nova_client:
        project_4 = upsert_project(
            "Compliance Baseline - Nova",
            nova_client,
            consulting,
            compliance_baseline,
            None,
            ProjectStatus.PAUSED,
            "Evaluacion de compliance y plan de remediacion.",
        )
    else:
        project_4 = None
    project_5 = upsert_project(
        "Observability Pilot",
        client,
        support,
        None,
        observability_product,
        ProjectStatus.ACTIVE,
        "Piloto de observabilidad con agentes y paneles de salud.",
    )

    def upsert_member(
        project: Project | None,
        user: User,
        role_in_project: str,
        allocation: int,
        required: bool,
    ) -> None:
        if not project:
            return
        if db.scalar(
            select(ProjectMember).where(
                ProjectMember.project_id == project.id,
                ProjectMember.user_id == user.id,
            )
        ):
            return
        db.add(
            ProjectMember(
                project_id=project.id,
                user_id=user.id,
                role_in_project=role_in_project,
                allocation_percentage=allocation,
                can_publish_docs=True,
                assignment_type=AssignmentType.MANUAL,
                is_required=required,
            )
        )

    upsert_member(project_1, collaborator_2, "Lead Engineer", 70, True)
    upsert_member(project_1, collaborator_3, "Security Analyst", 40, True)
    upsert_member(project_1, collaborator, "SOC Analyst", 30, False)
    upsert_member(project_2, collaborator_6, "Threat Lead", 50, True)
    upsert_member(project_2, collaborator_3, "Security Analyst", 40, False)
    if project_3:
        upsert_member(project_3, collaborator_2, "Network Lead", 60, True)
        upsert_member(project_3, collaborator_5, "Cloud Engineer", 40, False)
    if project_4:
        upsert_member(project_4, collaborator_3, "Compliance Analyst", 40, True)
        upsert_member(project_4, collaborator_6, "Threat Analyst", 30, False)
    upsert_member(project_5, collaborator_4, "DevOps Lead", 60, True)
    upsert_member(project_5, collaborator_5, "Platform Engineer", 40, False)

    def upsert_requirement(
        project: Project | None, skill_name: str, level: str, required: bool
    ) -> None:
        if not project:
            return
        skill = db.scalar(select(Skill).where(Skill.name == skill_name))
        if not skill:
            return
        if db.scalar(
            select(ProjectRequirement).where(
                ProjectRequirement.project_id == project.id,
                ProjectRequirement.skill_id == skill.id,
            )
        ):
            return
        db.add(
            ProjectRequirement(
                project_id=project.id,
                skill_id=skill.id,
                level=level,
                is_required=required,
            )
        )

    upsert_requirement(project_1, "Redes", "Senior", True)
    upsert_requirement(project_1, "FortiGate", "Mid", True)
    upsert_requirement(project_1, "Ciberseguridad", "Mid", False)
    upsert_requirement(project_2, "SOC", "Mid", True)
    upsert_requirement(project_2, "Threat Hunting", "Mid", False)
    upsert_requirement(project_3, "Redes", "Senior", True)
    upsert_requirement(project_3, "SIEM", "Mid", False)
    upsert_requirement(project_4, "Incident Response", "Mid", False)
    upsert_requirement(project_5, "DevOps", "Senior", True)
    upsert_requirement(project_5, "Kubernetes", "Mid", True)

    db.commit()

    pfsense_integration = db.scalar(
        select(Integration).where(Integration.name == "pfSense Main Edge")
    )

    if pfsense_integration and not db.scalar(
        select(Report).where(Report.title == "Reporte Ejecutivo Mensual")
    ):
        db.add(
            Report(
                organization_id=organization.id,
                client_id=client.id,
                integration_id=pfsense_integration.id,
                created_by=admin.id,
                title="Reporte Ejecutivo Mensual",
                report_type="executive",
                template_name="executive-v1",
                definition_json='{"widgets":["traffic","vpn","uptime"]}',
            )
        )

    db.commit()

    demo_application = db.scalar(
        select(JobApplication).where(JobApplication.email == "talent@ninjasec.local")
    )
    if not demo_application:
        demo_application = JobApplication(
            full_name="Carlos Bravo",
            email="talent@ninjasec.local",
            phone="+51 999 111 222",
            desired_role="SOC Analyst",
            skills_summary="SOC, SIEM, incident response",
            cv_url="https://example.com/cv/carlos-bravo.pdf",
            portfolio_url="https://example.com/portfolio/carlos-bravo",
            status=JobApplicationStatus.NEW,
            source="web",
        )
        db.add(demo_application)
        db.commit()
        db.refresh(demo_application)

    demo_application_2 = db.scalar(
        select(JobApplication).where(JobApplication.email == "talent2@ninjasec.local")
    )
    if not demo_application_2:
        demo_application_2 = JobApplication(
            full_name="Lucia Vargas",
            email="talent2@ninjasec.local",
            phone="+51 999 222 333",
            desired_role="Network Engineer",
            skills_summary="Routing, switching, FortiGate",
            cv_url="https://example.com/cv/lucia-vargas.pdf",
            portfolio_url="https://example.com/portfolio/lucia-vargas",
            status=JobApplicationStatus.SCREENING,
            source="referral",
        )
        db.add(demo_application_2)
        db.commit()
        db.refresh(demo_application_2)

    assignment_exists = db.scalar(
        select(ApplicationAssignment).where(
            ApplicationAssignment.application_id == demo_application.id,
            ApplicationAssignment.reviewer_user_id == collaborator.id,
        )
    )
    if not assignment_exists:
        db.add(
            ApplicationAssignment(
                application_id=demo_application.id,
                reviewer_user_id=collaborator.id,
                assigned_by_user_id=admin.id,
                role="reviewer",
                assigned_at=utcnow(),
            )
        )

    assignment_exists_2 = db.scalar(
        select(ApplicationAssignment).where(
            ApplicationAssignment.application_id == demo_application_2.id,
            ApplicationAssignment.reviewer_user_id == collaborator_2.id,
        )
    )
    if not assignment_exists_2:
        db.add(
            ApplicationAssignment(
                application_id=demo_application_2.id,
                reviewer_user_id=collaborator_2.id,
                assigned_by_user_id=admin.id,
                role="reviewer",
                assigned_at=utcnow(),
            )
        )

    # 29-P1 -- seed mínimo del catálogo de equipos, solo para poder probar
    # los filtros facetados. No pretende ser un catálogo real completo.
    catalog_seed = [
        dict(
            slug="cisco-catalyst-2960x", brand="Cisco", model="Catalyst 2960-X",
            category="switch", subcategory="access", osi_layer="L2", segment="enterprise",
            port_count=24, port_speed="1G", poe=True, poe_budget_w=370,
            stackable=True, rack_mountable=True, managed=True,
            switching_capacity_gbps=88.0, power_consumption_w=64,
            lifecycle_status="active", price_range_usd="1500-2500",
            use_cases="Distribución de acceso en oficinas medianas",
            tags="cisco,switch,poe,stackable",
            datasheet_url="https://www.cisco.com/c/en/us/products/switches/catalyst-2960-x-series-switches/index.html",
        ),
        dict(
            slug="mikrotik-ccr2004-1g", brand="MikroTik", model="CCR2004-1G-12S+2XS",
            category="router", subcategory="core", osi_layer="L3", segment="smb",
            port_count=14, port_speed="mixed", poe=False, stackable=False,
            rack_mountable=True, managed=True, throughput_mbps=8000,
            power_consumption_w=60, lifecycle_status="active",
            price_range_usd="700-900", use_cases="Router de borde para ISP pequeños",
            tags="mikrotik,router,routeros",
            datasheet_url="https://mikrotik.com/product/ccr2004_1g_12s_2xs",
        ),
        dict(
            slug="cisco-asa-5505", brand="Cisco", model="ASA 5505",
            category="firewall", subcategory="edge", osi_layer="L3", segment="soho",
            port_count=8, port_speed="100M", poe=False, stackable=False,
            rack_mountable=False, managed=True, power_consumption_w=25,
            lifecycle_status="eol", eos_date=date(2013, 9, 1), eol_date=date(2018, 9, 1),
            price_range_usd="200-400",
            use_cases="Firewall perimetral para oficinas pequeñas (descontinuado)",
            tags="cisco,firewall,eol",
            datasheet_url="https://www.cisco.com/c/en/us/support/security/asa-5505-adaptive-security-appliance/series.html",
        ),
        dict(
            slug="ubiquiti-unifi-ap-ac-pro", brand="Ubiquiti", model="UniFi AP AC Pro",
            category="access_point", subcategory="access", osi_layer="L2", segment="smb",
            poe=True, poe_budget_w=15, managed=True, throughput_mbps=1300,
            power_consumption_w=9, lifecycle_status="active",
            price_range_usd="150-200", use_cases="Wi-Fi gestionado para pymes",
            tags="ubiquiti,wifi,poe,unifi",
            datasheet_url="https://store.ui.com/us/en/products/unifi-ap-ac-pro",
        ),
    ]
    for entry in catalog_seed:
        if not db.scalar(select(CatalogDevice).where(CatalogDevice.slug == entry["slug"])):
            db.add(CatalogDevice(**entry))

    db.commit()

    seed_compliance_catalog(db)
    seed_risk_catalog(db)
    seed_hardening_catalog(db)
    seed_netdoctor_catalog(db)
    seed_module_demo_records(db)


def seed_compliance_catalog(db: Session) -> None:
    """24-P1 -- carga el catálogo de los 93 controles del Anexo A de ISO
    27001:2022. Idempotente: compara por código, no duplica si se llama
    de nuevo."""
    from app.modules.compliance.iso27001_2022 import ISO_27001_2022_CONTROLS

    framework = db.scalar(
        select(ComplianceFramework).where(ComplianceFramework.slug == "iso-27001-2022")
    )
    if framework is None:
        framework = ComplianceFramework(
            name="ISO/IEC 27001", version="2022", slug="iso-27001-2022"
        )
        db.add(framework)
        db.flush()

    existing_codes = set(
        db.scalars(
            select(ComplianceControl.code).where(
                ComplianceControl.framework_id == framework.id
            )
        ).all()
    )
    for code, category, title in ISO_27001_2022_CONTROLS:
        if code in existing_codes:
            continue
        db.add(
            ComplianceControl(
                framework_id=framework.id,
                code=code,
                parent_code=code.rsplit(".", 1)[0],
                category=category,
                title=title,
            )
        )
    db.commit()


_RISK_THREATS_SEED = [
    ("T-DEL-01", "Acceso lógico no autorizado", "Deliberada", "Uso de credenciales robadas o débiles para entrar a un sistema"),
    ("T-DEL-02", "Malware / ransomware", "Deliberada", "Software malicioso que compromete confidencialidad, integridad o disponibilidad"),
    ("T-DEL-03", "Ingeniería social / phishing", "Deliberada", "Manipulación de personal para obtener acceso o información"),
    ("T-DEL-04", "Denegación de servicio (DoS/DDoS)", "Deliberada", "Saturación deliberada de un servicio o recurso"),
    ("T-DEL-05", "Exfiltración de datos", "Deliberada", "Sustracción intencional de información sensible"),
    ("T-ACC-01", "Error humano de configuración", "Accidental", "Cambios de configuración incorrectos por descuido u omisión"),
    ("T-ACC-02", "Pérdida o daño de equipo", "Accidental", "Extravío, robo o daño físico de dispositivos con información"),
    ("T-ACC-03", "Fallo de hardware", "Accidental", "Falla física de un componente crítico de infraestructura"),
    ("T-AMB-01", "Corte de energía eléctrica", "Ambiental", "Interrupción del suministro eléctrico que afecta disponibilidad"),
    ("T-AMB-02", "Desastre natural", "Ambiental", "Sismo, inundación u otro evento que dañe infraestructura física"),
]

_RISK_VULNERABILITIES_SEED = [
    ("V-TEC-01", "Software sin parches de seguridad", "Técnica", "Versiones desactualizadas con vulnerabilidades conocidas (CVE)"),
    ("V-TEC-02", "Contraseñas débiles o por defecto", "Técnica", "Credenciales fáciles de adivinar o nunca rotadas"),
    ("V-TEC-03", "Falta de cifrado en tránsito o reposo", "Técnica", "Datos sensibles expuestos sin protección criptográfica"),
    ("V-TEC-04", "Ausencia de segmentación de red", "Técnica", "Un compromiso puntual se propaga sin restricción lateral"),
    ("V-TEC-05", "Puertos de administración expuestos", "Técnica", "Servicios de gestión accesibles sin lista blanca ni VPN"),
    ("V-ORG-01", "Falta de respaldo verificado", "Organizacional", "Copias de seguridad inexistentes o nunca restauradas en pruebas"),
    ("V-ORG-02", "Sin plan de respuesta a incidentes", "Organizacional", "No hay procedimiento definido ante un incidente de seguridad"),
    ("V-ORG-03", "Falta de capacitación del personal", "Organizacional", "Usuarios sin formación en buenas prácticas de seguridad"),
    ("V-FIS-01", "Control de acceso físico débil", "Física", "Centros de datos o racks accesibles sin control adecuado"),
    ("V-FIS-02", "Sin redundancia de energía", "Física", "Ausencia de UPS o generador ante corte eléctrico"),
]


def seed_risk_catalog(db: Session) -> None:
    """25-P2 -- catálogo global reutilizable de amenazas/vulnerabilidades
    (ISO 27005/MAGERIT). Idempotente: compara por código."""
    existing_threats = set(db.scalars(select(Threat.code).where(Threat.organization_id.is_(None))).all())
    for code, name, category, description in _RISK_THREATS_SEED:
        if code in existing_threats:
            continue
        db.add(Threat(code=code, name=name, category=category, description=description, is_global=True, organization_id=None))

    existing_vulns = set(db.scalars(select(Vulnerability.code).where(Vulnerability.organization_id.is_(None))).all())
    for code, name, category, description in _RISK_VULNERABILITIES_SEED:
        if code in existing_vulns:
            continue
        db.add(Vulnerability(code=code, name=name, category=category, description=description, is_global=True, organization_id=None))

    db.commit()


def seed_module_demo_records(db: Session) -> None:
    """Issue #66 -- los módulos 24/25/26/27 (compliance, riesgos, auditorías,
    arquitectura) solo tenían catálogo global sembrado; ningún cliente de
    demo tenía registros propios, así que las cuatro pantallas se veían
    vacías. Agrega datos reales para los 3 clientes base (Blue Shield Tech,
    Orion Logistics, Nova Retail) creados más arriba en este mismo archivo.
    Idempotente: cada bloque comprueba si el cliente ya tiene datos antes
    de insertar."""
    organization = db.scalar(select(Organization).where(Organization.slug == "ninjasec-internal"))
    if not organization:
        return
    admin_ops = db.scalar(select(User).where(User.email == "ops@ninjasec.local"))
    clients = {
        c.company_name: c
        for c in db.scalars(
            select(Client).where(Client.company_name.in_(["Blue Shield Tech", "Orion Logistics", "Nova Retail"]))
        ).all()
    }
    if not admin_ops or not clients:
        return

    # ── Compliance (24): estado de una docena de controles por cliente ──
    framework = db.scalar(select(ComplianceFramework).where(ComplianceFramework.slug == "iso-27001-2022"))
    if framework:
        control_codes = ["A.5.1", "A.5.9", "A.5.15", "A.5.23", "A.6.3", "A.7.4", "A.8.8", "A.8.16", "A.8.24"]
        controls = {
            c.code: c
            for c in db.scalars(
                select(ComplianceControl).where(ComplianceControl.framework_id == framework.id, ComplianceControl.code.in_(control_codes))
            ).all()
        }
        demo_status = [
            ("implemented", "applicable", 4, None),
            ("implemented", "applicable", 3, None),
            ("partial", "applicable", 2, "En progreso: falta cobertura en sedes remotas"),
            ("not_implemented", "applicable", 0, None),
            ("not_applicable", "not_applicable", 0, "Cliente no usa proveedores cloud externos"),
        ]
        for client in clients.values():
            if db.scalar(select(ClientControlStatus).where(ClientControlStatus.client_id == client.id)):
                continue
            for i, code in enumerate(control_codes):
                control = controls.get(code)
                if not control:
                    continue
                status, applicability, maturity, justification = demo_status[i % len(demo_status)]
                db.add(ClientControlStatus(
                    client_id=client.id, control_id=control.id,
                    applicability=applicability, implementation_status=status,
                    maturity_level=maturity, justification=justification,
                    responsible_user_id=admin_ops.id,
                ))

    # ── Riesgos (25): un activo y varios riesgos repartidos en el mapa de calor ──
    threats = list(db.scalars(select(Threat).where(Threat.is_global.is_(True)).order_by(Threat.code)).all())
    vulns = list(db.scalars(select(Vulnerability).where(Vulnerability.is_global.is_(True)).order_by(Vulnerability.code)).all())
    risk_positions = [(4, 5, "Exposición de datos de clientes"), (2, 3, "Configuración por defecto en switch de borde"), (5, 2, "Dependencia de proveedor único de conectividad")]
    for idx, client in enumerate(clients.values()):
        if db.scalar(select(Risk).where(Risk.client_id == client.id)):
            continue
        asset = RiskAsset(
            client_id=client.id, name="Servidor de aplicaciones principal", asset_type="hardware",
            confidentiality=4, integrity=4, availability=3, business_value=4,
        )
        db.add(asset)
        db.flush()
        for j, (likelihood, impact, title) in enumerate(risk_positions):
            risk = Risk(
                client_id=client.id, asset_id=asset.id, title=title,
                likelihood=likelihood, impact=impact, inherent_score=likelihood * impact,
                status="identified" if j else "assessed",
            )
            if threats:
                risk.threats = [threats[(idx + j) % len(threats)]]
            if vulns:
                risk.vulnerabilities = [vulns[(idx + j) % len(vulns)]]
            db.add(risk)

    # ── Auditorías (26): un encargo por cliente ──
    audit_seed = [
        ("Blue Shield Tech", "AUD-DEMO-BST-01", "Auditoría interna SGSI 2026", "iso_27001", "internal", "in_progress"),
        ("Orion Logistics", "AUD-DEMO-ORN-01", "Auditoría de controles de acceso", "cobit_2019", "internal", "planned"),
        ("Nova Retail", "AUD-DEMO-NVA-01", "Auditoría de cumplimiento PCI-adyacente", "custom", "external", "planned"),
    ]
    for company, code, title, framework_code, audit_type, status in audit_seed:
        client = clients.get(company)
        if not client or db.scalar(select(Audit).where(Audit.organization_id == organization.id, Audit.code == code)):
            continue
        db.add(Audit(
            organization_id=organization.id, client_id=client.id, code=code, title=title,
            objective="Evaluar el nivel de cumplimiento y la efectividad de los controles vigentes.",
            scope="Sedes principales y activos críticos del cliente.",
            framework=framework_code, audit_type=audit_type, lead_auditor_id=admin_ops.id, status=status,
        ))

    # ── Arquitectura (27): un modelo simple por cliente ──
    for client in clients.values():
        if db.scalar(select(ArchitectureModel).where(ArchitectureModel.client_id == client.id)):
            continue
        model = ArchitectureModel(
            organization_id=organization.id, client_id=client.id, name=f"Arquitectura actual — {client.company_name}",
            version="1.0", state="baseline", adm_phase="B", status="draft",
        )
        db.add(model)
        db.flush()
        firewall = ArchitectureElement(model_id=model.id, layer="technology", element_type="node", name="Firewall perimetral")
        app_server = ArchitectureElement(model_id=model.id, layer="application", element_type="application_component", name="Sistema de gestión interno")
        business_process = ArchitectureElement(model_id=model.id, layer="business", element_type="business_process", name="Operación diaria del cliente")
        db.add_all([firewall, app_server, business_process])
        db.flush()
        db.add_all([
            ArchitectureRelationship(model_id=model.id, source_element_id=firewall.id, target_element_id=app_server.id, relationship_type="serving", label="protege"),
            ArchitectureRelationship(model_id=model.id, source_element_id=app_server.id, target_element_id=business_process.id, relationship_type="serving", label="soporta"),
        ])

    db.commit()


_HARDENING_RULES_SEED = [
    ("H-01", "Firewall perimetral integrado y activo", "Perímetro y detección", "high",
     "El cliente debe tener al menos una integración de firewall (pfSense/FortiGate) en estado conectado.",
     "auto", "has_firewall_integration"),
    ("H-02", "Sistema de detección/monitoreo (SIEM) integrado", "Perímetro y detección", "high",
     "El cliente debe tener una integración Wazuh (o SIEM equivalente) en estado conectado.",
     "auto", "has_siem_integration"),
    ("H-03", "Recolección de eventos activa en los últimos 30 días", "Perímetro y detección", "medium",
     "Debe existir al menos una recolección de datos reciente sobre alguna integración del cliente.",
     "auto", "recent_collection"),
    ("H-04", "Sin eventos de fuerza bruta sin atender", "Gestión de incidentes", "critical",
     "No deben existir eventos de autenticación de severidad crítica sin resolver.",
     "auto", "no_critical_auth_events"),
    ("H-05", "Sin eventos de malware de severidad alta/crítica sin atender", "Gestión de incidentes", "critical",
     "No deben existir eventos de malware de severidad alta o crítica sin resolver.",
     "auto", "no_critical_malware_events"),
    ("H-06", "Política de contraseñas documentada y aplicada", "Identidad y accesos", "high",
     "Requiere revisión manual de la política de contraseñas vigente del cliente.",
     "manual", None),
    ("H-07", "Autenticación multifactor habilitada para accesos administrativos", "Identidad y accesos", "high",
     "Requiere confirmación manual de que MFA está activo en accesos privilegiados.",
     "manual", None),
    ("H-08", "Revisión periódica de cuentas con privilegios elevados", "Identidad y accesos", "medium",
     "Requiere evidencia manual de una revisión de cuentas privilegiadas en los últimos 90 días.",
     "manual", None),
    ("H-09", "Copias de respaldo con prueba de restauración reciente", "Continuidad", "high",
     "Requiere evidencia manual de una prueba de restauración de backup exitosa.",
     "manual", None),
    ("H-10", "Plan de continuidad/DRP documentado", "Continuidad", "medium",
     "Requiere confirmación manual de la existencia de un plan de recuperación ante desastres.",
     "manual", None),
    ("H-11", "Capacitación de concientización en seguridad realizada", "Concientización", "medium",
     "Requiere evidencia manual de capacitación reciente al personal del cliente.",
     "manual", None),
    ("H-12", "Control de acceso físico a infraestructura crítica", "Físico", "medium",
     "Requiere verificación manual in situ del control de acceso físico.",
     "manual", None),
]


def seed_hardening_catalog(db: Session) -> None:
    """31-P1 -- catálogo global de reglas de hardening técnico (estilo CIS
    Benchmarks). Idempotente por código."""
    existing = set(db.scalars(select(HardeningRule.code)).all())
    for code, title, category, severity, description, method, check_key in _HARDENING_RULES_SEED:
        if code in existing:
            continue
        db.add(HardeningRule(
            code=code, title=title, category=category, severity=severity,
            description=description, verification_method=method, check_key=check_key,
        ))
    db.commit()


_NETDOCTOR_ISSUES_SEED = [
    (
        "ND-IPCONF", "Conflicto de direcciones IP duplicadas", "Direccionamiento", "high",
        "Dos o más dispositivos pierden conectividad intermitentemente; el sistema operativo del host muestra una advertencia de 'IP address conflict'.",
        "Asignación estática manual duplicada, o un servidor DHCP entregando una IP que ya está reservada estáticamente.",
        {
            "cisco_ios": "show ip arp | include <ip>",
            "mikrotik": "/ip arp print where address=\"<ip>\"",
            "huawei": "display arp | include <ip>",
            "ubiquiti": "ip neigh show | grep <ip>",
        },
        "Reasignar la IP en conflicto, documentar el rango estático reservado, y excluirlo del pool DHCP.",
    ),
    (
        "ND-NOCONN", "Sin conectividad de red (host inalcanzable)", "Conectividad", "critical",
        "El host no responde a ping ni a ningún tráfico; el switch no muestra el puerto como up.",
        "Cable defectuoso, puerto administrativamente apagado, VLAN incorrecta, o NIC deshabilitada en el host.",
        {
            "cisco_ios": "show interfaces status",
            "mikrotik": "/interface print stats",
            "huawei": "display interface brief",
            "ubiquiti": "ifconfig",
        },
        "Verificar el cable físico, confirmar que el puerto está en 'no shutdown', y validar la VLAN asignada.",
    ),
    (
        "ND-SLOWPERF", "Rendimiento de red lento", "Rendimiento", "medium",
        "Transferencias de archivos y navegación notablemente más lentas de lo esperado, sin pérdida total de conectividad.",
        "Saturación de ancho de banda, duplex mismatch, o un enlace operando por debajo de su velocidad nominal.",
        {
            "cisco_ios": "show interfaces | include rate|duplex",
            "mikrotik": "/interface monitor-traffic interface=<if> once",
            "huawei": "display interface <if> | include rate",
            "ubiquiti": "ethtool <if>",
        },
        "Confirmar velocidad/dúplex negociados, identificar el proceso o host que satura el enlace, y considerar QoS.",
    ),
    (
        "ND-LATLOSS", "Latencia alta o pérdida de paquetes", "Rendimiento", "high",
        "Ping muestra tiempos de respuesta elevados o pérdida de paquetes intermitente entre dos puntos.",
        "Congestión de un enlace intermedio, errores CRC acumulados, o una ruta subóptima.",
        {
            "cisco_ios": "show interfaces | include CRC|input errors",
            "mikrotik": "/tool traceroute <destino>",
            "huawei": "display interface <if> | include CRC",
            "ubiquiti": "mtr <destino>",
        },
        "Correr traceroute/mtr para ubicar el salto problemático, revisar contadores de error de interfaz, reemplazar cableado si hay CRC.",
    ),
    (
        "ND-DNSFAIL", "Fallo de resolución DNS", "Servicios", "medium",
        "El host tiene conectividad IP (ping por dirección funciona) pero no puede resolver nombres de dominio.",
        "Servidor DNS inalcanzable, configuración de DNS incorrecta en el host, o firewall bloqueando el puerto 53.",
        {
            "cisco_ios": "show hosts",
            "mikrotik": "/ip dns print",
            "huawei": "display dns server",
            "ubiquiti": "cat /etc/resolv.conf",
        },
        "Verificar el servidor DNS configurado, probar resolución directa contra un DNS público (8.8.8.8), revisar reglas de firewall en el puerto 53.",
    ),
    (
        "ND-DHCPFAIL", "Cliente no obtiene IP por DHCP", "Servicios", "high",
        "El host queda con una IP APIPA (169.254.x.x) o sin IP asignada al conectarse a la red.",
        "Servidor DHCP caído, pool agotado, o el puerto del switch no reenvía tráfico DHCP (VLAN/relay mal configurado).",
        {
            "cisco_ios": "show ip dhcp pool",
            "mikrotik": "/ip dhcp-server print",
            "huawei": "display dhcp server pool",
            "ubiquiti": "dhclient -v <if>",
        },
        "Confirmar que el servicio DHCP está activo, revisar el tamaño del pool, y validar el DHCP relay si el cliente está en otra VLAN.",
    ),
    (
        "ND-VLANMIS", "Dispositivo en VLAN incorrecta", "VLAN", "medium",
        "El dispositivo tiene conectividad física pero no alcanza recursos que debería (está lógicamente en otra red).",
        "Puerto de acceso asignado a la VLAN equivocada.",
        {
            "cisco_ios": "show vlan brief",
            "mikrotik": "/interface bridge vlan print",
            "huawei": "display vlan",
            "ubiquiti": "bridge vlan show",
        },
        "Reasignar el puerto a la VLAN correcta con `switchport access vlan <id>` (o equivalente) y confirmar con `show vlan brief`.",
    ),
    (
        "ND-TRUNKMIS", "Puerto trunk mal configurado", "VLAN", "high",
        "Varias VLANs completas pierden conectividad entre switches, aunque cada switch individualmente funciona.",
        "El puerto trunk no permite las VLANs necesarias, o la VLAN nativa no coincide entre ambos extremos del enlace.",
        {
            "cisco_ios": "show interfaces trunk",
            "mikrotik": "/interface bridge vlan print",
            "huawei": "display port vlan",
            "ubiquiti": "bridge vlan show",
        },
        "Verificar la lista de VLANs permitidas en ambos extremos del trunk y que la VLAN nativa coincida en los dos switches.",
    ),
    (
        "ND-GWDOWN", "Gateway por defecto inalcanzable", "Direccionamiento", "critical",
        "El host puede alcanzar otros dispositivos en su misma subred pero no puede salir de ella.",
        "El router/firewall que actúa como gateway está caído, o la IP de gateway configurada en el host es incorrecta.",
        {
            "cisco_ios": "show ip route 0.0.0.0",
            "mikrotik": "/ip route print where dst-address=0.0.0.0/0",
            "huawei": "display ip routing-table",
            "ubiquiti": "ip route show default",
        },
        "Confirmar que el gateway responde a ping, validar la IP de gateway configurada en el host, revisar el estado del router.",
    ),
    (
        "ND-PORTDOWN", "Puerto físico caído / no negocia enlace", "Físico", "high",
        "El LED del puerto no enciende o parpadea en ámbar; la interfaz aparece como 'down/down'.",
        "Cable dañado, transceptor SFP defectuoso, o el puerto está deshabilitado administrativamente.",
        {
            "cisco_ios": "show interfaces status err-disabled",
            "mikrotik": "/interface ethernet print stats",
            "huawei": "display interface brief",
            "ubiquiti": "ethtool <if>",
        },
        "Probar con un cable/puerto conocido bueno, revisar si el puerto quedó en estado err-disabled y reactivarlo tras resolver la causa raíz.",
    ),
    (
        "ND-DUPLEX", "Discordancia de dúplex (half/full)", "Físico", "medium",
        "Rendimiento muy degradado con muchos errores de colisión tardía en un enlace específico.",
        "Un extremo del enlace está fijado a full-duplex y el otro a half-duplex (o auto-negociación deshabilitada en uno solo).",
        {
            "cisco_ios": "show interfaces | include duplex",
            "mikrotik": "/interface ethernet monitor <if> once",
            "huawei": "display interface <if> | include Duplex",
            "ubiquiti": "ethtool <if> | grep Duplex",
        },
        "Igualar la configuración de dúplex y velocidad en ambos extremos, preferentemente dejando auto-negociación activa en los dos.",
    ),
    (
        "ND-STPLOOP", "Loop de capa 2 / tormenta de broadcast", "VLAN", "critical",
        "La red completa se vuelve inestable, alto uso de CPU en switches, luces de puertos parpadeando excesivamente.",
        "Un enlace redundante sin STP habilitado, o un cable conectado por error creando un bucle físico.",
        {
            "cisco_ios": "show spanning-tree summary",
            "mikrotik": "/interface bridge print",
            "huawei": "display stp brief",
            "ubiquiti": "mstpctl showall",
        },
        "Confirmar que STP/RSTP está habilitado en todos los switches, identificar y desconectar el enlace físico que causa el loop.",
    ),
    (
        "ND-ACLBLOCK", "Tráfico bloqueado por ACL", "Seguridad", "medium",
        "Un servicio específico falla (ej. un puerto TCP) mientras el resto del tráfico funciona con normalidad.",
        "Una ACL o regla de firewall bloquea el puerto/protocolo requerido por la aplicación.",
        {
            "cisco_ios": "show access-lists",
            "mikrotik": "/ip firewall filter print",
            "huawei": "display acl all",
            "ubiquiti": "iptables -L -n -v",
        },
        "Revisar las reglas en orden, identificar cuál bloquea el tráfico esperado, y agregar una regla de permiso específica en vez de deshabilitar la ACL completa.",
    ),
    (
        "ND-NATMIS", "Traducción NAT incorrecta", "Direccionamiento", "medium",
        "Un servicio publicado hacia internet no es alcanzable externamente, aunque funciona correctamente desde la LAN.",
        "Regla de NAT/port-forwarding mal configurada, o la IP interna del servidor cambió sin actualizar la regla.",
        {
            "cisco_ios": "show ip nat translations",
            "mikrotik": "/ip firewall nat print",
            "huawei": "display nat session all",
            "ubiquiti": "iptables -t nat -L -n -v",
        },
        "Verificar que la regla de NAT apunta a la IP interna vigente del servidor y que el puerto externo coincide con lo publicado.",
    ),
]


def seed_netdoctor_catalog(db: Session) -> None:
    """28-P1 -- catálogo global de problemas comunes de networking, con
    comandos de diagnóstico por vendor. Idempotente por código."""
    existing = set(db.scalars(select(NetdoctorIssue.code)).all())
    for code, title, category, severity, symptoms, causes, commands, remediation in _NETDOCTOR_ISSUES_SEED:
        if code in existing:
            continue
        db.add(NetdoctorIssue(
            code=code, title=title, category=category, severity=severity,
            symptoms=symptoms, probable_causes=causes,
            diagnostic_commands=commands, remediation=remediation,
        ))
    db.commit()
