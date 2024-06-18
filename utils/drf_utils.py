from typing import Any

from rest_framework import viewsets, serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from constants.constants import RequestType
from utils.string_utils import is_bool_repr


class RecursiveField(serializers.ModelSerializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data


class MultiSerializerViewSet(viewsets.ModelViewSet):
    serializers = {
        RequestType.DEFAULT.value: None,
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers[RequestType.DEFAULT.value])


class LargeResultsSetPagination(PageNumberPagination):
    page_size = 500
    page_size_query_param = 'page_size'
    max_page_size = 500

    def get_qparms(self, partial_response: dict[str, Any], next_page: bool) -> dict[str, Any] | None:
        key = 'next' if next_page else "previous"
        if partial_response.get(key, None) is None:
            return None

        res = {}
        for k, v in self.request.query_params.items():
            val = v
            if is_bool_repr(v):
                val = v.lower() == "true"
            if v.isnumeric():
                val = int(v)
            res[k] = val
        res["page"] = partial_response["page"] + 1 if next_page else -1
        return res

    def get_paginated_response(self, data):
        response = {
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'count': self.page.paginator.count,
            'results': data,
            "pages": self.page.paginator.num_pages,
            "page_size": self.page_size,
            "page": int(self.request.query_params.get("page", 1))
        }
        response["nextQParms"] = self.get_qparms(response, next_page=True)
        response["previousQParms"] = self.get_qparms(response, next_page=False)
        return Response(response)
