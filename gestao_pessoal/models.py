from django.db import models, transaction

# Create your models here.
class Funcionario(models.Model):
    ESTADO_CIVIL_CHOICES = [
        ('C', 'Casado(a)'), ('D', 'Divorciado(a)'), ('S', 'Solteio(a)'), ('U', 'União Estável'), ('V', 'Viuvo(a)'),
    ] 

    SEXO_CHOICES = [
        ('M', 'Masculino'), ('F', 'Feminino'), ('X', 'Anonimixado'),
    ]

    RACA_COR_CHOICES = [ 
        ('AM', 'Amarela'),  ('BR', 'Branca'), ('IN', 'Indigena'), ('PA', 'Parda'), ('PR', 'Preta'), ('NA', 'Não Informado'),
    ]

    ESTADO_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins'),
    ]

    ORG_EMISSOR_CHOICES = [
        ('DETRAN', 'Departamento Estadual de Transito'), ('IFP', 'Instituto Félix Pacheco'), ('PC', 'Polícia Civil'), 
        ('SJC', 'Secretaria de Justiça e Cidadania'), ('SJT', 'Secretaria de Justiça e Trabalho'), ('SSP', 'Secretaria de Segurança Publica'),
    ]

    matricula = models.CharField(max_length=6, unique=True, blank=True, verbose_name='Matrícula') 
    nome_completo = models.CharField(max_length=100, verbose_name='Nome Completo')
    cep = models.CharField(max_length=9,blank=True, verbose_name="CEP")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    numero = models.CharField(max_length=7, verbose_name="Número")
    complemento = models.CharField(max_length=100, blank=True, null=True, verbose_name="Complemento")
    bairro = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bairro")
    municipio = models.CharField(max_length=100, verbose_name="Município")
    estado = models.CharField(max_length=2, choices=ESTADO_CHOICES, default='SP', verbose_name="UF")
    email = models.CharField(max_length=100, blank=True, null=True, verbose_name='E-mail')
    contato = models.CharField(max_length=20, blank=True, null=True, verbose_name='Contato')
    nome_mae = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nome da Mãe')
    nome_pai = models.CharField(max_length=100, blank=True, null=True, verbose_name='Nome do Pai')
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, verbose_name='Sexo')
    raca_cor = models.CharField(max_length=2, choices=RACA_COR_CHOICES, verbose_name='Raça/Cor')
    data_nascimento = models.DateField(blank=True, null=True, verbose_name='Data Nascimento')
    data_admissao = models.DateField(blank=True, null=True, verbose_name='Data Admissão')
    data_demissao = models.DateField(blank=True, null=True, verbose_name='Data Demissão')
    estado_civil = models.CharField(max_length=1, choices=ESTADO_CIVIL_CHOICES, verbose_name='Estado Civil')
    cpf = models.CharField(max_length=14, unique=True, verbose_name='CPF')
    rg = models.CharField(max_length=20, unique=True, verbose_name='R.G.')
    data_rg_emiss = models.DateField(verbose_name='Data Emissão RG')
    uf_rg = models.CharField(max_length=2, choices=ESTADO_CHOICES, verbose_name='UF de Emissão')
    org_emissor = models.CharField(max_length=6, choices=ORG_EMISSOR_CHOICES, verbose_name='Orgão Emissor RG')
    carteira_profi = models.CharField(max_length=11, blank=True, null=True, verbose_name='Carteira Profissional' )
    serie_carteira = models.CharField(max_length=4, blank=True, null=True, verbose_name='Séri   e Carteira Profissional' )
    uf_carteira = models.CharField(max_length=2, choices=ESTADO_CHOICES, blank=True, null=True, verbose_name='UF de emissão')
    data_carteira = models.DateField(blank=True, null=True, verbose_name='Data Emissão Carteira')
    pis = models.CharField(max_length=11, blank=True, null=True, verbose_name='P.I.S.')
    salario = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, blank=True, null=True, verbose_name='Salário')
    status = models.BooleanField(default=True, verbose_name='Status')
    
    def save(self, *args, **kwargs):
        # Usamos transaction.atomic para garantir que as duas etapas ocorram com segurança
        with transaction.atomic():
            # 1. Salva primeiro para garantir que o objeto receba um ID do banco de dados
            for field_name in ['nome_completo', 'nome_mae', 'nome_pai', 'cpf', 'rg', 'carteira_profi', 'serie_carteira', 'pis', 'endereco', 'numero', 'bairro', 'complemento', 'municipio'  ]:
                        value = getattr(self, field_name)
                        if value:
                            setattr(self, field_name, value.upper())

            if self.email: self.email = self.email.lower()

            super().save(*args, **kwargs)
            
            # 2. Verifica se a matrícula ainda não foi preenchida para este ID
            if not self.matricula:
                # Converte o ID atual para string e preenche com zeros à esquerda (ex: ID 1 vira "000001")
                self.matricula = str(self.id).zfill(6)
                
                # Salva novamente apenas atualizando o campo matrícula
                super().save(update_fields=['matricula'])

    def __str__(self):
        return f"{self.matricula} - {self.nome}"