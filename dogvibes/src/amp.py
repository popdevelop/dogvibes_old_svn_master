import gst
import hashlib
import random
import time
import logging
import shelve

from track import Track
from playlist import Playlist
from user import User

class DogError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Amp():
    def __init__(self, dogvibes, id):
        self.dogvibes = dogvibes
        self.pipeline = gst.Pipeline("amppipeline" + id)

        # create the tee element
        self.tee = gst.element_factory_make("tee", "tee")
        self.pipeline.add(self.tee)

        # listen for EOS
        self.bus = self.pipeline.get_bus()
        self.bus.add_signal_watch()
        self.bus.connect('message', self.pipeline_message)

        # Create amps playqueue
        if Playlist.name_exists(dogvibes.ampdbname + id) == False:
            self.dogvibes.create_playlist(dogvibes.ampdbname + id)
        tqplaylist = Playlist.get_by_name(dogvibes.ampdbname + id)
        self.tmpqueue_id = tqplaylist.id

        self.active_playlist_id = self.tmpqueue_id
        self.active_playlists_track_id = -1
        self.fallback_playlist_id = -1
        self.fallback_playlists_track_id = -1

        self.vote_version = 0

        # sources connected to the amp
        self.sources = shelve.open("amp" + id + ".shelve", writeback=True)

        # aquire all sources
        for key in self.sources.keys():
            self.dogvibes.sources[key].amp = self

        # the gstreamer source that is currently used for playback
        self.src = None

        logging.debug("Initiated amp %s", id)

        self.needs_push_update = False

    # Soon to be API
    def connect_source(self, name):
        if not self.dogvibes.sources.has_key(name):
            logging.warning ("Connect source - source does not exist")
            return

        if self.dogvibes.sources[name].amp != None:
            logging.warning ("Connect source - source is already connected to amp")
            return

        # Add amp as owner of source
        self.dogvibes.sources[name].amp = self
        self.sources[name] = name
        self.sources.sync()

    def disconnect_source(self, name):
        if not self.dogvibes.sources.has_key(name):
            logging.warning ("Connect source - source does not exist")
            return

        if self.dogvibes.sources[name].amp == None:
            logging.warning ("Source has no owner")
            return

        if self.dogvibes.sources[name].amp != self:
            logging.warning ("Amp not owner of this source")
            return

        del self.sources[name]
        self.sources.sync()

    def connect_speaker(self, nbr, request = None):
        nbr = int(nbr)
        if nbr > len(self.dogvibes.speakers) - 1:
            logging.warning("Connect speaker - speaker does not exist")

        speaker = self.dogvibes.speakers[nbr]

        if self.pipeline.get_by_name(speaker.name) == None:
            self.sink = self.dogvibes.speakers[nbr].get_speaker()
            self.pipeline.add(self.sink)
            self.tee.link(self.sink)
        else:
            logging.debug("Speaker %d already connected" % nbr)
        #self.needs_push_update = True
        # FIXME: activate when client connection has been fixed!

    def pad_added(self, element, pad, last):
        logging.debug("Lets add a speaker we found suitable elements to decode")
        pad.link(self.tee.get_pad("sink"))

    def change_track(self, tracknbr, relative):
        tracknbr = int(tracknbr)

        logging.debug("Change to track %d, is relative:%d", tracknbr, relative)

        if relative and (tracknbr > 1 or tracknbr < -1):
            raise DogError, "Relative change track greater/less than 1 not implemented"

        playlist = self.fetch_active_playlist()
        track = self.fetch_active_track()

        if track == None and relative:
            logging.warning("I am lost can not call relative because i do no know where I am")
            return

        # If we are in tmpqueue either removetrack or push it to the top
        if self.is_in_tmpqueue():
            if relative and (tracknbr == 1):
                # Remove track and goto next track
                playlist.remove_playlist_tracks_id(self.active_playlists_track_id)
                next_position = 0
            elif relative and (tracknbr == -1):
                # Do nothing since we are always on top in playqueue
                return
            else:
                # Move requested track to top of tmpqueue and play it
                self.active_playlists_track_id = tracknbr
                playlist.move_track(self.active_playlists_track_id, 1)
                next_position = 0

            # Check if tmpqueue no longer exists (all tracks has been removed)
            if playlist.length() <= 0:
                # Check if we used to be in a playlist
                if self.fallback_playlist_id != -1:
                    # Change one track forward in the playlist we used to be in
                    self.active_playlist_id = self.fallback_playlist_id
                    self.active_playlists_track_id = self.fallback_playlists_track_id
                    playlist = Playlist.get(self.active_playlist_id)
                    next_position = playlist.get_track_id(self.active_playlists_track_id).position - 1
                    next_position = next_position + 1
                    if next_position >= playlist.length():
                        # We were the last song in the playlist we used to be in, just stop everyting
                        self.set_state(gst.STATE_NULL)
                        return
                else:
                    # We have not entered any playlist yet, just stop playback
                    self.set_state(gst.STATE_NULL)
                    return
        elif (Playlist.get(self.tmpqueue_id).length() > 0) and relative:
            # Save the playlist that we curently are playing in for later use
            self.fallback_playlist_id = self.active_playlist_id
            self.fallback_playlists_track_id = self.active_playlists_track_id
            # Switch to playqueue
            self.active_playlist_id = self.tmpqueue_id
            playlist = Playlist.get(self.active_playlist_id)
            next_position = 0
        else:
            # We are inside a playlist
            if relative:
                next_position = track.position - 1 + tracknbr
            else:
                try:
                    next_position = playlist.get_track_id(tracknbr).position - 1
                    logging.debug("In a playlist trying position %d", next_position)
                except:
                    logging.debug("Could not find this position in the active playlist, no action")
                    return

        try:
            track = playlist.get_track_nbr(next_position)
        except:
            self.set_state(gst.STATE_NULL)
            self.active_playlists_track_id = -1
            logging.debug("Could not get to next positon in the active playlist")
            return

        self.active_playlists_track_id = track.ptid
        self.set_state(gst.STATE_NULL)
        self.start_track(playlist.get_track_id(self.active_playlists_track_id))

    def pipeline_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.next_track()
            #request.push({'state': self.get_state()})
            #request.push(self.track_to_client())
            self.vote_version += 1
            self.needs_push_update = True
            # TODO: is this enough? An update is pushed to the clients
            # but will the info be correct?


    def start_track(self, track):
        (pending, state, timeout) = self.pipeline.get_state()

        logging.debug ("Start track %s", track.uri)

        if self.src:
            self.pipeline.remove(self.src)
            if self.pipeline.get_by_name("decodebin2") != None:
                self.pipeline.remove(self.decodebin)

        self.src = None

        for key in self.sources.keys():
            if self.dogvibes.sources[key].uri_matches(track.uri):
                self.src = self.dogvibes.sources[key].get_src()
                self.dogvibes.sources[key].set_track(track)
                self.pipeline.add(self.src)
                self.src.link(self.tee)

        # Try decode bin if there where no match within the sources
        if self.src == None:
            logging.debug ("Decodebin is taking care of this uri")
            self.src = gst.element_make_from_uri(gst.URI_SRC, track.uri, "source")
            if self.src == None:
                logging.error("No suitable gstreamer element found for given uri")
                return False
            self.decodebin = gst.element_factory_make("decodebin2", "decodebin2")
            self.decodebin.connect('new-decoded-pad', self.pad_added)
            self.pipeline.add(self.src)
            self.pipeline.add(self.decodebin)
            self.src.link(self.decodebin)

        self.set_state(gst.STATE_PLAYING)

        return True

    def get_state(self):
        (pending, state, timeout) = self.pipeline.get_state()
        if state == gst.STATE_PLAYING:
            return 'playing'
        elif state == gst.STATE_NULL:
            return 'stopped'
        else:
            return 'paused'

    def set_state(self, state):
        if self.src == None:
            # FIXME return something sweet
            return
        logging.debug("set state try: "+str(state))
        res = self.pipeline.set_state(state)
        if res != gst.STATE_CHANGE_FAILURE:
            (pending, res, timeout) = self.pipeline.get_state()
            while (res != state):
                time.sleep(0.1)
                (pending, res, timeout) = self.pipeline.get_state()
            logging.debug("set state success: "+ str(state))
        else:
            logging.warning("set state failure: "+ str(state))
        return res

    def is_in_tmpqueue(self):
        return (self.tmpqueue_id == self.active_playlist_id)

    def fetch_active_playlist(self):
        try:
            playlist = Playlist.get(self.active_playlist_id)
            return playlist
        except:
            # The play list have been removed or disapperd use tmpqueue as fallback
            self.active_playlist_id = self.tmpqueue_id
            self.active_playlists_track_id = -1
            playlist = Playlist.get(self.active_playlist_id)
            return playlist

    def fetch_active_track(self):
        # Assume that fetch active playlist alreay been run
        playlist = Playlist.get(self.active_playlist_id)

        if playlist.length() <= 0:
            return None

        if self.active_playlists_track_id != -1:
            try:
                track = playlist.get_track_id(self.active_playlists_track_id)
                return track
            except:
                logging.debug("Could find any active track, %d on playlist %d", self.active_playlists_track_id, self.active_playlist_id)
                self.active_playlists_track_id = -1
                return None
        else:
            # Try the first active_play_list id
            track = playlist.get_track_nbr(0)
            self.active_playlists_track_id = track.ptid

            if self.start_track(track) == False:
                self.active_playlists_track_id = -1
                return None

            self.set_state(gst.STATE_PAUSED)
            return track

    def get_played_milliseconds(self):
        (pending, state, timeout) = self.pipeline.get_state ()
        if (state == gst.STATE_NULL):
            logging.debug ("getPlayedMilliseconds in state==NULL")
            return 0
        try:
             src = self.src.get_by_name("source")
             pos = (pos, form) = src.query_position(gst.FORMAT_TIME)
        except:
            pos = 0
        # We get nanoseconds from gstreamer elements, convert to ms
        return pos / 1000000

    def next_track(self):
        self.change_track(1, True)

    def get_active_playlist_id(self):
        if self.is_in_tmpqueue():
            return -1
        else:
            return self.active_playlist_id

    def get_status(self):
        status = {}

        # FIXME this should be speaker specific
        status['volume'] = self.dogvibes.speakers[0].get_volume()
        status['playlistversion'] = Playlist.get_version()

        playlist = self.fetch_active_playlist()

        # -1 is in tmpqueue
        status['playlist_id'] = self.get_active_playlist_id()
        status['vote_version'] = self.vote_version

        track = self.fetch_active_track()
        if track != None:
            status['uri'] = track.uri
            status['title'] = track.title
            status['artist'] = track.artist
            status['album'] = track.album
            status['duration'] = int(track.duration)
            status['elapsedmseconds'] = self.get_played_milliseconds()
            status['id'] = self.active_playlists_track_id
            status['index'] = track.position - 1
        else:
            status['uri'] = "dummy"

        (pending, state, timeout) = self.pipeline.get_state()
        if state == gst.STATE_PLAYING:
            status['state'] = 'playing'
        elif state == gst.STATE_NULL:
            status['state'] = 'stopped'
        else:
            status['state'] = 'paused'

        return status

    def track_to_client(self):
        track = self.fetch_active_track()
        if track == None:
            return []
        return { "album": track.album,
                 "artist": track.artist,
                 "title": track.title,
                 "uri": track.uri,
                 "duration": track.duration,
                 "id": self.active_playlists_track_id,
                 "index": track.position - 1 }

    def play_track(self, playlist_id, nbr):
        nbr = int(nbr)
        playlist_id = int(playlist_id) # TODO: should extract this from track

        logging.debug("Playing track %d on playlist %d", nbr, playlist_id)

        # -1 is tmpqueue
        if (playlist_id == -1):
            # Save last known playlist that is not the tmpqueue
            if (not self.is_in_tmpqueue()):
                self.fallback_playlist_id = self.active_playlist_id
                self.fallback_playlists_track_id = self.active_playlists_track_id
            self.active_playlist_id = self.tmpqueue_id
        else:
            self.active_playlist_id = playlist_id

        self.change_track(nbr, False)

    def stop(self):
        self.set_state(gst.STATE_NULL)

    # API

    def API_connectSource(self, name, request):
        self.connect_source(name)
        request.finish(name)

    def API_disconnectSource(self, name, request):
        self.disconnect_source(name)
        request.finish(name)

    def API_connectSpeaker(self, nbr, request):
        self.connect_speaker(nbr)
        request.finish()

    def API_disconnectSpeaker(self, nbr, request):
        nbr = int(nbr)
        if nbr > len(self.dogvibes.speakers) - 1:
            logging.warning ("disconnect speaker - speaker does not exist")

        speaker = self.dogvibes.speakers[nbr]

        if self.pipeline.get_by_name(speaker.name) != None:
            (pending, state, timeout) = self.pipeline.get_state()
            self.set_state(gst.STATE_NULL)
            rm = self.pipeline.get_by_name(speaker.name)
            self.pipeline.remove(rm)
            self.tee.unlink(rm)
            self.set_state(state)
        else:
            logging.warning ("disconnect speaker - speaker not found")
        request.finish()

    def API_getAllTracksInQueue(self, request):
        request.finish(self.dogvibes.get_all_tracks_in_playlist(self.tmpqueue_id))

    def API_getPlayedMilliSeconds(self, request):
        request.finish(self.get_played_milliseconds())

    def API_getStatus(self, request):
        request.finish(self.get_status())

    def API_nextTrack(self, request):
        self.next_track()
        request.push({'playlist_id': self.get_active_playlist_id()})
        request.push({'state': self.get_state()})
        request.push(self.track_to_client())
        request.finish()

    def API_playTrack(self, playlist_id, nbr, request):
        self.play_track(playlist_id, nbr)
        request.push({'playlist_id': self.get_active_playlist_id()})
        request.push({'state': self.get_state()})
        request.push(self.track_to_client())
        request.finish()

    def API_previousTrack(self, request):
        self.change_track(-1, True)
        request.push({'playlist_id': self.get_active_playlist_id()})
        request.push({'state': self.get_state()})
        request.push(self.track_to_client())
        request.finish()

    def API_play(self, request):
        playlist = self.fetch_active_playlist()
        track = self.fetch_active_track()
        if track != None:
            self.set_state(gst.STATE_PLAYING)

        request.push({'state': self.get_state()})
        request.finish()

    def API_pause(self, request):
        self.set_state(gst.STATE_PAUSED)
        # FIXME we need to push the state paused to all clients
        # when play token lost, request == None
        if request != None:
            request.push({'state': self.get_state()})
            request.finish()

    #def API_queue(self, uri, position, request): update when clients are ready...
    def API_addVote(self, uri, request):
        track = self.dogvibes.create_track_from_uri(uri)
        playlist = Playlist.get(self.tmpqueue_id)
        playlist.add_vote(track, request.user, request.avatar_url)

        self.needs_push_update = True
        self.vote_version += 1
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_removeVote(self, uri, request):
        track = self.dogvibes.create_track_from_uri(uri)
        playlist = Playlist.get(self.tmpqueue_id)
        playlist.remove_vote(track, request.user, request.avatar_url)

        self.needs_push_update = True
        self.vote_version += 1
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_queue(self, uri, request):
        position = -1 #put tracks last in queue as temporary default...
        tracks = self.dogvibes.create_tracks_from_uri(uri)
        playlist = Playlist.get(self.tmpqueue_id)

        if position == "1":
            #act as queue and play
            rmtrack = None

            # If in tmpqueue and state is playing and there are tracks in tmpqueue.
            # Then remove the currently playing track. Since we do not want to queue tracks
            # from just "clicking around".
            if self.is_in_tmpqueue() and self.get_state() == 'playing' and playlist.length() >= 1:
                rmtrack = playlist.get_track_nbr(0).ptid

            id = playlist.add_tracks(tracks, position)

            self.play_track(playlist.id, id)

            if rmtrack != None:
                playlist.remove_playlist_tracks_id(rmtrack)
        else:
            playlist.add_tracks(tracks, position)

        self.needs_push_update = True
        request.finish()

    def API_queueAndPlay(self, uri, request):
        tracks = self.dogvibes.create_tracks_from_uri(uri)
        playlist = Playlist.get(self.tmpqueue_id)

        rmtrack = None

        # If in tmpqueue and state is playing and there are tracks in tmpqueue.
        # Then remove the currently playing track. Since we do not want to queue tracks
        # from just "clicking around".
        if self.is_in_tmpqueue() and self.get_state() == 'playing' and playlist.length() >= 1:
            rmtrack = playlist.get_track_nbr(0).ptid

        id = playlist.add_tracks(tracks, 1)
        self.play_track(playlist.id, id)

        if rmtrack != None:
            playlist.remove_playlist_tracks_id(rmtrack)

        self.needs_push_update = True
        request.finish()

    def API_removeTrack(self, track_id, request):
        track_id = int(track_id)

        # For now if we are trying to remove the existing playing track. Do nothing.
        if (track_id == self.active_playlist_id):
            logging.warning("Not allowed to remove playing track")
            request.finish(error = 3)

        playlist = Playlist.get(self.tmpqueue_id)
        playlist.remove_playlist_tracks_id(track_id)
        self.needs_push_update = True
        self.vote_version += 1
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_removeTracks(self, track_ids, request):
        for track_id in track_ids.split(','):
            # don't crash on trailing comma
            if track_id != '':
                track_id = int(track_id)

                # For now if we are trying to remove the existing playing track. Do nothing.
                if (track_id == self.active_playlist_id):
                    logging.warning("Not allowed to remove playing track")
                    continue

                playlist = Playlist.get(self.tmpqueue_id)
                playlist.remove_playlist_tracks_id(track_id)
                self.needs_push_update = True
        self.vote_version += 1
        request.push({'vote_version': self.vote_version})
        request.finish()

    def API_seek(self, mseconds, request):
        if self.src == None:
            request.finish(0)
        ns = int(mseconds) * 1000000
        logging.debug("Seek with time to ns=%d" %ns)
        self.pipeline.seek_simple (gst.FORMAT_TIME, gst.SEEK_FLAG_FLUSH, ns)
        request.push({'duration': self.fetch_active_track().duration})
        request.finish()

    def API_setVolume(self, level, request):
        level = float(level)
        if (level > 1.0 or level < 0.0):
            raise DogError, 'Volume must be between 0.0 and 1.0'
        self.dogvibes.speakers[0].set_volume(level)
        request.push({'volume': self.dogvibes.speakers[0].get_volume()})
        request.finish()

    def API_stop(self, request):
        self.set_state(gst.STATE_NULL)
        request.push({'state': 'stopped'})
        request.finish()

    def API_getActivity(self, limit, request):
        request.finish(User.get_activity(int(limit)))

    def API_getUserInfo(self, request):
        user = User.find_by_or_create_from_username(request.user, request.avatar_url)
        request.finish(user.serialize())
