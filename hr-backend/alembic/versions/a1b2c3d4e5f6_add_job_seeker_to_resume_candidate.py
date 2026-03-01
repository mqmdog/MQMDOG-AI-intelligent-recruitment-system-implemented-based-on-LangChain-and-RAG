"""add job_seeker_id to resumes and candidates

Revision ID: a1b2c3d4e5f6
Revises: 4eea2dde5299
Create Date: 2026-03-01 02:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '4eea2dde5299'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # resumes 表: uploader_id 去 NOT NULL，新增 job_seeker_id
    op.alter_column('resumes', 'uploader_id',
                    existing_type=sa.String(100), nullable=True)
    op.add_column('resumes', sa.Column('job_seeker_id',
                  sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_resumes_job_seeker_id'),
                    'resumes', ['job_seeker_id'], unique=False)
    op.create_foreign_key(
        op.f('fk_resumes_job_seeker_id_job_seekers'),
        'resumes', 'job_seekers',
        ['job_seeker_id'], ['id'],
    )

    # candidates 表: creator_id 去 NOT NULL，新增 job_seeker_id
    op.alter_column('candidates', 'creator_id',
                    existing_type=sa.String(100), nullable=True)
    op.add_column('candidates', sa.Column(
        'job_seeker_id', sa.String(length=100), nullable=True))
    op.create_index(op.f('ix_candidates_job_seeker_id'),
                    'candidates', ['job_seeker_id'], unique=False)
    op.create_foreign_key(
        op.f('fk_candidates_job_seeker_id_job_seekers'),
        'candidates', 'job_seekers',
        ['job_seeker_id'], ['id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    # candidates 表: 回滚
    op.drop_constraint(op.f(
        'fk_candidates_job_seeker_id_job_seekers'), 'candidates', type_='foreignkey')
    op.drop_index(op.f('ix_candidates_job_seeker_id'), table_name='candidates')
    op.drop_column('candidates', 'job_seeker_id')
    op.alter_column('candidates', 'creator_id',
                    existing_type=sa.String(100), nullable=False)

    # resumes 表: 回滚
    op.drop_constraint(
        op.f('fk_resumes_job_seeker_id_job_seekers'), 'resumes', type_='foreignkey')
    op.drop_index(op.f('ix_resumes_job_seeker_id'), table_name='resumes')
    op.drop_column('resumes', 'job_seeker_id')
    op.alter_column('resumes', 'uploader_id',
                    existing_type=sa.String(100), nullable=False)
