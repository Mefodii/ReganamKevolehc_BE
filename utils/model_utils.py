from typing import Self

from django.core.validators import MinValueValidator
from django.db import models


class PositionedModel(models.Model):
    parent_name: str = ""
    position = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        abstract = True

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, 'parent_name'):
            raise TypeError(f"Class '{cls.__name__}' has no parent_name")
        super().__init_subclass__(**kwargs)

    def reorder(self, old_position: int | None, new_position: int | None):
        if not hasattr(self.__class__, 'parent_name'):
            raise TypeError(f"Class '{self.__class__.__name__}' has no parent_name")

        filters = {}
        order_mod = 0
        parent_name = self.parent_name

        filters[parent_name] = getattr(self, parent_name)
        if new_position and old_position:  # Instance was updated
            # mod == -1 -> instance is moved down in order, so all other objects in range has to be shifted down
            # mod == 1  -> instance is moved up in order, so all other objects in range has to be shifted up
            order_mod = -1 if old_position < new_position else 1
            gte, lte = sorted([old_position, new_position])
            filters[f"position__lte"] = lte
            filters[f"position__gte"] = gte
        if not old_position:  # Instance was created
            order_mod = 1
            filters[f"position__gte"] = new_position
        if not new_position:  # Instance was deleted
            order_mod = -1
            filters[f"position__gte"] = old_position

        objects = self.__class__.objects.filter(**filters).exclude(pk=self.pk).order_by("position")
        for o in objects:
            o.position = order_mod + o.position
            o.save()

    def updated(self, **kwargs):
        old_position: int = kwargs["old_position"]
        if self.position != old_position:
            self.reorder(old_position, self.position)

    def created(self, **kwargs):
        # Shift up by 1 all objects with position >= self.position
        self.reorder(None, self.position)

    def deleted(self, **kwargs):
        # Shift up by -1 all objects with position >= self.position
        self.reorder(self.position, None)


class TypedQuerySet(models.QuerySet):

    def filter(self, *args, **kwargs) -> Self:
        return super().filter(*args, **kwargs)

    def all(self) -> Self:
        return super().all()
