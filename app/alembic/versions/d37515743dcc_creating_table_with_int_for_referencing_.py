"""creating table with int for referencing creators

Revision ID: d37515743dcc
Revises: 
Create Date: 2021-08-25 04:19:51.300956

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as psql


# revision identifiers, used by Alembic.
revision = 'd37515743dcc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'creators',
        sa.Column('id', psql.INTEGER, primary_key=True),
        sa.Column('channel_name', psql.TEXT, primary_key=True),
        sa.Column('channel_id', psql.TEXT, nullable=False)
    )
    op.create_table(
        'videos',
        sa.Column('channel_id', psql.TEXT, primary_key=True),
        sa.Column('video_id', psql.TEXT, primary_key=True),
        sa.Column('date', psql.DATE),
        sa.Column('views', psql.INTEGER),
        sa.Column('description', psql.TEXT)
    )

def downgrade():
    op.drop_table('creators')
    op.drop_table('videos')
