"""Tests DeleteTailoringPlan against a fake repository double - no
Django, no database. See application/tailoring/delete_tailoring_plan.py.
"""
from application.tailoring.delete_tailoring_plan import DeleteTailoringPlan


class FakeTailoringRepository:
    def __init__(self) -> None:
        self.deleted_ids: list[str] = []

    def delete(self, plan_id):
        self.deleted_ids.append(plan_id)


class TestDeleteTailoringPlan:
    def test_deletes_the_plan(self):
        repository = FakeTailoringRepository()
        use_case = DeleteTailoringPlan(repository)

        use_case.execute("plan-1")

        assert repository.deleted_ids == ["plan-1"]
