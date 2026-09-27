from django import forms
from django.forms import inlineformset_factory

from .models import Locacao, ItemLocacao


class LocacaoForm(forms.ModelForm):
    class Meta:
        model = Locacao
        fields = ['cliente', 'data_retirada', 'sinal_pago', 'desconto_ajuste', 'indicado_por']
        widgets = {
            'data_retirada': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'sinal_pago': forms.TextInput(attrs={'autocomplete': 'off', 'inputmode': 'decimal'}),
            'desconto_ajuste': forms.TextInput(attrs={'autocomplete': 'off', 'inputmode': 'decimal'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['indicado_por'].required = False
        self.fields['indicado_por'].label = 'Indicado por (opcional)'
        # Não deixa a própria locação se indicar, e tira canceladas da lista
        qs = Locacao.objects.exclude(status=Locacao.STATUS_CANCELADA).select_related('cliente')
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields['indicado_por'].queryset = qs

        # Estilo premium (mesmo padrão do ClienteForm)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'w-5 h-5 rounded border-stone-300 text-[#B4977A] focus:ring-[#B4977A]'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-3 rounded-xl border border-stone-200 focus:border-[#B4977A] focus:ring-1 focus:ring-[#B4977A] outline-none transition-all bg-white/50 placeholder-stone-400',
                    'placeholder': field.label,
                })


class ItemLocacaoForm(forms.ModelForm):
    class Meta:
        model = ItemLocacao
        fields = ['produto', 'valor_aplicado']
        widgets = {
            'valor_aplicado': forms.TextInput(attrs={'autocomplete': 'off', 'inputmode': 'decimal'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['valor_aplicado'].required = False
        self.fields['valor_aplicado'].help_text = None

        base_class = (
            'w-full px-3 py-2.5 rounded-lg border border-stone-200 '
            'focus:border-[#B4977A] focus:ring-1 focus:ring-[#B4977A] '
            'outline-none transition-all bg-white/70 text-sm'
        )
        self.fields['produto'].widget.attrs.update({
            'class': base_class + ' item-produto-select',
        })
        self.fields['valor_aplicado'].widget.attrs.update({
            'class': base_class,
            'placeholder': 'Preço padrão',
        })


# Formset "pai/filho": uma Locação pode ter várias linhas de ItemLocacao.
# extra=1 -> já nasce com uma linha em branco na criação.
# can_delete=True -> permite remover peças (inclusive já salvas, na edição).
ItemLocacaoFormSet = inlineformset_factory(
    Locacao,
    ItemLocacao,
    form=ItemLocacaoForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)