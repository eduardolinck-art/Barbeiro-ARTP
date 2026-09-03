from urllib.parse import parse_qs, urlsplit

import flet as ft

from app import config, google_calendar
from app.repositories import mentores_repo
from app.views.agendamento_view import agendamento_view
from app.views.auth_view import auth_view
from app.views.historico_view import historico_view
from app.views.perfil_view import perfil_view


def main(page: ft.Page) -> None:
    page.title = "Mentorias — Academia Rafael Toro"
    page.theme_mode = ft.ThemeMode.LIGHT

    def esta_logado() -> bool:
        return page.session.contains_key("supabase_client") and page.session.contains_key("perfil_id")

    def view_login() -> ft.View:
        return ft.View("/login", [auth_view(page, lambda: page.go("/app"))])

    def view_app() -> ft.View:
        tabs = ft.Tabs(
            selected_index=0,
            expand=True,
            tabs=[
                ft.Tab(
                    text="Agendamento",
                    icon=ft.Icons.CALENDAR_MONTH,
                    content=agendamento_view(page),
                ),
                ft.Tab(
                    text="Histórico",
                    icon=ft.Icons.HISTORY,
                    content=historico_view(page),
                ),
                ft.Tab(
                    text="Perfil",
                    icon=ft.Icons.PERSON,
                    content=perfil_view(page, lambda: page.go("/login")),
                ),
            ],
        )
        return ft.View("/app", [tabs], padding=0)

    def view_conectar_mentor() -> ft.View:
        """Link secreto e individual: /conectar/<mentor_id>/<token>. Só quem tem o link exato
        de UM mentor consegue conectar a agenda DELE — evita conectar a agenda errada."""
        partes = [p for p in urlsplit(page.route).path.split("/") if p]
        mentor_id = partes[1] if len(partes) > 1 else None
        token = partes[2] if len(partes) > 2 else None

        mentor = mentores_repo.obter_mentor_por_link(mentor_id, token) if mentor_id and token else None

        if mentor is None:
            return ft.View(
                page.route,
                [ft.Text("Link inválido ou expirado.", size=16, color=ft.Colors.ERROR)],
                padding=20,
            )

        def conectar(e: ft.ControlEvent) -> None:
            page.launch_url(google_calendar.build_authorization_url(mentor.id))

        return ft.View(
            page.route,
            [
                ft.Text(f"Olá, {mentor.nome}!", size=20, weight=ft.FontWeight.BOLD),
                ft.Text("Clique abaixo para conectar sua Google Agenda ao sistema de mentorias."),
                ft.ElevatedButton("Conectar Google Agenda", icon=ft.Icons.LINK, on_click=conectar),
            ],
            padding=20,
        )

    def view_oauth_callback() -> ft.View:
        query = parse_qs(urlsplit(page.route).query)
        state = query.get("state", [None])[0]
        code = query.get("code", [None])[0]
        erro = query.get("error", [None])[0]

        if erro:
            texto = f"Autorização cancelada ou negada: {erro}"
        elif not state or not code:
            texto = "Parâmetros inválidos no retorno do Google."
        else:
            try:
                google_calendar.exchange_code_and_save(state, code)
                texto = "Agenda do Google conectada com sucesso! Já pode fechar esta janela."
            except Exception as exc:  # noqa: BLE001
                texto = f"Falha ao conectar a agenda: {exc}"

        return ft.View("/oauth2callback", [ft.Text(texto, size=16)], padding=20)

    def view_configuracao_pendente(detalhe: str) -> ft.View:
        return ft.View(
            page.route,
            [
                ft.Text("Configuração pendente", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(
                    "As variáveis de ambiente do Supabase/Google ainda não foram preenchidas "
                    "(veja o .env.example). Detalhe técnico:"
                ),
                ft.Text(detalhe, color=ft.Colors.ERROR, selectable=True),
            ],
            padding=20,
        )

    def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        rota_base = urlsplit(page.route).path

        try:
            if rota_base == "/oauth2callback":
                page.views.append(view_oauth_callback())
            elif rota_base.startswith("/conectar/"):
                page.views.append(view_conectar_mentor())
            elif rota_base == "/app":
                if not esta_logado():
                    page.go("/login")
                    return
                page.views.append(view_app())
            else:
                page.views.append(view_app() if esta_logado() else view_login())
        except Exception as exc:  # noqa: BLE001 - config ausente/inválida não pode derrubar o app
            page.views.append(view_configuracao_pendente(str(exc)))

        page.update()

    page.on_route_change = route_change
    page.go(page.route)


if __name__ == "__main__":
    # view=None: serve como app web puro, sem tentar abrir um navegador local automaticamente.
    # Em servidores headless (Render) tentar abrir um navegador local trava o processo — use
    # view=ft.AppView.WEB_BROWSER só se quiser que "python main.py" abra seu navegador sozinho
    # ao rodar na SUA máquina local.
    print(f"Mentoria App rodando em http://localhost:{config.PORT}")
    ft.app(target=main, view=None, port=config.PORT, host="0.0.0.0")
