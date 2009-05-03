using Gst;

public class DeviceSpeaker : GLib.Object, Speaker {
  private Element devicesink;
  private Element queue2;

  construct {
  }

  public Bin get_speaker () {
    Bin bin = new Bin("alsabin");
    this.devicesink = ElementFactory.make ("alsasink", "alsasink");
    this.queue2 = ElementFactory.make ("queue2", "queue2");
    this.devicesink.set ("sync", false);
    stdout.printf ("Creating device sink\n");
    bin.add_many (this.queue2, this.devicesink);
    this.queue2.link (this.devicesink);
    GhostPad gpad = new GhostPad ("sink", this.queue2.get_static_pad("sink"));
    bin.add_pad (gpad);
    return bin;
  }
}