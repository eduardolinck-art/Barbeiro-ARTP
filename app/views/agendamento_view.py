from datetime import date, time

import flet as ft

from app import google_calendar
from app.components.curso_modal import abrir_modal_curso
from app.components.datahora_modal import abrir_modal_data_hora
from app.components.mentor_modal import abrir_modal_mentor
from app.components.tema_modal import abrir_modal_tema
from app.google_calendar import GoogleCalendarError
from app.repositories import agendamentos_repo, mentores_repo, usuarios_repo


def agendamento_view(page: ft.Page) -> ft.Control:
    client = page.session.get("supabase_client")
    perfil_id = page.session.get("perfil_id")

    cursos = mentores_repo.listar_cursos(client)

    estado = {
        "curso_id": None, "curso_nome": None,
        "tema_id": None, "tema_nome": None,
        "mentor_id": None, "mentor_nome": None,
        "mentores_do_tema": [],  # ids dos mentores que cobrem o tema escolhido
        "data": None, "hora": None,
    }

    campo_curso = ft.TextField(label="Curso", read_only=True, hint_text="Toque para escolher")
    campo_tema = ft.TextField(label="Tema", read_only=True, hint_text="Escolha o curso primeiro")
    campo_mentor = ft.TextField(label="Mentor", read_only=True, hint_text="Escolha o tema primeiro")
    campo_data_hora = ft.TextField(label="Data e hora", read_only=True, hint_text="Escolha o mentor primeiro")
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

    def limpar_data_hora() -> None:
        estado["data"] = None
        estado["hora"] = None
        campo_data_hora.value = ""

    def limpar_mentor() -> None:
        estado["mentor_id"] = None
        estado["mentor_nome"] = None
        campo_mentor.value = ""
        campo_mentor.hint_text = "Escolha o tema primeiro"
        limpar_data_hora()

    def limpar_tema() -> None:
        estado["tema_id"] = None
        estado["tema_nome"] = None
        estado["mentores_do_tema"] = []
        campo_tema.value = ""
        limpar_mentor()

    def selecionar_curso(curso_id: str, nome: str) -> None:
        estado["curso_id"] = curso_id
        estado["curso_nome"] = nome
        campo_curso.value = nome
        campo_tema.hint_text = "Toque para escolher"
        limpar_tema()
        page.update()

    def selecionar_tema(tema_id: str, nome: str) -> None:
        estado["tema_id"] = tema_id
        estado["tema_nome"] = nome
        campo_tema.value = nome
        estado["mentores_do_tema"] = mentores_repo.listar_mentores_por_tema(client, tema_id)
        campo_mentor.hint_text = "Toque para escolher"
        limpar_mentor()
        page.update()

    def selecionar_mentor(mentor_id: str | None, nome: str) -> None:
        estado["mentor_id"] = mentor_id
        estado["mentor_nome"] = nome
        campo_mentor.value = nome
        campo_data_hora.hint_text = "Toque para escolher"
        limpar_data_hora()
        page.update()

    def selecionar_data_hora(dia: date, hora: time) -> None:
        estado["data"] = dia
        estado["hora"] = hora
        campo_data_hora.value = f"{dia.strftime('%d/%m/%Y')} às {hora.strftime('%H:%M')}"
        page.update()

    def abrir_curso(e: ft.ControlEvent) -> None:
        abrir_modal_curso(page, cursos, selecionar_curso)

    def abrir_tema(e: ft.ControlEvent) -> None:
        if not estado["curso_id"]:
            mensagem.value = "Escolha o curso antes de ver os temas."
            page.update()
            return
        mensagem.value = ""
        temas = mentores_repo.listar_temas_por_curso(client, estado["curso_id"])
        abrir_modal_tema(page, temas, selecionar_tema)

    def abrir_mentor(e: ft.ControlEvent) -> None:
        if not estado["tema_id"]:
            mensagem.value = "Escolha o tema antes de ver os mentores."
            page.update()
            return
        mensagem.value = ""
        abrir_modal_mentor(page, estado["mentores_do_tema"], selecionar_mentor)

    def abrir_data_hora(e: ft.ControlEvent) -> None:
        if estado["mentor_id"] is None and estado["mentor_nome"] is None:
            mensagem.value = "Escolha o mentor antes de ver os horários."
            page.update()
            return
        mensagem.value = ""
        ids_alternativos = [m.id for m in estado["mentores_do_tema"]]
        abrir_modal_data_hora(page, estado["mentor_id"], ids_alternativos, selecionar_data_hora)

    def confirmar(e: ft.ControlEvent) -> None:
        mensagem.value = ""
        selecionou_mentor = estado["mentor_id"] is not None or estado["mentor_nome"] is not None
        if not estado["curso_id"] or not estado["tema_id"] or not selecionou_mentor or not estado["data"] or not estado["hora"]:
            mensagem.value = "Preencha curso, tema, mentor e data/hora antes de confirmar."
            page.update()
            return

        carregando.visible = True
        botao_confirmar.disabled = True
        page.update()

        try:
            ids_do_tema = [m.id for m in estado["mentores_do_tema"]]
            mentor_id_final = estado["mentor_id"]
            if mentor_id_final is None:
                mentor_id_final = google_calendar.escolher_mentor_sem_preferencia(
                    ids_do_tema, estado["data"], estado["hora"]
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
                tema_id=estado["tema_id"],
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

            estado.update({
                "curso_id": None, "curso_nome": None,
                "tema_id": None, "tema_nome": None,
                "mentor_id": None, "mentor_nome": None,
                "mentores_do_tema": [],
                "data": None, "hora": None,
            })
            campo_curso.value = ""
            campo_tema.value = ""
            campo_tema.hint_text = "Escolha o curso primeiro"
            campo_mentor.value = ""
            campo_mentor.hint_text = "Escolha o tema primeiro"
            campo_data_hora.value = ""
            campo_data_hora.hint_text = "Escolha o mentor primeiro"
        except Exception as exc:  # noqa: BLE001
            if "duplicate key" in str(exc).lower() or "23505" in str(exc):
                mensagem.value = "Esse horário acabou de ser reservado por outra pessoa. Escolha outro."
            else:
                mensagem.value = f"Não foi possível concluir o agendamento: {exc}"
        finally:
            carregando.visible = False
            botao_confirmar.disabled = False
            page.update()

    campo_curso.on_click = abrir_curso
    campo_tema.on_click = abrir_tema
    campo_mentor.on_click = abrir_mentor
    campo_data_hora.on_click = abrir_data_hora
    botao_confirmar.on_click = confirmar

    return ft.Container(
        padding=20,
        content=ft.Column(
            [
                ft.Text("Agendar mentoria", size=22, weight=ft.FontWeight.BOLD),
                campo_curso,
                campo_tema,
                campo_mentor,
                campo_data_hora,
                mensagem,
                ft.Row([botao_confirmar, carregando]),
                comprovante,
            ],
            spacing=16,
        ),
    )
