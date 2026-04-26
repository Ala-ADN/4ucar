"""KPI field master dictionary — single source of truth for all ingestion mapping.

Every field has: identifier, French label, aliases (FR + abbreviated + Arabic),
expected data type, whether required for its domain, and optional bounds.

PROTOTYPE ONLY — Claude API used for column mapping demo purposes.
Production replacement: intfloat/multilingual-e5-large sentence embeddings
running locally on UCAR servers. Pre-compute embeddings for all KPI field
aliases at startup. At mapping time, encode column header and find nearest
neighbor by cosine similarity. Zero external calls, full data sovereignty.
Ollama + Mistral 7B as secondary fallback for ambiguous cases.
No code changes required in callers — same interface, different implementation.
"""

from dataclasses import dataclass, field
from typing import Literal

DataType = Literal["integer", "float", "percentage"]
Domain = Literal["academic", "finance", "operational", "environmental"]


@dataclass
class KpiField:
    identifier: str
    label_fr: str
    domain: Domain
    data_type: DataType
    required: bool
    aliases: list[str] = field(default_factory=list)
    min_value: float | None = None
    max_value: float | None = None


KPI_FIELDS: dict[str, KpiField] = {
    # ── ACADEMIC ─────────────────────────────────────────────────────────────
    "enrollment_total": KpiField(
        identifier="enrollment_total",
        label_fr="Effectif total des étudiants inscrits",
        domain="academic",
        data_type="integer",
        required=True,
        aliases=[
            "effectif total", "total inscrits", "nombre d'étudiants", "inscrits",
            "effectif", "etudiants inscrits", "nb etudiants", "total étudiants",
            "العدد الإجمالي للطلاب", "الطلاب المسجلون", "إجمالي الطلاب",
        ],
        min_value=0,
    ),
    "enrollment_male": KpiField(
        identifier="enrollment_male",
        label_fr="Effectif masculin",
        domain="academic",
        data_type="integer",
        required=False,
        aliases=[
            "effectif masculin", "hommes", "garçons", "étudiants masculins",
            "inscrits masculins", "الذكور", "الطلاب الذكور",
        ],
        min_value=0,
    ),
    "enrollment_female": KpiField(
        identifier="enrollment_female",
        label_fr="Effectif féminin",
        domain="academic",
        data_type="integer",
        required=False,
        aliases=[
            "effectif féminin", "femmes", "filles", "étudiantes", "inscrits féminins",
            "الإناث", "الطالبات",
        ],
        min_value=0,
    ),
    "success_rate": KpiField(
        identifier="success_rate",
        label_fr="Taux de réussite",
        domain="academic",
        data_type="percentage",
        required=True,
        aliases=[
            "taux de réussite", "taux réussite", "réussite", "% réussite",
            "taux de succès", "succès", "taux de passage",
            "نسبة النجاح", "معدل النجاح", "النجاح",
        ],
        min_value=0,
        max_value=100,
    ),
    "dropout_rate": KpiField(
        identifier="dropout_rate",
        label_fr="Taux d'abandon",
        domain="academic",
        data_type="percentage",
        required=True,
        aliases=[
            "taux d'abandon", "taux abandon", "abandon", "% abandon",
            "décrochage", "taux de décrochage",
            "نسبة التسرب", "معدل الانقطاع", "الانقطاع",
        ],
        min_value=0,
        max_value=100,
    ),
    "repetition_rate": KpiField(
        identifier="repetition_rate",
        label_fr="Taux de redoublement",
        domain="academic",
        data_type="percentage",
        required=True,
        aliases=[
            "taux de redoublement", "redoublement", "% redoublement",
            "taux redoublement", "redoublants",
            "نسبة الإعادة", "معدل الرسوب", "الرسوب",
        ],
        min_value=0,
        max_value=100,
    ),
    "attendance_rate": KpiField(
        identifier="attendance_rate",
        label_fr="Taux de présence",
        domain="academic",
        data_type="percentage",
        required=False,
        aliases=[
            "taux de présence", "présence", "assiduité", "taux assiduité",
            "% présence", "taux de fréquentation",
            "نسبة الحضور", "معدل الحضور", "الحضور",
        ],
        min_value=0,
        max_value=100,
    ),
    "student_teacher_ratio": KpiField(
        identifier="student_teacher_ratio",
        label_fr="Ratio étudiants/enseignants",
        domain="academic",
        data_type="float",
        required=False,
        aliases=[
            "ratio étudiants enseignants", "ratio étudiant/enseignant",
            "taux encadrement", "encadrement", "ratio e/e",
            "نسبة الطلاب للأساتذة", "نسبة التأطير",
        ],
        min_value=0,
    ),
    "exam_session_results": KpiField(
        identifier="exam_session_results",
        label_fr="Résultats par session d'examen",
        domain="academic",
        data_type="percentage",
        required=False,
        aliases=[
            "résultats session", "session principale", "session contrôle",
            "résultats examens", "session rattrap",
            "نتائج الامتحانات", "نتائج الدورة",
        ],
        min_value=0,
        max_value=100,
    ),
    # ── FINANCE ──────────────────────────────────────────────────────────────
    "budget_allocated": KpiField(
        identifier="budget_allocated",
        label_fr="Budget alloué",
        domain="finance",
        data_type="float",
        required=True,
        aliases=[
            "budget alloué", "budget prévu", "dotation", "allocation budgétaire",
            "budget initial", "budget accordé", "crédits alloués",
            "الميزانية المخصصة", "الاعتمادات المفتوحة", "الميزانية",
        ],
        min_value=0,
    ),
    "budget_consumed": KpiField(
        identifier="budget_consumed",
        label_fr="Budget consommé",
        domain="finance",
        data_type="float",
        required=True,
        aliases=[
            "budget consommé", "dépenses réalisées", "consommation budgétaire",
            "montant consommé", "dépenses effectives", "réalisé",
            "الميزانية المستهلكة", "النفقات الفعلية", "المنجز",
        ],
        min_value=0,
    ),
    "budget_execution_rate": KpiField(
        identifier="budget_execution_rate",
        label_fr="Taux d'exécution budgétaire",
        domain="finance",
        data_type="percentage",
        required=False,
        aliases=[
            "taux d'exécution", "taux exécution", "exécution budgétaire",
            "% exécution", "taux de consommation",
            "نسبة تنفيذ الميزانية", "نسبة الإنجاز", "معدل التنفيذ",
        ],
        min_value=0,
        max_value=100,
    ),
    "cost_per_student": KpiField(
        identifier="cost_per_student",
        label_fr="Coût par étudiant",
        domain="finance",
        data_type="float",
        required=False,
        aliases=[
            "coût par étudiant", "dépense par étudiant", "coût unitaire étudiant",
            "cout étudiant",
            "التكلفة لكل طالب", "تكلفة الطالب",
        ],
        min_value=0,
    ),
    "external_funding": KpiField(
        identifier="external_funding",
        label_fr="Financements externes",
        domain="finance",
        data_type="float",
        required=False,
        aliases=[
            "financements externes", "ressources propres", "fonds externes",
            "financement extérieur", "recettes propres",
            "التمويل الخارجي", "الموارد الذاتية",
        ],
        min_value=0,
    ),
    # ── OPERATIONAL ──────────────────────────────────────────────────────────
    "teaching_staff_count": KpiField(
        identifier="teaching_staff_count",
        label_fr="Effectif enseignants",
        domain="operational",
        data_type="integer",
        required=True,
        aliases=[
            "effectif enseignants", "nombre enseignants", "enseignants", "corps enseignant",
            "personnel enseignant", "nb enseignants",
            "عدد الأساتذة", "الهيئة التدريسية", "الأساتذة",
        ],
        min_value=0,
    ),
    "admin_staff_count": KpiField(
        identifier="admin_staff_count",
        label_fr="Effectif personnel administratif",
        domain="operational",
        data_type="integer",
        required=False,
        aliases=[
            "effectif administratif", "personnel administratif", "admin", "agents",
            "personnels", "administratifs",
            "الموظفون الإداريون", "العمال الإداريون",
        ],
        min_value=0,
    ),
    "absenteeism_rate": KpiField(
        identifier="absenteeism_rate",
        label_fr="Taux d'absentéisme",
        domain="operational",
        data_type="percentage",
        required=False,
        aliases=[
            "taux d'absentéisme", "absentéisme", "% absentéisme",
            "taux absence personnel", "absences",
            "نسبة الغياب", "معدل الغياب",
        ],
        min_value=0,
        max_value=100,
    ),
    "training_hours": KpiField(
        identifier="training_hours",
        label_fr="Heures de formation",
        domain="operational",
        data_type="float",
        required=False,
        aliases=[
            "heures de formation", "formation continue", "heures formation",
            "heures de perfectionnement",
            "ساعات التكوين", "ساعات التدريب",
        ],
        min_value=0,
    ),
    "publications_count": KpiField(
        identifier="publications_count",
        label_fr="Nombre de publications",
        domain="operational",
        data_type="integer",
        required=False,
        aliases=[
            "publications", "nombre de publications", "articles", "travaux publiés",
            "publications scientifiques",
            "عدد المنشورات", "المقالات العلمية",
        ],
        min_value=0,
    ),
    "active_research_projects": KpiField(
        identifier="active_research_projects",
        label_fr="Projets de recherche actifs",
        domain="operational",
        data_type="integer",
        required=False,
        aliases=[
            "projets de recherche", "projets actifs", "recherche", "projets en cours",
            "المشاريع البحثية النشطة", "مشاريع البحث",
        ],
        min_value=0,
    ),
    "phd_students_enrolled": KpiField(
        identifier="phd_students_enrolled",
        label_fr="Doctorants inscrits",
        domain="operational",
        data_type="integer",
        required=False,
        aliases=[
            "doctorants", "étudiants en thèse", "inscrits en doctorat",
            "thésards", "étudiants doctorat",
            "طلاب الدكتوراه", "المسجلون في الدكتوراه",
        ],
        min_value=0,
    ),
    "active_partnerships": KpiField(
        identifier="active_partnerships",
        label_fr="Conventions de partenariat actives",
        domain="operational",
        data_type="integer",
        required=False,
        aliases=[
            "partenariats", "conventions", "accords de partenariat",
            "partenariats actifs", "conventions actives",
            "الشراكات النشطة", "الاتفاقيات",
        ],
        min_value=0,
    ),
    "student_mobility_count": KpiField(
        identifier="student_mobility_count",
        label_fr="Étudiants en mobilité",
        domain="operational",
        data_type="integer",
        required=False,
        aliases=[
            "mobilité étudiante", "étudiants mobilité", "échanges", "erasmus",
            "الطلاب في التنقل الدراسي",
        ],
        min_value=0,
    ),
    "classroom_count": KpiField(
        identifier="classroom_count",
        label_fr="Nombre de salles",
        domain="operational",
        data_type="integer",
        required=False,
        aliases=[
            "salles", "amphithéâtres", "salles de cours", "locaux pédagogiques",
            "عدد القاعات",
        ],
        min_value=0,
    ),
    "it_equipment_count": KpiField(
        identifier="it_equipment_count",
        label_fr="Équipements informatiques",
        domain="operational",
        data_type="integer",
        required=False,
        aliases=[
            "équipements informatiques", "postes informatiques", "ordinateurs",
            "matériel informatique", "parc informatique",
            "المعدات الإعلامية", "الحواسيب",
        ],
        min_value=0,
    ),
    # ── ENVIRONMENTAL ────────────────────────────────────────────────────────
    "energy_kwh": KpiField(
        identifier="energy_kwh",
        label_fr="Consommation d'énergie (kWh)",
        domain="environmental",
        data_type="float",
        required=True,
        aliases=[
            "consommation énergie", "énergie", "kwh", "consommation électrique",
            "électricité", "énergie consommée",
            "استهلاك الطاقة", "الطاقة الكهربائية", "الكيلوواط",
        ],
        min_value=0,
    ),
    "water_m3": KpiField(
        identifier="water_m3",
        label_fr="Consommation d'eau (m³)",
        domain="environmental",
        data_type="float",
        required=False,
        aliases=[
            "consommation eau", "eau", "m3", "m³", "volume eau",
            "استهلاك الماء", "الماء", "المياه",
        ],
        min_value=0,
    ),
    "recycling_kg": KpiField(
        identifier="recycling_kg",
        label_fr="Volume de recyclage (kg)",
        domain="environmental",
        data_type="float",
        required=False,
        aliases=[
            "recyclage", "déchets recyclés", "kg recyclage", "volume recyclé",
            "التدوير", "النفايات المعاد تدويرها",
        ],
        min_value=0,
    ),
    "carbon_footprint": KpiField(
        identifier="carbon_footprint",
        label_fr="Empreinte carbone estimée",
        domain="environmental",
        data_type="float",
        required=False,
        aliases=[
            "empreinte carbone", "co2", "bilan carbone", "émissions carbone",
            "البصمة الكربونية", "انبعاثات الكربون",
        ],
        min_value=0,
    ),
    "sustainability_initiatives": KpiField(
        identifier="sustainability_initiatives",
        label_fr="Initiatives de développement durable actives",
        domain="environmental",
        data_type="integer",
        required=False,
        aliases=[
            "initiatives développement durable", "initiatives durabilité",
            "projets verts", "actions environnementales",
            "مبادرات الاستدامة", "المبادرات البيئية",
        ],
        min_value=0,
    ),
}


def build_alias_map() -> dict[str, str]:
    """Return a flat dict mapping every alias (lowercase) → canonical field identifier.

    Used by the Claude prompt builder and the fuzzy fallback mapper.
    """
    alias_map: dict[str, str] = {}
    for field_id, kpi_field in KPI_FIELDS.items():
        alias_map[field_id.lower()] = field_id
        alias_map[kpi_field.label_fr.lower()] = field_id
        for alias in kpi_field.aliases:
            alias_map[alias.lower()] = field_id
    return alias_map


def fields_for_domain(domain: Domain) -> dict[str, KpiField]:
    return {k: v for k, v in KPI_FIELDS.items() if v.domain == domain}


def required_fields_for_domain(domain: Domain) -> list[str]:
    return [k for k, v in KPI_FIELDS.items() if v.domain == domain and v.required]
