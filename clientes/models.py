from django.db import models

class Cliente(models.Model):
    ESTADO_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
    ]

    # 1. Informações Pessoais
    nome = models.CharField(max_length=200, verbose_name="Nome Completo")
    data_nascimento = models.DateField(null=True, blank=True, verbose_name="Data de Nascimento")
    rg = models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name="RG")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    
    # 2. Comunicação
    contato = models.CharField(max_length=20, verbose_name="Telefone/WhatsApp")
    email = models.EmailField(blank=True, null=True, verbose_name="E-mail")
    
    # 3. Endereço
    cep = models.CharField(max_length=9, verbose_name="CEP")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    numero = models.CharField(max_length=7, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, verbose_name="Bairro")
    municipio = models.CharField(max_length=100, verbose_name="Município")
    estado = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='SP', verbose_name="UF")
    
    # 4. Gestão e Histórico
    observacao = models.TextField(blank=True, null=True, verbose_name="Observações Internas")
    qtd_alugueis = models.PositiveIntegerField(default=0, verbose_name="Quantidade de Aluguéis")
    credito = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Crédito")
    ativo = models.BooleanField(default=True, verbose_name="Cliente Ativo")
    
    # 5. Datas de Controle
    data_cadastro = models.DateTimeField(auto_now_add=True, verbose_name="Data de Cadastro")
    data_ultima_compra = models.DateTimeField(null=True, blank=True, verbose_name="Data da Última Locação")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} ({self.cpf})"

    def save(self, *args, **kwargs):
        # Normalização de dados antes de salvar no banco
        if self.nome: self.nome = self.nome.upper()
        if self.rg: self.rg = self.rg.upper()
        if self.endereco: self.endereco = self.endereco.upper()
        if self.numero: self.numero = self.numero.upper()
        if self.complemento: self.complemento = self.complemento.upper()
        if self.bairro: self.bairro = self.bairro.upper()
        if self.municipio: self.municipio = self.municipio.upper()
        if self.observacao: self.observacao = self.observacao.upper()
        
        # Emails são padronizados em minúsculo por convenção técnica
        if self.email: self.email = self.email.lower()
        
        super(Cliente, self).save(*args, **kwargs)
