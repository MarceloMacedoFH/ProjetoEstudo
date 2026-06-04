from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'contato', 'municipio', 'estado', 'ativo', 'qtd_alugueis')
    list_filter = ('estado', 'ativo', 'data_cadastro')
    search_fields = ('nome', 'cpf', 'email')
    readonly_fields = ('data_cadastro', 'data_ultima_compra', 'qtd_alugueis')
    
    fieldsets = (
        ('Informações Pessoais', {
            'fields': ('nome', 'data_nascimento', 'rg', 'cpf', 'ativo')
        }),
        ('Comunicação', {
            'fields': ('contato', 'email')
        }),
        ('Endereço', {
            'fields': ('cep', 'endereco', 'complemento', 'bairro', 'municipio', 'estado')
        }),
        ('Histórico e Notas', {
            'fields': ('observacao', 'qtd_alugueis', 'data_cadastro', 'data_ultima_compra')
        }),
    )
