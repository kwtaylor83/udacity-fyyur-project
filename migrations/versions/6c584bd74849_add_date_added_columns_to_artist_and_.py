"""add date_added columns to Artist and Venue models

Revision ID: 6c584bd74849
Revises: ac8955c38a64
Create Date: 2020-02-04 13:31:20.129177

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6c584bd74849'
down_revision = 'ac8955c38a64'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('date_added', sa.DateTime(), nullable=True))
    op.add_column('Venue', sa.Column('date_added', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Venue', 'date_added')
    op.drop_column('Artist', 'date_added')
    # ### end Alembic commands ###