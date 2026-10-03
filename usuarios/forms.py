from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

CSS = (
    "w-full px-4 py-3 rounded-xl border border-stone-300 bg-white/70 text-sm "
    "focus:outline-none focus:border-stone-500"
)


class LoginForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "Usuário ou senha incorretos.",
        "inactive": "Este usuário está inativo.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": CSS, "placeholder": "Usuário", "autofocus": True}
        )
        self.fields["password"].widget.attrs.update({"class": CSS, "placeholder": "Senha"})


class UsuarioForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Senha",
        required=False,
        widget=forms.PasswordInput(attrs={"class": CSS, "autocomplete": "new-password"}),
    )
    password2 = forms.CharField(
        label="Confirmar senha",
        required=False,
        widget=forms.PasswordInput(attrs={"class": CSS, "autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "is_active", "is_superuser"]
        labels = {
            "username": "Usuário (login)",
            "first_name": "Nome",
            "last_name": "Sobrenome",
            "is_active": "Usuário ativo",
            "is_superuser": "Administrador (acesso total)",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": CSS}),
            "first_name": forms.TextInput(attrs={"class": CSS}),
            "last_name": forms.TextInput(attrs={"class": CSS}),
        }

    def clean(self):
        dados = super().clean()
        senha1 = dados.get("password1")
        senha2 = dados.get("password2")

        if not self.instance.pk and not senha1:
            self.add_error("password1", "Informe a senha.")

        if senha1 or senha2:
            if senha1 != senha2:
                self.add_error("password2", "As senhas não conferem.")
            else:
                try:
                    validate_password(senha1, self.instance)
                except ValidationError as erro:
                    self.add_error("password1", erro)
        return dados