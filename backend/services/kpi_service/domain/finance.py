"""Domain E - Finance & Resources KPI calculators (FIN-01..FIN-07).

All monetary values are TND (Tunisian Dinar). The dispatcher does not
currency-convert; the repository must normalise upstream.
"""

from __future__ import annotations

from collections.abc import Callable

from .inputs import (
    OPERATING_CATEGORIES,
    InstitutionFinanceInputs,
    RevenueSource,
    currently_enrolled,
)
from .result import KpiResult, build_kpi_result

DOMAIN = "FINANCE"


def _result(*, inputs: InstitutionFinanceInputs, **kw) -> KpiResult:
    return build_kpi_result(inputs, DOMAIN, **kw)


# ---------------------------------------------------------------------------
# FIN-01 Budget Execution Rate
# ---------------------------------------------------------------------------


def fin_01_budget_execution_rate(inputs: InstitutionFinanceInputs) -> KpiResult:
    lines = inputs.budget_lines
    classified = [
        ln for ln in lines if ln.allocated_tnd is not None and ln.actual_tnd is not None
    ]
    missing: list[str] = []
    warnings: list[str] = []

    if not lines:
        missing.append("budget_lines")
    if lines and not classified:
        missing.append("budget_lines.allocated_tnd / budget_lines.actual_tnd")
    if classified and len(classified) < len(lines):
        warnings.append(
            f"{len(lines) - len(classified)}/{len(lines)} budget lines "
            "missing allocated or actual"
        )

    if not classified:
        return _result(
            kpi_id="FIN-01",
            name="Budget Execution Rate",
            formula="100 * sum(actual_tnd) / sum(allocated_tnd)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"lines_with_data": 0},
        )

    allocated = sum(ln.allocated_tnd or 0.0 for ln in classified)
    actual = sum(ln.actual_tnd or 0.0 for ln in classified)
    if allocated == 0:
        return _result(
            kpi_id="FIN-01",
            name="Budget Execution Rate",
            formula="100 * sum(actual_tnd) / sum(allocated_tnd)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=["budget_lines.allocated_tnd (sum is zero)"],
            warnings=warnings,
            used={"lines_with_data": len(classified), "actual_tnd": actual},
        )

    value = 100.0 * actual / allocated
    return _result(
        kpi_id="FIN-01",
        name="Budget Execution Rate",
        formula="100 * sum(actual_tnd) / sum(allocated_tnd)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "lines_with_data": len(classified),
            "allocated_tnd": allocated,
            "actual_tnd": actual,
        },
    )


# ---------------------------------------------------------------------------
# FIN-02 Cost per Student
# ---------------------------------------------------------------------------


def fin_02_cost_per_student(inputs: InstitutionFinanceInputs) -> KpiResult:
    lines = inputs.budget_lines
    enrolled = currently_enrolled(inputs.students)
    missing: list[str] = []
    warnings: list[str] = []

    if not lines:
        missing.append("budget_lines")
    if not enrolled:
        if not inputs.students:
            missing.append("students")
        else:
            missing.append("students.status (enrolled denominator empty)")

    operating_lines = [
        ln
        for ln in lines
        if ln.actual_tnd is not None
        and (ln.category is None or ln.category in OPERATING_CATEGORIES)
    ]
    uncategorised = sum(1 for ln in lines if ln.category is None)
    if uncategorised:
        warnings.append(
            f"{uncategorised}/{len(lines)} budget lines lack a category - "
            "treated as operating expenditure"
        )

    if not operating_lines or not enrolled:
        return _result(
            kpi_id="FIN-02",
            name="Cost per Student",
            formula=(
                "sum(budget_lines.actual_tnd where category in operating) / "
                "count(currently enrolled students)"
            ),
            unit="TND/student",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={
                "operating_lines": len(operating_lines),
                "enrolled": len(enrolled),
            },
        )

    op_actual = sum(ln.actual_tnd or 0.0 for ln in operating_lines)
    value = op_actual / len(enrolled)
    return _result(
        kpi_id="FIN-02",
        name="Cost per Student",
        formula=(
            "sum(budget_lines.actual_tnd where category in operating) / "
            "count(currently enrolled students)"
        ),
        unit="TND/student",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "operating_categories": sorted(c.value for c in OPERATING_CATEGORIES),
            "operating_lines": len(operating_lines),
            "operating_actual_tnd": op_actual,
            "enrolled": len(enrolled),
        },
    )


# ---------------------------------------------------------------------------
# FIN-03 Research Funding Ratio - THE Research Income proxy
# ---------------------------------------------------------------------------


def fin_03_research_funding_ratio(inputs: InstitutionFinanceInputs) -> KpiResult:
    external = [
        p for p in inputs.funded_projects if p.is_external and p.amount_tnd is not None
    ]
    budget_with_alloc = [ln for ln in inputs.budget_lines if ln.allocated_tnd is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not inputs.funded_projects:
        missing.append("funded_projects")
    if not budget_with_alloc:
        if not inputs.budget_lines:
            missing.append("budget_lines")
        else:
            missing.append("budget_lines.allocated_tnd")

    if not external or not budget_with_alloc:
        return _result(
            kpi_id="FIN-03",
            name="Research Funding Ratio",
            formula="100 * sum(funded_projects.amount_tnd where is_external) / sum(budget_lines.allocated_tnd)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={
                "external_projects": len(external),
                "budget_lines_with_alloc": len(budget_with_alloc),
            },
        )

    research_income = sum(p.amount_tnd or 0.0 for p in external)
    total_budget = sum(ln.allocated_tnd or 0.0 for ln in budget_with_alloc)
    if total_budget == 0:
        return _result(
            kpi_id="FIN-03",
            name="Research Funding Ratio",
            formula="100 * sum(funded_projects.amount_tnd where is_external) / sum(budget_lines.allocated_tnd)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=["budget_lines.allocated_tnd (sum is zero)"],
            warnings=warnings,
            used={"research_income_tnd": research_income},
        )

    value = 100.0 * research_income / total_budget
    return _result(
        kpi_id="FIN-03",
        name="Research Funding Ratio",
        formula="100 * sum(funded_projects.amount_tnd where is_external) / sum(budget_lines.allocated_tnd)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "external_projects": len(external),
            "research_income_tnd": research_income,
            "total_budget_tnd": total_budget,
        },
    )


# ---------------------------------------------------------------------------
# FIN-04 Revenue Diversification Index
# ---------------------------------------------------------------------------


def fin_04_revenue_diversification(inputs: InstitutionFinanceInputs) -> KpiResult:
    lines = inputs.revenue_lines
    classified = [
        r for r in lines if r.amount_tnd is not None and r.source is not None
    ]
    missing: list[str] = []
    warnings: list[str] = []

    if not lines:
        missing.append("revenue_lines")
    if lines and not classified:
        missing.append("revenue_lines.source / revenue_lines.amount_tnd")
    if classified and len(classified) < len(lines):
        warnings.append(
            f"{len(lines) - len(classified)}/{len(lines)} revenue lines "
            "missing source or amount"
        )

    if not classified:
        return _result(
            kpi_id="FIN-04",
            name="Revenue Diversification Index",
            formula="100 * sum(amount_tnd where source != PUBLIC_FUNDING) / sum(amount_tnd)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"revenue_lines_with_data": 0},
        )

    total = sum(r.amount_tnd or 0.0 for r in classified)
    if total == 0:
        return _result(
            kpi_id="FIN-04",
            name="Revenue Diversification Index",
            formula="100 * sum(amount_tnd where source != PUBLIC_FUNDING) / sum(amount_tnd)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=["revenue_lines.amount_tnd (sum is zero)"],
            warnings=warnings,
            used={"revenue_lines_with_data": len(classified)},
        )

    diversified = sum(
        r.amount_tnd or 0.0
        for r in classified
        if r.source != RevenueSource.PUBLIC_FUNDING
    )
    value = 100.0 * diversified / total
    return _result(
        kpi_id="FIN-04",
        name="Revenue Diversification Index",
        formula="100 * sum(amount_tnd where source != PUBLIC_FUNDING) / sum(amount_tnd)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "revenue_lines_with_data": len(classified),
            "total_revenue_tnd": total,
            "diversified_tnd": diversified,
        },
    )


# ---------------------------------------------------------------------------
# FIN-05 Inventory Utilization Rate
# ---------------------------------------------------------------------------


def fin_05_inventory_utilization(inputs: InstitutionFinanceInputs) -> KpiResult:
    assets = inputs.assets
    classified = [a for a in assets if a.is_in_active_use is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not assets:
        missing.append("assets")
    if assets and not classified:
        missing.append("assets.is_in_active_use")
    if classified and len(classified) < len(assets):
        warnings.append(
            f"{len(assets) - len(classified)}/{len(assets)} assets missing is_in_active_use"
        )

    if not classified:
        return _result(
            kpi_id="FIN-05",
            name="Inventory Utilization Rate",
            formula="100 * count(assets.is_in_active_use=True) / count(assets with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"assets_with_flag": 0},
        )

    in_use = sum(1 for a in classified if a.is_in_active_use)
    value = 100.0 * in_use / len(classified)
    return _result(
        kpi_id="FIN-05",
        name="Inventory Utilization Rate",
        formula="100 * count(assets.is_in_active_use=True) / count(assets with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "assets_total_known": len(assets),
            "assets_with_flag": len(classified),
            "in_active_use": in_use,
        },
    )


# ---------------------------------------------------------------------------
# FIN-06 Project Budget Compliance
# ---------------------------------------------------------------------------


def fin_06_project_budget_compliance(inputs: InstitutionFinanceInputs) -> KpiResult:
    completed = inputs.completed_projects
    classified = [
        p
        for p in completed
        if p.budget_allocated_tnd is not None and p.budget_actual_tnd is not None
    ]
    missing: list[str] = []
    warnings: list[str] = []

    if not completed:
        missing.append("completed_projects")
    if completed and not classified:
        missing.append("completed_projects.budget_allocated_tnd / budget_actual_tnd")
    if classified and len(classified) < len(completed):
        warnings.append(
            f"{len(completed) - len(classified)}/{len(completed)} completed projects "
            "missing allocated or actual budget"
        )

    if not classified:
        return _result(
            kpi_id="FIN-06",
            name="Project Budget Compliance",
            formula="100 * count(completed_projects where actual <= allocated) / count(with both budgets)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"projects_with_budgets": 0},
        )

    within = sum(
        1
        for p in classified
        if (p.budget_actual_tnd or 0.0) <= (p.budget_allocated_tnd or 0.0)
    )
    value = 100.0 * within / len(classified)
    return _result(
        kpi_id="FIN-06",
        name="Project Budget Compliance",
        formula="100 * count(completed_projects where actual <= allocated) / count(with both budgets)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "projects_with_budgets": len(classified),
            "within_budget": within,
        },
    )


# ---------------------------------------------------------------------------
# FIN-07 Payroll Accuracy Rate
# ---------------------------------------------------------------------------


def fin_07_payroll_accuracy_rate(inputs: InstitutionFinanceInputs) -> KpiResult:
    payslips = inputs.payslips
    classified = [p for p in payslips if p.issued_without_correction is not None]
    missing: list[str] = []
    warnings: list[str] = []

    if not payslips:
        missing.append("payslips")
    if payslips and not classified:
        missing.append("payslips.issued_without_correction")
    if classified and len(classified) < len(payslips):
        warnings.append(
            f"{len(payslips) - len(classified)}/{len(payslips)} payslips "
            "missing issued_without_correction"
        )

    if not classified:
        return _result(
            kpi_id="FIN-07",
            name="Payroll Accuracy Rate",
            formula="100 * count(payslips.issued_without_correction=True) / count(payslips with flag)",
            unit="%",
            inputs=inputs,
            value=None,
            missing=missing,
            warnings=warnings,
            used={"payslips_with_flag": 0},
        )

    clean = sum(1 for p in classified if p.issued_without_correction)
    value = 100.0 * clean / len(classified)
    return _result(
        kpi_id="FIN-07",
        name="Payroll Accuracy Rate",
        formula="100 * count(payslips.issued_without_correction=True) / count(payslips with flag)",
        unit="%",
        inputs=inputs,
        value=value,
        missing=[],
        warnings=warnings,
        used={
            "payslips_with_flag": len(classified),
            "without_correction": clean,
        },
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

DOMAIN_E_CALCULATORS: list[Callable[[InstitutionFinanceInputs], KpiResult]] = [
    fin_01_budget_execution_rate,
    fin_02_cost_per_student,
    fin_03_research_funding_ratio,
    fin_04_revenue_diversification,
    fin_05_inventory_utilization,
    fin_06_project_budget_compliance,
    fin_07_payroll_accuracy_rate,
]
