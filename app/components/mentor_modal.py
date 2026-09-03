from typing import Callable

import flet as ft

from app.models import Mentor


def abrir_modal_mentor(page: ft.Page, mentores: list[Mentor], on_select: Callable[[str | None, str], None]) -> None:
    dialog = ft.AlertDialog(title=ft.Text("Selecionar profissional"))

    def selecionar(mentor_id: str | None, nome: str) -> None:
        page.close(dialog)
        on_select(mentor_id, nome)

    itens = [
        ft.ListTile(
            title=ft.Text("Sem preferência"),
            leading=ft.Icon(ft.Icons.SHUFFLE),
            on_click=lambda e: selecionar(None, "Sem preferência"),
        ),
        ft.Divider(),
    ]
    itens += [
        ft.ListTile(
            title=ft.Text(mentor.nome),
            leading=ft.Icon(ft.Icons.PERSON_OUTLINE),
            on_click=lambda e, m=mentor: selecionar(m.id, m.nome),
        )
        for mentor in mentores
    ]

    dialog.content = ft.Column(itens, tight=True, scroll=ft.ScrollMode.AUTO, width=350, height=400)
    page.open(dialog)
