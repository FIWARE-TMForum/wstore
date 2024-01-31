from djongo import models
from decimal import Decimal, ROUND_DOWN
from django.core.exceptions import ValidationError


class CustomDecimalField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.quantize_value = Decimal(f".{'0' * (self.decimal_places - 1)}1" if self.decimal_places else "1.")

    def _force_precision(self, value):
        return value.quantize(self.quantize_value, rounding=ROUND_DOWN)

    def from_db_value(self, value, expression, connection):
        return self._force_precision(value.to_decimal())

    def to_python(self, value):
        try:
            return self._force_precision(Decimal(value)) if value else None
        except:
            raise ValidationError("`value` cannot be converted to Decimal")

    def validate(self, value, model_instance):
        value = self.to_python(value)
        return super().validate(value, model_instance)
