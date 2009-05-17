#!/usr/bin/env python
import hashlib
import gobject
import gst
import dbus
import dbus.service
import dbus.mainloop.glib
# import spources
from spotifysource import SpotifySource

# import speakers
from devicespeaker import DeviceSpeaker

# import track
from track import Track

class Dogvibes(dbus.service.Object):
    def __init__(self, bus, object_name):
        dbus.service.Object.__init__(self, bus, object_name)

        # Add all sources
        self.sources = [SpotifySource("spotify", "gyllen", "bobidob10")]

        # Add all spekers
        self.speakers = [DeviceSpeaker("devicesink")]

class Amplifier(dbus.service.Object):
    def __init__(self, bus, object_name):
        dbus.service.Object.__init__(self, bus, object_name)



class Amplifier(dbus.service.Object):
    def __init__(self, dogvibes, bus, object_name):
        self.dogvibes = dogvibes
        self.pipeline = gst.Pipeline ("amppipeline")

        # create volume element
        self.volume = gst.element_factory_make("volume", "volume")
        self.pipeline.add(self.volume)

        # create the tee element
        self.tee = gst.element_factory_make("tee", "tee")
        self.pipeline.add(self.tee)

        # link volume with tee
        self.volume.link(self.tee)

        # create the playqueue
        self.playqueue = []
        self.playqueue_position = 0

        self.src = None

        # spotify is special FIXME: not how its supposed to be
        self.spotify = self.dogvibes.sources[0].get_src ()


        dbus.service.Object.__init__(self, bus, object_name)

    # DBus API

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='i', out_signature='')
    def ConnectSpeaker(self, nbr):
        if nbr > len(self.dogvibes.speakers) - 1:
            print "Speaker does not exist"

        speaker = self.dogvibes.speakers[nbr];

        if (self.pipeline.get_by_name (speaker.name) == None):
            self.sink = self.dogvibes.speakers[nbr].get_speaker ();
            self.pipeline.add(self.sink)
            self.tee.link(self.sink)
        else:
            print "Speaker %d already connected" % nbr

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='i', out_signature='')
    def DisconnectSpeaker(self, nbr):
        if nbr > len(self.dogvibes.speakers) - 1:
            print "Speaker does not exist"

        speaker = self.dogvibes.speakers[nbr];

        if (self.pipeline.get_by_name (speaker.name) != None):
            (pending, state, timeout) = self.pipeline.get_state()
            self.pipeline.set_state(gst.STATE_NULL)
            rm = self.pipeline.get_by_name (speaker.name)
            self.pipeline.remove (rm)
            self.tee.unlink (rm)
            self.pipeline.set_state(state)
        else:
            print "Speaker not connected"


    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='', out_signature='aa{ss}')
    def GetAllTracksInQueue(self):
        ret = []
        for track in self.playqueue:
            ret.append(track.to_dict())
        return ret

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='', out_signature='i')
    def GetPlayedMilliSeconds(self):
        (pos, form) = self.pipeline.query_position(gst.FORMAT_TIME)
        return pos / gst.MSECOND

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='', out_signature='a{ss}')
    def GetStatus(self):
        if (len(self.playqueue) == 0):
            return {}
        return {"uri": self.playqueue[self.playqueue_position - 1].uri, "playqueuehash": self.GetHashFromPlayQueue()}

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='', out_signature='i')
    def GetQueuePosition(self):
        return self.playqueue_position

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='', out_signature='')
    def NextTrack(self):
        self.ChangeTrack(self.playqueue_position + 1)

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='i', out_signature='')
    def PlayTrack(self, tracknbr):
        self.ChangeTrack(tracknbr)
        self.Play()

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='', out_signature='')
    def PreviousTrack(self):
        self.ChangeTrack(self.playqueue_position - 1)

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='', out_signature='')
    def Play(self):
        self.PlayOnlyIfNull(self.playqueue[self.playqueue_position])


    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='', out_signature='')
    def Pause(self):
        self.pipeline.set_state(gst.STATE_PAUSED)


    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='s', out_signature='')
    def Queue(self, uri):
        print "Queued track:%s" % uri
        self.playqueue.append(Track(uri))

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='i', out_signature='')
    def RemoveFromQueue(self, nbr):
        if (nbr > len(self.playqueue)):
            print "Too big of a number for removing"
            return

        self.playqueue.remove(self.playqueue[nbr])

        if (nbr <= self.playqueue_position):
            self.playqueue_position = self.playqueue_position - 1

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='i', out_signature='')
    def Seek(self, mseconds):
        print "Implement me"
        # FIXME
        #    pipeline.seek_simple (Format.TIME, SeekFlags.NONE, ((int64) msecond) * MSECOND);
        # self.pipeline.seek_simple (Track(uri))


    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='d', out_signature='')
    def SetVolume(self, vol):
        if (vol > 2 or vol < 0):
            print "Volume must be between 0.0 and 2.0"
        self.volume.set_property("volume", vol)

    @dbus.service.method("com.Dogvibes.Amp",
                         in_signature='', out_signature='')
    def Stop(self):
        self.pipeline.set_state(gst.STATE_NULL)


    # Internal functions

    def ChangeTrack(self, tracknbr):
        if (tracknbr > len(self.playqueue) - 1):
            return

        if (tracknbr == self.playqueue_position):
            return

        if (tracknbr < 0):
            tracknbr = 0

        self.playqueue_position = tracknbr
        (pending, state, timeout) = self.pipeline.get_state()
        self.pipeline.set_state(gst.STATE_NULL)
        self.PlayOnlyIfNull(self.playqueue[self.playqueue_position])
        self.pipeline.set_state(state)

    def GetHashFromPlayQueue(self):
        ret = ""
        for track in self.playqueue:
            ret += track.uri
        print hashlib.md5(ret).hexdigest()

        return hashlib.md5(ret).hexdigest()

    def PlayOnlyIfNull(self, track):
        (pending, state, timeout) = self.pipeline.get_state ()
        if (state != gst.STATE_NULL):
            self.pipeline.set_state(gst.STATE_PLAYING)
            return

        if (self.src):
            self.pipeline.remove (self.src)
            if (self.spotify_in_use == False):
                print "removed a decodebin"
                self.pipeline.remove (self.decodebin)

        if track.uri[0:7] == "spotify":
            print "It was a spotify uri"
            self.src = self.spotify
            # FIXME ugly
            self.dogvibes.sources[0].set_track(track)
            self.pipeline.add(self.src)
            self.src.link(self.volume)
            self.spotify_in_use = True
        else:
            print "Decodebin is taking care of this uri"
            self.src = gst.element_make_from_uri(gst.URI_SRC, track.uri, "source")
            self.decodebin = gst.element_factory_make ("decodebin2", "decodebin2")
            self.decodebin.connect('new-decoded-pad', self.PadAdded)
            self.pipeline.add(self.src)
            self.pipeline.add(self.decodebin)
            self.src.link(self.decodebin)
            self.spotify_in_use = False

        self.pipeline.set_state(gst.STATE_PLAYING)

    def PadAdded(self, element, pad, last):
        print "Lets add a speaker we found suitable elements to decode"
        pad.link (self.volume.get_pad("sink"))

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    session_bus = dbus.SystemBus()
    name = dbus.service.BusName("com.Dogvibes", session_bus)

    # Create the dogvibes object
    dogvibes = Dogvibes(session_bus, '/com/dogvibes/dogvibes')

    # Create a single Amplifier
    amp0 = Amplifier(dogvibes, session_bus, '/com/dogvibes/amp/0')

    # FIXME this is added because we are lazy
    amp0.ConnectSpeaker(0)

    mainloop = gobject.MainLoop()
    print "Running Dogvibes."
    print "   ->Vibe the dog!"
    print "                 .--.    "
    print "                / \aa\_  "
    print "         ,      \_/ ,_Y) "
    print "        ((.------`\"=(    "
    print "         \   \      |o   "
    print "         /)  /__\  /     "
    print "        / \ \_  / /|     "
    print "        \_)\__) \_)_)    "
    mainloop.run()