using Gst;

public class SpotifyInput : GLib.Object, Input {
  public string user;
  public string pass;
  private Element spotify;


  construct {
    try {
      var gc = GConf.Client.get_default ();
      user = gc.get_string ("/apps/dogvibes/spotify/username");
      pass = gc.get_string ("/apps/dogvibes/spotify/password");
      stdout.printf ("Creating spotify input with %s %s\n", user, pass);
    } catch (GLib.Error e) {
      stderr.printf ("Oops: %s\n", e.message);
    }
    this.user = user;
    this.pass = pass;
  }

  private void runsearch () {
  }

  public Bin get_src (string key) {
    Bin bin = new Bin("spotifybin");
    this.spotify = ElementFactory.make ("spotify", "spotify");
    stdout.printf ("Logging on: playing %s\n", key);
    spotify.set ("user", user);
    spotify.set ("pass", pass);
    spotify.set ("buffer-time", (int64) 10000000);
    spotify.set ("uri", key);
    bin.add (this.spotify);
    GhostPad gpad = new GhostPad ("src", this.spotify.get_static_pad("src"));
    bin.add_pad (gpad);
    return bin;
  }

  public string[] search (string searchstring) {
	string[] test = {};

	try {
	  string[] argus = {"search", user, pass, searchstring};
	  string[] envps = {"LD_LIBRARY_PATH=/home/gyllen/X11bin/lib/"};
	  string uris;
	  GLib.Process.spawn_sync (".", argus, envps, 0, runsearch, out uris);
	  test = uris.split ("\n");
	  stdout.printf ("%s\n", uris);
	} catch (GLib.Error e) {
	  stdout.printf ("ERROR SO INTERNAL: %s\n", e.message);
	}

	stdout.printf ("I did a search on %s\n", searchstring);

	return test;
  }
}