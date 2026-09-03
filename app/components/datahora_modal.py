from datetime import date, datetime, time, timedelta
from typing import Callable

import flet as ft

from app import google_calendar
from app.google_calendar import GoogleCalendarError


def abrir_modal_data_hora(
    page: ft.Page,
    mentor_id: str | None,
    mentores_ids_para_sem_preferencia: list[str],
    on_select: Callable[[date, time], None],
) -> None:
    """Se `mentor_id` for None (usuário escolheu "Sem preferência"), mostra a união dos horários
    livres entre `mentores_ids_para_sem_preferencia`."""

    def mostrar_erro(mensagem: str) -> None:
        page.open(ft.SnackBar(ft.Text(mensagem), bgcolor=ft.Colors.ERROR))

    def ao_escolher_data(e: ft.ControlEvent) -> None:
        valor = date_picker.value
        dia = valor.date() if isinstance(valor, datetime) else valor
        if dia is None:
            return
        mostrar_horarios(dia)

    def mostrar_horarios(dia: date) -> None:
        try:
            if mentor_id:
                horarios = google_calendar.listar_horarios_livres(mentor_id, dia)
            else:
                horarios = google_calendar.listar_horarios_livres_varios(
                    mentores_ids_para_sem_preferencia, dia
                )
        except GoogleCalendarError as exc:
            mostrar_erro(str(exc))
            return

        if not horarios:
            mostrar_erro("Nenhum horário disponível nessa data. Tente outro dia.")
            return

        def selecionar(hora: time) -> None:
            page.close(dialog_horarios)
            on_select(dia, hora)

        dialog_horarios = ft.AlertDialog(
            title=ft.Text(f"Horários livres em {dia.strftime('%d/%m/%Y')}"),
            content=ft.Column(
                [
                    ft.ListTile(
                        title=ft.Text(hora.strftime("%H:%M")),
                        leading=ft.Icon(ft.Icons.SCHEDULE),
                        on_click=lambda e, h=hora: selecionar(h),
                    )
                    for hora in horarios
                ],
                tight=True,
                scroll=ft.ScrollMode.AUTO,
                width=300,
                height=350,
            ),
        )
        page.open(dialog_horarios)

    date_picker = ft.DatePicker(
        first_date=datetime.now(),
        last_date=datetime.now() + timedelta(days=60),
        on_change=ao_escolher_data,
    )
    page.open(date_picker)
