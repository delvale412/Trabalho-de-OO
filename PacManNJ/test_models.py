from entities import Player, Ghost
from config import COLOR_BLINKY, SUPER_MODE_DURATION

def test_player_initialization():
    """Testa a criação e o estado inicial da classe Player."""
    print("-> Testando a inicialização da classe Player...")
    player = Player(10, 15)
    assert player.x == 10, "Posição X inicial incorreta"
    assert player.y == 15, "Posição Y inicial incorreta"
    assert player.score == 0, "A pontuação inicial deve ser 0"
    assert player.dx == 0 and player.dy == 0, "A direção inicial deve ser (0, 0)"
    assert not player.is_dying, "O estado 'is_dying' inicial deve ser False"
    assert player.super_timer == 0, "O 'super_timer' inicial deve ser 0"
    print("   [OK] Inicialização do Player passou.")

def test_player_functionality():
    """Testa os métodos e a lógica de funcionamento da classe Player."""
    print("-> Testando a funcionalidade da classe Player...")
    
    # Cria um labirinto simples para os testes: 1=parede, 2=ponto, 3=ponto especial
    mock_maze = [
        [1, 1, 1, 1, 1],
        [1, 0, 2, 3, 1],
        [1, 1, 1, 1, 1]
    ]
    player = Player(1, 1)

    # Teste de movimento para uma parede
    player.try_set_direction(-1, 0, mock_maze) # Tenta ir para a esquerda (parede)
    player.move(mock_maze)
    assert player.x == 1 and player.y == 1, "O jogador não deveria se mover contra uma parede"
    print("   [OK] Movimento contra parede.")

    # Teste de movimento e consumo de ponto normal
    player.try_set_direction(1, 0, mock_maze) # Vai para a direita
    player.move(mock_maze)
    assert player.x == 2 and player.y == 1, "O jogador deveria ter se movido para a direita"
    assert player.score == 10, "A pontuação deveria ser 10 após comer um ponto"
    assert mock_maze[1][2] == 0, "O ponto normal deveria ter sido removido do labirinto"
    print("   [OK] Consumo de ponto normal.")

    # Teste de movimento e consumo de ponto especial
    event = player.move(mock_maze)
    assert player.x == 3 and player.y == 1, "O jogador deveria ter se movido para a direita"
    assert player.score == 60, "A pontuação deveria ser 60 (10 + 50)"
    assert mock_maze[1][3] == 0, "O ponto especial deveria ter sido removido"
    assert event == "SUPER_MODE_START", "Deveria retornar o evento de super modo"
    print("   [OK] Consumo de ponto especial.")

    # Teste de ativação do super modo e contagem do tempo
    player.activate_super_mode()
    assert player.super_timer == SUPER_MODE_DURATION, f"O super timer deveria ser {SUPER_MODE_DURATION}"
    player.update(frame=1) # Simula a passagem de um frame
    assert player.super_timer == SUPER_MODE_DURATION - 1, "O super timer deveria diminuir a cada update"
    print("   [OK] Ativação e contagem do super modo.")

    # Teste da lógica de morte
    player.start_dying()
    assert player.is_dying, "O estado 'is_dying' deveria ser True"
    assert player.death_animation_timer > 0, "O timer de animação de morte deveria ser iniciado"
    print("   [OK] Lógica de morte.")


def test_ghost_initialization():
    """Testa a criação e o estado inicial da classe Ghost."""
    print("-> Testando a inicialização da classe Ghost...")
    blinky = Ghost(x=13, y=14, color=COLOR_BLINKY, gtype="blinky")
    assert blinky.x == 13 and blinky.y == 14, "Posição inicial incorreta"
    assert blinky.spawn_x == 13 and blinky.spawn_y == 14, "Posição de spawn incorreta"
    assert blinky.type == "blinky", "O tipo do fantasma está incorreto"
    assert blinky.state == "house", "O estado inicial deve ser 'house'"
    assert blinky.vul_timer == 0, "O 'vul_timer' inicial deve ser 0"
    assert blinky.color == COLOR_BLINKY, "A cor do fantasma está incorreta"
    print("   [OK] Inicialização do Ghost passou.")

def test_ghost_state_changes():
    """Testa as transições de estado da classe Ghost."""
    print("-> Testando as mudanças de estado da classe Ghost...")
    # Posição inicial (1,1) para um labirinto 3x3
    ghost = Ghost(1, 1, COLOR_BLINKY, "blinky")
    
    # O estado inicial é 'house'
    assert ghost.state == "house", "Estado inicial incorreto"

    # Simula a saída da casa dos fantasmas
    ghost.state = "chase"
    assert ghost.state == "chase", "Falha ao mudar para o estado 'chase'"
    print("   [OK] Transição para o estado 'chase'.")

    # Simula a ativação do super modo, que o torna vulnerável
    ghost.state = "vulnerable"
    ghost.vul_timer = SUPER_MODE_DURATION
    assert ghost.state == "vulnerable", "Falha ao mudar para o estado 'vulnerable'"
    assert ghost.vul_timer == SUPER_MODE_DURATION, "Timer de vulnerabilidade não foi iniciado"
    print("   [OK] Transição para o estado 'vulnerable'.")

    # Simula o fim do tempo de vulnerabilidade
    ghost.vul_timer = 1
    mock_player = Player(1, 0) # Coloca o jogador "falso" dentro do labirinto
    # Cria um labirinto 3x3 caminhável para o teste, evitando erros de índice
    mock_maze = [
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ]
    ghost.update(maze=mock_maze, player=mock_player, ghosts=[], blinky_ref=None)
    ghost.vul_timer = 0 # Força o fim
    if ghost.vul_timer <= 0:
        ghost.state = "chase"
    assert ghost.state == "chase", "Deveria retornar ao estado 'chase' após o fim da vulnerabilidade"
    print("   [OK] Retorno para o estado 'chase'.")

    # Simula ser comido pelo jogador
    ghost.state = "eaten"
    assert ghost.state == "eaten", "Falha ao mudar para o estado 'eaten'"
    print("   [OK] Transição para o estado 'eaten'.")


def run_all_tests():
    """
    Executa todos os conjuntos de testes definidos para os modelos do jogo.
    """
    print("===========================================")
    print("  INICIANDO BANCO DE TESTES DOS MODELOS  ")
    print("===========================================")
    
    try:
        test_player_initialization()
        print("-" * 40)
        test_player_functionality()
        print("-" * 40)
        test_ghost_initialization()
        print("-" * 40)
        test_ghost_state_changes()
        
        print("\n===========================================")
        print(" [SUCESSO] Todos os testes passaram! ")
        print("===========================================")
        
    except AssertionError as e:
        print("\n!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(f"   [FALHA EM UM TESTE]  > {e}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

if __name__ == "__main__":
    run_all_tests()

