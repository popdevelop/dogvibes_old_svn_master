import unittest
import optparse
import simplejson
import time
import urllib
import searchresults
import random

#change the following setup for testing
#*********************************
#dogvibes user
user = "gyllen"
#*********************************

#valid track information
valid_uris = [{'album': 'Stop The Clocks', 'votes': '0', 'voters': [], 'title': 'Wonderwall', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2CT3r93YuSHtm57mjxvjhH', 'album_uri': 'spotify://spotify:album:1f4I0SpE0O8yg4Eg2ywwv1', 'duration': 258613, 'id': '1'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': "Don't Look Back In Anger", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:7H0jlAh4VoUtdeBUurXae9', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 287827, 'id': '2'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Wonderwall (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:18VX67SULc7JttH3OCJhoe', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 252600, 'id': '3'}, {'album': 'Familiar To Millions', 'votes': '0', 'voters': [], 'title': "Don't Look Back In Anger", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:7DyaMtpjSalQDyfBhetmeb', 'album_uri': 'spotify://spotify:album:4igsdVB30QyztMvUhiDYdE', 'duration': 327600, 'id': '4'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Wonderwall', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5bj4hb0QYTs44PDiwbI5CS', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 258906, 'id': '5'}, {'album': 'Heathen Chemistry', 'votes': '0', 'voters': [], 'title': 'Stop Crying Your Heart Out', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:3Od1CcijhWjHvrWubZcTKy', 'album_uri': 'spotify://spotify:album:7iSuRVjwGRSND33oGK1DWr', 'duration': 303133, 'id': '6'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Champagne Supernova', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2o9F2fDAzOukxPJd3E7KPg', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 450373, 'id': '7'}, {'album': 'Be Here Now', 'votes': '0', 'voters': [], 'title': 'Stand By Me', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:0C0N5NC7eLj0bjuvyoxV0v', 'album_uri': 'spotify://spotify:album:1GhXE04xrZS3CUOIO6MX4r', 'duration': 356627, 'id': '8'}, {'album': 'Oasis', 'votes': '0', 'voters': [], 'title': 'Oasis', 'artist': 'Soundscapes - Relaxing Music', 'uri': 'spotify://spotify:track:2OBKFZCMYmA2uMfDYNBIds', 'album_uri': 'spotify://spotify:album:2Cthj8vgO3jfxf8jPTm4nI', 'duration': 389227, 'id': '9'}, {'album': 'Definitely Maybe', 'votes': '0', 'voters': [], 'title': 'Live Forever', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:6etTGUYDxGHcqHYI4xBr1w', 'album_uri': 'spotify://spotify:album:4wXjHwpYza7sCw1vKKSfOm', 'duration': 276867, 'id': '10'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Some Might Say', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2j4l3NjUbc7Rn5QyiOPHEf', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 328533, 'id': '11'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Morning Glory', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:1JbZfGJvTwB8gL2lvNwy74', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 303533, 'id': '12'}, {'album': 'Familiar To Millions', 'votes': '0', 'voters': [], 'title': 'Champagne Supernova', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:23jVJY4xZEBCJjbqjjxZ3q', 'album_uri': 'spotify://spotify:album:4igsdVB30QyztMvUhiDYdE', 'duration': 392067, 'id': '13'}, {'album': "Bella's Lullaby: Sentimental Piano Music", 'votes': '0', 'voters': [], 'title': 'Relaxing Oasis', 'artist': 'Michael Silverman', 'uri': 'spotify://spotify:track:673LSyfLrz6fyYsOYDPmNY', 'album_uri': 'spotify://spotify:album:3OeNb61nRXUnMyoTDI2aRG', 'duration': 141307, 'id': '14'}, {'album': 'Heathen Chemistry', 'votes': '0', 'voters': [], 'title': 'Little By Little', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2eRaVQyrYYVDoreahhjdeu', 'album_uri': 'spotify://spotify:album:7iSuRVjwGRSND33oGK1DWr', 'duration': 292867, 'id': '15'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Champagne Supernova (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:2C9dkOD7JndaNenSihfHjG', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 300680, 'id': '16'}, {'album': 'Wibbling Rivalry', 'votes': '0', 'voters': [], 'title': "Noel's Track", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5MR2GAKVGpd6BS1HUIBesn', 'album_uri': 'spotify://spotify:album:7grONM99Dy9bjNFpOGdg10', 'duration': 425343, 'id': '17'}, {'album': 'Definitely Maybe', 'votes': '0', 'voters': [], 'title': 'Supersonic', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:0t2TNeixujbaKqEeMSXaLu', 'album_uri': 'spotify://spotify:album:4wXjHwpYza7sCw1vKKSfOm', 'duration': 283707, 'id': '18'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Stand By Me (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:0BJYM0K7daKdA4orsSA5bB', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 287747, 'id': '19'}, {'album': 'Who Killed Amanda Palmer', 'votes': '0', 'voters': [], 'title': 'Oasis', 'artist': 'Amanda Palmer', 'uri': 'spotify://spotify:track:2hbyKayBajgNfANABSVwYy', 'album_uri': 'spotify://spotify:album:55MoQXHYxkNlD5lxZOjoeG', 'duration': 126933, 'id': '20'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': "She's Electric", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2P17rrqMxe014BjoUjsjpL', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 220533, 'id': '21'}, {'album': 'The Masterplan', 'votes': '0', 'voters': [], 'title': 'The Masterplan', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2U251IRExvlUvri5awaJEz', 'album_uri': 'spotify://spotify:album:44CgYD439MapEZryBlTJxD', 'duration': 322507, 'id': '22'}, {'album': 'Essential Bands', 'votes': '0', 'voters': [], 'title': 'The Importance Of Being Idle', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5wo4UpIU17W5knrznFyYqu', 'album_uri': 'spotify://spotify:album:2ravCeM1o3ZoDZkMbRA2Df', 'duration': 221200, 'id': '23'}, {'album': 'Be Here Now', 'votes': '0', 'voters': [], 'title': "Don't Go Away", 'artist': 'Oasis', 'uri': 'spotify://spotify:track:2ERjXtXdYW2ezoJSFSKZwp', 'album_uri': 'spotify://spotify:album:1GhXE04xrZS3CUOIO6MX4r', 'duration': 288640, 'id': '24'}, {'album': 'A Tribute To Oasis', 'votes': '0', 'voters': [], 'title': 'Live Forever (Cover Version)', 'artist': 'Various Artists - Oasis Tribute', 'uri': 'spotify://spotify:track:5LRw05NYgex2DPuK79Q8tH', 'album_uri': 'spotify://spotify:album:4zPmkx8ivb4VkMkUtYVCqG', 'duration': 272080, 'id': '25'}, {'album': "(What's The Story) Morning Glory", 'votes': '0', 'voters': [], 'title': 'Cast No Shadow', 'artist': 'Oasis', 'uri': 'spotify://spotify:track:5zwyQT5gJ0VX5zJoFMDLt7', 'album_uri': 'spotify://spotify:album:1FB977nQEiAr8jel6O2Zn3', 'duration': 291600, 'id': '26'}]

def amp(call, errorcode=0):
    call = "http://dogvib.es/%s/amp/0/%s" % (user, call)

    print "calling: %s" % call

    ret = simplejson.load(urllib.urlopen(call))
    if ret['error'] != errorcode and errorcode != -1:
        raise Exception()

    # return result if there is one
    try:
        r = ret['result']
        return r
    except:
        return None

def dogvibes(call, errorcode=0):
    call = "http://dogvib.es/%s/dogvibes/%s" % (user, call)

    print "calling: %s" % call

    ret = simplejson.load(urllib.urlopen(call))
    if ret['error'] != errorcode and errorcode != -1:
        raise Exception()

    # return result if there is one
    try:
        r = ret['result']
        return r
    except:
        return None

# Tests
class testTheDog(unittest.TestCase):
    def setUp(self):
        amp("stop")
        dogvibes("cleanDatabase")

class testCornerCases(testTheDog):
    def test_playing_with_no_tracks(self):
        amp("play")
        amp("play")
        amp("stop")
        amp("pause")
        amp("play")
        amp("stop")
        amp("pause")

class testQueue(testTheDog):
    def test_normal_use(self):
        for i in range(0,5):
            amp("queue?uri=%s" % valid_uris[i]['uri'])

        res = amp("getAllTracksInQueue")

        i = 0
        for r in res:
            self.assertTrue(r['uri'] == valid_uris[i]['uri'], "queue does not work")
            i = i + 1

    def test_queue_and_play(self):
        amp("queueAndPlay?uri=%s" % valid_uris[0]['uri'])
        time.sleep(5)
        amp("pause")
        amp("stop")

    def test_skipping(self):    
        for i in range(0,3):
            amp("queue?uri=%s" % valid_uris[i]['uri'])

        amp("play")

        for i in range(0,3):
            res = amp("getStatus")
            amp("seek?mseconds=%d" % (int(res['duration'] - 5000)))
            time.sleep(10)

        time.sleep(5)
        amp("getStatus")
        time.sleep(2)
        amp("getStatus")
        amp("queue?uri=%s" % valid_uris[0]['uri'])
        amp("play")
        time.sleep(3)
        amp("pause")

class testPlaylist(testTheDog):
    pid = None

    def setUp(self):
        testTheDog.setUp(self)
        # test creating and removing playlist
        dogvibes("createPlaylist?name=%s" % "testlist")

        # add five songs to playlist
        self.pid = dogvibes("getAllPlaylists")[0]['id']
        for i in range(0,5):
            dogvibes("addTracksToPlaylist?playlist_id=%s&uri=%s" % (self.pid, valid_uris[i]['uri']))

    def test_moving(self):
        res = dogvibes("getAllTracksInPlaylist?playlist_id=%s" % self.pid)

        # check consistency
        i = 0
        for r in res:
            self.assertTrue(r['title'] == valid_uris[i]['title'], "inconsistency in playlist")
            i = i + 1
        
        dogvibes("moveTrackInPlaylist?playlist_id=%s&track_id=%s&position=%s" % (self.pid, res[4]['id'], 1))
        res = dogvibes("getAllTracksInPlaylist?playlist_id=%s" % self.pid)
        # check if move was successfull
        self.assertTrue(res[0]['uri'] == valid_uris[4]['uri'], "move was unsuccessfull")

        dogvibes("moveTrackInPlaylist?playlist_id=%s&track_id=%s&position=%s" % (self.pid, res[3]['id'], 3))
        res = dogvibes("getAllTracksInPlaylist?playlist_id=%s" % self.pid)
        # check if move was successfull
        self.assertTrue(res[2]['uri'] == valid_uris[2]['uri'], "move was unsuccessfull")
        
    def test_addingremoving(self):
        ret = dogvibes("getAllPlaylists")
        dogvibes("removePlaylist?id=%s" % ret[0]['id'])
        # create new playlist with same name
        dogvibes("createPlaylist?name=%s" % "testlist")

    def test_skipping(self):
        amp("playTrack?playlist_id=%s&nbr=1" % self.pid)
        amp("nextTrack")
        time.sleep(1)
        amp("nextTrack")
        time.sleep(1)
        amp("nextTrack")
        time.sleep(1)
        amp("nextTrack")
        time.sleep(1)
        amp("nextTrack")
        time.sleep(1)
        amp("nextTrack")
        amp("pause")
        # do play
        amp("play")
        time.sleep(2)
        amp("stop")
        amp("previousTrack")
        time.sleep(1)
        amp("previousTrack")
        time.sleep(1)
        amp("previousTrack")
        time.sleep(1)
        amp("previousTrack")
        time.sleep(1)
        amp("previousTrack")
        time.sleep(1)
        amp("previousTrack")
        time.sleep(1)
        amp("stop")
   
class testVoting(testTheDog):
    def setUp(self):
        testTheDog.setUp(self)
        # add five votes for anonymous
        for i in range(0,5):
            amp("addVote?uri=%s" % valid_uris[i]['uri'])

    def check_list_order(self):
        lastvote = 100

        list = amp("getAllTracksInQueue")
        # skip first entry sice we never change position for that
        for l in list[1:len(list)]:
            self.assertTrue(lastvote >= int(l['votes']), "list not correctly ordered lastvote:%s votes:%s" % (lastvote, l['votes']))
            lastvote = int(l['votes'])

    def test_vote_count(self):
        # check integrety
        res = amp("getUserInfo")
        self.assertTrue(res['votes'] == 0, "Incorrect vote count") 

        # add five more votes
        for i in range(0,5):
            amp("addVote?uri=%s" % valid_uris[7]['uri'])

        # remove five wrong votes
        for i in range(0,5):
            amp("removeVote?uri=%s" % valid_uris[7]['uri'])
       
        # check integrety
        res = amp("getUserInfo")
        self.assertTrue(res['votes'] == 0, "Incorrect vote count") 

        # remove five correct votes
        for i in range(0,5):
            amp("removeVote?uri=%s" % valid_uris[i]['uri'])
        
        # check integrety
        res = amp("getUserInfo")
        self.assertTrue(res['votes'] == 5, "not all votes given back correctly")

    def test_voting_numbers(self):
        # add one vote for gyllen      
        amp("addVote?uri=%s&user=gyllen" % valid_uris[0]['uri'])
        res = amp("getUserInfo?user=gyllen")

        amp("play")

        # check integrity
        self.assertTrue(res['votes'] == 4, "Incorrect vote count")
        amp("addVote?uri=%s&user=gyllen" % valid_uris[4]['uri'])

        list = amp("getAllTracksInQueue")
        self.assertTrue(list[1]['uri'] == valid_uris[4]['uri'], "Inconsistency on moving tracks with voting")
        res = amp("getUserInfo?user=gyllen")
        # check integrity
        self.assertTrue(res['votes'] == 3, "Incorrect vote count user has %s votes" % res['votes']) 
        self.check_list_order()
        amp("nextTrack")
        res = amp("getUserInfo?user=gyllen")
        # check integrity
        self.assertTrue(res['votes'] == 4, "Incorrect vote count user has %s votes" % res['votes']) 

        amp("pause")

    def test_voting_sorting1(self):
        # add five votes for gyllen
        for i in range(0,5):
            amp("addVote?uri=%s&user=gyllen" % valid_uris[i]['uri'])
        
        self.check_list_order()

        # add five votes for arne
        amp("addVote?uri=%s&user=arne" % valid_uris[3]['uri'])

        self.check_list_order()

        amp("addVote?uri=%s&user=arne" % valid_uris[4]['uri'])

        self.check_list_order()

        amp("addVote?uri=%s&user=arne" % valid_uris[5]['uri'])

        self.check_list_order()

        amp("addVote?uri=%s&user=arne" % valid_uris[6]['uri'])

        self.check_list_order()

        amp("addVote?uri=%s&user=arne" % valid_uris[7]['uri'])

        self.check_list_order()
    
        # remove one vote from gyllen
        amp("removeVote?uri=%s&user=gyllen" % valid_uris[3]['uri'])

        self.check_list_order()

        # remove one vote from arne
        amp("removeVote?uri=%s&user=arne" % valid_uris[6]['uri'])

        self.check_list_order()

        # add one vote from sven
        amp("addVote?uri=%s&user=sven" % valid_uris[3]['uri'])

        self.check_list_order()

        amp("play")
        amp("nextTrack")
        amp("nextTrack")
        amp("stop")

        # remove one vote from arne
        amp("removeVote?uri=%s&user=arne" % valid_uris[7]['uri'])

        self.check_list_order()

        # add one vote from sven
        amp("addVote?uri=%s&user=sven" % valid_uris[3]['uri'])

        self.check_list_order()

        amp("addVote?uri=%s&user=sven" % valid_uris[2]['uri'])

        self.check_list_order()

        amp("addVote?uri=%s&user=sven" % valid_uris[1]['uri'])

        self.check_list_order()

        amp("removeVote?uri=%s&user=sven" % valid_uris[2]['uri'])

        self.check_list_order()

        amp("addVote?uri=%s&user=sven" % valid_uris[2]['uri'])

        self.check_list_order()

        amp("removeVote?uri=%s&user=sven" % valid_uris[2]['uri'])

        self.check_list_order()

        # add five votes for pelle
        for i in range(6,11):
            amp("addVote?uri=%s&user=sven" % valid_uris[i]['uri'])

        self.check_list_order()

    def test_voting_random(self):
        fake_users = ["gyllen", "brissmyr", "jimtegel", "tilljoel", "cirkkajoel", "nisse", "pelle", "kalle", "david", "sven", "arne", "kallekanin", "kalleduva", "dennis", "katt", "hatt", "bip", "bap", "tap", "zap", "zup"]
        amp("addVote?user=%s&uri=%s" % ("gyllen", valid_uris[7]['uri']))
        amp("play")

        time.sleep(5)

        for i in range(0, 100):
            remadd = random.randint(0, 30)
            ruser = fake_users[random.randint(0, len(fake_users) - 1)]
            ruri = valid_uris[random.randint(0, len(valid_uris) - 1)]['uri']
            if remadd < 22:
                amp("addVote?user=%s&uri=%s" % (ruser, ruri), -1)
            elif remadd < 28:
                amp("removeVote?user=%s&uri=%s" % (ruser, ruri), -1)
            else:
                res = amp("getStatus")
                amp("seek?mseconds=%d" % (int(res['duration'] - 5000)), -1)

            self.check_list_order()

#    def test_voting_sorting2(self):
#        # add five votes for gyllen
#        for i in range(0,5):
#            amp("addVote?uri=%s&user=gyllen" % valid_uris[i]['uri'])
#
#        # add five votes for sven
#        for i in range(0,5):
#            amp("addVote?uri=%s&user=sven" % valid_uris[i]['uri'])
#
#        for i in range(0,5):
#            self.assertTrue(list[i]['uri'] == valid_uris[i]['uri'], "Inconsistency on moving tracks with voting")
#
#        # remove two votes form gyllen
#        amp("removeVote?uri=%s&user=gyllen" % valid_uris[0]['uri'])
#        amp("removeVote?uri=%s&user=gyllen" % valid_uris[1]['uri'])
#
#        amp("addVote?uri=%s&user=gyllen" % valid_uris[0]['uri'])
#
#        # check consistency
#        for i in range(0,5):
#            self.assertTrue(list[i]['uri'] == valid_uris[i]['uri'], "Inconsistency on moving tracks with voting")

class testSearching(testTheDog):
    def test_searching(self):
        res = dogvibes("search?query=kotte")
        self.assertTrue(res == searchresults.kotte, "search for kotte failed")

        res = dogvibes("search?query=kalle%20kanin")
        self.assertTrue(res == searchresults.kalle_kanin, "search for 'kalle kanin' failed")

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(testCornerCases)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(testQueue)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(testPlaylist)
    unittest.TextTestRunner(verbosity=2).run(suite)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(testVoting)
    unittest.TextTestRunner(verbosity=2).run(suite)

    suite = unittest.TestLoader().loadTestsFromTestCase(testSearching)
    unittest.TextTestRunner(verbosity=2).run(suite)
