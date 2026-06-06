from django import forms
from .models import Cliente

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = [
            'nome', 'data_nascimento', 'rg', 'cpf', 'credito', 'contato', 'email',
            'cep', 'endereco', 'numero', 'complemento', 'bairro', 'municipio', 'estado',
            'observacao', 'ativo'
        ]
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
            'observacao': forms.Textarea(attrs={'rows': 3}),
            'credito': forms.TextInput(attrs={
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