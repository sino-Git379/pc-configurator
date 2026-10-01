import json

from django import forms

from .models import Component


class ComponentForm(forms.ModelForm):
    specs_json = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Component
        fields = ["category", "name", "price", "thumbnail"]

    def clean_specs_json(self):
        raw_specs = self.cleaned_data.get("specs_json", "")
        if not raw_specs:
            return {}

        try:
            specs = json.loads(raw_specs)
        except json.JSONDecodeError as error:
            raise forms.ValidationError("Характеристики должны быть корректным JSON.") from error

        if not isinstance(specs, dict):
            raise forms.ValidationError("Характеристики должны быть JSON-объектом.")
        return specs

    def save(self, commit=True):
        component = super().save(commit=False)
        component.specs = self.cleaned_data["specs_json"]
        if commit:
            component.save()
            self.save_m2m()
        return component