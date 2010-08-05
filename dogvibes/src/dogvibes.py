import gobject
import gst
import os
import config
import sys
import shelve

import threading

from amp import Amp

# import spources
from filesource import FileSource
from spotifysource import SpotifySource
from srradiosource import SRRadioSource
#from youtubesource import YoutubeSource

from albumart import AlbumArt

# import speakers
from devicespeaker import DeviceSpeaker
from fakespeaker import FakeSpeaker

from track import Track
from playlist import Playlist
from user import User

class Dogvibes():
    ampdbname = "qurkloxuiikkolkjhhf"

    def __init__(self):

        # load configuration
        try: cfg = config.load("dogvibes.conf")
        except Exception, e:
            print "ERROR: Cannot load configuration file\n"
            sys.exit(1)

        # initiate
        self.needs_push_update = False
        self.search_history = []

        # create sources struct
        self.sources = shelve.open('dogvibes.shelve', writeback=True)

        # add all speakers, should also be stored in database as sources
        self.speakers = [DeviceSpeaker("devicesink"), FakeSpeaker("fakespeaker")]

        first_boot = False
        if len(self.sources) == 0:
            first_boot = True
            spot_user = cfg["SPOTIFY_USER"]
            spot_pass = cfg["SPOTIFY_PASS"]
            self.modify_spotifysource(spot_user, spot_pass)
            self.modify_srradiosource();

        # add all amps, currently only one
        amp0 = Amp(self, "0")
        amp0.connect_speaker(0)
        self.amps = [amp0]

        if first_boot == True:
            # currently connect all sources to the first amp
            for key in self.sources.keys():
                amp0.connect_source(key)

    def create_track_from_uri(self, uri):
        track = None
        for name,source in self.sources.iteritems():
            if source:
                track = source.create_track_from_uri(uri)
                if track != None:
                    return track
        raise ValueError('Could not create track from URI')

    def create_tracks_from_uri(self, uri):
        tracks = []
        for name,source in self.sources.iteritems():
            if source:
                tracks = source.create_tracks_from_uri(uri)
                if tracks != None:
                    return tracks
        raise ValueError('Could not create track from URI')

    def create_tracks_from_album(self, album):
        tracks = []
        for name,source in self.sources.iteritems():
            if source:
                tracks = source.create_tracks_from_album(album)
                if tracks != None:
                    return tracks
        raise ValueError('Could not create track from Album')

    def modify_spotifysource(self, username, password):
        if self.sources.has_key("spotify"):
            self.sources["spotify"].amp.stop()
            self.sources["spotify"].relogin(username, password)
            self.sources.sync()
        else:
            spotifysource = SpotifySource("spotify", username, password)
            self.sources["spotify"] = spotifysource
            self.sources.sync()

    def modify_srradiosource(self):
        if self.sources.has_key("srradiosource"):
            pass
        else:
            srradiosource = SRRadioSource("srradio")
            self.sources["srradio"] = srradiosource
            self.sources.sync()

    def get_all_tracks_in_playlist(self, playlist_id):
        try:
            playlist = Playlist.get(playlist_id)
        except ValueError as e:
            raise
        tracks = playlist.get_all_tracks()
        ret = [track.__dict__ for track in tracks]
        return ret

    def do_search(self, query, request):
        ret = []
        for name,source in self.sources.iteritems():
            if query.startswith(source.search_prefix + ":"):
                newquery = query.split(":",1)
                ret = source.search(newquery[1])
                request.finish(ret)
                return

        #if no prefix, just use spotify, if there exists such a source
        for name,source in self.sources.iteritems():
            if source.search_prefix == "spotify":
                ret = source.search(query)
                request.finish(ret)
                return
        request.finish(ret)

    def fetch_albumart(self, artist, album, size, request):
        try:
            request.finish(AlbumArt.get_image(artist, album, size), raw = True)
        except ValueError as e:
            request.finish(AlbumArt.get_standard_image(size), raw = True)

    def create_playlist(self, name):
        Playlist.create(name)

    def get_album(self, album_uri, request):
        album = None
        for name, source in self.sources.iteritems():
            album = source.get_album(album_uri)
            if album != None:
                break
        request.finish(album)

    # API

    def API_modifySpotifySource(self, username, password, request):
        self.modify_spotifysource(username, password)
        request.finish()

    def API_getAllSources(self, request):
        request.finish()

    def API_search(self, query, request):
        threading.Thread(target=self.do_search, args=(query, request)).start()

    def API_getAlbums(self, query, request):
        ret = []
        for name, source in self.sources.iteritems():
            if source:
                ret += source.get_albums(query)
        request.finish(ret)

    def API_getAlbum(self, album_uri, request):
        threading.Thread(target=self.get_album,
                         args=(album_uri, request)).start()

    def API_list(self, type, request):
        ret = []
        for name, source in self.sources.itermitems():
            if source:
                ret += source.list(type)
        request.finish(ret)

    def API_getAlbumArt(self, artist, album, size, request):
        threading.Thread(target=self.fetch_albumart,
                         args=(artist, album, size, request)).start()

    def API_createPlaylist(self, name, request):
        self.create_playlist(name)
        request.finish()

    def API_removePlaylist(self, id, request):
        Playlist.remove(id)
        self.needs_push_update = True
        request.finish()

    def API_addTrackToPlaylist(self, playlist_id, uri, request):
        track = self.create_track_from_uri(uri)
        try:
            playlist = Playlist.get(playlist_id)
        except ValueError as e:
            raise
        self.needs_push_update = True
        request.finish(playlist.add_track(track, request.user))
        
    def API_addTracksToPlaylist(self, playlist_id, uri, request):
        tracks = self.create_tracks_from_uri(uri)
        try:
            playlist = Playlist.get(playlist_id)
        except ValueError as e:
            raise
        self.needs_push_update = True
        request.finish(playlist.add_tracks(tracks, request.user, -1))
        
    def API_removeTrackFromPlaylist(self, playlist_id, track_id, request):
        try:
            playlist = Playlist.get(playlist_id)
            playlist.remove_track_id(int(track_id))
        except ValueError as e:
            raise
        self.needs_push_update = True
        request.finish()

    def API_removeTracksFromPlaylist(self, playlist_id, track_ids, request):
        try:
            playlist = Playlist.get(playlist_id)
            for track_id in track_ids.split(','):
                # don't crash on railing comma
                if track_id != '':
                    playlist.remove_track_id(int(track_id))
        except ValueError as e:
            raise
        self.needs_push_update = True
        request.finish()

    def API_getAllPlaylists(self, request):
        all_playlists = [playlist.to_dict() for playlist in Playlist.get_all()]
        all_playlists = filter(lambda x:x['name'][0:len(self.ampdbname)] != self.ampdbname,all_playlists)
        request.finish(all_playlists)

    def API_getAllTracksInPlaylist(self, playlist_id, request):
        request.finish(self.get_all_tracks_in_playlist(playlist_id))

    def API_renamePlaylist(self, playlist_id, name, request):
        try:
            Playlist.rename(playlist_id, name)
        except ValueError as e:
            raise
        self.needs_push_update = True
        request.finish()

    def API_moveTrackInPlaylist(self, playlist_id, track_id, position, request):
        try:
            playlist = Playlist.get(playlist_id)
            playlist.move_track(int(track_id), int(position))
        except ValueError as e:
            raise
        self.needs_push_update = True
        request.finish()

    def API_getSearchHistory(self, nbr, request):
        request.finish(self.search_history[-int(nbr):])

    def API_getAllVotes(self, request):
        request.finish({"title":"julles jularbo", "artist":"calle jularbo", "album": "kalles jul", "user":"gyllen", "time":100, "votes":1, "duration":0, "votes":3})
