import re

from django import forms
from django.forms import inlineformset_factory

from clientes.models import Cliente

from .models import Locacao, ItemLocacao


def _formatar_cliente_com_cpf(cliente):
    """Usado como label do select de cliente: 'NOME (000.000.000-00)'."""
    cpf_digitos = re.sub(r'\D', '', cliente.cpf or '')
    if len(cpf_digitos) == 11:
        cpf_formatado = f"{cpf_digitos[0:3]}.{cpf_digitos[3:6]}.{cpf_digitos[6:9]}-{cpf_digitos[9:11]}"
        return f"{cliente.nome} ({cpf_formatado})"
    # CPF fora do padrão (não tem 11 dígitos numéricos) — sinaliza em vez de
    # esconder o problema, pra facilitar encontrar cadastros com erro de digitação.
    return f"{cliente.nome} (⚠ CPF inválido: {cliente.cpf or 'não informado'})"


class LocacaoForm(forms.ModelForm):
    class Meta:
        model = Locacao
        fields = ['cliente', 'data_retirada', 'sinal_pago', 'desconto', 'indicado_por']
        widgets = {
            'data_retirada': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'sinal_pago': forms.TextInput(attrs={'autocomplete': 'off', 'inputmode': 'decimal'}),
            'desconto': forms.TextInput(attrs={'autocomplete': 'off', 'inputmode': 'decimal'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['cliente'].label_from_instance = _formatar_cliente_com_cpf
        # O cliente agora é escolhido por um campo de busca (nome ou CPF) na tela;
        # o campo real do formulário guarda apenas o id do cliente selecionado.
        self.fields['cliente'].widget = forms.HiddenInput()
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

    @property
    def cliente_label(self):
        """Texto do campo de busca de cliente (somente o nome) ao abrir/reabrir o formulário."""
        pk = self['cliente'].value()
        if pk:
            try:
                cliente = Cliente.objects.filter(pk=pk).first()
            except (ValueError, TypeError):
                cliente = None
            if cliente:
                return cliente.nome
        return ''


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