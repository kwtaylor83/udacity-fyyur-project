"""in Show model raname show_date to start_time

Revision ID: a0c0fc6481ef
Revises: 9306a8ef1810
Create Date: 2020-01-23 09:17:28.632645

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a0c0fc6481ef'
down_revision = '9306a8ef1810'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Show', sa.Column('start_time', sa.DateTime(), nullable=False))
    op.drop_column('Show', 'show_date')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Show', sa.Column('show_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=False))
    op.drop_column('Show', 'start_time')
    # ### end Alembic commands ###
