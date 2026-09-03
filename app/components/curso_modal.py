from typing import Callable

import flet as ft

from app.models import Curso


def abrir_modal_curso(page: ft.Page, cursos: list[Curso], on_select: Callable[[str, str], None]) -> None:
    dialog = ft.AlertDialog(title=ft.Text("Selecionar assunto"))

    def selecionar(curso_id: str, nome: str) -> None:
        page.close(dialog)
        on_select(curso_id, nome)

    itens = [
        ft.ListTile(
            title=ft.Text(curso.nome),
            leading=ft.Icon(ft.Icons.MENU_BOOK_OUTLINED),
            on_click=lambda e, c=curso: selecionar(c.id, c.nome),
        )
        for curso in cursos
    ]

    dialog.content = ft.Column(itens, tight=True, scroll=ft.ScrollMode.AUTO, width=350, height=300)
    page.open(dialog)
