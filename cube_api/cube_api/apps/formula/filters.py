import django_filters
from .models import Formula


class FormulaFilter(django_filters.FilterSet):
    difficulty = django_filters.BaseInFilter(field_name='difficulty', lookup_expr='in')

    class Meta:
        model = Formula
        fields = ['category', 'is_custom', 'difficulty']