from typing import List, Dict, Any
from ..models import FilterCondition, FilterExpression, FilterOperator
import logging

logger = logging.getLogger(__name__)

class FilterEvaluator:
    @staticmethod
    def evaluate(supplier: Dict[str, Any], expression: FilterExpression) -> bool:
        if not expression.conditions:
            return True
        results = []
        for cond in expression.conditions:
            field_value = supplier.get(cond.field)
            # Handle special fields like 'domain' from website
            if cond.field == 'domain' and field_value is None:
                field_value = supplier.get('website', '') or supplier.get('source_url', '')
            operator = cond.operator
            value = cond.value
            if operator == FilterOperator.EQ:
                result = field_value == value
            elif operator == FilterOperator.NEQ:
                result = field_value != value
            elif operator == FilterOperator.LT:
                result = field_value is not None and field_value < value
            elif operator == FilterOperator.LTE:
                result = field_value is not None and field_value <= value
            elif operator == FilterOperator.GT:
                result = field_value is not None and field_value > value
            elif operator == FilterOperator.GTE:
                result = field_value is not None and field_value >= value
            elif operator == FilterOperator.CONTAINS:
                result = value in str(field_value)
            elif operator == FilterOperator.NOT_CONTAINS:
                result = value not in str(field_value)
            elif operator == FilterOperator.IN:
                result = field_value in value
            elif operator == FilterOperator.NOT_IN:
                result = field_value not in value
            elif operator == FilterOperator.EXISTS:
                result = field_value is not None
            elif operator == FilterOperator.NOT_EXISTS:
                result = field_value is None
            else:
                result = False
            results.append(result)
        if expression.logic == "AND":
            return all(results)
        elif expression.logic == "OR":
            return any(results)
        elif expression.logic == "NOT":
            return not results[0] if results else False
        else:
            return all(results)