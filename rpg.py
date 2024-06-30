import pygame
import math
import random

# Inicialización de Pygame
pygame.init()

# Constantes
ANCHO, ALTO = 800, 600
FPS = 60
FOV = math.pi / 3
NUM_RAYOS = 120
MAX_DEPTH = 800
TEX_WIDTH, TEX_HEIGHT = 64, 64

# Colores
NEGRO = (0, 0, 0)
BLANCO = (255, 255, 255)

# Configuración de la pantalla
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("RPG Clásico")

# Cargar texturas (asegúrate de que las imágenes estén en el mismo directorio que el script)
textura_muro1 = pygame.image.load("muro1.jpeg").convert()
textura_muro2 = pygame.image.load("muro2.jpeg").convert()

# Cargar sprite de enemigo (asegúrate de que la imagen tenga el tamaño adecuado, e.g., 64x64)
sprite_enemigo = pygame.image.load("enemigo.png").convert_alpha()
sprite_jefe = pygame.image.load("jefe.png").convert_alpha()  # Asegúrate de tener esta imagen

# Mapa del mundo
mapa = [
    [1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 1, 0, 1, 0, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 0, 1, 1, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
]
mapa_ancho = len(mapa[0])
mapa_alto = len(mapa)

# Posición y ángulo inicial del jugador
jugador_x, jugador_y = 128, 128  # Ajustamos la posición inicial para que esté en una celda vacía
jugador_ang = 0
jugador_salud = 50
curas_disponibles = 5  # Cambiado de 3 a 5

# Contador de enemigos derrotados
enemigos_derrotados = 0
jefe_derrotado = False
jefe_generado = False

# Definir clase Enemigo
class Enemigo:
    def __init__(self, x, y, salud=20):
        self.x = x
        self.y = y
        self.salud = salud

# Lista de enemigos
enemigos = []

def es_posicion_valida(x, y):
    """ Verifica si la posición es válida (no hay un muro). """
    if x < 0 or x >= mapa_ancho * TEX_WIDTH or y < 0 or y >= mapa_alto * TEX_HEIGHT:
        return False
    muro_x = int(x / TEX_WIDTH)
    muro_y = int(y / TEX_HEIGHT)
    return mapa[muro_y][muro_x] == 0

def generar_enemigo_aleatorio():
    """ Genera un enemigo en una posición aleatoria válida. """
    while True:
        x = random.randint(0, mapa_ancho - 1) * TEX_WIDTH + TEX_WIDTH // 2
        y = random.randint(0, mapa_alto - 1) * TEX_WIDTH + TEX_WIDTH // 2

        if es_posicion_valida(x, y):
            enemigos.append(Enemigo(x, y))
            break

def movimiento_jugador():
    global jugador_x, jugador_y, jugador_ang, jugador_salud, curas_disponibles
    keys = pygame.key.get_pressed()
    velocidad_mov = 3  # Ajustar velocidad del jugador
    velocidad_rot = 0.05

    nueva_x, nueva_y = jugador_x, jugador_y

    if keys[pygame.K_w]:
        nueva_x += math.cos(jugador_ang) * velocidad_mov
        nueva_y += math.sin(jugador_ang) * velocidad_mov
    if keys[pygame.K_s]:
        nueva_x -= math.cos(jugador_ang) * velocidad_mov
        nueva_y -= math.sin(jugador_ang) * velocidad_mov
    if keys[pygame.K_a]:
        jugador_ang -= velocidad_rot
    if keys[pygame.K_d]:
        jugador_ang += velocidad_rot
    if keys[pygame.K_h] and curas_disponibles > 0:  # Curarse
        jugador_salud = 50
        curas_disponibles -= 1

    if es_posicion_valida(nueva_x, nueva_y):
        jugador_x, jugador_y = nueva_x, nueva_y

    # Generar enemigo aleatorio si se cumplen condiciones
    if random.random() < 0.15:  # Ajusta la probabilidad según desees
        generar_enemigo_aleatorio()

def raycasting(pantalla, px, py, p_ang):
    zbuffer = [MAX_DEPTH] * NUM_RAYOS  # Crear un zbuffer para los enemigos
    for rayo in range(NUM_RAYOS):
        ang_rayo = p_ang - FOV / 2 + FOV * rayo / NUM_RAYOS
        distancia_muro = 0
        hit_wall = False

        while not hit_wall and distancia_muro < MAX_DEPTH:
            distancia_muro += 1
            x = int(px + distancia_muro * math.cos(ang_rayo))
            y = int(py + distancia_muro * math.sin(ang_rayo))

            if x < 0 or x >= ANCHO or y < 0 or y >= ALTO:
                hit_wall = True
                distancia_muro = MAX_DEPTH
            else:
                muro_x = int(x / TEX_WIDTH)
                muro_y = int(y / TEX_HEIGHT)
                
                if muro_y >= 0 and muro_y < mapa_alto and muro_x >= 0 and muro_x < mapa_ancho:
                    if mapa[muro_y][muro_x] == 1:
                        hit_wall = True
                        distancia_proyectada = distancia_muro * math.cos(p_ang - ang_rayo)
                        altura_muro = min(int(50000 / (distancia_proyectada + 0.0001)), ALTO)

                        if muro_x % 2 == 0 and muro_y % 2 == 0:
                            color = textura_muro1.get_at((int(x) % TEX_WIDTH, int(y) % TEX_HEIGHT))
                        else:
                            color = textura_muro2.get_at((int(x) % TEX_WIDTH, int(y) % TEX_HEIGHT))

                        pygame.draw.rect(pantalla, color, (rayo * (ANCHO // NUM_RAYOS), (ALTO - altura_muro) // 2, ANCHO // NUM_RAYOS, altura_muro))
                        zbuffer[rayo] = distancia_proyectada
                else:
                    hit_wall = True

    return zbuffer

def primer_turno_enemigo():
    """Simula el primer turno del enemigo y verifica si huye exitosamente."""
    accion_enemigo = random.choice(["atacar", "huir"])
    if accion_enemigo == "huir" and random.random() < 0.25:
        return True  # El enemigo ha huido exitosamente
    elif accion_enemigo == "atacar":
        global jugador_salud
        jugador_salud -= 5
    return False  # El enemigo no huyó

def combate(enemigo):
    global jugador_salud, turno_jugador, enemigos_derrotados, jefe_derrotado, curas_disponibles

    pantalla.fill(NEGRO)
    fuente = pygame.font.Font(None, 36)
    
    enemigo_es_jefe = enemigo.salud == 10000

    ayuda = fuente.render("Presiona 'A' para atacar, 'H' para curarte" + ("" if enemigo_es_jefe else ", 'F' para huir"), True, BLANCO)
    pantalla.blit(ayuda, (ANCHO // 2 - ayuda.get_width() // 2, ALTO // 2 + 50))
    pygame.display.flip()

    turno_jugador = True
    combatiendo = True

    if primer_turno_enemigo():
        combatiendo = False
        enemigos.remove(enemigo)
        return

    while combatiendo and jugador_salud > 0:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                return
            if evento.type == pygame.KEYDOWN:
                if turno_jugador:
                    if evento.key == pygame.K_a:
                        enemigo.salud -= 10
                        turno_jugador = False
                    elif evento.key == pygame.K_h and curas_disponibles > 0:
                        jugador_salud = 50
                        curas_disponibles -= 1
                    elif evento.key == pygame.K_f and not enemigo_es_jefe:  # Huir solo si no es el jefe
                        combatiendo = False
                        return

        if enemigo.salud <= 0:
            enemigos.remove(enemigo)
            enemigos_derrotados += 1
            combatiendo = False
            if enemigo_es_jefe:
                jefe_derrotado = True
            return

        if not turno_jugador:
            jugador_salud -= 5
            turno_jugador = True

        pantalla.fill(NEGRO)
        enemigo_salud_texto = "Infinito" if enemigo_es_jefe else enemigo.salud  # Actualizamos el texto de la salud
        texto = fuente.render(f"Jugador Salud: {jugador_salud} - Enemigo Salud: {enemigo_salud_texto}", True, BLANCO)
        pantalla.blit(texto, (ANCHO // 2 - texto.get_width() // 2, ALTO // 2 - 100))
        pantalla.blit(sprite_enemigo if not enemigo_es_jefe else sprite_jefe, (ANCHO // 2 - sprite_enemigo.get_width() // 2, ALTO // 2 - sprite_enemigo.get_height() // 2))
        pantalla.blit(ayuda, (ANCHO // 2 - ayuda.get_width() // 2, ALTO // 2 + 50))
        pygame.display.flip()

    if jugador_salud <= 0:
        if enemigo_es_jefe:
            pantalla_perdiste(True)  # Indicamos que se perdió contra el jefe
        else:
            pantalla_perdiste()

def pantalla_jeferinal(jefe):
    pantalla.fill(NEGRO)
    fuente = pygame.font.Font(None, 74)
    texto = fuente.render("¡Enfrentamiento Final!", True, BLANCO)
    pantalla.blit(texto, (ANCHO // 2 - texto.get_width() // 2, ALTO // 2 - texto.get_height() // 2))
    pygame.display.flip()
    pygame.time.delay(3000)
    combate(jefe)

def pantalla_perdiste(contra_jefe=False):
    pantalla.fill(NEGRO)
    fuente = pygame.font.Font(None, 74)
    if contra_jefe:
        texto1 = fuente.render("Puedes derrotar enemigos,", True, BLANCO)
        texto2 = fuente.render("pero nunca a Jesucristo", True, BLANCO)
        pantalla.blit(texto1, (ANCHO // 2 - texto1.get_width() // 2, ALTO // 2 - texto1.get_height()))
        pantalla.blit(texto2, (ANCHO // 2 - texto2.get_width() // 2, ALTO // 2))
    else:
        texto = fuente.render("¡Perdiste!", True, BLANCO)
        pantalla.blit(texto, (ANCHO // 2 - texto.get_width() // 2, ALTO // 2 - texto.get_height() // 2))
    pygame.display.flip()
    pygame.time.delay(3000)
    reiniciar_juego()

def reiniciar_juego():
    global jugador_x, jugador_y, jugador_ang, jugador_salud, enemigos, enemigos_derrotados, jefe_derrotado, curas_disponibles
    jugador_x, jugador_y = 128, 128
    jugador_ang = 0
    jugador_salud = 50
    curas_disponibles = 5  # Cambiado de 3 a 5
    enemigos = []
    enemigos_derrotados = 0
    jefe_derrotado = False

def main():
    global jugador_salud, jefe_derrotado, jefe_generado

    clock = pygame.time.Clock()

    while True:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                return

        movimiento_jugador()
        pantalla.fill(NEGRO)
        zbuffer = raycasting(pantalla, jugador_x, jugador_y, jugador_ang)

        for enemigo in enemigos:
            dx, dy = enemigo.x - jugador_x, enemigo.y - jugador_y
            distancia_enemigo = math.sqrt(dx * dx + dy * dy)
            angulo_enemigo = math.atan2(dy, dx) - jugador_ang

            if -FOV / 2 < angulo_enemigo < FOV / 2:
                x_enemigo = ANCHO / 2 + (ANCHO / 2) * angulo_enemigo / (FOV / 2)
                if 0 <= x_enemigo < NUM_RAYOS and distancia_enemigo > 0 and distancia_enemigo < zbuffer[int(x_enemigo)]:
                    sprite_a_usar = sprite_jefe if enemigo.salud == 10000 else sprite_enemigo
                    escala = 2500 / (distancia_enemigo + 0.0001)
                    enemigo_imagen = pygame.transform.scale(sprite_a_usar, (int(escala), int(escala)))
                    pantalla.blit(enemigo_imagen, (x_enemigo - enemigo_imagen.get_width() // 2, ALTO // 2 - enemigo_imagen.get_height() // 2))

                    if distancia_enemigo < 50:  # Si el jugador está cerca del enemigo
                        combate(enemigo)

        pygame.display.flip()
        clock.tick(FPS)

        if jugador_salud <= 0:
            pantalla_perdiste()

        if enemigos_derrotados >= 5 and not jefe_generado:  # Cambiado de 10 a 5
            jefe = Enemigo(400, 300, salud=10000)  # Salud muy alta para el jefe
            enemigos.append(jefe)
            jefe_generado = True
            pantalla_jeferinal(jefe)

        if jefe_derrotado:
            pantalla_perdiste(True)  # Indicamos que se perdió contra el jefe

if __name__ == "__main__":
    main()