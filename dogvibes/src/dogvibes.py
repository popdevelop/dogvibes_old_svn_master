import gobject
import gst
import os
import config
import sys

import threading

from amp import Amp

# import spources
from spotifysource import SpotifySource
from filesource import FileSource
from srradiosource import SRRadioSource
from albumart import AlbumArt

# import speakers
from devicespeaker import DeviceSpeaker
from fakespeaker import FakeSpeaker

from track import Track
from playlist import Playlist
from source import Source

class Dogvibes():
    ampdbname = "qurkloxuiikkolkjhhf"

    def __init__(self):
        

        try: cfg = config.load("dogvibes.conf")
        except Exception, e:
            print "ERROR: Cannot load configuration file\n"
            sys.exit(1)

        self.sources = []

        srradiosource = SRRadioSource("srradiosource")
        self.sources.append(srradiosource)

        # Hackidooda and laziness to always create correct source, remove in real release
        if Source.length() > 1:
            allsources = Source.get_all()
            # FIXME this should be dynamic
            for source in allsources:
                if source.type == "spotify":
                    spotifysource = SpotifySource("spotify", source.user, source.passw)
                    self.sources.append(spotifysource)
        else:
            # This is just here because of laziness
            if(cfg['ENABLE_SPOTIFY_SOURCE'] == '1'):
                spot_user = cfg["SPOTIFY_USER"]
                spot_pass = cfg["SPOTIFY_PASS"]
                self.create_spotifysource(spot_user, spot_pass)
            if(cfg['ENABLE_FILE_SOURCE'] == '1'):
                self.create_filesource(cfg["FILE_SOURCE_ROOT"])

        # add all speakers, should also be stored in database as sources
        self.speakers = [DeviceSpeaker("devicesink"), FakeSpeaker("fakespeaker")]

        self.needs_push_update = False

        self.search_history = []

        # add all amps
        amp0 = Amp(self, "0")
        amp0.connect_speaker(0)
        self.amps = [amp0]

        # add sources to amp, assume spotify source on first position, laziness
        amp0.connect_source(0)
        amp0.connect_source(1)

    def create_track_from_uri(self, uri):
        track = None
        for source in self.sources:
            if source:
                track = source.create_track_from_uri(uri);
                if track != None:
                    return track
        raise ValueError('Could not create track from URI')
        
    def create_tracks_from_uri(self, uri):
        tracks = []
        for source in self.sources:
            if source:
                tracks = source.create_tracks_from_uri(uri);
                if tracks != None:
                    return tracks
        raise ValueError('Could not create track from URI')

    def create_tracks_from_album(self, album):
        tracks = []
        for source in self.sources:
            if source:
                tracks = source.create_tracks_from_album(album);
                if tracks != None:
                    return tracks
        raise ValueError('Could not create track from Album')

    def create_spotifysource(self, user, passw):
        spotifysource = SpotifySource("spotify", user, passw)
        # FIXME: this logs in to the spotify source for the moment
        spotifysource.get_src()
        self.sources.append(spotifysource)
        Source.add(user, passw, "spotify")

    def create_filesource(self, dir):
        pass

    def get_all_tracks_in_playlist(self, playlist_id):
        try:
            playlist = Playlist.get(playlist_id)
        except ValueError as e:
            raise
        return [track.__dict__ for track in playlist.get_all_tracks()]

    def do_search(self, query, request):
        ret = []
        for source in self.sources:
            if source:
                ret += source.search(query)
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
        for source in self.sources:
            album = source.get_album(album_uri);
            if album != None:
                break
        request.finish(album)

    # API

    def API_createSpotifySource(self, user, passw, request):
        self.create_spotifysource(user, passw)
        request.finish()

    def API_createFileSource(self, dir, request):
        self.create_filesource(dir)
        request.finish()

    def API_getAllSources(self, request):
        request.finish()

    def API_search(self, query, request):
        threading.Thread(target=self.do_search, args=(query, request)).start()

    def API_getAlbums(self, query, request):
        ret = []
        for source in self.sources:
            if source:
                ret += source.get_albums(query)
        request.finish(ret)

    def API_getAlbum(self, album_uri, request):
        threading.Thread(target=self.get_album,
                         args=(album_uri, request)).start()

    def API_list(self, type, request):
        ret = []
        for source in self.sources:
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
        request.finish(playlist.add_track(track, request))
        
    def API_addTracksToPlaylist(self, playlist_id, uri, request):
        tracks = self.create_tracks_from_uri(uri)
        try:
            playlist = Playlist.get(playlist_id)
        except ValueError as e:
            raise
        self.needs_push_update = True
        request.finish(playlist.add_tracks(tracks, request))
        
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
                if track_id != '': # don't crash on railing comma
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
