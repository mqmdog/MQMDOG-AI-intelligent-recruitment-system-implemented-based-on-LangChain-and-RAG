from sqlalchemy import select
from sqlalchemy.orm import selectinload

from . import BaseRepo
from models.candidate import CandidateAIScoreModel


class CandidateAIScoreRepo(BaseRepo):
    async def create_candidate_score(
        self, candidate_id: str, candidate_score_dict: dict
    ) -> CandidateAIScoreModel:
        candidate_score = CandidateAIScoreModel(
            **candidate_score_dict, candidate_id=candidate_id
        )
        self.session.add(candidate_score)
        return candidate_score

    async def get_by_candidate_id(self, candidate_id: str) -> CandidateAIScoreModel | None:
        return await self.session.scalar(
            select(CandidateAIScoreModel)
            .where(CandidateAIScoreModel.candidate_id == candidate_id)
            .options(selectinload(CandidateAIScoreModel.candidate))
        )
