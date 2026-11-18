"""Mobile identity, sessions, account access and verified WhatsApp linking.

Revision ID: 20261118_0002
Revises: 20261107_0001
"""
from alembic import op
from sqlalchemy import inspect

from app.db.base import Base
import app.db.models  # noqa: F401

revision = "20261118_0002"
down_revision = "20261107_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("patient_profiles")}
    if "display_name" not in columns:
        op.add_column("patient_profiles", Base.metadata.tables["patient_profiles"].c.display_name.copy())
    if "sex" not in columns:
        op.add_column("patient_profiles", Base.metadata.tables["patient_profiles"].c.sex.copy())
    for name in ("mobile_credentials", "mobile_sessions", "patient_access", "whatsapp_link_challenges"):
        Base.metadata.tables[name].create(bind, checkfirst=True)


def downgrade() -> None:
    bind = op.get_bind()
    for name in ("whatsapp_link_challenges", "patient_access", "mobile_sessions", "mobile_credentials"):
        Base.metadata.tables[name].drop(bind, checkfirst=True)
    with op.batch_alter_table("patient_profiles") as batch:
        batch.drop_column("sex")
        batch.drop_column("display_name")
