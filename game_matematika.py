import pygame
import random
import sys
import math
from abc import ABC, abstractmethod
import json # Tambahkan: Untuk penyimpanan data level

# --- KONFIGURASI ---
WIDTH, HEIGHT = 850, 650
FPS = 60

COLORS = {
    'bg_soft': (245, 247, 255),
    'primary': (100, 149, 237),
    'secondary': (255, 105, 180),
    'white': (255, 255, 255),
    'text_dark': (44, 62, 80),
    'accent': (255, 215, 0),
    'particle': (255, 105, 180), 
    'bg_symbol': (180, 190, 220),
    'locked': (180, 180, 180)
}

# --- 1. ENCAPSULATION & STRUKTUR DATA KOMPLEKS (Level & Score Management) ---
class LevelManager:
    """
    Mengelola progress level menggunakan Dictionary dan Enkapsulasi.
    Mengimplementasikan persistensi data menggunakan file JSON.
    """
    def __init__(self, filename='level_data.json'):
        self.filename = filename
        # Struktur Data: Dictionary of Dictionaries untuk menyimpan status dan skor
        self._level_data = {i: {"unlocked": False, "best_score": 0} for i in range(1, 9)}
        
        self.load_data() # Memuat data yang tersimpan saat objek dibuat
        
        # Level 1 selalu terbuka, memastikan game selalu bisa dimulai
        self._level_data[1]["unlocked"] = True 

    def is_unlocked(self, level):
        """Mengecek status apakah suatu level sudah terbuka."""
        return self._level_data.get(level, {}).get("unlocked", False)

    def unlock_next(self, current_level):
        """Membuka level berikutnya jika tersedia dan menyimpan data."""
        if current_level + 1 in self._level_data:
            self._level_data[current_level + 1]["unlocked"] = True
            self.save_data()

    def load_data(self):
        """Mencoba memuat data level dari file JSON."""
        try:
            with open(self.filename, 'r') as f:
                # Kunci JSON adalah string, konversi kembali ke integer
                loaded_data = json.load(f)
                self._level_data = {int(k): v for k, v in loaded_data.items()}
            # print("Level data berhasil dimuat.") # Debugging
        except FileNotFoundError:
            # print("File data tidak ditemukan. Membuat data baru.") # Debugging
            self.save_data() 
        except Exception:
            # print(f"Error memuat data: {e}. Menggunakan data default.") # Debugging
            pass # Lanjut dengan data default jika gagal

    def save_data(self):
        """Menyimpan data level ke file JSON."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self._level_data, f, indent=4)
            # print("Level data berhasil disimpan.") # Debugging
        except Exception:
            # print(f"Error menyimpan data: {e}") # Debugging
            pass

# --- 2. DEKORASI & PARTIKEL ---
class BackgroundSymbol:
    """Objek dekorasi latar belakang, bergerak dan berputar lambat."""
    def __init__(self):
        self.size = random.randint(25, 50)
        self.font = pygame.font.SysFont("Arial", self.size, bold=True)
        self.text = random.choice(["+", "-", "×", "÷", "π", "√", "∑", "∞", "Δ", "Ω"])
        self.x, self.y = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.speed = random.uniform(0.6, 1.5)
        self.angle = random.randint(0, 360)
        self.rot_speed = random.uniform(0.2, 0.8)

    def update(self):
        """Memperbarui posisi dan rotasi simbol."""
        self.y -= self.speed
        self.angle += self.rot_speed
        if self.y < -60: # Reset posisi simbol ke bawah jika keluar layar
            self.y = HEIGHT + 60
            self.x = random.randint(0, WIDTH)

    def draw(self, screen):
        """Menggambar simbol dengan sedikit transparansi."""
        surf = self.font.render(self.text, True, COLORS['bg_symbol'])
        surf.set_alpha(110)
        rot_surf = pygame.transform.rotate(surf, self.angle)
        screen.blit(rot_surf, (self.x, self.y))

class Particle:
    """Objek partikel yang muncul saat jawaban benar (efek visual)."""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.vx, self.vy = random.uniform(-5, 5), random.uniform(-5, 5)
        self.lifetime = 255 # Alpha value

    def update(self):
        """Memperbarui posisi dan mengurangi lifetime (transparansi)."""
        self.x += self.vx; self.y += self.vy; self.lifetime -= 10

    def draw(self, screen):
        """Menggambar partikel jika masih hidup."""
        if self.lifetime > 0:
            s = pygame.Surface((8, 8), pygame.SRCALPHA)
            # Warna partikel menggunakan alpha (lifetime)
            pygame.draw.circle(s, (*COLORS['particle'], int(self.lifetime)), (4, 4), 4)
            screen.blit(s, (self.x, self.y))

# --- 3. ENCAPSULATION: CHARACTER DENGAN GETTER/SETTER ---
class Character:
    """Karakter/Maskot yang memberikan feedback visual melalui animasinya."""
    def __init__(self, x, y):
        self._x = x  # Atribut privat (Enkapsulasi)
        self._y = y
        self.jump, self.shake, self.timer = 0, 0, 0
        self.state = "IDLE" # Status: IDLE, HAPPY, SAD

    @property
    def position(self):
        """Getter untuk posisi (Enkapsulasi)."""
        return (self._x, self._y)

    @position.setter
    def position(self, value):
        """Setter untuk posisi (Enkapsulasi)."""
        self._x, self._y = value

    def update(self):
        """Memperbarui animasi karakter berdasarkan state."""
        self.timer += 0.1
        if self.state == "IDLE": 
            self.jump = math.sin(self.timer) * 8 # Animasi bernapas
            self.shake = 0
        elif self.state == "HAPPY": 
            self.jump = abs(math.sin(self.timer * 3)) * -40 # Melompat bahagia
        elif self.state == "SAD": 
            self.shake = math.sin(self.timer * 15) * 8 # Bergoyang sedih
            
        # Reset state setelah durasi tertentu
        if self.state != "IDLE" and self.timer > 2: 
            self.state = "IDLE"; self.timer = 0

    def draw(self, screen):
        """Menggambar karakter (bola kuning dengan mata dan mulut)."""
        pos_x, pos_y = self.position
        # Perhitungan posisi dengan efek animasi (jump/shake)
        r = pygame.Rect(pos_x + self.shake - 40, pos_y + self.jump - 40, 80, 80)
        pygame.draw.ellipse(screen, COLORS['accent'], r) # Wajah
        # Mata
        pygame.draw.circle(screen, (0,0,0), (r.centerx-15, r.centery-10), 5)
        pygame.draw.circle(screen, (0,0,0), (r.centerx+15, r.centery-10), 5)
        # Mulut (arc)
        arc_r = (r.x+20, r.y+35, 40, 30) if self.state != "SAD" else (r.x+20, r.y+45, 40, 20)
        start_angle = math.pi if self.state != "SAD" else 0
        end_angle = 0 if self.state != "SAD" else math.pi
        pygame.draw.arc(screen, (0,0,0), arc_r, start_angle, end_angle, 3)

# --- 4. ABSTRACTION & POLYMORPHISM & INHERITANCE: MATH ENGINE ---
class MathEngine(ABC):
    """Kelas Abstrak untuk mendefinisikan blueprint operasi matematika."""
    def __init__(self, level):
        # Limit angka didasarkan pada level
        self.limit = 5 + (level * 5)
        self.num1, self.num2 = random.randint(1, self.limit), random.randint(1, self.limit)
        self.ans, self.sym = 0, ""
        
    @abstractmethod
    def generate(self):
        """Method abstrak: Wajib diimplementasikan untuk menghasilkan soal dan jawaban."""
        pass

class Addition(MathEngine):
    """Subclass: Mengimplementasikan operasi Penjumlahan."""
    def generate(self): 
        self.ans = self.num1 + self.num2
        self.sym = "+"

class Subtraction(MathEngine):
    """Subclass: Mengimplementasikan operasi Pengurangan."""
    def generate(self):
        # Memastikan hasil tidak negatif
        if self.num1 < self.num2: self.num1, self.num2 = self.num2, self.num1
        self.ans = self.num1 - self.num2
        self.sym = "-"

class Multiplication(MathEngine):
    """Subclass: Mengimplementasikan operasi Perkalian."""
    def generate(self):
        # Batasan perkalian lebih kecil agar tidak terlalu sulit
        self.num1 = random.randint(1, 5 + (self.limit // 10))
        self.num2 = random.randint(1, 10)
        self.ans = self.num1 * self.num2
        self.sym = "x"

# --- 5. MAIN APP ---
class MathBuddyApp:
    """Kelas Utama yang Mengelola semua alur aplikasi (menu, level, game loop)."""
    def __init__(self):
        """Inisialisasi Pygame, assets, dan objek utama."""
        pygame.init(); pygame.mixer.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("MathBuddy: Level Adventure")
        self.clock = pygame.time.Clock()
        self.font_big = pygame.font.SysFont("Arial Rounded MT Bold", 70)
        self.font_sm = pygame.font.SysFont("Arial Rounded MT Bold", 28)
        
        # Inisialisasi Objek dengan OOP
        self.lvl_manager = LevelManager()
        self.character = Character(WIDTH // 2, 120)
        self.bg_symbols = [BackgroundSymbol() for _ in range(35)]
        self.particles = []
        
        # Pemuatan suara (dengan penanganan error jika file tidak ditemukan)
        try:
            self.snd_ok = pygame.mixer.Sound('correct.mp3')
            self.snd_wrong = pygame.mixer.Sound('incorrect.mp3')
            pygame.mixer.music.load('gamez.mp3')
            pygame.mixer.music.play(-1)
        except: 
            self.snd_ok = self.snd_wrong = None
            print("Perhatian: File audio tidak ditemukan. Game berjalan tanpa suara.")

    def draw_base(self):
        """Menggambar latar belakang dan simbol dekorasi."""
        self.screen.fill(COLORS['bg_soft'])
        for s in self.bg_symbols: 
            s.update()
            s.draw(self.screen)

    def draw_text(self, text, y, font, color, x=WIDTH//2):
        """Fungsi pembantu untuk menggambar teks di tengah layar (default)."""
        surf = font.render(text, True, color)
        self.screen.blit(surf, surf.get_rect(center=(x, y)))

    def start_menu(self):
        """Menampilkan menu awal."""
        while True:
            self.draw_base()
            self.character.update(); self.character.draw(self.screen)
            self.draw_text("MathBuddy", 250, self.font_big, COLORS['primary'])
            
            # Tombol MULAI
            btn = pygame.Rect(WIDTH//2-100, 400, 200, 60)
            pygame.draw.rect(self.screen, COLORS['secondary'], btn, border_radius=15)
            self.draw_text("MULAI", 430, self.font_sm, COLORS['white'])
            
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(e.pos): return
                
            pygame.display.flip(); self.clock.tick(FPS)

    def level_selection(self):
        """Menampilkan layar pemilihan level."""
        while True:
            self.draw_base()
            self.draw_text("PILIH LEVEL", 100, self.font_big, COLORS['primary'])
            btns = []
            cols = 4
            start_x, start_y = (WIDTH - (cols*120))//2 + 60, 250
            
            # Loop untuk membuat tombol level
            for i in range(1, 9):
                r = pygame.Rect(0, 0, 100, 100)
                r.center = (start_x + ((i-1) % cols)*120, start_y + ((i-1) // cols)*120)
                unlocked = self.lvl_manager.is_unlocked(i)
                color = COLORS['secondary'] if unlocked else COLORS['locked']
                
                pygame.draw.rect(self.screen, color, r, border_radius=15)
                txt = str(i) if unlocked else "X"
                self.draw_text(txt, r.centery, self.font_sm, COLORS['white'], r.centerx)
                btns.append((r, i))

            # Tombol KEMBALI
            back_btn = pygame.Rect(WIDTH//2-100, 555, 200, 50)
            pygame.draw.rect(self.screen, (150, 150, 150), back_btn, border_radius=10)
            self.draw_text("KEMBALI", 580, self.font_sm, COLORS['white'])
            
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if back_btn.collidepoint(e.pos): return None # Kembali ke menu awal
                    for rect, l_num in btns:
                        # Memilih level hanya jika sudah terbuka
                        if rect.collidepoint(e.pos) and self.lvl_manager.is_unlocked(l_num): 
                            return l_num
                            
            pygame.display.flip(); self.clock.tick(FPS)

    def play_level(self, level):
        """Game loop utama untuk level yang dipilih (10 soal)."""
        q_idx, lives = 1, 3 # Inisialisasi nomor soal dan nyawa
        
        while q_idx <= 10 and lives > 0:
            # Polimorfisme: Menentukan operasi yang tersedia berdasarkan level
            ops = [Addition, Subtraction]
            if level >= 3: ops.append(Multiplication)
            
            # Membuat soal baru (Polimorfisme)
            task = random.choice(ops)(level)
            task.generate()
            
            # Menyiapkan opsi jawaban (mengandung jawaban benar dan jawaban pengecoh)
            opts = [task.ans, task.ans+random.randint(1,5), task.ans-random.randint(1,5)]
            random.shuffle(opts)
            
            ans_done = False
            while not ans_done and lives > 0:
                self.draw_base()
                
                # Update dan gambar partikel
                for p in self.particles[:]:
                    p.update(); p.draw(self.screen)
                    if p.lifetime <= 0: self.particles.remove(p)
                    
                self.character.update(); self.character.draw(self.screen)
                
                # UI Info
                self.draw_text(f"LEVEL {level} - Soal {q_idx}/10", 60, self.font_sm, COLORS['text_dark'])
                self.draw_text(f"NYAWA: {'Σ' * lives}", 40, self.font_sm, COLORS['secondary'], WIDTH-150)
                
                # Kotak Soal
                pygame.draw.rect(self.screen, COLORS['white'], (WIDTH//2-180, 200, 360, 100), border_radius=20)
                self.draw_text(f"{task.num1} {task.sym} {task.num2} = ?", 250, self.font_big, COLORS['primary'])
                
                # Opsi Jawaban
                choices = []
                for i, o in enumerate(opts):
                    r = pygame.Rect(WIDTH//2-120, 340+(i*75), 240, 60)
                    pygame.draw.rect(self.screen, COLORS['primary'], r, border_radius=12)
                    self.draw_text(str(o), r.centery, self.font_sm, COLORS['white'])
                    choices.append((r, o))
                    
                # Event Handling Jawaban
                for e in pygame.event.get():
                    if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                    if e.type == pygame.MOUSEBUTTONDOWN:
                        for rect, val in choices:
                            if rect.collidepoint(e.pos):
                                if val == task.ans:
                                    # Jawaban Benar
                                    if self.snd_ok: self.snd_ok.play()
                                    for _ in range(15): self.particles.append(Particle(rect.centerx, rect.centery))
                                    self.character.state = "HAPPY"
                                    q_idx += 1
                                else:
                                    # Jawaban Salah
                                    if self.snd_wrong: self.snd_wrong.play()
                                    lives -= 1
                                    self.character.state = "SAD"
                                
                                ans_done = True
                                self.character.timer = 0 # Reset timer animasi
                                
                pygame.display.flip(); self.clock.tick(FPS)
                
        # Hasil Akhir Level
        if lives > 0:
            self.lvl_manager.unlock_next(level) # Buka level berikutnya
            return "WIN"
        return "LOSE"

    def result_screen(self, status):
        """Menampilkan layar hasil (Menang atau Kalah)."""
        while True:
            self.draw_base(); self.character.update(); self.character.draw(self.screen)
            title = "LEVEL BERHASIL!" if status == "WIN" else "GAME OVER!"
            color = COLORS['primary'] if status == "WIN" else COLORS['secondary']
            self.draw_text(title, 250, self.font_big, color)
            
            # Tombol OK
            btn = pygame.Rect(WIDTH//2-100, 400, 200, 60)
            pygame.draw.rect(self.screen, COLORS['secondary'], btn, border_radius=15)
            self.draw_text("OK", 430, self.font_sm, COLORS['white'])
            
            for e in pygame.event.get():
                if e.type == pygame.QUIT: pygame.quit(); sys.exit()
                if e.type == pygame.MOUSEBUTTONDOWN and btn.collidepoint(e.pos): return
                
            pygame.display.flip(); self.clock.tick(FPS)

if __name__ == "__main__":
    app = MathBuddyApp()
    while True:
        app.start_menu()
        while True:
            chosen_lvl = app.level_selection()
            if chosen_lvl is None: 
                break
            res = app.play_level(chosen_lvl)
            app.result_screen(res)