from django.forms import ModelForm

from wb.models import ApiKey


class ApiForm(ModelForm):
    class Meta:
        model = ApiKey
        fields = ['api', ]
