import re

import flet as ft

from app.repositories import usuarios_repo
from app.supabase_client import novo_client

_REGEX_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _email_valido(valor: str) -> bool:
    return bool(_REGEX_EMAIL.match(valor.strip()))


def _celular_valido(valor: str) -> bool:
    digitos = re.sub(r"\D", "", valor)
    return len(digitos) in (10, 11)


def auth_view(page: ft.Page, ao_autenticar) -> ft.Control:
    """Tela de login/cadastro. `ao_autenticar()` é chamado após sucesso (o caller navega para /app)."""

    modo_cadastro = ft.Ref[bool]()
    modo_cadastro.current = False

    titulo = ft.Text("Entrar", size=24, weight=ft.FontWeight.BOLD)
    erro_texto = ft.Text("", color=ft.Colors.ERROR)

    campo_nome = ft.TextField(label="Nome completo", visible=False)
    campo_celular = ft.TextField(label="Celular", visible=False, hint_text="(99) 99999-9999")
    campo_email = ft.TextField(label="E-mail")
    campo_senha = ft.TextField(label="Senha", password=True, can_reveal_password=True)

    botao_principal = ft.ElevatedButton("Entrar")
    botao_alternar = ft.TextButton("Não tem conta? Cadastre-se")
    carregando = ft.ProgressRing(visible=False, width=20, height=20)

    def alternar_modo(e: ft.ControlEvent | None = None) -> None:
        modo_cadastro.current = not modo_cadastro.current
        erro_texto.value = ""
        if modo_cadastro.current:
            titulo.value = "Criar conta"
            campo_nome.visible = True
            campo_celular.visible = True
            botao_principal.text = "Cadastrar"
            botao_alternar.text = "Já tem conta? Entrar"
        else:
            titulo.value = "Entrar"
            campo_nome.visible = False
            campo_celular.visible = False
            botao_principal.text = "Entrar"
            botao_alternar.text = "Não tem conta? Cadastre-se"
        page.update()

    def submeter(e: ft.ControlEvent) -> None:
        erro_texto.value = ""

        if not _email_valido(campo_email.value or ""):
            erro_texto.value = "Informe um e-mail válido."
            page.update()
            return
        if not campo_senha.value or len(campo_senha.value) < 6:
            erro_texto.value = "A senha precisa ter pelo menos 6 caracteres."
            page.update()
            return
        if modo_cadastro.current:
            if not (campo_nome.value or "").strip():
                erro_texto.value = "Informe seu nome completo."
                page.update()
                return
            if not _celular_valido(campo_celular.value or ""):
                erro_texto.value = "Informe um celular válido, com DDD."
                page.update()
                return

        carregando.visible = True
        botao_principal.disabled = True
        page.update()

        try:
            client = novo_client()
            if modo_cadastro.current:
                resultado = client.auth.sign_up(
                    {"email": campo_email.value.strip(), "password": campo_senha.value}
                )
                if resultado.user is None:
                    raise RuntimeError("Não foi possível criar a conta. Tente novamente.")
                usuarios_repo.criar_perfil(
                    client,
                    user_id=resultado.user.id,
                    nome=campo_nome.value.strip(),
                    celular=campo_celular.value.strip(),
                    email=campo_email.value.strip(),
                )
            else:
                resultado = client.auth.sign_in_with_password(
                    {"email": campo_email.value.strip(), "password": campo_senha.value}
                )
                if resultado.user is None:
                    raise RuntimeError("E-mail ou senha incorretos.")

            page.session.set("supabase_client", client)
            page.session.set("perfil_id", resultado.user.id)
            ao_autenticar()
        except Exception as exc:  # noqa: BLE001 - qualquer erro do Supabase Auth vira mensagem de UI
            erro_texto.value = _mensagem_amigavel(str(exc))
        finally:
            carregando.visible = False
            botao_principal.disabled = False
            page.update()

    botao_principal.on_click = submeter
    botao_alternar.on_click = alternar_modo

    return ft.Container(
        alignment=ft.alignment.center,
        expand=True,
        content=ft.Container(
            width=380,
            padding=30,
            border_radius=12,
            bgcolor=ft.Colors.SURFACE,
            content=ft.Column(
                [
                    titulo,
                    campo_nome,
                    campo_celular,
                    campo_email,
                    campo_senha,
                    erro_texto,
                    ft.Row([botao_principal, carregando]),
                    botao_alternar,
                ],
                tight=True,
                spacing=14,
            ),
        ),
    )


def _mensagem_amigavel(erro: str) -> str:
    if "already registered" in erro.lower() or "already exists" in erro.lower():
        return "Já existe uma conta com esse e-mail."
    if "invalid login credentials" in erro.lower():
        return "E-mail ou senha incorretos."
    return "Não foi possível concluir. Tente novamente em instantes."
