import pygame
from customtkinter import *
from pygame import *
import socket
import json
from threading import Thread
import time
# Лаунчер

class ConnectWindow(CTk):
    def __init__(self):
        super().__init__()

        self.name = None
        self.host = None
        self.port = None

        # --- Дизайн лаунчера ---
        self.title('Ping-Pong Launcher')
        self.geometry('350x450')
        self.configure(fg_color="#222222")

        CTkLabel(self, text='🎾 Ping-Pong Launcher', font=('Comic Sans MS', 24, 'bold'), text_color="#00FFAA").pack(pady=20)

        CTkLabel(self, text='Введіть своє ім`я:', font=('Arial', 16)).pack(pady=(10,0))
        self.name_entry = CTkEntry(self, placeholder_text='Ваше ім`я', height=40)
        self.name_entry.pack(padx=20, fill='x')

        CTkLabel(self, text='Хост сервера:', font=('Arial', 16)).pack(pady=(10,0))
        self.host_entry = CTkEntry(self, placeholder_text='localhost', height=40)
        self.host_entry.pack(padx=20, fill='x')

        CTkLabel(self, text='Порт сервера:', font=('Arial', 16)).pack(pady=(10,0))
        self.port_entry = CTkEntry(self, placeholder_text='8080', height=40)
        self.port_entry.pack(padx=20, fill='x')

        CTkButton(self, text='Грати', command=self.open_game, height=50, fg_color="#00FFAA", hover_color="#00CC88").pack(pady=20, padx=40, fill='x')
        CTkButton(self, text='Вихід', command=self.destroy, height=40, fg_color="#FF5555", hover_color="#CC4444").pack(pady=10, padx=40, fill='x')

    def open_game(self):
        self.name = self.name_entry.get()
        self.host = self.host_entry.get()
        self.port = int(self.port_entry.get())
        self.destroy()

def connect_to_server(host, port):
    while True:
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((host, port))
            buffer = ""
            game_state = {}
            my_id = int(client.recv(24).decode())
            return my_id, game_state, buffer, client
        except:
            pass

def run_game(name, host, port):
    # --- Pygame ---
    WIDTH, HEIGHT = 800, 600
    init()
    screen = display.set_mode((WIDTH, HEIGHT))
    display.set_caption("Ping-Pong")
    clock = pygame.time.Clock()
    # --- фон ---
    bg = image.load("images.jfif").convert()  # заміни на свій фон
    bg = transform.scale(bg, (WIDTH, HEIGHT))
    # --- звук ---
    pygame.mixer.init()
    pygame.mixer.music.load("bensound-leftorright (1).mp3")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
    # --- підключення до сервера ---
    my_id, game_state, buffer, client = connect_to_server(host, port)
    game_over = False
    you_winner = None

    # --- прийом даних ---
    def receive():
        nonlocal game_state, buffer, game_over
        while not game_over:
            try:
                data = client.recv(1024).decode()
                buffer += data
                while "\n" in buffer:
                    packet, buffer = buffer.split("\n", 1)
                    if packet.strip():
                        game_state = json.loads(packet)
            except:
                game_state["winner"] = -1
                break

    Thread(target=receive, daemon=True).start()

    # --- шрифти ---
    font_win = font.Font(None, 72)
    font_main = font.Font(None, 36)

    while True:
        for e in event.get():
            if e.type == QUIT:
                exit()

        screen.blit(bg, (0, 0))

        if "countdown" in game_state and game_state["countdown"] > 0:
            countdown_text = font.Font(None, 72).render(str(game_state["countdown"]), True, (255, 255, 255))
            screen.blit(countdown_text, (WIDTH // 2 - 20, HEIGHT // 2 - 30))
            display.update()
            continue

        if "winner" in game_state and game_state["winner"] is not None:
            if you_winner is None:
                you_winner = (game_state["winner"] == my_id)

            text = "Ти переміг!" if you_winner else "Пощастить наступним разом!"
            win_text = font_win.render(text, True, (255, 215, 0))
            text_rect = win_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(win_text, text_rect)

            text2 = font_win.render('К - рестарт', True, (255, 215, 0))
            text_rect2 = text2.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 120))
            screen.blit(text2, text_rect2)

            display.update()
            continue

        if game_state:
            # Малюємо платформи та м'яч
            draw.rect(screen, (0, 255, 0), (20, game_state['paddles']['0'], 20, 100))
            draw.rect(screen, (255, 0, 255), (WIDTH - 40, game_state['paddles']['1'], 20, 100))
            draw.circle(screen, (255, 255, 255), (game_state['ball']['x'], game_state['ball']['y']), 10)
            score_text = font_main.render(f"{game_state['scores'][0]} : {game_state['scores'][1]}", True, (255, 255, 255))
            screen.blit(score_text, (WIDTH // 2 - 25, 20))
        else:
            waiting_text = font_main.render(f"Очікування гравців...", True, (255, 255, 255))
            screen.blit(waiting_text, (WIDTH // 2 - 100, HEIGHT // 2))

        display.update()
        clock.tick(60)

        keys_pressed = key.get_pressed()
        if keys_pressed[K_w]:
            client.send(b"UP")
        elif keys_pressed[K_s]:
            client.send(b"DOWN")

# -------------------
# Запуск лаунчера
# -------------------
if __name__ == "__main__":
    win = ConnectWindow()
    win.mainloop()
    if win.name and win.host and win.port:
        run_game(win.name, win.host, win.port)
