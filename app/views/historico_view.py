import flet as ft

from app.components.star_rating import StarRating
from app.repositories import agendamentos_repo, avaliacoes_repo


def historico_view(page: ft.Page) -> ft.Control:
    client = page.session.get("supabase_client")
    perfil_id = page.session.get("perfil_id")

    agendamentos = agendamentos_repo.listar_historico_usuario(client, perfil_id)

    if not agendamentos:
        return ft.Container(
            padding=20,
            content=ft.Text("Você ainda não tem encontros realizados.", color=ft.Colors.OUTLINE),
        )

    linhas = []
    for agendamento in agendamentos:
        avaliacao_existente = avaliacoes_repo.obter_avaliacao(client, agendamento.id)
        nota_inicial = avaliacao_existente.nota if avaliacao_existente else 0
        confirmacao = ft.Text("", size=12, color=ft.Colors.GREEN)

        def salvar(nota: int, agendamento_id=agendamento.id, confirmacao=confirmacao) -> None:
            avaliacoes_repo.salvar_avaliacao(client, agendamento_id, nota)
            confirmacao.value = "Avaliação salva!"
            page.update()

        linhas.append(
            ft.Container(
                padding=16,
                border_radius=8,
                bgcolor=ft.Colors.SURFACE,
                content=ft.Column(
                    [
                        ft.Text(
                            f"{agendamento.data.strftime('%d/%m/%Y')} às {agendamento.hora.strftime('%H:%M')}",
                            weight=ft.FontWeight.BOLD,
                        ),
                        ft.Text(f"Curso: {agendamento.curso_nome or agendamento.curso_id}"),
                        ft.Text(f"Mentor: {agendamento.mentor_nome or agendamento.mentor_id}"),
                        ft.Row(
                            [
                                ft.Text("Sua avaliação:"),
                                StarRating(nota_inicial=nota_inicial, on_change=salvar),
                            ]
                        ),
                        confirmacao,
                    ],
                    spacing=6,
                ),
            )
        )

    return ft.Container(
        padding=20,
        content=ft.Column(
            [ft.Text("Histórico de encontros", size=22, weight=ft.FontWeight.BOLD), *linhas],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
        ),
    )
