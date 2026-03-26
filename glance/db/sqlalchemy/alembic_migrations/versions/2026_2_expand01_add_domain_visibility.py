# Copyright 2026 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Add domain visibility to images

Revision ID: 2026_2_expand01
Revises: zed_expand01
Create Date: 2026-03-26 13:00:00.000000

"""

from alembic import op
from sqlalchemy import Enum

# revision identifiers, used by Alembic.
revision = '2026_2_expand01'
down_revision = 'zed_expand01'
branch_labels = None
depends_on = None

MYSQL_ENGINE = 'InnoDB'
MYSQL_CHARSET = 'utf8'

old_visibility = ('private', 'public', 'shared', 'community')
new_visibility = ('private', 'public', 'shared', 'community', 'domain')


def upgrade():
    """Add 'domain' to the image_visibility enum.

    This migration adds support for domain-scoped image visibility,
    allowing images to be shared with all projects within a specific
    Keystone domain without exposing them to the entire region.
    """
    bind = op.get_bind()
    engine = bind.engine

    if engine.name == 'mysql':
        # MySQL requires recreating the enum type
        op.execute(
            "ALTER TABLE images MODIFY COLUMN visibility "
            "ENUM('private', 'public', 'shared', 'community', 'domain') "
            "NOT NULL DEFAULT 'shared'"
        )
    elif engine.name == 'postgresql':
        # PostgreSQL requires adding the new value to the enum type
        op.execute("ALTER TYPE image_visibility ADD VALUE 'domain'")
    # SQLite doesn't have true enum types, so no migration needed