from datetime import date, time

import flet as ft

from app import google_calendar
from app.components.curso_modal import abrir_modal_curso
from app.components.datahora_modal import abrir_modal_data_hora
from app.components.mentor_modal import abrir_modal_mentor
from app.google_calendar import GoogleCalendarError
from app.repositories import agendamentos_repo, mentores_repo, usuarios_repo


def agendamento_view(page: ft.Page) -> ft.Control:
    client = page.session.get("supabase_client")
    perfil_id = page.session.get("perfil_id")

    mentores = mentores_repo.listar_mentores(client)
    cursos = mentores_repo.listar_cursos(client)
    mentores_por_id = {m.id: m for m in mentores}

    estado = {"mentor_id": None, "mentor_nome": None, "curso_id": None, "curso_nome": None,
              "data": None, "hora": None}

    campo_mentor = ft.TextField(label="Mentor", read_only=True, hint_text="Toque para escolher")
    campo_curso = ft.TextField(label="Curso", read_only=True, hint_text="Toque para escolher")
    campo_data_hora = ft.TextField(label="Data e hora", read_only=True, hint_text="Toque para escolher")
    mensagem = ft.Text("", color=ft.Colors.ERROR)
    carregando = ft.ProgressRing(visible=False, width=20, height=20)
    botao_confirmar = ft.ElevatedButton("Confirmar agendamento", icon=ft.Icons.CHECK)

    protocolo_texto = ft.Text("", size=18, weight=ft.FontWeight.BOLD)
    comprovante = ft.Container(
        visible=False,
        padding=16,
        border_radius=8,
        bgcolor=ft.Colors.SURFACE,
        content=ft.Column(
            [
                ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN), ft.Text("Mentoria confirmada!")]),
                protocolo_texto,
            ]
        ),
    )

    def limpar_selecao_data_hora() -> None:
        estado["data"] = None
        estado["hora"] = None
        campo_data_hora.value = ""

    def selecionar_mentor(mentor_id: str | None, nome: str) -> None:
        estado["mentor_id"] = mentor_id
        estado["mentor_nome"] = nome
        campo_mentor.value = nome
        limpar_selecao_data_hora()
        page.update()

    def selecionar_curso(curso_id: str, nome: str) -> None:
        estado["curso_id"] = curso_id
        estado["curso_nome"] = nome
        campo_curso.value = nome
        page.update()

    def selecionar_data_hora(dia: date, hora: time) -> None:
        estado["data"] = dia
        estado["hora"] = hora
        campo_data_hora.value = f"{dia.strftime('%d/%m/%Y')} às {hora.strftime('%H:%M')}"
        page.update()

    def abrir_mentor(e: ft.ControlEvent) -> None:
        abrir_modal_mentor(page, mentores, selecionar_mentor)

    def abrir_curso(e: ft.ControlEvent) -> None:
        abrir_modal_curso(page, cursos, selecionar_curso)

    def abrir_data_hora(e: ft.ControlEvent) -> None:
        if estado["mentor_id"] is None and estado["mentor_nome"] is None:
            mensagem.value = "Escolha o mentor antes de ver os horários."
            page.update()
            return
        mensagem.value = ""
        ids_alternativos = list(mentores_por_id.keys())
        abrir_modal_data_hora(page, estado["mentor_id"], ids_alternativos, selecionar_data_hora)

    def confirmar(e: ft.ControlEvent) -> None:
        mensagem.value = ""
        if not estado["curso_id"] or not estado["data"] or not estado["hora"]:
            mensagem.value = "Preencha mentor, curso e data/hora antes de confirmar."
            page.update()
            return

        carregando.visible = True
        botao_confirmar.disabled = True
        page.update()

        try:
            mentor_id_final = estado["mentor_id"]
            if mentor_id_final is None:
                mentor_id_final = google_calendar.escolher_mentor_sem_preferencia(
                    list(mentores_por_id.keys()), estado["data"], estado["hora"]
                )
                if mentor_id_final is None:
                    mensagem.value = "Nenhum mentor está livre nesse horário. Escolha outro horário."
                    return

            if agendamentos_repo.existe_conflito(mentor_id_final, estado["data"], estado["hora"]):
                mensagem.value = "Esse horário acabou de ser reservado. Escolha outro."
                return

            perfil = usuarios_repo.obter_perfil(client, perfil_id)

            agendamento = agendamentos_repo.criar_agendamento(
                client,
                mentorado_id=perfil_id,
                mentor_id=mentor_id_final,
                curso_id=estado["curso_id"],
                data=estado["data"],
                hora=estado["hora"],
            )

            try:
                event_id = google_calendar.create_event(
                    mentor_id_final, agendamento, perfil.email, perfil.nome
                )
                agendamentos_repo.atualizar_status(client, agendamento.id, "agendado")
                client.table("agendamentos").update({"google_event_id": event_id}).eq(
                    "id", agendamento.id
                ).execute()
            except GoogleCalendarError as exc:
                mensagem.value = f"Agendamento salvo, mas houve um problema com o Google Agenda: {exc}"

            protocolo_texto.value = f"Protocolo: {agendamento.protocolo}"
            comprovante.visible = True

            estado.update({"mentor_id": None, "mentor_nome": None, "curso_id": None,
                            "curso_nome": None, "data": None, "hora": None})
            campo_mentor.value = ""
            campo_curso.value = ""
            campo_data_hora.value = ""
        except Exception as exc:  # noqa: BLE001
            if "duplicate key" in str(exc).lower() or "23505" in str(exc):
                mensagem.value = "Esse horário acabou de ser reservado por outra pessoa. Escolha outro."
            else:
                mensagem.value = f"Não foi possível concluir o agendamento: {exc}"
        finally:
            carregando.visible = False
            botao_confirmar.disabled = False
            page.update()

    campo_mentor.on_click = abrir_mentor
    campo_curso.on_click = abrir_curso
    campo_data_hora.on_click = abrir_data_hora
    botao_confirmar.on_click = confirmar

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Text("Agendar mentoria", size=22, weight=ft.FontWeight.BOLD),
                campo_mentor,
                campo_curso,
                campo_data_hora,
                mensagem,
                ft.Row([botao_confirmar, carregando]),
                comprovante,
            ],
            spacing=16,
        ),
    )
