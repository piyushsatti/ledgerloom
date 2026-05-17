"""Shared types for all statement parsers."""

from dataclasses import dataclass, field


@dataclass
class RawTransaction:
    """A single parsed transaction before normalization or categorization."""
    date: str                        # YYYY-MM-DD
    raw_description: str             # original text from statement
    amount: float                    # negative = out, positive = in
    balance: float | None = None
    tx_method: str | None = None     # interac, visa_debit, etransfer, online, atm, paypal


@dataclass
class ParseResult:
    """Output of any statement parser."""
    transactions: list[RawTransaction] = field(default_factory=list)
    summary: dict = field(default_factory=dict)
    period: tuple[str, str] | None = None


@dataclass
class SplitExpense:
    """A real shared expense from Splitwise (not a payment or settlement)."""
    date: str
    description: str
    sw_category: str
    total_cost: float
    user_share: float
    group_name: str = ""
    source_file: str = ""
    counterparties: str = "[]"


@dataclass
class SplitPayment:
    """A payment between people on Splitwise."""
    date: str
    from_person: str
    to_person: str
    amount: float
    group_name: str = ""
    source_file: str = ""
