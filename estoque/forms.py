from django import forms
from .models import Categoria

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['descricao', 'categoria_pai']
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Digite o nome da categoria'
            }),
            'categoria_pai': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtro: Apenas categorias principais (sem pai) que ainda não possuem subcategorias.
        # Isso garante uma hierarquia de no máximo 2 níveis e evita que uma categoria 
        # que já é subcategoria se torne pai de outra.
        qs = Categoria.objects.filter(categoria_pai__isnull=True)

        # Se for edição, garantimos que a categoria atual não apareça na lista
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        self.fields['categoria_pai'].queryset = qs

    def clean(self):
        cleaned_data = super().clean()
        categoria_pai = cleaned_data.get('categoria_pai')
        
        # Validação extra de segurança para garantir o mesmo princípio do __init__
        if self.instance and categoria_pai == self.instance:
            raise forms.ValidationError(
                {"categoria_pai": "Uma categoria não pode ser pai de si mesma."}
            )
            
        return cleaned_data