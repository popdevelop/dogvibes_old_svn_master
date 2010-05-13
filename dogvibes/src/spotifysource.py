import gst
import urlparse, urllib
import xml.etree.ElementTree as ET
from track import Track

class SpotifySource:

    def __init__(self, name, user, passw):
        self.name = name
        self.passw = passw
        self.user = user
        self.created = False
        self.amp = None

        #spotifydogvibes.login(user, passw);

    @classmethod
    def strip_protocol(self, uri):
        uri = uri.split("://")
        if len(uri) != 2:
            return None
        return uri[1]

    def create_track_from_uri(self, uri):
        uri = SpotifySource.strip_protocol(uri)
        url = "http://ws.spotify.com/lookup/1/?uri=" + uri

        try:
            e = ET.parse(urllib.urlopen(url))
        except Exception as e:
            return None

        ns = "http://www.spotify.com/ns/music/1"

        if 'album' in uri:
            title = ""
            artist = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
            album = e.find('.//{%s}name' % ns).text
            duration = 0
            album_uri = uri
        else:
            title = e.find('.//{%s}name' % ns).text
            artist = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
            album = e.find('.//{%s}album/{%s}name' % (ns, ns)).text
            duration = int(float(e.find('.//{%s}length' % ns).text) * 1000)
            album_uri = "spotify://" + e.find('.//{%s}album' % ns).attrib['href']

        track = Track("spotify://"+uri)
        track.title = title
        track.artist = artist
        track.album = album
        track.album_uri = album_uri
        track.duration = duration

        return track

    def create_playlists(self, spot_user, spot_pass):
        pass
        # Use this when connection to spotify works

        # spotifydogvibes.login(spot_user, spot_pass)
        #pl = spotifydogvibes.get_playlists()
        #for l in pl:
        #    print l
        #    songs = spotifydogvibes.get_songs(l["index"])
        #    print "found " + str(len(songs)) + " songs in playlist " + str(l["index"])
        # -- spam --
        #for s in songs:
            #print s
        #spotifydogvibes.logout()


    def get_src(self):
        if self.created == False:
            self.bin = gst.Bin(self.name)
            self.spotify = gst.element_factory_make("spot", "spot")
            self.spotify.set_property ("user", self.user);
            self.spotify.set_property ("pass", self.passw);
            self.spotify.set_property ("buffer-time", 10000000);
            self.bin.add(self.spotify)
            gpad = gst.GhostPad("src", self.spotify.get_static_pad("src"))
            self.bin.add_pad(gpad)
            self.created = True
            # Connect playtoken lost signal
            self.spotify.connect('play-token-lost', self.play_token_lost)
        return self.bin

    def search(self, query):
        tracks = []

        query = urllib.quote(urllib.unquote(query).encode('utf8'),'=&?/')

        url = u"http://ws.spotify.com/search/1/track?q=%s" % query

        try:
            u = urllib.urlopen(url)
            tree = ET.parse(u)
        except:
            return []

        ns = "http://www.spotify.com/ns/music/1"

        for e in tree.findall('.//{%s}track' % ns):
            track = {}
            track['title'] = e.find('.//{%s}name' % ns).text
            track['artist'] = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
            track['album'] = e.find('.//{%s}album/{%s}name' % (ns, ns)).text
            track['album_uri'] = "spotify://" + tree.find('.//{%s}album' % ns).attrib['href']
            track['duration'] = int(float(e.find('.//{%s}length' % ns).text) * 1000)
            track['uri'] = "spotify://" + e.items()[0][1]
            track['popularity'] = e.find('.//{%s}popularity' % ns).text
            territories = e.find('.//{%s}album/{%s}availability/{%s}territories' % (ns, ns, ns)).text
            if 'SE' in territories or territories == 'worldwide':
                tracks.append(track)

        return tracks

    def get_albums(self, query):
        #artist_uri = SpotifySource.strip_protocol(artist_uri)

        ns = "http://www.spotify.com/ns/music/1"

        query = urllib.quote(urllib.unquote(query).encode('utf8'),'=&?/')
        url = u"http://ws.spotify.com/search/1/artist?q=%s" % query

        try:
            u = urllib.urlopen(url)
            tree = ET.parse(u)
        except:
            return []

        artist_uri = tree.find('.//{%s}artist' % ns)
        if artist_uri == None:
            print "ERROR: Empty fetch from %s" % url
            return []

        artist_uri = artist_uri.attrib['href']

        url = u"http://ws.spotify.com/lookup/1/?uri=%s&extras=albumdetail" % artist_uri

        try:
            u = urllib.urlopen(url)
            tree = ET.parse(u)
        except:
            return []

        albums = []

        for e in tree.findall('.//{%s}album' % ns):
            album = {}
            album['uri'] = 'spotify://' + e.attrib['href']
            album['name'] = e.find('.//{%s}name' % ns).text
            album['artist'] = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
            album['released'] = e.find('.//{%s}released' % ns).text
            territories = e.find('.//{%s}availability/{%s}territories' % (ns, ns)).text
            if territories != None and ('SE' in territories or territories == 'worldwide'):
                albums.append(album)

        return albums

    def get_album(self, album_uri):
        album_uri = SpotifySource.strip_protocol(album_uri)

        url = "http://ws.spotify.com/lookup/1/?uri=%s&extras=trackdetail" % album_uri

        try:
            u = urllib.urlopen(url)
            tree = ET.parse(u)
        except:
            return None

        ns = "http://www.spotify.com/ns/music/1"

        root = ET.XML(urllib.urlopen(url).read())

        album = {}
        tracks = []

        album['name'] = tree.find('.//{%s}name' % ns).text
        album['released'] = tree.find('.//{%s}released' % ns).text
        album['uri'] = album_uri

        territories = tree.find('.//{%s}availability/{%s}territories' % (ns, ns)).text
        if 'SE' not in territories and territories != 'worldwide':
            return None

        for e in tree.findall('.//{%s}track' % ns):
            track = {}
            track['title'] = e.find('.//{%s}name' % ns).text
            track['track-number'] = e.find('.//{%s}track-number' % ns).text
            track['disc-number'] = e.find('.//{%s}disc-number' % ns).text
            track['duration'] = int(float(e.find('.//{%s}length' % ns).text) * 1000)
            track['artist'] = e.find('.//{%s}artist/{%s}name' % (ns, ns)).text
            track['duration'] = int(float(e.find('.//{%s}length' % ns).text) * 1000)
            track['uri'] = "spotify://" + e.items()[0][1]
            track['popularity'] = e.find('.//{%s}popularity' % ns).text
            tracks.append(track)

        album['tracks'] = tracks
        return album

    def list(self, type):
        return[]

    def set_track(self, track):
        self.spotify.set_property ("uri", track.uri)

    def uri_matches(self, uri):
        return (uri[0:10] == "spotify://")

    def play_token_lost(self, data):
        # Pause connected amp if play_token_lost is recieved
        if self.amp != None:
            self.amp.API_pause()

if __name__ == '__main__':
    src = SpotifySource(None, None, None)
#    print src.get_albums("Kent")
    print src.get_album("spotify://spotify:album:6G9fHYDCoyEErUkHrFYfs4")
