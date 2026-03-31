"""Initial schema — all 6 tables

Revision ID: 001
Revises:
Create Date: 2026-03-30
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── ENUMs ──────────────────────────────────────────────────────────────────
    fund_type_enum = sa.Enum(
        "large_cap", "large_mid", "mid_cap", "small_cap", "flexi_cap", "index",
        name="fundtype",
    )
    signal_label_enum = sa.Enum(
        "strong_buy", "buy", "hold", "sell",
        name="signallabel",
    )
    alert_type_enum = sa.Enum("mf_signal", "stock_signal", name="alerttype")
    alert_channel_enum = sa.Enum("telegram", "email", name="alertchannel")
    alert_status_enum = sa.Enum("sent", "failed", name="alertstatus")

    # ── users_portfolio ────────────────────────────────────────────────────────
    op.create_table(
        "users_portfolio",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("fund_name", sa.String(100), nullable=False),
        sa.Column("fund_type", fund_type_enum, nullable=False),
        sa.Column("isin", sa.String(20), nullable=True),
        sa.Column("invested_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("units_held", sa.Numeric(10, 4), nullable=False),
        sa.Column("purchase_nav", sa.Numeric(10, 4), nullable=False),
        sa.Column("purchase_date", sa.Date(), nullable=False),
        sa.Column("target_pct", sa.Numeric(5, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_portfolio_purchase_date", "users_portfolio", ["purchase_date"])

    # ── cash_state ─────────────────────────────────────────────────────────────
    op.create_table(
        "cash_state",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("total_available", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("deployed_amount", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("emergency_fund", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("last_updated", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── mf_signals ─────────────────────────────────────────────────────────────
    op.create_table(
        "mf_signals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("nifty_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("nifty_52w_high", sa.Numeric(10, 2), nullable=False),
        sa.Column("drawdown_pct", sa.Numeric(5, 2), nullable=False),
        sa.Column("nifty_pe", sa.Numeric(6, 2), nullable=True),
        sa.Column("nifty_pb", sa.Numeric(6, 2), nullable=True),
        sa.Column("drawdown_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("valuation_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("macro_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("composite_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("signal", sa.String(20), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("deploy_pct_hint", sa.Numeric(5, 2), nullable=False),
        sa.Column("fund_allocation_hint", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mf_signals_computed_at", "mf_signals", ["computed_at"], postgresql_ops={"computed_at": "DESC"})

    # ── stock_watchlist ────────────────────────────────────────────────────────
    op.create_table(
        "stock_watchlist",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ticker", sa.String(20), nullable=False),
        sa.Column("company_name", sa.String(100), nullable=True),
        sa.Column("sector", sa.String(50), nullable=True),
        sa.Column("target_buy_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("position_size", sa.Numeric(12, 2), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("added_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker"),
    )
    op.create_index("ix_stock_watchlist_ticker", "stock_watchlist", ["ticker"])

    # ── stock_signals ──────────────────────────────────────────────────────────
    op.create_table(
        "stock_signals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("watchlist_id", sa.UUID(), nullable=False),
        sa.Column("computed_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("current_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("fundamental_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("technical_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("event_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("composite_score", sa.Numeric(5, 2), nullable=False),
        sa.Column("signal_label", signal_label_enum, nullable=False),
        sa.Column("rsi", sa.Numeric(5, 2), nullable=True),
        sa.Column("macd_signal", sa.String(10), nullable=True),
        sa.Column("vs_200dma_pct", sa.Numeric(6, 2), nullable=True),
        sa.Column("pe_ratio", sa.Numeric(6, 2), nullable=True),
        sa.Column("roe", sa.Numeric(6, 2), nullable=True),
        sa.Column("reasoning", sa.String(500), nullable=True),
        sa.ForeignKeyConstraint(["watchlist_id"], ["stock_watchlist.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_signals_watchlist_computed", "stock_signals", ["watchlist_id", "computed_at"])

    # ── alert_log ──────────────────────────────────────────────────────────────
    op.create_table(
        "alert_log",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("alert_type", alert_type_enum, nullable=False),
        sa.Column("ref_id", sa.UUID(), nullable=True),
        sa.Column("channel", alert_channel_enum, nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), server_default=sa.func.now()),
        sa.Column("status", alert_status_enum, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_alert_log_type_sent_at", "alert_log", ["alert_type", "sent_at"])


def downgrade() -> None:
    op.drop_table("alert_log")
    op.drop_table("stock_signals")
    op.drop_table("stock_watchlist")
    op.drop_table("mf_signals")
    op.drop_table("cash_state")
    op.drop_table("users_portfolio")

    op.execute("DROP TYPE IF EXISTS alertstatus")
    op.execute("DROP TYPE IF EXISTS alertchannel")
    op.execute("DROP TYPE IF EXISTS alerttype")
    op.execute("DROP TYPE IF EXISTS signallabel")
    op.execute("DROP TYPE IF EXISTS fundtype")
