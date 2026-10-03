import json

from django import forms
from django.utils import timezone

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


class CheckoutForm(forms.Form):
    delivery_date = forms.DateField(
        input_formats=["%Y-%m-%d"],
        error_messages={"required": "Выберите удобную дату доставки."},
    )
    email = forms.EmailField(error_messages={"required": "Укажите email для получения чека."})

    def clean_delivery_date(self):
        delivery_date = self.cleaned_data["delivery_date"]
        if delivery_date < timezone.localdate():
            raise forms.ValidationError("Дата доставки не может быть в прошлом.")
        return delivery_date