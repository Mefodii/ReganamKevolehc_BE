from enum import Enum


class RequestType(Enum):
    LIST = "list"
    RETRIEVE = "retrieve"
    CREATE = "create"
    UPDATE = "update"
    PARTIAL_UPDATE = "partial_update"
    DEFAULT = "default"


MODEL_LIST_SEPARATOR = ">;<"
