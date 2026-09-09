from typing import Callable

import flet as ft

from app.models import Tema


def abrir_modal_tema(page: ft.Page, temas: list[Tema], on_select: Callable[[str, str], None]) -> None:
    dialog = ft.AlertDialog(title=ft.Text("Selecionar tema"))

    def selecionar(tema_id: str, nome: str) -> None:
        page.close(dialog)
        on_select(tema_id, nome)

    if temas:
        itens = [
            ft.ListTile(
                title=ft.Text(tema.nome),
                leading=ft.Icon(ft.Icons.TOPIC_OUTLINED),
                on_click=lambda e, t=tema: selecionar(t.id, t.nome),
            )
            for tema in temas
        ]
    else:
        itens = [ft.Text("Nenhum tema cadastrado para esse curso ainda.")]

    dialog.content = ft.Column(itens, tight=True, scroll=ft.ScrollMode.AUTO, width=350, height=300)
    page.open(dialog)
