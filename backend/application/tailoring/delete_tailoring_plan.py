"""Delete-tailoring-plan use case.

    repository needs: delete(plan_id: str) -> None

Deliberately the only thing this touches is the plan itself (and its
TailoringChange rows, which cascade at the database level - see
infrastructure/database/repositories/tailoring_repository.py). Removing
one tailored-CV run must never affect the Analysis it was generated
from, or the CV/job documents behind that analysis - those are only
ever removed by deleting the document itself (see
application/documents/delete_document.py), which cascades downward
through Analysis to every tailoring plan in turn.
"""


class DeleteTailoringPlan:
    def __init__(self, repository) -> None:
        self._repository = repository

    def execute(self, plan_id: str) -> None:
        self._repository.delete(plan_id)
