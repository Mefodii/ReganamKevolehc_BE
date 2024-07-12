from typing import Self

from django.db import models


def reorder(instance: models.Model, old_order: int | None, new_order: int | None,
            field_name: str, parent_name: str | None) -> None:
    if not old_order and not new_order:
        return

    filters = {}
    order_mod = 0
    model = type(instance)

    if parent_name:
        filters[parent_name] = getattr(instance, parent_name)
    if new_order and old_order:  # Instance was updated
        # mod == -1 -> instance is moved down in order, so all other objects in range has to be shifted down
        # mod == 1  -> instance is moved up in order, so all other objects in range has to be shifted up
        order_mod = -1 if old_order < new_order else 1
        gte, lte = sorted([old_order, new_order])
        filters[f"{field_name}__lte"] = lte
        filters[f"{field_name}__gte"] = gte
    if not old_order:  # Instance was created
        order_mod = 1
        filters[f"{field_name}__gte"] = new_order
    if not new_order:  # Instance was deleted
        order_mod = -1
        filters[f"{field_name}__gte"] = old_order
    objects = model.objects.filter(**filters).exclude(pk=instance.pk).order_by(field_name)
    for o in objects:
        new_attr = getattr(o, field_name) + order_mod
        setattr(o, field_name, new_attr)
        o.save()


class TypedQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs) -> Self:
        return super().filter(*args, **kwargs)
