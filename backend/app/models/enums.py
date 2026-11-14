import enum


class CategoryType(str, enum.Enum):
    income = "income"
    expense = "expense"


class TransactionType(str, enum.Enum):
    income = "income"
    expense = "expense"


class TransactionStatus(str, enum.Enum):
    completed = "completed"
    pending = "pending"
