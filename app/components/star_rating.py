from typing import Callable

import flet as ft


class StarRating(ft.Row):
    """Avaliação de 0 a 5 estrelas. Passe `somente_leitura=True` para só exibir."""

    def __init__(
        self,
        nota_inicial: int = 0,
        somente_leitura: bool = False,
        on_change: Callable[[int], None] | None = None,
    ):
        super().__init__(spacing=2)
        self.nota = nota_inicial
        self.somente_leitura = somente_leitura
        self.on_change = on_change
        self.controls = [self._estrela(valor) for valor in range(1, 6)]

    def _estrela(self, valor: int) -> ft.IconButton:
        preenchida = valor <= self.nota
        return ft.IconButton(
            icon=ft.Icons.STAR if preenchida else ft.Icons.STAR_BORDER,
            icon_color=ft.Colors.AMBER if preenchida else ft.Colors.GREY_400,
            disabled=self.somente_leitura,
            data=valor,
            on_click=self._ao_clicar,
            icon_size=28,
        )

    def _ao_clicar(self, e: ft.ControlEvent) -> None:
        self.nota = e.control.data
        self.controls = [self._estrela(valor) for valor in range(1, 6)]
        self.update()
        if self.on_change:
            self.on_change(self.nota)
