import pygame
import random

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Game constants
WINDOW_WIDTH = 480  # Changed for mobile
WINDOW_HEIGHT = 720  # Changed for mobile
FPS = 60
PLAYER_SPEED = 4
BULLET_SPEED = 6
ENEMY_SPEED = 2
ENEMY_SPAWN_RATE = 2000  # milliseconds
BULLET_COOLDOWN = 300  # milliseconds
ITEM_SPEED = 3
ITEM_SPAWN_CHANCE = 0.1  # 10% chance to spawn item when enemy is hit
EXPLOSION_DURATION = 500  # milliseconds
INVINCIBLE_DURATION = 2000  # milliseconds
ENEMY_BULLET_SPEED = 5
ENEMY_SHOOT_CHANCE = 0.01  # 1% chance per frame

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Game class
class GalagaGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("꽃님이의 갤러그")
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_over = False
        self.score = 0
        self.stage = 1
        self.lives = 3  # 기본 생명 3개
        self.last_enemy_spawn = 0
        self.last_bullet_shot = 0
        self.invincible_until = 0
        self.blink_timer = 0
        
        # Load assets
        self.load_assets()
        
        # Initialize game objects
        self.reset_game()
        
        # Start background music
        pygame.mixer.music.play(-1)  # -1 for infinite loop

    def reset_game(self):
        self.player = pygame.Rect(WINDOW_WIDTH // 2 - 50, WINDOW_HEIGHT - 150, 100, 100)
        self.bullets = []
        self.enemies = []
        self.items = []
        self.explosions = []
        self.enemy_bullets = []
        self.score = 0
        self.stage = 1
        self.lives = 3
        self.game_over = False
        self.invincible_until = 0

    def load_assets(self):
        # Load images
        self.player_img = pygame.image.load("assets/player.png").convert_alpha()
        self.enemy_img = pygame.image.load("assets/enemy.png").convert_alpha()
        self.bullet_img = pygame.image.load("assets/bullet.png").convert_alpha()
        self.explosion_img = pygame.image.load("assets/explosion.png").convert_alpha()
        self.item_img = pygame.image.load("assets/item.png").convert_alpha()
        
        # Load heart image with fallback
        try:
            self.heart_img = pygame.image.load("assets/heart.png").convert_alpha()
            self.heart_img = pygame.transform.scale(self.heart_img, (30, 30))
            self.use_heart_image = True
        except FileNotFoundError:
            self.use_heart_image = False
            self.heart_img = pygame.Surface((30, 30), pygame.SRCALPHA)
            # Draw a simple heart shape
            pygame.draw.circle(self.heart_img, (255, 0, 0), (15, 10), 8)  # Left circle
            pygame.draw.circle(self.heart_img, (255, 0, 0), (15, 10), 8)  # Right circle
            points = [(15, 20), (8, 10), (22, 10)]  # Triangle points
            pygame.draw.polygon(self.heart_img, (255, 0, 0), points)
        
        self.backgrounds = [
            pygame.image.load(f"assets/background_stage{i}.png").convert()
            for i in range(1, 5)
        ]
        
        # Load sounds
        self.shoot_sound = pygame.mixer.Sound("assets/shoot.wav")
        self.hit_sound = pygame.mixer.Sound("assets/hit.wav")
        try:
            self.player_hit_sound = pygame.mixer.Sound("assets/player_hit.wav")
        except FileNotFoundError:
            self.player_hit_sound = self.hit_sound  # Use hit sound as fallback
        
        pygame.mixer.music.load("assets/bgm.mp3")
        
        # Scale images
        self.player_img = pygame.transform.scale(self.player_img, (100, 100))
        self.enemy_img = pygame.transform.scale(self.enemy_img, (30, 30))
        self.bullet_img = pygame.transform.scale(self.bullet_img, (8, 15))
        self.explosion_img = pygame.transform.scale(self.explosion_img, (40, 40))
        self.item_img = pygame.transform.scale(self.item_img, (25, 25))
        for i in range(4):
            self.backgrounds[i] = pygame.transform.scale(self.backgrounds[i], (WINDOW_WIDTH, WINDOW_HEIGHT))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_SPACE:
                        self.reset_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.running = False
                elif event.key == pygame.K_SPACE:
                    self.shoot_bullet()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_over:
                    self.reset_game()
                else:
                    self.shoot_bullet()

    def update(self):
        if self.game_over:
            return

        current_time = pygame.time.get_ticks()
        
        # Move player
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.player.left > 0:
            self.player.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT] and self.player.right < WINDOW_WIDTH:
            self.player.x += PLAYER_SPEED
            
        # Touch controls for mobile
        if pygame.mouse.get_pressed()[0]:  # Left mouse button or touch
            mouse_x = pygame.mouse.get_pos()[0]
            if mouse_x < self.player.centerx and self.player.left > 0:
                self.player.x -= PLAYER_SPEED
            elif mouse_x > self.player.centerx and self.player.right < WINDOW_WIDTH:
                self.player.x += PLAYER_SPEED
            
        # Spawn enemies
        if current_time - self.last_enemy_spawn > ENEMY_SPAWN_RATE:
            self.spawn_enemy()
            self.last_enemy_spawn = current_time
            
        # Update bullets
        for bullet in self.bullets[:]:
            bullet.y -= BULLET_SPEED
            if bullet.bottom < 0:
                self.bullets.remove(bullet)
                
        # Update enemy bullets
        for bullet in self.enemy_bullets[:]:
            bullet.y += ENEMY_BULLET_SPEED
            if bullet.top > WINDOW_HEIGHT:
                self.enemy_bullets.remove(bullet)
                
        # Update enemies
        for enemy in self.enemies[:]:
            enemy.y += ENEMY_SPEED + (self.stage - 1) * 0.5
            if enemy.top > WINDOW_HEIGHT:
                self.enemies.remove(enemy)
            # Enemy shooting
            if random.random() < ENEMY_SHOOT_CHANCE:
                self.enemy_shoot(enemy)
                
        # Update items
        for item in self.items[:]:
            item.y += ITEM_SPEED
            if item.top > WINDOW_HEIGHT:
                self.items.remove(item)
            elif item.colliderect(self.player):
                self.items.remove(item)
                self.score += 50
                
        # Update explosions
        for explosion in self.explosions[:]:
            if current_time - explosion['time'] > EXPLOSION_DURATION:
                self.explosions.remove(explosion)
                
        # Check collisions
        self.check_collisions()
        
        # Update stage based on score
        if self.score >= 3000 and self.stage < 4:
            self.stage = 4
        elif self.score >= 2000 and self.stage < 3:
            self.stage = 3
        elif self.score >= 1000 and self.stage < 2:
            self.stage = 2

    def shoot_bullet(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_bullet_shot > BULLET_COOLDOWN:
            bullet = pygame.Rect(self.player.centerx - 4, self.player.top, 8, 15)
            self.bullets.append(bullet)
            self.shoot_sound.play()
            self.last_bullet_shot = current_time

    def enemy_shoot(self, enemy):
        bullet = pygame.Rect(enemy.centerx - 4, enemy.bottom, 8, 15)
        self.enemy_bullets.append(bullet)

    def spawn_enemy(self):
        x = random.randint(0, WINDOW_WIDTH - 30)
        enemy = pygame.Rect(x, -30, 30, 30)
        self.enemies.append(enemy)

    def create_explosion(self, x, y):
        self.explosions.append({
            'rect': pygame.Rect(x - 25, y - 25, 50, 50),
            'time': pygame.time.get_ticks()
        })

    def spawn_item(self, x, y):
        if random.random() < ITEM_SPAWN_CHANCE:
            item = pygame.Rect(x, y, 25, 25)
            self.items.append(item)

    def check_collisions(self):
        current_time = pygame.time.get_ticks()
        
        # Check player-enemy bullet collisions
        if current_time > self.invincible_until:
            for bullet in self.enemy_bullets[:]:
                if bullet.colliderect(self.player):
                    self.enemy_bullets.remove(bullet)
                    self.player_hit()
                    break

        # Check bullet-enemy collisions
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.colliderect(enemy):
                    self.bullets.remove(bullet)
                    self.enemies.remove(enemy)
                    self.score += 100
                    self.hit_sound.play()
                    self.create_explosion(enemy.centerx, enemy.centery)
                    self.spawn_item(enemy.centerx, enemy.centery)
                    break

    def player_hit(self):
        current_time = pygame.time.get_ticks()
        if current_time > self.invincible_until:
            self.lives -= 1
            self.player_hit_sound.play()
            self.invincible_until = current_time + INVINCIBLE_DURATION
            if self.lives <= 0:
                self.game_over = True

    def draw(self):
        # Draw background
        self.screen.blit(self.backgrounds[self.stage - 1], (0, 0))
        
        # Draw player (with blink effect if invincible)
        current_time = pygame.time.get_ticks()
        if current_time > self.invincible_until or (current_time // 100) % 2 == 0:
            self.screen.blit(self.player_img, self.player)
        
        # Draw bullets
        for bullet in self.bullets:
            self.screen.blit(self.bullet_img, bullet)
            
        # Draw enemy bullets
        for bullet in self.enemy_bullets:
            self.screen.blit(self.bullet_img, bullet)
            
        # Draw enemies
        for enemy in self.enemies:
            self.screen.blit(self.enemy_img, enemy)
            
        # Draw items
        for item in self.items:
            self.screen.blit(self.item_img, item)
            
        # Draw explosions
        for explosion in self.explosions:
            self.screen.blit(self.explosion_img, explosion['rect'])
            
        # Draw score and stage
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        stage_text = font.render(f"Stage: {self.stage}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(stage_text, (10, 50))
        
        # Draw lives (hearts)
        for i in range(self.lives):
            self.screen.blit(self.heart_img, (10 + i * 35, 90))
        
        # Draw game over screen
        if self.game_over:
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
            overlay.set_alpha(128)
            overlay.fill(BLACK)
            self.screen.blit(overlay, (0, 0))
            
            game_over_font = pygame.font.Font(None, 72)
            game_over_text = game_over_font.render("Game Over", True, RED)
            restart_font = pygame.font.Font(None, 36)
            restart_text = restart_font.render("Tap to restart", True, WHITE)
            
            self.screen.blit(game_over_text, 
                           (WINDOW_WIDTH // 2 - game_over_text.get_width() // 2, 
                            WINDOW_HEIGHT // 2 - 50))
            self.screen.blit(restart_text, 
                           (WINDOW_WIDTH // 2 - restart_text.get_width() // 2, 
                            WINDOW_HEIGHT // 2 + 50))
        
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = GalagaGame()
    game.run()
    pygame.quit()
