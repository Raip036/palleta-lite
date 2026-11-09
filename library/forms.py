from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        clean_one = super().clean
        if isinstance(data, (list, tuple)):
            if not data:
                # An empty list would skip validation, so run it once to enforce "required"
                return [clean_one(None, initial)]
            return [clean_one(d, initial) for d in data]
        return [clean_one(data, initial)]


class UploadForm(forms.Form):
    files = MultipleFileField()
    tags = forms.CharField(
        required=False,
        help_text="Comma-separated, applied to all files",
    )

class EditVideoForm(forms.Form):
    title = forms.CharField(max_length=200)   # strips whitespace, so "   " is rejected
    tags = forms.CharField(
        required=False,
        help_text="Comma-separated",
    )
