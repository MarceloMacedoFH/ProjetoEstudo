from django.contrib import admin
from .models import Produto, Categoria, Conservacao, Status, Cor

# Register your models here.
admin.site.register(Conservacao),
admin.site.register(Status),
admin.site.register(Cor),

@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    # As colunas que você quer que apareçam na listagem
    list_display = ('codigo', 'descricao', 'categoria', 'status', 'preco_aluguel_padrao')

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    # As colunas que você quer que apareçam na listagem
    list_display = ('categoria_pai', 'descricao',)


