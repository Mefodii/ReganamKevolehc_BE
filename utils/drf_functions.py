from rest_framework import viewsets, serializers

from utils.constants import DEFAULT


class RecursiveField(serializers.ModelSerializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class MultiSerializerViewSet(viewsets.ModelViewSet):
    serializers = {
        DEFAULT: None,
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers[DEFAULT])