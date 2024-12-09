"""activeadmin

Revision ID: 930371cd3879
Revises: d28eec64ea27
Create Date: 2024-09-14 15:33:04.849401

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '930371cd3879'
down_revision = 'd28eec64ea27'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('active_admin_session',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('admin_id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.String(length=255), nullable=False),
    sa.Column('last_active', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('admin_id'),
    sa.UniqueConstraint('session_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('active_admin_session')
    # ### end Alembic commands ###
