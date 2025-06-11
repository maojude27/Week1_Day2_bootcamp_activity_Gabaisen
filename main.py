import flet as ft

def main(page: ft.Page):
    page.title = "Phone UI"
    page.window.width = 400
    page.window.height = 800
    page.bgcolor = "black"

    # Header
    header = ft.Container(
        content=ft.Row(
            [
                ft.Image(src="avatar.jpeg", width=40, height=40),
                ft.Text("Jude Thaddeus R. Gabaisen", size=20, weight=ft.FontWeight.BOLD),
            ],
            alignment=ft.MainAxisAlignment.START,
            spacing=10,
        ),
        padding=ft.padding.all(16),
        bgcolor="black",
        height=80,
    )

    # Main content area
    content = ft.Container(
        content=ft.Text("", size=16),
        alignment=ft.alignment.center,
        expand=True,
    )

    # Bottom Navigation Bar
    page.navigation_bar = ft.NavigationBar(
        destinations=[
            ft.NavigationBarDestination(icon="home", label="Home"),
            ft.NavigationBarDestination(icon="chat", label="Chat"),
            ft.NavigationBarDestination(icon="settings", label="Settings"),
        ]
    )

    page.add(
        ft.Column(
            [header, content],
            spacing=0,
            expand=True,
        )
    )

ft.app(target=main)