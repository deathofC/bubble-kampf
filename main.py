import pygame, os, sys, random
from datetime import datetime

# Tenta importar as bibliotecas de voz
try:
    import speech_recognition as sr
    import pyttsx3
    VOZ_ATIVADA = True
except ImportError:
    VOZ_ATIVADA = False
    print("Aviso: 'pyttsx3' ou 'SpeechRecognition' não encontradas.")
    print("Para habilitar, instale com: pip install pyttsx3 SpeechRecognition PyAudio")

dirpath = os.getcwd()
sys.path.append(dirpath)
if getattr(sys, 'frozen', False):
    os.chdir(sys._MEIPASS)

# --- 1. CONFIGURAÇÕES GERAIS ---
pygame.init()

# Resolução da tela e do jogo (para o efeito pixelado)
LARGURA_TELA = 1000
ALTURA_TELA = 700
LARGURA_JOGO = 320
ALTURA_JOGO = 224
FPS = 60

# Paleta de Cores
COR_FUNDO = (15, 25, 20)
COR_TEXTO = (100, 255, 120)
COR_CAIXA_INPUT = (25, 50, 40)
COR_BOTAO = (30, 70, 50)
COR_BOTAO_HOVER = (50, 110, 75)
COR_JOGADOR = (80, 255, 100)
COR_BOLHA = (80, 200, 180)
COR_PROJETIL = (255, 80, 150)
COR_DECORACAO = (180, 200, 80)
AMARELO = (200, 220, 50)
CINZA = (70, 110, 80)

# Fontes
NOME_FONTE = 'PressStart2P-Regular.ttf'
TAMANHO_FONTE_GRANDE = 20
TAMANHO_FONTE_MEDIO = 16
TAMANHO_FONTE_PEQUENO = 10
TAMANHO_FONTE_INFO = 8

# Constantes do Jogo
ATRASO_TIRO_JOGADOR = 250

# --- 2. TELA, FONTES E RELÓGIO ---
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
superficie_jogo = pygame.Surface((LARGURA_JOGO, ALTURA_JOGO))
pygame.display.set_caption("Bubble Popper Adventure")
relogio = pygame.time.Clock()
pygame.mixer.music.load('data/assets/OST.mp3')
pygame.mixer.music.play(1)
# Tenta carregar a fonte pixelada, se não, usa uma padrão
try:
    fonte_titulo = pygame.font.Font(NOME_FONTE, TAMANHO_FONTE_GRANDE)
    fonte_botao = pygame.font.Font(NOME_FONTE, TAMANHO_FONTE_MEDIO)
    fonte_pequena = pygame.font.Font(NOME_FONTE, TAMANHO_FONTE_PEQUENO)
    fonte_info = pygame.font.Font(NOME_FONTE, TAMANHO_FONTE_INFO)
    print(f"Fonte '{NOME_FONTE}' carregada.")
except FileNotFoundError:
    print(f"AVISO: Fonte '{NOME_FONTE}' não encontrada. Usando fontes padrão.")
    fonte_titulo = pygame.font.Font(None, 40)
    fonte_botao = pygame.font.Font(None, 28)
    fonte_pequena = pygame.font.Font(None, 20)
    fonte_info = pygame.font.Font(None, 16)

# --- 4. FUNÇÕES AUXILIARES ---
def falar(texto):
    if not VOZ_ATIVADA: return
    try:
        engine = pyttsx3.init(); engine.say(texto); engine.runAndWait()
    except Exception as e: print(f"Erro na síntese de voz: {e}")

def reconhecer_fala(reconhecedor, microfone):
    if not all([VOZ_ATIVADA, reconhecedor, microfone]):
        return {"success": False, "error": "Recursos de voz indisponíveis."}
    with microfone as source:
        reconhecedor.adjust_for_ambient_noise(source, duration=0.5)
        try: audio = reconhecedor.listen(source, timeout=5)
        except sr.WaitTimeoutError: return {"success": False, "error": "Nenhuma fala detectada."}
    
    resposta = {"success": True, "error": None, "transcription": None}
    try: resposta["transcription"] = reconhecedor.recognize_google(audio, language="pt-BR")
    except sr.RequestError: resposta.update({"success": False, "error": "API indisponível"})
    except sr.UnknownValueError: resposta["error"] = "Não entendi o que você disse"
    return resposta

def desenhar_texto(texto, fonte, cor, superficie, x, y, centralizado=False):
    obj_texto = fonte.render(texto, True, cor) # True para anti-aliasing
    rect_texto = obj_texto.get_rect()
    if centralizado: rect_texto.center = (x, y)
    else: rect_texto.topleft = (x, y)
    superficie.blit(obj_texto, rect_texto)

def salvar_log(pontuacao):
    agora = datetime.now()
    log = f"Pontos: {pontuacao}, Data: {agora.strftime('%d-%m-%Y %H:%M:%S')}\n"
    with open("log.dat", "a", encoding="utf-8") as f:
        f.write(log)

def ler_logs():
    try:
        with open("log.dat", "r", encoding="utf-8") as f:
            # Retorna as últimas 5 partidas
            return [linha.strip() for linha in f.readlines()[-5:]]
    except FileNotFoundError:
        return ["Nenhum log encontrado."]

# --- 5. CLASSES DO JOGO ---
class Jogador(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.image.load('data/assets/player2_imresizer.png').convert_alpha()
        
        self.rect = self.image.get_rect(centerx=LARGURA_JOGO / 2, bottom=ALTURA_JOGO - 5)
        self.velocidade_x = 0
        self.ultimo_tiro = pygame.time.get_ticks()

    def update(self):
        self.velocidade_x = 0
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]: self.velocidade_x = -3
        elif teclas[pygame.K_RIGHT]: self.velocidade_x = 3
        
        self.rect.x += self.velocidade_x
        
        # Mantém o jogador dentro da tela
        if self.rect.left < 0: self.rect.left = 0
        if self.rect.right > LARGURA_JOGO: self.rect.right = LARGURA_JOGO

    def atirar(self, todos_os_sprites, projeteis):
        agora = pygame.time.get_ticks()
        if agora - self.ultimo_tiro > ATRASO_TIRO_JOGADOR:
            self.ultimo_tiro = agora
            projetil = Projetil(self.rect.centerx, self.rect.top)
            todos_os_sprites.add(projetil)
            projeteis.add(projetil)

class Projetil(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([4, 10])
        self.image.fill(COR_PROJETIL)
        self.rect = self.image.get_rect(centerx=x, bottom=y)
        self.velocidade_y = -5

    def update(self):
        self.rect.y += self.velocidade_y
        # Remove o projétil se ele sair da tela
        if self.rect.bottom < 0:
            self.kill()

class Bolha(pygame.sprite.Sprite):
    def __init__(self, tamanho):
        super().__init__()
        self.image = pygame.Surface([tamanho, tamanho], pygame.SRCALPHA)
        pygame.draw.circle(self.image, COR_BOLHA, (tamanho//2, tamanho//2), tamanho//2)
        
        # Posição inicial aleatória
        self.rect = self.image.get_rect(
            x=random.randrange(0, LARGURA_JOGO - tamanho),
            y=random.randrange(-50, -20)
        )
        self.velocidade_y = random.uniform(0.5, 2.0)
        self.velocidade_x = random.uniform(-1.5, 1.5)

    def update(self):
        self.rect.y += self.velocidade_y
        self.rect.x += self.velocidade_x
        # Se a bolha sair da tela, reposiciona ela em cima
        if self.rect.top > ALTURA_JOGO or self.rect.left > LARGURA_JOGO or self.rect.right < 0:
            self.rect.x = random.randrange(0, LARGURA_JOGO - self.rect.width)
            self.rect.y = random.randrange(-50, -20)

class ObjetoDecorativo(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.tamanho = 12
        self.image = pygame.Surface([self.tamanho, self.tamanho])
        self.image.fill(COR_DECORACAO)
        self.rect = self.image.get_rect(
            center=(random.randrange(self.tamanho, LARGURA_JOGO - self.tamanho),
                    random.randrange(self.tamanho, ALTURA_JOGO - self.tamanho))
        )
        self.velocidade_x = random.choice([-1, 1])
        self.velocidade_y = random.choice([-1, 1])

    def update(self):
        self.rect.x += self.velocidade_x
        self.rect.y += self.velocidade_y
        # Bate e volta nas bordas da tela
        if self.rect.left < 0 or self.rect.right > LARGURA_JOGO: self.velocidade_x *= -1
        if self.rect.top < 0 or self.rect.bottom > ALTURA_JOGO: self.velocidade_y *= -1

# --- 6. TELAS E LÓGICA PRINCIPAL ---
def redimensionar_e_desenhar(superficie_alvo):
    # Desenha a superficie do jogo (baixa res) na tela principal (alta res)
    superficie_escalada = pygame.transform.scale(superficie_jogo, (LARGURA_TELA, ALTURA_TELA))
    superficie_alvo.blit(superficie_escalada, (0, 0))
    pygame.display.flip()

def obter_pos_mouse_escalada():
    mx, my = pygame.mouse.get_pos()
    escala_x = LARGURA_TELA / LARGURA_JOGO
    escala_y = ALTURA_TELA / ALTURA_JOGO
    return (mx / escala_x, my / escala_y)

def tela_obter_nome():
    nome_usuario = ''
    caixa_input = pygame.Rect((LARGURA_JOGO - 200) / 2, 100, 200, 25)
    botao_voz = pygame.Rect(caixa_input.centerx - 60, caixa_input.bottom + 10, 120, 20)
    reconhecedor = sr.Recognizer() if VOZ_ATIVADA else None
    microfone = sr.Microphone() if VOZ_ATIVADA else None
    rodando = True
    
    while rodando:
        pos_mouse = obter_pos_mouse_escalada()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if botao_voz.collidepoint(pos_mouse) and VOZ_ATIVADA:
                    desenhar_texto("Ouvindo...", fonte_pequena, COR_TEXTO, superficie_jogo, botao_voz.centerx, botao_voz.centery, True)
                    redimensionar_e_desenhar(tela)
                    resposta = reconhecer_fala(reconhecedor, microfone)
                    if resposta["success"] and resposta["transcription"]:
                        nome_usuario = resposta["transcription"].title()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_RETURN:
                    if nome_usuario: rodando = False
                elif evento.key == pygame.K_BACKSPACE:
                    nome_usuario = nome_usuario[:-1]
                else:
                    nome_usuario += evento.unicode
        
        superficie_jogo.fill(COR_FUNDO)
        desenhar_texto("INSIRA SEU NOME", fonte_titulo, COR_TEXTO, superficie_jogo, LARGURA_JOGO / 2, 60, True)
        
        pygame.draw.rect(superficie_jogo, COR_CAIXA_INPUT, caixa_input)
        pygame.draw.rect(superficie_jogo, COR_TEXTO, caixa_input, 1) # Borda
        desenhar_texto(nome_usuario, fonte_botao, COR_TEXTO, superficie_jogo, caixa_input.x + 5, caixa_input.y + 5)
        
        if VOZ_ATIVADA:
            cor_btn = COR_BOTAO_HOVER if botao_voz.collidepoint(pos_mouse) else COR_BOTAO
            pygame.draw.rect(superficie_jogo, cor_btn, botao_voz)
            desenhar_texto("Ditar Nome", fonte_pequena, COR_TEXTO, superficie_jogo, botao_voz.centerx, botao_voz.centery, True)
        
        desenhar_texto("Pressione ENTER", fonte_pequena, CINZA, superficie_jogo, LARGURA_JOGO / 2, caixa_input.bottom + 40, True)
        redimensionar_e_desenhar(tela)
        
    return nome_usuario

def menu_principal(nome_usuario):
    falar(f"Bem-vindo, {nome_usuario}!")
    botao_iniciar = pygame.Rect((LARGURA_JOGO - 100) / 2, 120, 100, 40)
    while True:
        pos_mouse = obter_pos_mouse_escalada()
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if evento.type == pygame.MOUSEBUTTONDOWN:
                if botao_iniciar.collidepoint(pos_mouse): return True
                
        superficie_jogo.fill(COR_FUNDO)
        desenhar_texto(f"Bem-vindo,", fonte_pequena, COR_TEXTO, superficie_jogo, LARGURA_JOGO / 2, 60, True)
        desenhar_texto(nome_usuario, fonte_botao, COR_TEXTO, superficie_jogo, LARGURA_JOGO / 2, 85, True)
        
        cor_btn = COR_BOTAO_HOVER if botao_iniciar.collidepoint(pos_mouse) else COR_BOTAO
        pygame.draw.rect(superficie_jogo, cor_btn, botao_iniciar)
        desenhar_texto("INICIAR", fonte_botao, COR_TEXTO, superficie_jogo, botao_iniciar.centerx, botao_iniciar.centery, True)
        
        redimensionar_e_desenhar(tela)

def tela_fim_de_jogo(pontuacao_final):
    salvar_log(pontuacao_final)
    logs = ler_logs()
    esperando = True
    while esperando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: pygame.quit(); sys.exit()
            if evento.type == pygame.KEYUP: esperando = False
            
        superficie_jogo.fill(COR_FUNDO)
        desenhar_texto("FIM DE JOGO", fonte_titulo, COR_TEXTO, superficie_jogo, LARGURA_JOGO/2, 40, True)
        desenhar_texto(f"Pontos: {pontuacao_final}", fonte_botao, COR_TEXTO, superficie_jogo, LARGURA_JOGO/2, 80, True)
        desenhar_texto("Últimas Partidas:", fonte_pequena, AMARELO, superficie_jogo, LARGURA_JOGO/2, 110, True)
        
        y_pos = 130
        for log in logs:
            desenhar_texto(log, fonte_info, COR_TEXTO, superficie_jogo, LARGURA_JOGO/2, y_pos, True)
            y_pos += 15
            
        desenhar_texto("Pressione qualquer tecla", fonte_pequena, CINZA, superficie_jogo, LARGURA_JOGO/2, ALTURA_JOGO - 20, True)
        redimensionar_e_desenhar(tela)

def loop_do_jogo():
    # Estado do jogo
    pausado = False
    pontuacao_bolhas = 0
    temporizador_geral = 0
    rodando = True

    # Grupos de sprites
    todos_os_sprites = pygame.sprite.Group()
    bolhas = pygame.sprite.Group()
    projeteis = pygame.sprite.Group()

    # Criação dos objetos iniciais
    jogador = Jogador()
    objeto_deco = ObjetoDecorativo()
    todos_os_sprites.add(jogador, objeto_deco)
    
    # Efeito de pulsar para o "sol"
    raio_sol = 20
    pulso_sol = 0.1

    while rodando:
        relogio.tick(FPS)
        
        # Gerenciador de eventos
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT: rodando = False
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_SPACE: pausado = not pausado
        
        if not pausado:
            # --- Lógica do Jogo ---
            teclas = pygame.key.get_pressed()
            if teclas[pygame.K_UP]: jogador.atirar(todos_os_sprites, projeteis)
            
            temporizador_geral += 1
            todos_os_sprites.update()
            
            # Adiciona uma nova bolha a cada 1.5 segundos
            if temporizador_geral % (FPS * 1.5) == 0:
                nova_bolha = Bolha(random.choice([18, 24, 30]))
                todos_os_sprites.add(nova_bolha)
                bolhas.add(nova_bolha)
            
            # Verifica colisão entre projéteis e bolhas
            acertos = pygame.sprite.groupcollide(projeteis, bolhas, True, True)
            if acertos:
                pontuacao_bolhas += len(acertos) * 10
            
            # Verifica colisão entre jogador e bolhas (fim de jogo)
            if pygame.sprite.spritecollide(jogador, bolhas, False):
                rodando = False
        
        # --- Desenho na tela ---
        superficie_jogo.fill(COR_FUNDO)
        
        # Sol pulsante no fundo
        raio_sol += pulso_sol
        if raio_sol > 25 or raio_sol < 20: pulso_sol *= -1
        pygame.draw.circle(superficie_jogo, AMARELO, (LARGURA_JOGO - 30, 30), int(raio_sol))
        
        todos_os_sprites.draw(superficie_jogo)
        
        # Calcula e exibe a pontuação
        pontos_por_tempo = temporizador_geral // FPS
        pontuacao_total = pontos_por_tempo + pontuacao_bolhas
        desenhar_texto(f"SCORE:{pontuacao_total}", fonte_pequena, COR_TEXTO, superficie_jogo, 5, 5)
        desenhar_texto("ESPAÇO: PAUSE", fonte_info, CINZA, superficie_jogo, 5, 18)

        # Exibe a tela de pausa se o jogo estiver pausado
        if pausado:
            desenhar_texto("PAUSA", fonte_titulo, COR_TEXTO, superficie_jogo, LARGURA_JOGO / 2, ALTURA_JOGO / 2, True)

        redimensionar_e_desenhar(tela)
        
    return pontuacao_total

# --- 7. EXECUÇÃO PRINCIPAL ---
if __name__ == '__main__':
    nome_jogador = tela_obter_nome()
    if nome_jogador:
        if menu_principal(nome_jogador):
            pontuacao_final = loop_do_jogo()
            tela_fim_de_jogo(pontuacao_final)
            
    pygame.quit()
    sys.exit()