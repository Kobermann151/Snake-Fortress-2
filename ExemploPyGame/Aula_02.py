import pygame
import sys

# Inicializa todos os módulos integrados do PyGame
pygame.init()

# -----------------------------------------------------------------------------
# CONFIGURAÇÕES DA JANELA E CONSTANTES
# -----------------------------------------------------------------------------
LARGURA_TELA = 800
ALTURA_TELA = 600
TITULO = "Python Crash - Aula 2: Inputs & Movimento"
FPS = 60  # Taxa de atualização (quadros por segundo)

# Definição de cores básicas usando tuplas (Red, Green, Blue)
COR_FUNDO = (30, 41, 59)  # Um tom de azul bem escuro (Slate 800)
COR_RETANGULO = (55, 118, 171)  # Azul clássico da logo do Python

# Cria a janela do jogo com as dimensões especificadas
tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption(TITULO)

# Objeto responsável por gerenciar o tempo e limitar a taxa de FPS
relogio = pygame.time.Clock()

# -----------------------------------------------------------------------------
# ESTADO DO PERSONAGEM (VARIÁVEIS DE CONTROLE)
# -----------------------------------------------------------------------------
# Tamanho do nosso quadrado/personagem (largura e altura)
tam_personagem = 50

# Posição inicial centralizada na tela
pos_x = (LARGURA_TELA - tam_personagem) // 2
pos_y = (ALTURA_TELA - tam_personagem) // 2

# [CONTEÚDO AULA 2]: Velocidade escalar fixa do movimento [cite: 35]
velocidade_base = 5

# [CONTEÚDO AULA 2]: Vetores de direção da cobra (dir_x, dir_y) [cite: 35]
# O jogo começa com o quadrado se movimentando automaticamente para a direita
dir_x = velocidade_base
dir_y = 0

# -----------------------------------------------------------------------------
# CARREGAMENTO DA IMAGEM (COM FALLBACK SE O ARQUIVO NÃO EXISTIR)
# -----------------------------------------------------------------------------
imagem_personagem = None
usa_imagem = False

try:
    # Tentativa de carregar a imagem do disco
    imagem_original = pygame.image.load("personagem.png")

    # Redimensiona a imagem para que se ajuste perfeitamente ao tamanho do nosso personagem
    imagem_personagem = pygame.transform.scale(imagem_original, (tam_personagem, tam_personagem))
    usa_imagem = True
    print("[INFO] Imagem 'personagem.png' carregada com sucesso!")

except FileNotFoundError:
    # Se a imagem não for encontrada, criamos uma imagem customizada em memória
    print("[Aviso] Imagem 'personagem.png' não encontrada. Criando uma textura alternativa em memória...")

    # Criamos uma superfície vazia de tamanho tam_personagem x tam_personagem
    imagem_personagem = pygame.Surface((tam_personagem, tam_personagem), pygame.SRCALPHA)

    # Desenhamos uma bolinha amarela e olhos nela para simular uma carinha simples
    pygame.draw.circle(imagem_personagem, (254, 240, 138), (tam_personagem // 2, tam_personagem // 2),
                       tam_personagem // 2)
    pygame.draw.circle(imagem_personagem, (15, 23, 42), (tam_personagem // 3, tam_personagem // 3), 4)  # Olho Esquerdo
    pygame.draw.circle(imagem_personagem, (15, 23, 42), (2 * tam_personagem // 3, tam_personagem // 3),
                       4)  # Olho Direito
    pygame.draw.arc(imagem_personagem, (15, 23, 42),
                    (tam_personagem // 4, tam_personagem // 3, tam_personagem // 2, tam_personagem // 3), 3.14, 0,
                    2)  # Sorriso

    usa_imagem = True

# -----------------------------------------------------------------------------
# LAÇO PRINCIPAL DO JOGO (GAME LOOP)
# -----------------------------------------------------------------------------
rodando = True
while rodando:
    # 1. PROCESSAMENTO DE EVENTOS & INPUTS (Mecânica de clique único para a Aula 2) [cite: 34]
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False

        # Captura o exato momento em que uma tecla é pressionada [cite: 12]
        elif evento.type == pygame.KEYDOWN:
            # SE APERTAR ESQUERDA (Seta ou 'A'): Só aceita se não estiver indo para a direita [cite: 12]
            if evento.key in [pygame.K_LEFT, pygame.K_a]:
                if dir_x == 0:  # Trava de eixo: evita que ela mude de sentido diretamente
                    dir_x = -velocidade_base
                    dir_y = 0

            # SE APERTAR DIREITA (Seta ou 'D'): Só aceita se não estiver indo para a esquerda [cite: 12]
            elif evento.key in [pygame.K_RIGHT, pygame.K_d]:
                if dir_x == 0:
                    dir_x = velocidade_base
                    dir_y = 0

            # SE APERTAR CIMA (Seta ou 'W'): Só aceita se não estiver indo para baixo [cite: 12]
            elif evento.key in [pygame.K_UP, pygame.K_w]:
                if dir_y == 0:
                    dir_x = 0
                    dir_y = -velocidade_base

            # SE APERTAR BAIXO (Seta ou 'S'): Só aceita se não estiver indo para cima [cite: 12]
            elif evento.key in [pygame.K_DOWN, pygame.K_s]:
                if dir_y == 0:
                    dir_x = 0
                    dir_y = velocidade_base

    # 2. MOVIMENTAÇÃO AUTOMÁTICA E CONTÍNUA [cite: 12, 35]
    # O quadrado se move sozinho com base no vetor de direção atualizado pelas teclas
    pos_x += dir_x
    pos_y += dir_y

    # 3. COLISÃO COM AS BORDAS DA TELA (Versão corrigida com reset de direção)
    # Comportamento temporário da Aula 2: travar nas bordas de forma fluida.
    # Na Aula 5, essa lógica será substituída pela chamada da tela de Game Over! [cite: 18, 38]
    if pos_x < 0:
        pos_x = 0
        dir_x = 0  # Liberta o eixo X para permitir comandos imediatos em Y
    elif pos_x > LARGURA_TELA - tam_personagem:
        pos_x = LARGURA_TELA - tam_personagem
        dir_x = 0

    if pos_y < 0:
        pos_y = 0
        dir_y = 0  # Liberta o eixo Y para permitir comandos imediatos em X
    elif pos_y > ALTURA_TELA - tam_personagem:
        pos_y = ALTURA_TELA - tam_personagem
        dir_y = 0

    # 4. RENDERIZAÇÃO (Desenho dos elementos na tela)
    # Limpa a tela com a cor de fundo
    tela.fill(COR_FUNDO)

    # Renderiza o personagem (Imagem carregada ou a textura alternativa)
    if usa_imagem:
        tela.blit(imagem_personagem, (pos_x, pos_y))
    else:
        pygame.draw.rect(tela, COR_RETANGULO, (pos_x, pos_y, tam_personagem, tam_personagem))

    # Atualiza o display físico para renderizar o frame
    pygame.display.flip()

    # Mantém a execução cravada na taxa de FPS configurada
    relogio.tick(FPS)

# Finaliza o ambiente de forma limpa e segura
pygame.quit()
sys.exit()
#teste
