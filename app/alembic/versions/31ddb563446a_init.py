"""init

Revision ID: 31ddb563446a
Revises: 
Create Date: 2021-07-21 04:47:36.296238

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '31ddb563446a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'creators',
        sa.Column('channel_name', postgresql.TEXT, primary_key=True),
        sa.Column('channel_id', postgresql.TEXT)
    )


def downgrade():
    op.drop_table('creators')
