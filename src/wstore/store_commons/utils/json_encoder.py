from django.core.serializers.json import DjangoJSONEncoder
from bson import Decimal128


class CustomEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal128):
            obj = obj.to_decimal()
        return super().default(obj)
