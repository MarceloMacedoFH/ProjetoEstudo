from django import forms
from .models import Funcionario, Cargo

class CargoForm(forms.ModelForm):
    class Meta:
        model = Cargo
        fields = [
            'descricao', 'status'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicando estilo premium a todos os campos automaticamente
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'w-5 h-5 rounded border-stone-300 text-[#B4977A] focus:ring-[#B4977A]'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-3 rounded-xl border border-stone-200 focus:border-[#B4977A] focus:ring-1 focus:ring-[#B4977A] outline-none transition-all bg-white/50 placeholder-stone-400',
                    'placeholder': field.label
                })        

class FuncionarioForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = [
            'nome_completo', 'email', 'nome_mae', 'nome_pai', 'sexo', 'raca_cor', 'data_nascimento', 'data_admissao', 'data_demissao',
            'estado_civil', 'cpf', 'rg', 'data_rg_emiss', 'uf_rg', 'org_emissor', 'carteira_profi', 'serie_carteira', 'uf_carteira',
            'data_carteira', 'pis', 'salario', 'cep', 'endereco', 'numero', 'complemento', 'bairro', 'municipio', 'estado', 'contato', 'status', 'cargo'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'data_admissao': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'data_demissao': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'data_rg_emiss': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'data_carteira': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'salario': forms.TextInput(attrs={
                'autocomplete': 'off',
                'inputmode': 'decimal',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aplicando estilo premium a todos os campos automaticamente
        for field_name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({
                    'class': 'w-5 h-5 rounded border-stone-300 text-[#B4977A] focus:ring-[#B4977A]'
                })
            else:
                field.widget.attrs.update({
                    'class': 'w-full px-4 py-3 rounded-xl border border-stone-200 focus:border-[#B4977A] focus:ring-1 focus:ring-[#B4977A] outline-none transition-all bg-white/50 placeholder-stone-400',
                    'placeholder': field.label
                })