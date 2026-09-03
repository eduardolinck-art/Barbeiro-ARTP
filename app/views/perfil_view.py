import flet as ft

from app.repositories import usuarios_repo


def perfil_view(page: ft.Page, ao_sair) -> ft.Control:
    client = page.session.get("supabase_client")
    perfil_id = page.session.get("perfil_id")
    perfil = usuarios_repo.obter_perfil(client, perfil_id)

    campo_nome = ft.TextField(label="Nome completo", value=perfil.nome if perfil else "")
    campo_celular = ft.TextField(label="Celular", value=perfil.celular if perfil else "")
    campo_email = ft.TextField(label="E-mail", value=perfil.email if perfil else "")
    mensagem = ft.Text("")

    def salvar(e: ft.ControlEvent) -> None:
        mensagem.value = ""
        mensagem.color = ft.Colors.ERROR
        try:
            usuarios_repo.atualizar_perfil(
                client, perfil_id, nome=campo_nome.value.strip(), celular=campo_celular.value.strip()
            )

            email_atual = perfil.email if perfil else ""
            if campo_email.value.strip() and campo_email.value.strip() != email_atual:
                client.auth.update_user({"email": campo_email.value.strip()})
                mensagem.value = (
                    "Dados salvos. Enviamos um link de confirmação para o novo e-mail — "
                    "ele só passa a valer depois que você confirmar."
                )
                mensagem.color = ft.Colors.PRIMARY
                campo_email.value = email_atual
            else:
                mensagem.value = "Dados atualizados com sucesso."
                mensagem.color = ft.Colors.GREEN
        except Exception as exc:  # noqa: BLE001
            mensagem.value = f"Não foi possível salvar: {exc}"
        page.update()

    def sair(e: ft.ControlEvent) -> None:
        try:
            client.auth.sign_out()
        except Exception:  # noqa: BLE001
            pass
        page.session.clear()
        ao_sair()

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Text("Perfil", size=22, weight=ft.FontWeight.BOLD),
                campo_nome,
                campo_celular,
                campo_email,
                mensagem,
                ft.Row(
                    [
                        ft.ElevatedButton("Salvar", icon=ft.Icons.SAVE, on_click=salvar),
                        ft.OutlinedButton("Sair", icon=ft.Icons.LOGOUT, on_click=sair),
                    ]
                ),
            ],
            spacing=16,
        ),
    )
