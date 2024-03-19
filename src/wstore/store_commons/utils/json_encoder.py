from django.core.serializers.json import DjangoJSONEncoder
from bson import Decimal128, ObjectId


class CustomEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal128):
            obj = obj.to_decimal()

        if isinstance(obj, ObjectId):
            return str(obj)

        return super().default(obj)
