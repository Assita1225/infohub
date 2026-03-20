from app.extensions import mongo


EXPENSE_CATEGORIES = ['餐饮', '交通', '购物', '娱乐', '住房', '通讯', '医疗', '教育', '其他']
INCOME_CATEGORIES = ['工资', '兼职', '理财', '红包', '其他']


def ensure_indexes():
    """创建索引（幂等）"""
    mongo.db.finance_records.create_index(
        [("date", -1), ("type", 1)],
        name="finance_date_type",
    )
