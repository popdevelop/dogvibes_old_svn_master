from track import Track
import logging
import gdata.youtube
import gdata.youtube.service
import re

def PrintVideoFeed(feed):
    for entry in feed.entry:
         PrintEntryDetails(entry)

def PrintEntryDetails(entry):
    print 'Video title: %s' % entry.media.title.text
    print 'Video published on: %s ' % entry.published.text
    print 'Video description: %s' % entry.media.description.text
    print 'Video category: %s' % entry.media.category[0].text
    print 'Video tags: %s' % entry.media.keywords.text
    print 'Video watch page: %s' % entry.media.player.url
    print 'Video flash player URL: %s' % entry.GetSwfUrl()
    print 'Video duration: %s' % entry.media.duration.seconds

    print 'Video view count: %s' % entry.statistics.view_count

    # show alternate formats
    for alternate_format in entry.media.content:
        if 'isDefault' not in alternate_format.extension_attributes:
            print 'Alternate format: %s | url: %s ' % (alternate_format.type,
                                                 alternate_format.url)

    # show thumbnails
    for thumbnail in entry.media.thumbnail:
        print 'Thumbnail url: %s' % thumbnail.url              


class YoutubeSource:

    def __init__(self, name):
        self.name = name
        self.amp = None
        self.search_prefix = "youtube"

    def create_track_from_uri(self, uri):
        if 'youtube' not in uri:
            return None
        p = re.compile('http://www.youtube.com/v/(.*)\?.*$')
        m = p.match(uri)

        client = gdata.youtube.service.YouTubeService()
        client.ssl = False

        entry = client.GetYouTubeVideoEntry(video_id=m.group(1))
        logging.debug("Created track from uri %s in youtubesource", uri)

        track = Track(entry.media.title.text)
        track.artist = "YOUTUBE VIDEO"
        track.album = entry.media.category[0].text
        track.album_uri = None
        track.duration = int(entry.media.duration.seconds)*1000

        return track     

    def create_tracks_from_uri(self, uri):
        if 'youtube' not in uri:
            return None
        else:
            return [self.create_track_from_uri(uri)]

    def get_albums(self, query):
        return []

    def get_album(self, query):
        return None

    def search(self, q):
        client = gdata.youtube.service.YouTubeService()
        client.ssl = False
        
        query = gdata.youtube.service.YouTubeVideoQuery()
        query.vq = q
        query.orderby = 'viewCount'
        #FIXME first 5 and then spotify or interleave?
        query.max_results = '5'

        feed = client.YouTubeQuery(query)

        #PrintVideoFeed(feed)

        #instead of flash, use rtsp, these should work
        #for alternate_format in entry.media.content:
        #    if 'isDefault' not in alternate_format.extension_attributes:
        #        print 'Alternate format: %s | url: %s ' % (alternate_format.type,
        #                                             alternate_format.url)

        #FIXME use for albumart?
        #for thumbnail in entry.media.thumbnail:
        #print 'Thumbnail url: %s' % thumbnail.url              

        tracks = []
        for entry in feed.entry:
            track = {}
            track['title'] = entry.media.title.text
            track['artist'] = "YOUTUBE VIDEO"
            track['album'] = entry.media.category[0].text
            track['album_uri'] = None
            track['duration'] = int(entry.media.duration.seconds)*1000
            track['uri'] = entry.GetSwfUrl()
            track['popularity'] = "0"
            tracks.append(track)
        return tracks

    def uri_matches(self, uri):
        return False

    def list(self, type):
        return[]
