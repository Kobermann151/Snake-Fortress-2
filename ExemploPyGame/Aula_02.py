import pygame
import random

pygame.init()

LARGURA = 1000
ALTURA = 700
GRID = 20

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Snake Duel Future - Corrigido")

clock = pygame.time.Clock()

fonte = pygame.font.SysFont("Arial", 24, True)
fonte_g = pygame.font.SysFont("Arial", 60, True)
fonte_m = pygame.font.SysFont("Arial", 32, True)

CORES = [(255,255,0),(255,70,70),(80,150,255)]

FUNDO = (12,12,18)
FUNDO_FLASH = (35,35,55)
HUD = (25,25,35)
BRANCO = (240,240,240)
VERDE = (0,255,120)
AMARELO = (255,220,80)

# ---------------------------------------------------------------------
# Carregamento de imagens (opcional). Se o arquivo não existir ou não
# puder ser lido, o jogo cai automaticamente no desenho geométrico
# original (retângulo/círculo), sem travar.
# Coloque os arquivos em uma pasta "assets/" ao lado do script:
#   assets/cabeca_p1.png         -> cabeça (viva) da cobra do Player 1
#   assets/cabeca_p2.png         -> cabeça (viva) da cobra do Player 2
#   assets/cabeca_p1_morte.png   -> cabeça da cobra do Player 1 ao morrer
#   assets/cabeca_p2_morte.png   -> cabeça da cobra do Player 2 ao morrer
#   assets/fruta1.png ... fruta5.png -> 5 variações visuais da comida
#                                       (todas valem os mesmos pontos,
#                                        é só estética, sorteada ao nascer)
#   assets/bomba.png             -> bomba
#   assets/menu_fundo.jpg (ou .png) -> imagem de fundo da tela de menu
#                                       (redimensionada para cobrir a tela
#                                        inteira, cortando o excesso)
# ---------------------------------------------------------------------

def carregar_imagem(caminho, tamanho):
    try:
        img = pygame.image.load(caminho).convert_alpha()
        return pygame.transform.smoothscale(img, (tamanho, tamanho))
    except (pygame.error, FileNotFoundError):
        return None

def carregar_fundo(caminho, largura_alvo, altura_alvo):
    """Carrega uma imagem de fundo e a redimensiona para cobrir totalmente
    a área alvo (estilo 'background-size: cover'), cortando o excesso
    para não distorcer a proporção original. Retorna None se falhar."""
    try:
        img = pygame.image.load(caminho).convert()
    except (pygame.error, FileNotFoundError):
        return None

    w,h = img.get_size()
    escala = max(largura_alvo / w, altura_alvo / h)
    novo_w, novo_h = int(w*escala)+1, int(h*escala)+1

    img = pygame.transform.smoothscale(img, (novo_w, novo_h))

    # Recorta o centro da imagem redimensionada para bater exatamente
    # com o tamanho alvo
    x_corte = (novo_w - largura_alvo) // 2
    y_corte = (novo_h - altura_alvo) // 2

    superficie = pygame.Surface((largura_alvo, altura_alvo))
    superficie.blit(img, (0,0), (x_corte, y_corte, largura_alvo, altura_alvo))

    return superficie

IMG_CABECA_P1       = carregar_imagem("imagens/cabeca_p1.png", GRID)
IMG_CABECA_P2       = carregar_imagem("assets/cabeca_p2.png", GRID)
IMG_CABECA_P1_MORTE = carregar_imagem("assets/cabeca_p1_morte.png", GRID)
IMG_CABECA_P2_MORTE = carregar_imagem("assets/cabeca_p2_morte.png", GRID)
IMG_BOMBA           = carregar_imagem("assets/bomba.png", GRID)
IMG_FUNDO_MENU       = carregar_fundo("assets/menu_fundo.jpg", LARGURA, ALTURA)

# Lista com as 5 frutas. Imagens ausentes viram None e são ignoradas
# automaticamente na hora de sortear (fallback pro retângulo verde).
IMAGENS_FRUTAS = [
    carregar_imagem(f"assets/fruta{i}.png", GRID) for i in range(1,6)
]

# Estados possíveis do jogo
MENU = "menu"
JOGANDO = "jogando"
FIM = "fim"

class Snake:

    def __init__(self,x,y,cor,img_cabeca=None,img_cabeca_morte=None):
        self.body = [(x,y)]
        self.dir = (1,0)
        self.size = 5
        self.score = 0
        self.cor = cor
        self.img_cabeca = img_cabeca              # cabeça viva
        self.img_cabeca_morte = img_cabeca_morte   # cabeça ao morrer (só usada no Game Over)
        self.morta = False                         # vira True quando essa cobra causa sua própria derrota

    def move(self):
        x,y = self.body[0]

        nx = x + self.dir[0] * GRID
        ny = y + self.dir[1] * GRID

        nx = (nx // GRID) * GRID
        ny = (ny // GRID) * GRID

        self.body.insert(0,(nx,ny))

        while len(self.body) > self.size:
            self.body.pop()

    def draw(self):
        for i,part in enumerate(self.body):

            # A cabeça (índice 0) usa imagem PNG, se disponível.
            # Se a cobra estiver marcada como "morta" (Game Over) e houver
            # uma imagem específica de morte, ela tem prioridade sobre a viva.
            if i == 0:
                if self.morta and self.img_cabeca_morte is not None:
                    tela.blit(self.img_cabeca_morte, part)
                    continue
                if self.img_cabeca is not None:
                    tela.blit(self.img_cabeca, part)
                    continue

            brilho = max(100,255-(i*5))

            cor = (
                min(self.cor[0], brilho),
                min(self.cor[1], brilho),
                min(self.cor[2], brilho)
            )

            pygame.draw.rect(
                tela,
                cor,
                (*part,GRID-2,GRID-2),
                border_radius=5
            )

def sortear_imagem_fruta():
    """Sorteia uma das 5 imagens de fruta (ignora as que não foram carregadas).
    Se nenhuma estiver disponível, retorna None (fallback geométrico)."""
    disponiveis = [img for img in IMAGENS_FRUTAS if img is not None]
    if not disponiveis:
        return None
    return random.choice(disponiveis)

def nova_comida(p1,p2,bombas):

    while True:

        x = random.randint(0,(LARGURA//GRID)-1) * GRID
        y = random.randint(3,(ALTURA//GRID)-1) * GRID

        pos = (x,y)

        ocupado = pos in p1.body or pos in bombas
        if p2 is not None:
            ocupado = ocupado or pos in p2.body

        if not ocupado:
            return pos, sortear_imagem_fruta()

def nova_bomba(p1,p2,food,bombas):

    while True:

        x = random.randint(0,(LARGURA//GRID)-1) * GRID
        y = random.randint(3,(ALTURA//GRID)-1) * GRID

        pos = (x,y)

        ocupado = pos in p1.body or pos == food or pos in bombas
        if p2 is not None:
            ocupado = ocupado or pos in p2.body

        if not ocupado:
            return pos

NIVEL_INICIO_BOMBAS = 2   # bombas só começam a aparecer a partir deste nível
MAX_BOMBAS = 10           # teto para não lotar o campo

def atualizar_bombas(nivel,p1,p2,food,bombas):
    """Garante que existam (nivel - NIVEL_INICIO_BOMBAS + 1) bombas no campo,
    respeitando o teto MAX_BOMBAS. Bombas já criadas nunca são removidas."""

    if nivel < NIVEL_INICIO_BOMBAS:
        return bombas

    qtd_desejada = min(nivel - NIVEL_INICIO_BOMBAS + 1, MAX_BOMBAS)

    while len(bombas) < qtd_desejada:
        bombas.append(nova_bomba(p1,p2,food,bombas))

    return bombas

def novo_jogo(modo_jogadores):

    p1 = Snake(200,360,CORES[0],IMG_CABECA_P1,IMG_CABECA_P1_MORTE)
    p1.dir = (1,0)

    if modo_jogadores == 2:
        p2 = Snake(800,360,CORES[2],IMG_CABECA_P2,IMG_CABECA_P2_MORTE)
        p2.dir = (-1,0)
    else:
        p2 = None

    bombas = []
    food, food_img = nova_comida(p1,p2,bombas)

    return p1,p2,food,food_img,bombas

# --- Estado inicial: começa no menu ---
estado = MENU
modo_jogadores = 1  # padrão, será definido ao escolher no menu

p1 = None
p2 = None
food = None
food_img = None
bombas = []
vencedor = ""

while True:

    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit

        if evento.type == pygame.KEYDOWN:

            if estado == MENU:

                if evento.key in (pygame.K_1, pygame.K_KP1):
                    modo_jogadores = 1
                    p1,p2,food,food_img,bombas = novo_jogo(modo_jogadores)
                    estado = JOGANDO

                if evento.key in (pygame.K_2, pygame.K_KP2):
                    modo_jogadores = 2
                    p1,p2,food,food_img,bombas = novo_jogo(modo_jogadores)
                    estado = JOGANDO

            elif estado == JOGANDO:

                if evento.key == pygame.K_w and p1.dir != (0,1): p1.dir=(0,-1)
                if evento.key == pygame.K_s and p1.dir != (0,-1): p1.dir=(0,1)
                if evento.key == pygame.K_a and p1.dir != (1,0): p1.dir=(-1,0)
                if evento.key == pygame.K_d and p1.dir != (-1,0): p1.dir=(1,0)

                if p2 is not None:
                    if evento.key == pygame.K_UP and p2.dir != (0,1): p2.dir=(0,-1)
                    if evento.key == pygame.K_DOWN and p2.dir != (0,-1): p2.dir=(0,1)
                    if evento.key == pygame.K_LEFT and p2.dir != (1,0): p2.dir=(-1,0)
                    if evento.key == pygame.K_RIGHT and p2.dir != (-1,0): p2.dir=(1,0)

            elif estado == FIM:

                if evento.key == pygame.K_r:
                    p1,p2,food,food_img,bombas = novo_jogo(modo_jogadores)
                    vencedor = ""
                    estado = JOGANDO

                if evento.key == pygame.K_m:
                    p1 = None
                    p2 = None
                    food = None
                    food_img = None
                    bombas = []
                    vencedor = ""
                    estado = MENU

    # ---------------------- TELA DE MENU ----------------------
    if estado == MENU:

        if IMG_FUNDO_MENU is not None:
            tela.blit(IMG_FUNDO_MENU, (0,0))
            # Camada escura semitransparente por cima da imagem,
            # para o texto continuar legível independente da foto
            overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
            overlay.fill((0,0,0,140))
            tela.blit(overlay, (0,0))
        else:
            tela.fill(FUNDO)

        titulo = fonte_g.render("SNAKE DUEL", True, AMARELO)
        tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 180))

        op1 = fonte_m.render("Pressione 1 - Jogador unico", True, BRANCO)
        op2 = fonte_m.render("Pressione 2 - Dois jogadores", True, BRANCO)

        tela.blit(op1, (LARGURA//2 - op1.get_width()//2, 350))
        tela.blit(op2, (LARGURA//2 - op2.get_width()//2, 400))

        pygame.display.flip()
        clock.tick(30)
        continue

    # ------------------- LÓGICA DO JOGO -------------------
    if estado == JOGANDO:

        p1.move()
        if p2 is not None:
            p2.move()

        c1 = p1.body[0]
        c2 = p2.body[0] if p2 is not None else None

        if c1 == food:
            p1.score += 10
            p1.size += 1
            food, food_img = nova_comida(p1,p2,bombas)

        if p2 is not None and c2 == food:
            p2.score += 10
            p2.size += 1
            food, food_img = nova_comida(p1,p2,bombas)

        # Nível é calculado a partir da pontuação total, e usado para
        # decidir quantas bombas devem existir no campo
        score_p2_atual = p2.score if p2 is not None else 0
        nivel = ((p1.score + score_p2_atual) // 50) + 1
        bombas = atualizar_bombas(nivel,p1,p2,food,bombas)

        x1,y1 = c1

        if x1 < 0 or x1 >= LARGURA or y1 < 60 or y1 >= ALTURA:
            vencedor = "PLAYER 2" if p2 is not None else "FIM DE JOGO"
            p1.morta = True
            estado = FIM

        # Autocolisão da p1 (ignora a cabeça, índice 0)
        if c1 in p1.body[1:]:
            vencedor = "PLAYER 2" if p2 is not None else "FIM DE JOGO"
            p1.morta = True
            estado = FIM

        # Colisão da p1 com bomba
        if c1 in bombas:
            vencedor = "PLAYER 2" if p2 is not None else "FIM DE JOGO"
            p1.morta = True
            estado = FIM

        if p2 is not None:

            x2,y2 = c2

            if x2 < 0 or x2 >= LARGURA or y2 < 60 or y2 >= ALTURA:
                vencedor = "PLAYER 1"
                p2.morta = True
                estado = FIM

            # Autocolisão da p2
            if c2 in p2.body[1:]:
                vencedor = "PLAYER 1"
                p2.morta = True
                estado = FIM

            # Colisão da p2 com bomba
            if c2 in bombas:
                vencedor = "PLAYER 1"
                p2.morta = True
                estado = FIM

            # Colisão da cabeça da p1 com o corpo (ou cabeça) da p2
            if c1 in p2.body:
                vencedor = "PLAYER 2"
                p1.morta = True
                estado = FIM

            # Colisão da cabeça da p2 com o corpo (ou cabeça) da p1
            if c2 in p1.body:
                vencedor = "PLAYER 1"
                p2.morta = True
                estado = FIM

            # Colisão de cabeça com cabeça = empate (sobrepõe os resultados acima)
            if c1 == c2:
                vencedor = "EMPATE"
                p1.morta = True
                p2.morta = True
                estado = FIM

    # ------------------- DESENHO -------------------
    score_p2 = p2.score if p2 is not None else 0
    total_score = p1.score + score_p2
    nivel = (total_score // 50) + 1

    tela.fill(FUNDO_FLASH if total_score >= 200 and pygame.time.get_ticks() // 150 % 2 else FUNDO)

    pygame.draw.rect(tela,HUD,(0,0,LARGURA,55))

    if p2 is not None:
        txt = fonte.render(f"P1: {p1.score}   P2: {p2.score}   NIVEL: {nivel}",True,BRANCO)
    else:
        txt = fonte.render(f"SCORE: {p1.score}   NIVEL: {nivel}",True,BRANCO)

    tela.blit(txt,(20,15))

    if food_img is not None:
        tela.blit(food_img, food)
    else:
        pygame.draw.rect(tela, VERDE, (food[0], food[1], GRID, GRID))

    # Desenho das bombas: imagem PNG se disponível, senão círculo com pavio
    for bx,by in bombas:
        if IMG_BOMBA is not None:
            tela.blit(IMG_BOMBA, (bx,by))
        else:
            centro = (bx + GRID//2, by + GRID//2)
            pygame.draw.circle(tela, (30,30,30), centro, GRID//2)
            pygame.draw.circle(tela, (255,90,30), centro, GRID//2, 2)
            pygame.draw.line(tela, (255,180,60), (centro[0]+2,by), (centro[0]+6,by-6), 2)

    p1.draw()
    if p2 is not None:
        p2.draw()

    if estado == FIM:
        texto1 = fonte_g.render(vencedor,True,(255,70,70))
        tela.blit(texto1,(LARGURA//2-texto1.get_width()//2,ALTURA//2-70))

        prompt = fonte_m.render("R - Reiniciar     M - Menu", True, BRANCO)
        tela.blit(prompt,(LARGURA//2-prompt.get_width()//2,ALTURA//2+10))

    pygame.display.flip()
    clock.tick(8 + nivel)