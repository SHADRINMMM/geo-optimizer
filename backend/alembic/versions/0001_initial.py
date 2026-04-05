"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("propelauth_user_id", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("plan", sa.String(), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_propelauth_user_id", "users", ["propelauth_user_id"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # sites
    op.create_table(
        "sites",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("domain", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sites_user_id", "sites", ["user_id"])
    op.create_index("ix_sites_domain", "sites", ["domain"])
    op.create_index("ix_sites_slug", "sites", ["slug"], unique=True)

    # site_profiles
    op.create_table(
        "site_profiles",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("site_id", sa.String(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("business_name", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("short_description", sa.String(300), nullable=True),
        sa.Column("business_type", sa.String(), nullable=True),
        sa.Column("business_category", sa.String(), nullable=True),
        sa.Column("address", sa.String(), nullable=True),
        sa.Column("city", sa.String(), nullable=True),
        sa.Column("country", sa.String(), nullable=True, server_default="RU"),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("website", sa.String(), nullable=True),
        sa.Column("hours", sa.String(), nullable=True),
        sa.Column("instagram", sa.String(), nullable=True),
        sa.Column("vk", sa.String(), nullable=True),
        sa.Column("telegram_channel", sa.String(), nullable=True),
        sa.Column("products_services", sa.JSON(), nullable=True),
        sa.Column("faq", sa.JSON(), nullable=True),
        sa.Column("target_queries", sa.JSON(), nullable=True),
        sa.Column("unique_features", sa.JSON(), nullable=True),
        sa.Column("google_rating", sa.Float(), nullable=True),
        sa.Column("google_review_count", sa.Integer(), nullable=True),
        sa.Column("raw_crawl_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("site_id"),
    )
    op.create_index("ix_site_profiles_site_id", "site_profiles", ["site_id"])

    # site_files
    op.create_table(
        "site_files",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("site_id", sa.String(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("file_type", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("r2_key", sa.String(), nullable=True),
        sa.Column("public_url", sa.String(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_site_files_site_id", "site_files", ["site_id"])

    # site_reviews
    op.create_table(
        "site_reviews",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("site_id", sa.String(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("text", sa.Text(), nullable=True),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("review_date", sa.String(), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_site_reviews_site_id", "site_reviews", ["site_id"])

    # generation_jobs
    op.create_table(
        "generation_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("site_id", sa.String(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("celery_task_id", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("progress_step", sa.String(), nullable=True),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_generation_jobs_site_id", "generation_jobs", ["site_id"])

    # monitoring_jobs
    op.create_table(
        "monitoring_jobs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("site_id", sa.String(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("engine", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_jobs_site_id", "monitoring_jobs", ["site_id"])

    # monitoring_results
    op.create_table(
        "monitoring_results",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("job_id", sa.String(), sa.ForeignKey("monitoring_jobs.id"), nullable=False),
        sa.Column("site_id", sa.String(), sa.ForeignKey("sites.id"), nullable=False),
        sa.Column("engine", sa.String(), nullable=False),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("mentioned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("snippet", sa.Text(), nullable=True),
        sa.Column("product_mentions", sa.JSON(), nullable=True),
        sa.Column("competitor_mentions", sa.JSON(), nullable=True),
        sa.Column("full_response", sa.Text(), nullable=True),
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_results_job_id", "monitoring_results", ["job_id"])
    op.create_index("ix_monitoring_results_site_id", "monitoring_results", ["site_id"])


def downgrade() -> None:
    op.drop_table("monitoring_results")
    op.drop_table("monitoring_jobs")
    op.drop_table("generation_jobs")
    op.drop_table("site_reviews")
    op.drop_table("site_files")
    op.drop_table("site_profiles")
    op.drop_table("sites")
    op.drop_table("users")
