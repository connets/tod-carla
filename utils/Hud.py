import datetime
import math
import os

import carla
import pygame

from utils.Carlasupport import get_actor_display_name

def _fmt_pct(v):
    return 'n/d' if v is None else '%.1f %%' % (100.0 * v)


def _fmt_level(v):
    return 'n/d' if v is None else 'liv. %d' % v


class HUD(object):
    """Class for HUD text"""

    def __init__(self, player, clock, display, telemetry=None):
        """Constructor method.

        telemetry: callable opzionale che restituisce un dict con le grandezze
        della teleguida (loss_ratio, quality_level, link_lost, visible). Sta fuori
        da questa classe perche' vivono nel controller lato agente, e l'HUD non
        deve dipendere dai listener.
        """
        self.display = display
        self._telemetry = telemetry
        self.dim = (display.get_width(), display.get_height())
        self.player = player
        self.clock = clock

        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 12 if os.name == 'nt' else 14)
        self._notifications = FadingText(font, (display.get_width(), 40), (0, self.display.get_height() - 40))
        # self.help = HelpText(pygame.font.Font(mono, 24), width, height)
        self.server_fps = 0
        self.frame = 0
        self.simulation_time = 0
        self._show_info = True
        self._info_text = []
        self._server_clock = pygame.time.Clock()

    def on_world_tick(self, timestamp):
        """Gets informations from the world at every tick"""
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        # 'frame_count' non esiste su carla.Timestamp (il campo e' 'frame'), e in
        # co-simulazione after_world_tick passa un float: accetta entrambi.
        self.frame = getattr(timestamp, 'frame', self.frame)
        self.simulation_time = getattr(timestamp, 'elapsed_seconds', timestamp)

    def tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        # 'frame_count' non esiste su carla.Timestamp (il campo e' 'frame'), e in
        # co-simulazione after_world_tick passa un float: accetta entrambi.
        self.frame = getattr(timestamp, 'frame', self.frame)
        self.simulation_time = getattr(timestamp, 'elapsed_seconds', timestamp)

        """HUD method for every tick"""
        self._notifications.tick(self.player, self.clock)
        if not self._show_info:
            return
        transform = self.player.get_transform()
        vel = self.player.get_velocity()
        control = self.player.get_control()
        heading = 'N' if abs(transform.rotation.yaw) < 89.5 else ''
        heading += 'S' if abs(transform.rotation.yaw) > 90.5 else ''
        heading += 'E' if 179.5 > transform.rotation.yaw > 0.5 else ''
        heading += 'W' if -0.5 > transform.rotation.yaw > -179.5 else ''
        # colhist = sim_world.collision_sensor.get_collision_history()
        # collision = [colhist[x + self.frame - 200] for x in range(0, 200)]
        # max_col = max(1.0, max(collision))
        # collision = [x / max_col for x in collision]
        # vehicles = world.world.get_actors().filter('vehicle.*')
        # Telemetria della teleguida: e' opzionale e non deve MAI far cadere il
        # rendering, quindi ogni errore viene assorbito.
        try:
            tele = self._telemetry() if self._telemetry else {}
        except Exception:
            tele = {}
        vehicles = tele.get('visible') or []

        self._info_text = [
            'Server:  % 16.0f FPS' % self.server_fps,
            'Client:  % 16.0f FPS' % self.clock.get_fps(),
            '',
            'Vehicle: % 20s' % get_actor_display_name(self.player, truncate=20),
            'Simulation time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)),
            '',
            'Speed:   % 15.0f km/h' % (3.6 * math.sqrt(vel.x**2 + vel.y**2 + vel.z**2)),
            u'Heading:% 16.0f\N{DEGREE SIGN} % 2s' % (transform.rotation.yaw, heading),
            'Location:% 20s' % ('(% 5.1f, % 5.1f)' % (transform.location.x, transform.location.y)),
            # 'GNSS:% 24s' % ('(% 2.6f, % 3.6f)' % (sim_world.gnss_sensor.lat, sim_world.gnss_sensor.lon)),
            'Height:  % 18.0f m' % transform.location.z,
            '',
            '--- Teleguida ---',
            'Perdita:% 18s' % _fmt_pct(tele.get('loss_ratio')),
            'Qualita camera:% 11s' % _fmt_level(tele.get('quality_level')),
            'Canale:% 19s' % ('PERSO' if tele.get('link_lost') else 'ok'),
            '']
        if isinstance(control, carla.VehicleControl):
            self._info_text += [
                ('Throttle:', control.throttle, 0.0, 1.0),
                ('Steer:', control.steer, -1.0, 1.0),
                ('Brake:', control.brake, 0.0, 1.0),
                ('Reverse:', control.reverse),
                ('Hand brake:', control.hand_brake),
                ('Manual:', control.manual_gear_shift),
                'Gear:        %s' % {-1: 'R', 0: 'N'}.get(control.gear, control.gear)]
        elif isinstance(control, carla.WalkerControl):
            self._info_text += [
                ('Speed:', control.speed, 0.0, 5.556),
                ('Jump:', control.jump)]
        self._info_text += [
            '',
            "Visti dall'operatore:% 5d" % len(vehicles)]

        # 'vehicles' arriva gia' pronto dalla telemetria come lista di (distanza, nome):
        # sono i veicoli che il teleoperatore VEDE nell'ultimo stato ricevuto, non quelli
        # realmente presenti nel mondo. E' l'informazione giusta per questo HUD, e non
        # costa una RPC per frame (che e' il modo in cui si pianta il server CARLA).
        for distance, label in sorted(vehicles)[:8]:
            self._info_text.append('% 4dm %s' % (distance, label))

    def toggle_info(self):
        """Toggle info on or off"""
        self._show_info = not self._show_info

    def notification(self, text, seconds=2.0):
        """Notification text"""
        self._notifications.set_text(text, seconds=seconds)

    def error(self, text):
        """Error text"""
        self._notifications.set_text('Error: %s' % text, (255, 0, 0))

    def render(self):
        """Render for HUD class"""
        if self._show_info:
            info_surface = pygame.Surface((220, self.dim[1]))
            info_surface.set_alpha(100)
            self.display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            for item in self._info_text:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, list):
                    if len(item) > 1:
                        points = [(x + 8, v_offset + 8 + (1 - y) * 30) for x, y in enumerate(item)]
                        pygame.draw.lines(self.display, (255, 136, 0), False, points, 2)
                    item = None
                    v_offset += 18
                elif isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                        pygame.draw.rect(self.display, (255, 255, 255), rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                        pygame.draw.rect(self.display, (255, 255, 255), rect_border, 1)
                        fig = (item[1] - item[2]) / (item[3] - item[2])
                        if item[2] < 0.0:
                            rect = pygame.Rect(
                                (bar_h_offset + fig * (bar_width - 6), v_offset + 8), (6, 6))
                        else:
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (fig * bar_width, 6))
                        pygame.draw.rect(self.display, (255, 255, 255), rect)
                    item = item[0]
                if item:  # At this point has to be a str.
                    surface = self._font_mono.render(item, True, (255, 255, 255))
                    self.display.blit(surface, (8, v_offset))
                v_offset += 18
        self._notifications.render(self.display)
        # self.help.render(display)




# ==============================================================================
# -- FadingText ----------------------------------------------------------------
# ==============================================================================



class FadingText(object):
    """ Class for fading text """

    def __init__(self, font, dim, pos):
        """Constructor method"""
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        """Set fading text"""
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        """Fading text method for every tick"""
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        """Render fading text method"""
        display.blit(self.surface, self.pos)


# ==============================================================================
# -- HelpText ------------------------------------------------------------------
# ==============================================================================


class HelpText(object):
    """Helper class to handle text output using pygame"""
    def __init__(self, font, width, height):
        self.font = font
        self.line_space = 18
        self.dim = (780, self.line_space + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill((0, 0, 0, 0))
        for n, line in enumerate([]):
            text_texture = self.font.render(line, True, (255, 255, 255))
            self.surface.blit(text_texture, (22, n * self.line_space))
            self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        self._render = not self._render

    def render(self, display):
        if self._render:
            display.blit(self.surface, self.pos)