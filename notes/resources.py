from import_export import resources

from notes.models import Note


class NoteResource(resources.ModelResource):
    class Meta:
        model = Note
