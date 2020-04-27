import pympris
import dbus
from dbus.mainloop.glib import DBusGMainLoop


class MprisControl:
    def __init__(self):
        self.__dbus_loop = DBusGMainLoop()
        self.__bus = dbus.SessionBus(mainloop=self.__dbus_loop)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def get_players(self) -> [pympris.MediaPlayer]:
        players = list(pympris.available_players())
        return [pympris.MediaPlayer(player, self.__bus) for player in players]

    def get_playing_players(self) -> [pympris.MediaPlayer]:
        players = self.get_players()
        return [player for player in players if player.player.PlaybackStatus == 'Playing']

    def __get_priority_player(self, players: [pympris.MediaPlayer]) -> pympris.Player:
        if len(players) > 0:
            for player in players:
                if player.root.Identity == 'Spotify':
                    return player.player
            return players[0].player

    def play_pause_auto(self) -> None:
        player = self.__get_priority_player(self.get_playing_players())
        if player is not None:
            player.PlayPause()
            return
        player = self.__get_priority_player(self.get_players())
        if player is not None:
            player.PlayPause()
            return

