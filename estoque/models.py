from django.db import models

# Create your models here.
class Categoria(models.Model):
    # Removemos o unique=True daqui
    descricao = models.CharField(max_length=100, verbose_name='Descrição')
    categoria_pai = models.ForeignKey(
        'self',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='subcategorias',
        verbose_name='Categoria Pai'
    )

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['descricao']
        # Garante que não existam duas subcategorias "SLIM" dentro de "TERNO"
        unique_together = ('descricao', 'categoria_pai')

    def __str__(self):
        full_path = [self.descricao]
        p = self.categoria_pai
        while p is not None:
            full_path.append(p.descricao)
            p = p.categoria_pai 
        return ' -> '.join(full_path[::-1])
    
    def save(self, *args, **kwargs):
        # Normalização de dados antes de salvar no banco
        if self.descricao: self.descricao = self.descricao.upper()
        
        super(Categoria, self).save(*args, **kwargs)


class Status(models.Model):
    descricao = models.CharField(max_length=50, blank=False, null=False, unique=True, verbose_name='Descrição')

    class Meta():
        verbose_name = 'Status'
        verbose_name_plural = 'Status'
        ordering = ['descricao']

    def __str__(self):
        return self.descricao


class Conservacao(models.Model):
    descricao = models.CharField(max_length=50, blank=False, null=False, unique=True, verbose_name='Descrição')
    
    class Meta():
        verbose_name = 'Conservação'
        verbose_name_plural = 'Conservações'
        ordering = ['descricao']

    def __str__(self):
        return self.descricao
    

class Cor(models.Model):
    descricao = models.CharField(max_length=40, unique=True, verbose_name="Nome da Cor")
    
    codigo_hex = models.CharField(
        max_length=7, null=True, blank=True,
        help_text="Código hexadecimal da cor com # (Ex: #000080 para Azul Marinho). "
                  "Isso permite exibir a cor real na tela do sistema ou site."
    )

    class Meta:
        verbose_name = "Cor"
        verbose_name_plural = "Cores"
        ordering = ['descricao']

    def __str__(self):
        return self.descricao

class Produto(models.Model):
    GENERO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('U', 'Unissex'),
        ('I', 'Infantil'),
    ]

    # 1. Informações Básicas
    descricao = models.CharField(max_length=150, null=False, blank=False, verbose_name="Descrição do Produto")
    codigo = models.CharField(max_length=50, null=False, blank=False, unique=True, verbose_name="Código Produto")
    codigo_barras = models.CharField(max_length=100, blank=True, null=True, verbose_name="Código de Barras / RFID")
    observacao = models.TextField(blank=True, null=True, verbose_name="Observação do Estilo")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, verbose_name="Categoria")

    # 2. Atributos Físicos e Variações
    cor_principal = models.ForeignKey(Cor, on_delete=models.PROTECT, verbose_name='Cor Principal')
    tamanho_etiqueta = models.CharField(max_length=10, verbose_name="Tamanho de Etiqueta")
    genero = models.CharField(max_length=1, choices=GENERO_CHOICES, verbose_name="Gênero")
    marca_estilista = models.CharField(max_length=100, blank=True, null=True, verbose_name="Marca ou Estilista")

    # 3. Gestão de Estoque e Locação
    status = models.ForeignKey(Status, on_delete=models.PROTECT, verbose_name="Status")
    conservacao = models.ForeignKey(Conservacao, on_delete=models.PROTECT, verbose_name="Conservação")
    total_locacoes = models.PositiveIntegerField(default=0, verbose_name="Número de Locações Realizadas")

    # 4. Precificação e Valores Financeiros
    preco_aluguel_padrao = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Preço do Aluguel")
    preco_custo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name="Preço de Custo de Compra")
    multa_atraso_diaria = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Multa por Dia de Atraso", help_text="Valor cobrado por cada dia de atraso na devolução")

    # Metadados e representação
    class Meta:
        verbose_name = "Produto"
        verbose_name_plural = "Produtos"
        ordering = ['descricao']

    def __str__(self):
        return f"{self.codigo} - {self.descricao} (Tam: {self.tamanho_etiqueta})"