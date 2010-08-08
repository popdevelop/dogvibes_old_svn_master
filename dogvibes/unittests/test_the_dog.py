import unittest
import optparse
import simplejson
import time
import urllib

#change the following setup for testing
#*********************************
#dogvibes user
user = "gyllen"
#*********************************

#valid uris to use for test
valid_uris = [
"spotify://spotify:track:2CT3r93YuSHtm57mjxvjhH",
"spotify://spotify:track:7H0jlAh4VoUtdeBUurXae9",
"spotify://spotify:track:18VX67SULc7JttH3OCJhoe",
#"spotify://spotify:track:7DyaMtpjSalQDyfBhetmeb",
#"spotify://spotify:track:5bj4hb0QYTs44PDiwbI5CS",
#"spotify://spotify:track:3Od1CcijhWjHvrWubZcTKy",
#"spotify://spotify:track:2o9F2fDAzOukxPJd3E7KPg",
#"spotify://spotify:track:0C0N5NC7eLj0bjuvyoxV0v",
#"spotify://spotify:track:2OBKFZCMYmA2uMfDYNBIds",
#"spotify://spotify:track:6etTGUYDxGHcqHYI4xBr1w",
#"spotify://spotify:track:2j4l3NjUbc7Rn5QyiOPHEf",
#"spotify://spotify:track:1JbZfGJvTwB8gL2lvNwy74",
#"spotify://spotify:track:23jVJY4xZEBCJjbqjjxZ3q",
#"spotify://spotify:track:673LSyfLrz6fyYsOYDPmNY",
#"spotify://spotify:track:2eRaVQyrYYVDoreahhjdeu",
#"spotify://spotify:track:2C9dkOD7JndaNenSihfHjG",
#"spotify://spotify:track:5MR2GAKVGpd6BS1HUIBesn",
#"spotify://spotify:track:0t2TNeixujbaKqEeMSXaLu",
#"spotify://spotify:track:0BJYM0K7daKdA4orsSA5bB",
#"spotify://spotify:track:2hbyKayBajgNfANABSVwYy",
#"spotify://spotify:track:2P17rrqMxe014BjoUjsjpL",
#"spotify://spotify:track:2U251IRExvlUvri5awaJEz",
#"spotify://spotify:track:5wo4UpIU17W5knrznFyYqu",
#"spotify://spotify:track:2ERjXtXdYW2ezoJSFSKZwp",
#"spotify://spotify:track:5LRw05NYgex2DPuK79Q8tH",
#"spotify://spotify:track:5zwyQT5gJ0VX5zJoFMDLt7"
]

def amp(call):
    call = "http://dogvib.es/%s/amp/0/%s" % (user, call)

    print "calling: %s" % call

    ret = simplejson.load(urllib.urlopen(call))
    if ret['error'] != 0:
        raise Exception()

    return ret

def dogvibes(call):
    call = "http://dogvib.es/%s/dogvibes/%s" % (user, call)

    print "calling: %s" % call

    ret = simplejson.load(urllib.urlopen(call))
    if ret['error'] != 0:
        raise Exception()

    return ret

# Tests
class testTheDog(unittest.TestCase):
    def setUp(self):
        amp("stop")
        dogvibes("cleanDatabase")

class testQueue(testTheDog):
    def runTest(self):
        for uri in valid_uris:
            amp("queue?uri=%s" % (uri))

        res = amp("getAllTracksInQueue")

        i = 0
        for r in res['result']:
            self.assertTrue(r['uri'] == valid_uris[i], "queue does not work")
            i = i + 1

class testQueueAndPlay(testTheDog):
    def runTest(self):
        amp("queueAndPlay?uri=%s" % valid_uris[0])
        time.sleep(5)
        amp("pause")
        amp("stop")

if __name__ == "__main__":
   unittest.main()


   
