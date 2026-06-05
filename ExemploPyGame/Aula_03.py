import pygame
import sys
import random
import os

# Inicializa todos os módulos integrados do PyGame
pygame.init()

# Inicializa o sistema de som do PyGame (Mixer)
pygame.mixer.init()

# Inicializa o módulo de fontes do PyGame para o placar
pygame.font.init()

# -----------------------------------------------------------------------------
# CONFIGURAÇÕES DA JANELA E CONSTANTES
# -----------------------------------------------------------------------------
LARGURA_TELA = 800
ALTURA_TELA = 600
TITULO = "Python Crash - Implementação de Efeitos Sonoros"

# Definição de cores básicas usando tuplas (Red, Green, Blue)
COR_FUNDO = (30, 41, 59)  # Tom de azul escuro (Slate 800)
COR_CABECA = (34, 197, 94)  # Verde para fallback da cabeça
COR_CORPO = (22, 163, 74)  # Verde escuro para fallback do corpo
COR_MACA = (239, 68, 68)  # Vermelho para fallback da maçã
COR_BOMBA = (244, 63, 94)  # Rosa/Vermelho forte para fallback da bomba
COR_TEXTO = (248, 250, 252)  # Branco suave para o placar

# Cria a janela do jogo com as dimensões especificadas
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption(TITULO)

# Objeto responsável por gerenciar o tempo e limitar a taxa de FPS
relogio = pygame.time.Clock()

# Fonte para renderização do Score, Vidas e Fase na tela
fonte_game = pygame.font.SysFont("Arial", 24, bold=True)

# -----------------------------------------------------------------------------
# TABELA DE PROGRESSÃO DAS 5 FASES
# -----------------------------------------------------------------------------
CONFIG_FASES = {
    1: {"fps": 5, "chance_bomba": 0.15, "tempo_item": 6000},
    2: {"fps": 6, "chance_bomba": 0.25, "tempo_item": 5000},
    3: {"fps": 7, "chance_bomba": 0.35, "tempo_item": 4500},
    4: {"fps": 8, "chance_bomba": 0.45, "tempo_item": 4000},
    5: {"fps": 10, "chance_bomba": 0.60, "tempo_item": 3000}
}

# -----------------------------------------------------------------------------
# ESTADO GLOBAL DO JOGO (PONTUAÇÃO, VIDAS E MÉTRICAS)
# -----------------------------------------------------------------------------
score = 0
vidas = 3
fase_atual = 1

vidas_ganhas_consecutivas = 0
pontos_acumulados_proxima_vida = 0

tam_personagem = 50
velocidade_base = tam_personagem

pos_x = 0
pos_y = 0
dir_x = 0
dir_y = 0
corpo_cobra = []
cobra_viva = True

# -----------------------------------------------------------------------------
# CARREGAMENTO DOS SPRITES (COM FALLBACK GEOMÉTRICO)
# -----------------------------------------------------------------------------
sprites = {}
usa_sprites = True
pasta_imagens = "Imagens"

arquivos_sprites = {
    "cabeca": "snake_green_head.png",
    "morta": "snake_green_xx.png",
    "corpo": "snake_green_blob.png",
    "maca_vermelha": "apple_alt.png",
    "maca_verde": "apple_green.png",
    "bomba": "bomb.png"
}

print("[INFO] Carregando recursos visuais...")
for chave, arquivo in arquivos_sprites.items():
    caminho = os.path.join(pasta_imagens, arquivo)
    try:
        img = pygame.image.load(caminho).convert_alpha()
        sprites[chave] = pygame.transform.scale(img, (tam_personagem, tam_personagem))
    except (FileNotFoundError, pygame.error):
        print(f"[Aviso] Falha ao carregar '{caminho}'. Fallback geométrico ativado para {chave}.")
        usa_sprites = False

# -----------------------------------------------------------------------------
# CARREGAMENTO DOS EFEITOS SONOROS (COM FALLBACK SE O ARQUIVO NÃO EXISTIR)
# -----------------------------------------------------------------------------
som_morte = None
pasta_sons = "Sons"  # Atenção ao Case Sensitivity!

try:
    caminho_som = os.path.join(pasta_sons, "morreu.mp3")
    som_morte = pygame.mixer.Sound(caminho_som)
    print("[INFO] Efeito sonoro 'morreu.mp3' carregado com sucesso!")
except (FileNotFoundError, pygame.error):
    print("[Aviso] Arquivo de som 'Sons/morreu.mp3' não encontrado. O jogo rodará em modo silencioso.")

# -----------------------------------------------------------------------------
# GERENCIAMENTO DE ITENS (DINÂMICO POR FASE)
# -----------------------------------------------------------------------------
momento_geracao = 0
pos_fruta = None
tipo_fruta = None
pos_bomba = None
bomba_ativa = False


def gerar_posicao_aleatoria():
    colunas = LARGURA_TELA // tam_personagem
    linhas = ALTURA_TELA // tam_personagem
    while True:
        x = random.randint(0, colunas - 1) * tam_personagem
        y = random.randint(0, linhas - 1) * tam_personagem
        if [x, y] not in corpo_cobra:
            return x, y


def spawnar_itens():
    global pos_fruta, tipo_fruta, pos_bomba, bomba_ativa, momento_geracao
    momento_geracao = pygame.time.get_ticks()

    chance_bomba = CONFIG_FASES[fase_atual]["chance_bomba"]

    if random.random() < chance_bomba:
        pos_bomba = gerar_posicao_aleatoria()
        bomba_ativa = True

        if random.random() < 0.50:
            pos_fruta = gerar_posicao_aleatoria()
            tipo_fruta = random.choice(["vermelha", "verde"])
        else:
            pos_fruta = None
            tipo_fruta = None
    else:
        pos_fruta = gerar_posicao_aleatoria()
        tipo_fruta = random.choice(["vermelha", "verde"])
        pos_bomba = None
        bomba_ativa = False


# -----------------------------------------------------------------------------
# FUNÇÕES DE FLUXO DE JOGO
# -----------------------------------------------------------------------------
def reiniciar_posicao_cobra():
    global pos_x, pos_y, dir_x, dir_y, corpo_cobra, cobra_viva
    pos_x = (LARGURA_TELA // 2) // tam_personagem * tam_personagem
    pos_y = (ALTURA_TELA // 2) // tam_personagem * tam_personagem

    # Começa se movendo automaticamente para a direita
    dir_x = velocidade_base
    dir_y = 0

    corpo_cobra = [
        [pos_x, pos_y],
        [pos_x - tam_personagem, pos_y],
        [pos_x - (2 * tam_personagem), pos_y]
    ]
    cobra_viva = True


def aplicar_morte_por_colisao(motivo):
    global vidas, vidas_ganhas_consecutivas, pontos_acumulados_proxima_vida

    vidas -= 1
    vidas_ganhas_consecutivas = 0
    pontos_acumulados_proxima_vida = 0

    print(f"[MORTE] Motivo: {motivo} | Vidas restantes: {vidas}")

    # [NOVO]: Toca o áudio de morte se o arquivo foi carregado com sucesso
    if som_morte:
        som_morte.play()

    if vidas > 0:
        reiniciar_posicao_cobra()
        spawnar_itens()


def aplicar_morte_por_bomba():
    global score, vidas, vidas_ganhas_consecutivas, pontos_acumulados_proxima_vida

    vidas -= 1
    vidas_ganhas_consecutivas = 0
    score = max(0, score - 100)
    pontos_acumulados_proxima_vida = 0

    print(f"[EXPLOSÃO] Atingiu uma bomba! Vidas restantes: {vidas} | Score atual: {score}")

    # [NOVO]: Toca o áudio de morte também ao explodir na bomba
    if som_morte:
        som_morte.play()

    if vidas > 0:
        reiniciar_posicao_cobra()
        spawnar_itens()


# Inicialização do cenário
reiniciar_posicao_cobra()
spawnar_itens()

# -----------------------------------------------------------------------------
# LAÇO PRINCIPAL DO JOGO (GAME LOOP)
# -----------------------------------------------------------------------------
rodando = True
while rodando:
    tempo_atual = pygame.time.get_ticks()
    config_fase_atual = CONFIG_FASES[fase_atual]
    tempo_limite_item = config_fase_atual["tempo_item"]

    # 1. PROCESSAMENTO DE EVENTOS & INPUTS
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        elif evento.type == pygame.KEYDOWN:
            if vidas <= 0:
                score = 0
                vidas = 3
                fase_atual = 1
                vidas_ganhas_consecutivas = 0
                pontos_acumulados_proxima_vida = 0
                reiniciar_posicao_cobra()
                spawnar_itens()
                continue

            if evento.key in [pygame.K_LEFT, pygame.K_a] and dir_x == 0:
                dir_x = -velocidade_base;
                dir_y = 0
            elif evento.key in [pygame.K_RIGHT, pygame.K_d] and dir_x == 0:
                dir_x = velocidade_base;
                dir_y = 0
            elif evento.key in [pygame.K_UP, pygame.K_w] and dir_y == 0:
                dir_x = 0;
                dir_y = -velocidade_base
            elif evento.key in [pygame.K_DOWN, pygame.K_s] and dir_y == 0:
                dir_x = 0;
                dir_y = velocidade_base

    # 2. LÓGICA DE ATUALIZAÇÃO DO JOGO
    if vidas > 0:
        if tempo_atual - momento_geracao > tempo_limite_item:
            spawnar_itens()

        # Calcula o próximo passo teórico da cabeça
        proximo_x = pos_x + dir_x
        proximo_y = pos_y + dir_y

        # A) DETECÇÃO DE COLISÃO COM AS PAREDES
        if proximo_x < 0 or proximo_x > LARGURA_TELA - tam_personagem or proximo_y < 0 or proximo_y > ALTURA_TELA - tam_personagem:
            aplicar_morte_por_colisao("Colisão com a Parede")
            continue

        nova_cabeca = [proximo_x, proximo_y]

        # B) DETECÇÃO DE AUTO-COLISÃO
        if nova_cabeca in corpo_cobra:
            aplicar_morte_por_colisao("Auto-colisão com o Corpo")
            continue

        # C) DETECÇÃO DE COLISÃO COM A BOMBA
        colidiu_com_bomba = False
        if bomba_ativa:
            if nova_cabeca == list(pos_bomba):
                colidiu_com_bomba = True
            else:
                for parte in corpo_cobra:
                    if parte == list(pos_bomba):
                        colidiu_com_bomba = True
                        break

        if colidiu_com_bomba:
            aplicar_morte_por_bomba()
            continue

        # Se passou por todas as validações, move a cobra
        pos_x = proximo_x
        pos_y = proximo_y
        corpo_cobra.insert(0, nova_cabeca)

        # D) LÓGICA DE NUTRIÇÃO E PONTUAÇÃO
        comeu_fruta = False
        if pos_fruta and nova_cabeca == list(pos_fruta):
            comeu_fruta = True
            score += 10
            pontos_acumulados_proxima_vida += 10

            if pontos_acumulados_proxima_vida >= 100:
                pontos_acumulados_proxima_vida -= 100
                if vidas < 6:
                    vidas += 1
                    vidas_ganhas_consecutivas += 1

            if (vidas_ganhas_consecutivas >= 2 or score >= 1000) and fase_atual < 5:
                fase_atual += 1
                vidas_ganhas_consecutivas = 0

            spawnar_itens()

        if not comeu_fruta:
            corpo_cobra.pop()

    # 3. RENDERIZAÇÃO GRÁFICA DA INTERFACE
    tela.fill(COR_FUNDO)

    if pos_fruta:
        if usa_sprites:
            sprite_maca = sprites["maca_vermelha"] if tipo_fruta == "vermelha" else sprites["maca_verde"]
            tela.blit(sprite_maca, pos_fruta)
        else:
            pygame.draw.rect(tela, COR_MACA,
                             (pos_fruta[0] + 5, pos_fruta[1] + 5, tam_personagem - 10, tam_personagem - 10))

    if bomba_ativa and pos_bomba:
        if usa_sprites:
            tela.blit(sprites["bomba"], pos_bomba)
        else:
            pygame.draw.rect(tela, COR_BOMBA,
                             (pos_bomba[0] + 5, pos_bomba[1] + 5, tam_personagem - 10, tam_personagem - 10))

    for indice, parte in enumerate(corpo_cobra):
        if indice == 0:
            if usa_sprites:
                sprite_cabeca = sprites["cabeca"] if vidas > 0 else sprites["morta"]
                tela.blit(sprite_cabeca, (parte[0], parte[1]))
            else:
                cor_cabeca_atual = COR_CABECA if vidas > 0 else (127, 136, 140)
                pygame.draw.rect(tela, cor_cabeca_atual, (parte[0], parte[1], tam_personagem, tam_personagem))
        else:
            if usa_sprites:
                tela.blit(sprites["corpo"], (parte[0], parte[1]))
            else:
                pygame.draw.rect(tela, COR_CORPO, (parte[0] + 2, parte[1] + 2, tam_personagem - 4, tam_personagem - 4))

    # Placar de Informações
    texto_score = f"SCORE: {score}"
    texto_vidas = f"VIDAS: {vidas}"
    texto_fase = f"FASE: {fase_atual}" if fase_atual < 5 else "FASE: FINAL (5)"

    if vidas <= 0:
        texto_game_over = fonte_game.render("GAME OVER - Pressione qualquer tecla para reiniciar", True, COR_BOMBA)
        tela.blit(texto_game_over, (LARGURA_TELA // 2 - 230, ALTURA_TELA // 2))

    sup_score = fonte_game.render(texto_score, True, COR_TEXTO)
    sup_vidas = fonte_game.render(texto_vidas, True, COR_TEXTO)
    sup_fase = fonte_game.render(texto_fase, True, COR_TEXTO)

    tela.blit(sup_score, (LARGURA_TELA - 160, 20))
    tela.blit(sup_vidas, (LARGURA_TELA - 160, 50))
    tela.blit(sup_fase, (LARGURA_TELA - 160, 80))

    pygame.display.flip()
    relogio.tick(config_fase_atual["fps"])

pygame.quit()
sys.exit()
