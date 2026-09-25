from django import forms
from django.core.exceptions import NON_FIELD_ERRORS
from .models import Categoria, Status, Conservacao, Cor, Produto, Tecido

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
        error_messages = {
            # Mensagem do unique_together (descricao + categoria_pai) quando há categoria pai
            NON_FIELD_ERRORS: {
                'unique_together': 'Já existe uma categoria com este nome neste nível.',
            },
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

    def clean_descricao(self):
        # O model grava em maiúsculas no save(). Normalizamos aqui também para que
        # a checagem de duplicidade compare "terno" com "TERNO" antes de salvar.
        return self.cleaned_data['descricao'].strip().upper()

    def clean(self):
        cleaned_data = super().clean()
        descricao = cleaned_data.get('descricao')
        categoria_pai = cleaned_data.get('categoria_pai')
        
        # Validação extra de segurança para garantir o mesmo princípio do __init__
        if self.instance and categoria_pai == self.instance:
            raise forms.ValidationError(
                {"categoria_pai": "Uma categoria não pode ser pai de si mesma."}
            )

        # O unique_together do model NÃO é verificado quando categoria_pai é vazio
        # (NULL nunca é igual a NULL). Por isso checamos as categorias principais à mão.
        if descricao and categoria_pai is None:
            duplicadas = Categoria.objects.filter(descricao=descricao, categoria_pai__isnull=True)
            if self.instance.pk:
                duplicadas = duplicadas.exclude(pk=self.instance.pk)
            if duplicadas.exists():
                self.add_error('descricao', 'Já existe uma categoria com este nome neste nível.')
            
        return cleaned_data

class StatusForm(forms.ModelForm):
    class Meta:
        model = Status
        fields = ['descricao', 'ativo']
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Disponível, Alugado, Lavanderia...'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-stone-300 text-[#B4977A] focus:ring-[#B4977A]'
            }),
        }
        error_messages = {
            'descricao': {
                'unique': 'Já existe um status cadastrado com esta descrição.',
            },
        }

    def clean_descricao(self):
        return self.cleaned_data['descricao'].strip().upper()

class TecidoForm(forms.ModelForm):
    class Meta:
        model = Tecido
        fields = ['descricao', 'ativo']
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: GABARDINE ITALIANA'}),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-stone-300 text-[#B4977A] focus:ring-[#B4977A]'
            }),
        }
        error_messages = {
            'descricao': {
                'unique': 'Já existe um tecido cadastrado com este nome.',
            },
        }
 
    def clean_descricao(self):
        # O model grava em maiúsculas no save(). Normalizamos aqui também para que
        # a checagem de duplicidade compare "seda" com "SEDA" antes de salvar.
        return self.cleaned_data['descricao'].strip().upper()

class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'descricao', 'codigo', 'codigo_barras', 'categoria',
            'cor_principal', 'tecido', 'tamanho_etiqueta', 'genero', 'marca_estilista', 
            'status', 'conservacao', 'preco_aluguel_padrao', 'preco_custo', 
            'multa_atraso_diaria', 'observacao', 'ativo'
        ]
        widgets = {
            'descricao': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Vestido Sereia Renda'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'REF-001'}),
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            'categoria': forms.Select(attrs={'class': 'form-control'}),
            'cor_principal': forms.Select(attrs={'class': 'form-control'}),
            'tecido': forms.Select(attrs={'class': 'form-control'}),
            'tamanho_etiqueta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 38, P, M...'}),
            'genero': forms.Select(attrs={'class': 'form-control'}),
            'marca_estilista': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'conservacao': forms.Select(attrs={'class': 'form-control'}),
            'preco_aluguel_padrao': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'preco_custo': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'multa_atraso_diaria': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'observacao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-stone-300 text-[#B4977A] focus:ring-[#B4977A]'
            }),
        }
        error_messages = {
            'codigo': {
                'unique': 'Já existe um produto cadastrado com este código.',
            },
        }

    def clean_codigo(self):
        # O model grava o código em maiúsculas no save(); normalizamos antes da checagem.
        return self.cleaned_data['codigo'].strip().upper()

class ConservacaoForm(forms.ModelForm):
    class Meta:
        model = Conservacao
        fields = ['descricao', 'ativo']
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Novo, Excelente, Com marcas de uso...'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-stone-300 text-[#B4977A] focus:ring-[#B4977A]'
            }),
        }
        error_messages = {
            'descricao': {
                'unique': 'Já existe uma conservação cadastrada com esta descrição.',
            },
        }

    def clean_descricao(self):
        return self.cleaned_data['descricao'].strip().upper()

class CorForm(forms.ModelForm):
    class Meta:
        model = Cor
        fields = ['descricao', 'codigo_hex', 'ativo']
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Ex: Off-White, Marsala, Azul Serenity...'
            }),
            'codigo_hex': forms.TextInput(attrs={
                'class': 'form-control h-12 p-1', 
                'type': 'color',
                'title': 'Selecione a cor para visualização no sistema'
            }),
            'ativo': forms.CheckboxInput(attrs={
                'class': 'w-5 h-5 rounded border-stone-300 text-[#B4977A] focus:ring-[#B4977A]'
            }),
        }
        error_messages = {
            'descricao': {
                'unique': 'Já existe uma cor cadastrada com este nome.',
            },
        }

    def clean_descricao(self):
        return self.cleaned_data['descricao'].strip().upper()