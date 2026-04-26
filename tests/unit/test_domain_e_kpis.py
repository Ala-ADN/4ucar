"""Unit tests for Domain E (Finance & Resources) KPI calculators."""

from __future__ import annotations

from datetime import date

import pytest

from backend.services.kpi_service.domain import (
    Asset,
    BudgetCategory,
    BudgetLine,
    CompletedProject,
    FundedProject,
    InstitutionFinanceInputs,
    Payslip,
    RevenueLine,
    RevenueSource,
    Student,
    StudentStatus,
    compute_finance_domain,
)
from backend.services.kpi_service.domain.finance import (
    fin_01_budget_execution_rate,
    fin_02_cost_per_student,
    fin_03_research_funding_ratio,
    fin_04_revenue_diversification,
    fin_05_inventory_utilization,
    fin_06_project_budget_compliance,
    fin_07_payroll_accuracy_rate,
)

PERIOD_START = date(2026, 1, 1)
PERIOD_END = date(2026, 12, 31)


def _inputs(**overrides) -> InstitutionFinanceInputs:
    base = dict(
        institution_id="inst-1",
        institution_code="INSAT",
        period_start=PERIOD_START,
        period_end=PERIOD_END,
    )
    base.update(overrides)
    return InstitutionFinanceInputs(**base)


# ---------------------------------------------------------------------------
# FIN-01
# ---------------------------------------------------------------------------


class TestFin01BudgetExecution:
    def test_basic(self):
        lines = [
            BudgetLine(id="1", allocated_tnd=100_000, actual_tnd=85_000),
            BudgetLine(id="2", allocated_tnd=50_000, actual_tnd=45_000),
        ]
        result = fin_01_budget_execution_rate(_inputs(budget_lines=lines))
        # (85000 + 45000) / (100000 + 50000) = 130000/150000 = ~86.67%
        assert result.value == pytest.approx(86.6666666, abs=0.001)

    def test_partial_data_warns(self):
        lines = [
            BudgetLine(id="1", allocated_tnd=100_000, actual_tnd=80_000),
            BudgetLine(id="2", allocated_tnd=50_000, actual_tnd=None),
        ]
        result = fin_01_budget_execution_rate(_inputs(budget_lines=lines))
        assert result.value == 80.0  # only first line used
        assert any("missing allocated or actual" in w for w in result.warnings)

    def test_no_data(self):
        result = fin_01_budget_execution_rate(_inputs())
        assert result.value is None
        assert "budget_lines" in result.missing_fields

    def test_zero_allocated_is_uncomputable(self):
        lines = [BudgetLine(id="1", allocated_tnd=0, actual_tnd=1000)]
        result = fin_01_budget_execution_rate(_inputs(budget_lines=lines))
        assert result.value is None
        assert any("sum is zero" in m for m in result.missing_fields)


# ---------------------------------------------------------------------------
# FIN-02
# ---------------------------------------------------------------------------


class TestFin02CostPerStudent:
    def test_excludes_research_category(self):
        lines = [
            BudgetLine(id="1", category=BudgetCategory.OPERATIONS, actual_tnd=300_000),
            BudgetLine(id="2", category=BudgetCategory.SALARIES, actual_tnd=700_000),
            BudgetLine(id="3", category=BudgetCategory.RESEARCH, actual_tnd=500_000),  # excluded
        ]
        students = [Student(id=f"s{i}", status=StudentStatus.ACTIVE) for i in range(100)]
        result = fin_02_cost_per_student(_inputs(budget_lines=lines, students=students))
        assert result.value == 10_000.0  # (300k + 700k) / 100

    def test_uncategorised_lines_treated_as_operating_with_warning(self):
        lines = [
            BudgetLine(id="1", category=None, actual_tnd=400_000),
        ]
        students = [Student(id=f"s{i}", status=StudentStatus.ACTIVE) for i in range(100)]
        result = fin_02_cost_per_student(_inputs(budget_lines=lines, students=students))
        assert result.value == 4_000.0
        assert any("lack a category" in w for w in result.warnings)

    def test_no_students(self):
        lines = [BudgetLine(id="1", category=BudgetCategory.OPERATIONS, actual_tnd=100_000)]
        result = fin_02_cost_per_student(_inputs(budget_lines=lines))
        assert result.value is None


# ---------------------------------------------------------------------------
# FIN-03
# ---------------------------------------------------------------------------


class TestFin03ResearchFundingRatio:
    def test_basic(self):
        funded = [
            FundedProject(id="p1", title="A", amount_tnd=200_000, is_external=True, is_active=True),
            FundedProject(id="p2", title="B", amount_tnd=50_000, is_external=False, is_active=True),
        ]
        budget = [BudgetLine(id="1", allocated_tnd=1_000_000)]
        result = fin_03_research_funding_ratio(
            _inputs(funded_projects=funded, budget_lines=budget)
        )
        assert result.value == 20.0  # 200k / 1M

    def test_skips_internal_projects(self):
        funded = [
            FundedProject(id="p1", title="A", amount_tnd=300_000, is_external=False, is_active=True),
        ]
        budget = [BudgetLine(id="1", allocated_tnd=1_000_000)]
        result = fin_03_research_funding_ratio(
            _inputs(funded_projects=funded, budget_lines=budget)
        )
        assert result.value is None  # no external projects

    def test_no_budget(self):
        funded = [
            FundedProject(id="p1", title="A", amount_tnd=300_000, is_external=True, is_active=True),
        ]
        result = fin_03_research_funding_ratio(_inputs(funded_projects=funded))
        assert result.value is None
        assert "budget_lines" in result.missing_fields


# ---------------------------------------------------------------------------
# FIN-04
# ---------------------------------------------------------------------------


class TestFin04RevenueDiversification:
    def test_basic(self):
        revenues = [
            RevenueLine(id="1", source=RevenueSource.PUBLIC_FUNDING, amount_tnd=600_000),
            RevenueLine(id="2", source=RevenueSource.TUITION, amount_tnd=200_000),
            RevenueLine(id="3", source=RevenueSource.RESEARCH, amount_tnd=150_000),
            RevenueLine(id="4", source=RevenueSource.CONSULTANCY, amount_tnd=50_000),
        ]
        result = fin_04_revenue_diversification(_inputs(revenue_lines=revenues))
        # (200k + 150k + 50k) / 1M = 40%
        assert result.value == 40.0

    def test_only_public(self):
        revenues = [RevenueLine(id="1", source=RevenueSource.PUBLIC_FUNDING, amount_tnd=1_000_000)]
        result = fin_04_revenue_diversification(_inputs(revenue_lines=revenues))
        assert result.value == 0.0

    def test_no_data(self):
        result = fin_04_revenue_diversification(_inputs())
        assert result.value is None


# ---------------------------------------------------------------------------
# FIN-05
# ---------------------------------------------------------------------------


class TestFin05InventoryUtilization:
    def test_basic(self):
        assets = [
            Asset(id="1", is_in_active_use=True),
            Asset(id="2", is_in_active_use=True),
            Asset(id="3", is_in_active_use=False),
            Asset(id="4", is_in_active_use=True),
        ]
        result = fin_05_inventory_utilization(_inputs(assets=assets))
        assert result.value == 75.0

    def test_partial_data_warns(self):
        assets = [
            Asset(id="1", is_in_active_use=True),
            Asset(id="2", is_in_active_use=None),
        ]
        result = fin_05_inventory_utilization(_inputs(assets=assets))
        assert result.value == 100.0
        assert any("missing is_in_active_use" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# FIN-06
# ---------------------------------------------------------------------------


class TestFin06ProjectBudgetCompliance:
    def test_basic(self):
        projects = [
            CompletedProject(id="1", budget_allocated_tnd=100_000, budget_actual_tnd=90_000),
            CompletedProject(id="2", budget_allocated_tnd=50_000, budget_actual_tnd=55_000),  # over
            CompletedProject(id="3", budget_allocated_tnd=200_000, budget_actual_tnd=200_000),  # exact = within
            CompletedProject(id="4", budget_allocated_tnd=80_000, budget_actual_tnd=75_000),
        ]
        result = fin_06_project_budget_compliance(_inputs(completed_projects=projects))
        assert result.value == 75.0  # 3 of 4 within

    def test_no_data(self):
        result = fin_06_project_budget_compliance(_inputs())
        assert result.value is None
        assert "completed_projects" in result.missing_fields


# ---------------------------------------------------------------------------
# FIN-07
# ---------------------------------------------------------------------------


class TestFin07PayrollAccuracy:
    def test_basic(self):
        payslips = [
            Payslip(id=f"p{i}", issued_without_correction=(i % 10 != 0))
            for i in range(50)
        ]
        # i%10==0 is corrupted: i ∈ {0, 10, 20, 30, 40} = 5 of 50 → 90% clean
        result = fin_07_payroll_accuracy_rate(_inputs(payslips=payslips))
        assert result.value == 90.0

    def test_partial_data_warns(self):
        payslips = [
            Payslip(id="1", issued_without_correction=True),
            Payslip(id="2", issued_without_correction=None),
        ]
        result = fin_07_payroll_accuracy_rate(_inputs(payslips=payslips))
        assert result.value == 100.0
        assert any("missing issued_without_correction" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def test_dispatcher_runs_all_seven():
    results = compute_finance_domain(_inputs())
    assert {r.kpi_id for r in results} == {f"FIN-{i:02d}" for i in range(1, 8)}
    for r in results:
        if r.value is None:
            assert r.missing_fields, f"{r.kpi_id} returned None without missing_fields"


def test_realistic_insat_fixture():
    budget = [
        BudgetLine(id="b1", category=BudgetCategory.OPERATIONS, allocated_tnd=2_500_000,
                   actual_tnd=2_300_000),
        BudgetLine(id="b2", category=BudgetCategory.SALARIES, allocated_tnd=8_000_000,
                   actual_tnd=7_900_000),
        BudgetLine(id="b3", category=BudgetCategory.INFRASTRUCTURE, allocated_tnd=1_500_000,
                   actual_tnd=1_400_000),
        BudgetLine(id="b4", category=BudgetCategory.RESEARCH, allocated_tnd=500_000,
                   actual_tnd=480_000),
    ]
    revenues = [
        RevenueLine(id="r1", source=RevenueSource.PUBLIC_FUNDING, amount_tnd=10_000_000),
        RevenueLine(id="r2", source=RevenueSource.TUITION, amount_tnd=1_500_000),
        RevenueLine(id="r3", source=RevenueSource.RESEARCH, amount_tnd=800_000),
        RevenueLine(id="r4", source=RevenueSource.CONSULTANCY, amount_tnd=200_000),
    ]
    funded = [
        FundedProject(id=f"fp{i}", title=f"Proj {i}", amount_tnd=80_000 + i * 5_000,
                      is_external=(i % 3 != 0), is_active=True)
        for i in range(10)
    ]
    students = [
        Student(id=f"s{i}", status=StudentStatus.ACTIVE) for i in range(1500)
    ]
    assets = [
        Asset(id=f"a{i}", is_in_active_use=(i % 5 != 0)) for i in range(200)
    ]
    completed = [
        CompletedProject(id=f"c{i}", budget_allocated_tnd=100_000,
                         budget_actual_tnd=95_000 + (10_000 if i % 4 == 0 else 0))
        for i in range(20)
    ]
    payslips = [
        Payslip(id=f"ps{i}", issued_without_correction=(i % 50 != 0))
        for i in range(600)
    ]
    inputs = _inputs(
        budget_lines=budget,
        revenue_lines=revenues,
        assets=assets,
        completed_projects=completed,
        payslips=payslips,
        funded_projects=funded,
        students=students,
    )
    results = {r.kpi_id: r for r in compute_finance_domain(inputs)}
    assert {r for r in results} == {f"FIN-{i:02d}" for i in range(1, 8)}
    for kpi_id, r in results.items():
        assert r.value is not None, f"{kpi_id} unexpectedly missing"
