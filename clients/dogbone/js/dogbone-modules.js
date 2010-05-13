/*
 * Modules for handling playlists, searches, etc...
 */

var Config = {
  defaultUser: "",
  defaultServer: "localhost:2000",
  defaultProtocol: "ws",
  resizeable: true,
  draggableOptions: {
    revert: 'invalid', 
    scroll: false,
    revertDuration: 100, 
    helper: 'clone', 
    cursorAt: { left: 5 },
    appendTo: "#drag-dummy", 
    zIndex: 1000,
    addClasses: false,
    start: function() { $(this).click(); }
  },
  sortableOptions: {
    revert: 100, 
    scroll: false, 
    helper: 'clone', 
    appendTo: "#drag-dummy", 
    zIndex: 1000,
    addClasses: false
  }  
};


/* TODO: remove when all dependencies are solved */
var UI = {
  titlebar: "#titlebar",
  navigation: "#navigation",
  trackinfo: "#trackinfo",
  currentsong: "#currentsong"
};

/* TODO: Find out a good way to handle titlebar */
var Titlebar = {
  set: function(text) {
    $(UI.titlebar).empty();
    $(UI.titlebar).append($("<li class='selected'>"+text+"</li>"));
  }
};

/**************************
 * Prototype extensions
 **************************/

/* remove a prefix from a string */
String.prototype.removePrefix = function(prefix) {
  if(this.indexOf(prefix) === 0) {
    return this.substr(prefix.length);
  }
  return false;
};

/* Create a function for converting msec to time string */
Number.prototype.msec2time = function() {
  var ts = Math.floor(this / 1000);
  if(!ts) { ts=0; }
  if(ts===0) { return "0:00"; }
  var m = Math.round(ts/60 - 0.5);
  var s = Math.round(ts - m*60);
  if (s<10 && s>=0){
    s="0" + s;
  }
  return m + ":" + s;
};

/******************
 * Helper classes
 ******************/
var ResultTable = function(config) {
  var self = this;
  /* Default configuration */
  this.options = {
    name: "Table",
    idTag: "id",
    highlightClass: "playing",
    sortable: false,
    click: function(e) {
      $(document).dblclick();
      var tbl = $(this).data('self');
      tbl.selectMulti = e.shiftKey ? true : false;
      var nbr = $(this).data('nbr');
      tbl.selectItem(nbr);
    },
    dblclick: $.noop,
    callbacks: {
      album: function(element) {
        var a = $('<a/>').attr('href', '#album/' + element.album_uri);
        element.contents().wrap(a);
      },      
      artist: function(element) {
        var a = $('<a/>').attr('href', '#artist/' + element.text());
        element.contents().wrap(a);
      }    
    }
  };
  
  /* Set user configuration */
  $.extend(true, this.options, config);
  
  this.ui = {
    content: "#" + self.options.name + "-content",
    items  : "#" + self.options.name + "-items"
  };  
  
  /* Some properties */
  this.items = [];
  this.data  = {};
  this.selectedItem = false;
  this.selectedItems = [];
  this.fields = [];
  this.selectMulti = false;
  
  /* Configure table fields by looking for table headers if not provided
   * in options */
  if(typeof(this.options.fields) == "undefined") {
    $(".template", self.ui.content).children().each(function(i, el) {
      if("id" in el) {
        var field = el.id.removePrefix(self.options.name + "-");
        if(field !== false) {
          self.fields.push(field);
        }
      }
    });
  } else {
    this.fields = this.options.fields;
  }

  if(self.options.sortable) {
    $(self.ui.content).tablesorter();
  }
  
  /***** Methods *****/
  this.display = function() {
    var self = this;
    self.selectedItems = [];
    /* Empty items */
    $(self.ui.items).empty();
    /* Fill with new items */
    $(self.items).each(function(i, el) {
      var tr = $("<tr></tr>");
      var id = self.options.idTag in el ? el[self.options.idTag] : i;
      /* Store some data */
      tr.data('id', id);
      tr.data('nbr', i);
      tr.data('self', self);
      tr.attr('id', self.options.name+"-item-nbr-"+i);
      /* always add uri */
      if("uri" in el) { tr.data('uri', el.uri); }
      $(self.fields).each(function(j, field) {
        var content = $("<td></td>");
        if(field in el) {
          var value = el[field];
          /* FIXME: assumption: Convert to time string if value is numeric */
          if(typeof(value) == "number") {
            value = value.msec2time();
            content.addClass("time");
          }
          content.append(value);
        }
        if(field in self.options.callbacks) {
          content.id = id;
          content.nbr = i;
          content.album_uri = el.album_uri;
          self.options.callbacks[field](content);
        }        
        tr.append(content);
      });
      tr.click(self.options.click);
      tr.dblclick(self.options.dblclick);
      $(self.ui.items).append(tr);
      /* Save rows internally */
      self.data[i] = tr;      
    });
    
    $("tr:visible",this.ui.items).filter(":odd").addClass("odd");
        
    /* Update tablesorter */
    $(self.ui.content).trigger("update");
  };
  
  this.empty = function() {
    $(this.ui.items).empty();
  };
  
  this.selectItem = function(index) {
    var self = this;
    index = parseInt(index, 10);
    if(!self.selectMulti) {
      self.deselectAll();
    }
    if(index > self.items.length) { return; }
    if(self.selectMulti===false || self.selectedItem===false) {
      self.selectedItem = index;
    }

    /* Create the selection range */
    var min = self.selectedItem < index ? self.selectedItem : index;
    var max = self.selectedItem < index ? index : self.selectedItem;
    self.selectedItems = [];
    for(var i = min; i <= max; i++) {
      self.selectedItems.push(i);
      self.data[i].addClass("selected");
    }
  };
  this.deselectAll = function() {
    this.selectedItem = false;
    this.selectedItems = [];
    $("tr", this.ui.items).removeClass("selected");
  };
  this.clearHighlight = function() {
    $("tr", this.ui.items).removeClass(this.options.highlightClass);  
  };
  this.highlightItem = function(index) {
    if(index in this.data) {
      this.data[index].addClass(this.options.highlightClass);
    }
  };
};


var NavList = {
  /* Store all sections globally */
  sections: Array(),
  /* Section object */  
  Section: function(container, type) {
    this.ul = $(container);
    this.ul.addClass(type);
    NavList.sections.push(this);
    this.items = Array();
    $(UI.navigation).append(this.ul);    
    this.addItem = function(id, item) {
      this.items[id] = $(item);
      this.ul.append(this.items[id]);
    };
    this.selectItem= function(id) {
      $(NavList.sections).each(function(i ,el) {
        el.deselect();
      });
      if(typeof(this.items) != "undefined" && id in this.items) {
        this.items[id].addClass('selected');
      }
    };
    this.deselect = function() {
      for(var i in this.items) {
        this.items[i].removeClass('selected');
      }
    };
    this.empty = function() {
      this.items = Array();
      this.ul.empty();
    };
  }
};


/**************************
 * Modules 
 **************************/

var Main = {
  ui: {
    page   : "#playqueue",
    section: "#Main-section"
  },
  init: function() {
    /* Bug in jQuery: you can't have same function attached to multiple events! */    
    Main.ui.list = new NavList.Section(Main.ui.section, '');
    Main.ui.list.addItem("home", $("<li class='home'><a href='#home'>Home</a><li>"));
    $(document).bind("Page.home", Main.setHome);
    Main.ui.playqueue = $("<li class='playqueue'><a href='#playqueue'>Play queue</a></li>");
    Main.ui.playqueue.droppable({
      hoverClass: 'drophover',
      tolerance: 'pointer',
      drop: function(event, ui) {
        var uri = ui.draggable.data("uri");
        Dogvibes.queue(uri);
      }
    });
    Main.ui.list.addItem("playqueue", Main.ui.playqueue);
    $(document).bind("Page.playqueue", Main.setQueue); 
    
    /* Online / Offline */
    $(document).bind("Server.error", function() {
      $(Main.ui.page).removeClass();
      $(Main.ui.page).addClass("disconnected");
    });
    $(document).bind("Server.connected", function() {
      $(Main.ui.page).removeClass("disconnected");
    });
  },
  setQueue: function() {
    Titlebar.set(Dogbone.page.title);
    Main.ui.list.selectItem(Dogbone.page.id);
    Playqueue.fetch();
  },
  setHome: function() {
    Titlebar.set(Dogbone.page.title);
    Main.ui.list.selectItem(Dogbone.page.id);
  }  
};

var Playqueue = {
  ui: {
    page: "#playqueue"
  },
  table: false,
  hash: false,
  init: function() {
    /* Create a table for our tracks */
    Playqueue.table = new ResultTable(
    {
      name: 'Playqueue', 
      dblclick: function() {
        var id = $(this).data('id');
        Dogvibes.playTrack(id, "-1");
      },
      /* Add a remove-icon  */
      callbacks: {
        space: function(element) {        
          $('<span> remove </span>')
            .data('id', element.id)
            .data('nbr', element.nbr)
            .attr("title", "remove track(s) from playqueue")
            .click(function(e) {
              var id = $(this).data('id');
              var nbr = $(this).data('nbr');
              /* if clicked item is in selected range, remove entire range */
              if( Playqueue.table.selectedItems.indexOf(nbr) != -1 ) {
                id = [];
                $(Playqueue.table.selectedItems).each(function(i, el) {
                  id.push(Playqueue.table.data[el].data('id'));
                  $("#Playqueue-item-nbr-"+el).remove();
                });
                $(id).get().join(',');
              } else {
                $("#Playqueue-item-nbr-"+nbr).remove();
              }
              Dogvibes.removeTrack(id);              
              e.preventDefault();
              return false;
          }).appendTo(element);
        }
      }
    });
    
    $(document).bind("Status.playlistchange", function() { Playqueue.fetch(); });
    $(document).bind("Status.state", function() { Playqueue.set(); });
    $(document).bind("Status.playlist", function() { Playqueue.set(); });
    $(document).bind("Server.connected", Playqueue.fetch);
  },
  fetch: function() {
    if(Dogbone.page.id != "playqueue") { return; }
    if(Dogvibes.server.connected) { 
      Playqueue.hash = Dogvibes.status.playlistversion;
      Dogvibes.getAllTracksInQueue("Playqueue.update");
    }
  },
  update: function(json) { 
    if(json.error !== 0) {
      return;
    }
    Playqueue.table.items = json.result;
    Playqueue.table.display();
    Playqueue.set();
    /* Make draggable/sortable. TODO: move into ResultTable */
    $(function() {
      $("tr", Playqueue.table.ui.items).draggable(Config.draggableOptions);
    });     
  },
  set: function() {
    if(Dogvibes.status.state == "playing" &&
       Dogvibes.status.playlist_id == -1) {
      $("li.playqueue").addClass('playing'); 
      Playqueue.table.highlightItem(Dogvibes.status.index);      
    } 
    else {
      $("li.playqueue").removeClass('playing');    
      Playqueue.table.clearHighlight();     
    }
  }
};

var PlayControl = {
  ui: {
    controls: "#PlayControl",
    prevBtn : "#pb-prev",
    playBtn : "#pb-play",
    nextBtn : "#pb-next",
    volume  : "#Volume-slider",
    seek    : "#TimeInfo-slider",
    elapsed : "#TimeInfo-elapsed",
    duration: "#TimeInfo-duration"
  },
  volSliding: false,
  seekSliding: false,
  updateTimer: false,
  init: function() {
    $(document).bind("Status.state", PlayControl.set);
    $(document).bind("Status.volume", PlayControl.setVolume);
    $(document).bind("Status.elapsed", function() {
      PlayControl.setTime({result: Dogvibes.status.elapsedmseconds});
    });
    
    PlayControl.updateTimer = setTimeout(function() {
      Dogvibes.getPlayedMilliSecs("PlayControl.setTime");
    }, 100);
    
    $(PlayControl.ui.volume).slider( {
      start: function(e, ui) { PlayControl.volSliding = true; },
      stop: function(e, ui) { PlayControl.volSliding = false; },
      change: function(event, ui) { 
        Dogvibes.setVolume(ui.value/100);
      }
    });
    
    $(PlayControl.ui.seek).slider( {
      start: function(e, ui) { PlayControl.seekSliding = true; },
      stop: function(e, ui) { PlayControl.seekSliding = false; },
      change: function(event, ui) { 
        Dogvibes.seek(Math.round((ui.value*Dogvibes.status.duration)/100));
      }
    });    
    
    $(PlayControl.ui.nextBtn).click(function() {
      Dogvibes.next();
      this.blur();
    });

    $(PlayControl.ui.playBtn).click(function() {
      PlayControl.toggle();
      this.blur();      
    });
    
    $(PlayControl.ui.prevBtn).click(function() {
      Dogvibes.prev();
      this.blur();      
    });
  },
  set: function() {
    $(PlayControl.ui.controls).removeClass();
    $(PlayControl.ui.controls).addClass(Dogvibes.status.state);
    if(Dogvibes.status.state == "stopped") {
      PlayControl.setTime({result: 0});
      $(PlayControl.ui.seek).slider( "option", "disabled", true );
    } else {
      $(PlayControl.ui.seek).slider( "option", "disabled", false );
    }
    //$(PlayControl.ui.duration).text(Dogvibes.status.duration.msec2time());    
  },
  toggle: function() {
    if(Dogvibes.status.state == "playing") {
      Dogvibes.pause();
    } else {
      Dogvibes.play();
    }
    PlayControl.set();
  },
  setVolume: function() {
    if(PlayControl.volSliding) { return; }
    $(PlayControl.ui.volume).slider('option', 'value', Dogvibes.status.volume*100);  
  },
  setTime: function(elapsed) {
    //$(PlayControl.ui.elapsed).text(Dogvibes.status.elapsedmseconds.msec2time());
    if(PlayControl.seekSliding) { return; }
    $(PlayControl.ui.seek).slider('option', 'value', (elapsed.result/Dogvibes.status.duration)*100); 
    /* Fetch another time update */
    if(PlayControl.updateTimer) {
      clearTimeout(PlayControl.updateTimer);
      PlayControl.updateTimer = setTimeout(function() {
        Dogvibes.getPlayedMilliSecs("PlayControl.setTime");
      }, 500);      
    }
  }  
};

var ConnectionIndicator = {
  ui: {
    icon: "#ConnectionIndicator-icon"
  },
  icon: false,
  init: function() {
    ConnectionIndicator.icon = $(ConnectionIndicator.ui.icon);
    if(ConnectionIndicator.icon) {
      $(document).bind("Server.connecting", function() {
        ConnectionIndicator.icon.removeClass();
        //ConnectionIndicator.icon.addClass("connecting");
      });
      $(document).bind("Server.error", function() {
        ConnectionIndicator.icon.removeClass();
        ConnectionIndicator.icon.addClass("error");
      });
      $(document).bind("Server.connected", function() {
        ConnectionIndicator.icon.removeClass();
        ConnectionIndicator.icon.addClass("connected");
      });       
    }
  }
};

var TrackInfo = {
  ui: {
    artist  : "#TrackInfo-artist",
    title   : "#TrackInfo-title",
    albumArt: "#TrackInfo-albumArt"
  },
  init: function() {
    if($(TrackInfo.ui.artist) && $(TrackInfo.ui.title)) {
      $(document).bind("Status.songinfo", TrackInfo.set);
    }
  },
  set: function() {
    $(TrackInfo.ui.artist).text(Dogvibes.status.artist);
    $(TrackInfo.ui.title).text(Dogvibes.status.title);
    var img = Dogvibes.albumArt(Dogvibes.status.artist, Dogvibes.status.album, 180);
    /* Create a new image and crossfade over */
    var newImg = new Image();
    newImg.src = img;
    newImg.id  = 'TrackInfo-newAlbumArt';
    /* Don't show image until fully loaded */
    $(newImg).load(function() {
      $(newImg)
        .appendTo('#currentsong')
        .fadeIn(500, function() {
          $(TrackInfo.ui.albumArt).remove();
          $(newImg).attr("id", "TrackInfo-albumArt");
        });
    });
  }
};

var Playlist = {
  ui: {
    section : "#Playlist-section",
    newPlist: "#Newlist-section"
  },
  table: false,
  selectedList: "",
  init: function() {
    Playlist.ui.list =    new NavList.Section(Playlist.ui.section, 'playlists');
    Playlist.ui.newList = new NavList.Section(Playlist.ui.newPlist, 'last');
    Playlist.ui.newBtn  = $("<li class='newlist'><a>New playlist</a></li>");
    Playlist.ui.newBtn.click(function() {
      var name = prompt("Enter new playlist name");
      if(name) {
        Dogvibes.createPlaylist(name, "Playlist.fetchAll");
      }
    });
    Playlist.ui.newList.addItem('newlist', Playlist.ui.newBtn);

    /* Handle offline/online */
    $(document).bind("Server.error", function() {
      $(Playlist.table.ui.content).hide();
      $("#playlist").addClass("disconnected");
    });
    $(document).bind("Server.connected", function() {
      $(Playlist.table.ui.content).show();
      $("#playlist").removeClass("disconnected");
    });
    
    /* Create a table for the tracks */
    Playlist.table = new ResultTable(
    {
      name: 'Playlist',
      highlightClass: "listplaying",
      /* Dblclick event */
      dblclick: function() {
        var index = $(this).data('id');
        Playlist.playItem(index);
      },
      /* Add a remove-icon  */
      callbacks: {
        space: function(element) {        
          $('<span> remove </span>')
            .data('id', element.id)
            .data('nbr', element.nbr)
            .attr("title", "remove track(s) from playlist")
            .click(function(e) {
              var id = $(this).data("id");
              var nbr =$(this).data("nbr"); 
              var pid = Playlist.selectedList;
              /* if clicked item is in selected range, remove entire range */
              if( Playlist.table.selectedItems.indexOf(nbr) != -1 ) {
                id = [];
                $(Playlist.table.selectedItems).each(function(i, el) {
                  id.push(Playlist.table.data[el].data('id'));
                  $("#Playlist-item-nbr-"+el).remove();
                });
                id = $(id).get().join(',');

              } else {
                $("#Playlist-item-nbr-"+nbr).remove();
              }
              Dogvibes.removeFromPlaylist(id, pid);
              e.preventDefault();
              return false;
          }).appendTo(element);
        }
      }
    });

    /* Setup events */
    $(document).bind("Page.playlist", Playlist.setPage);
    $(document).bind("Status.playlistchange", function() { Playlist.setPage(); });   
    $(document).bind("Server.connected", function() { Playlist.fetchAll(); });
    
    $(document).bind("Status.state", function() { Playlist.set(); });    
    $(document).bind("Status.songinfo", function() { Playlist.set(); });    
    $(document).bind("Status.playlist", function() { Playlist.set(); });       
    /* Handle sorts */
    $(Playlist.table.ui.items).bind("sortupdate", function(event, ui) {
      var items = $(this).sortable('toArray');
      var trackPos =$(ui.item).data("nbr"); 
      var trackID = $(ui.item).data("id");
      var position;
      for(var i = 0; i < items.length; i++) {
        if(items[i] == "Playlist-item-nbr-"+trackPos) {
          position = i;
          break;
        }
      }
      Dogvibes.move(Playlist.selectedList, trackID, (position+1), "Playlist.setPage");
    });               
  },
  setPage: function() {
    if(Dogbone.page.id != "playlist") { return; }
    Playlist.ui.list.selectItem(Dogbone.page.param);
    Titlebar.set(Dogbone.page.title);
    
    if(Dogvibes.server.connected) {
      /* Save which list that is selected */
      Playlist.selectedList = Dogbone.page.param;
      /* Load new items */
      Dogvibes.getAllTracksInPlaylist(Playlist.selectedList, "Playlist.handleResponse");
    }
  },
  fetchAll: function() {
    Dogvibes.getAllPlaylists("Playlist.update");
  },
  update: function(json) {
    Playlist.ui.list.empty();
    if(json.error !== 0) {
      alert("Couldn't get playlists");
      return;
    }
    $(json.result).each(function(i, el) {
      /* Create list item */
      var item = 
      $('<li></li>')
      .attr("id", "Playlist-"+el.id)
      .append(
        $('<a></a>')
        .attr("href", "#playlist/"+el.id)
        .text(el.name)
        .click(function() {
          $(this).blur();
        })
      );
      /* Make droppable */
      item.droppable({
        hoverClass: 'drophover',
        tolerance: 'pointer',
        drop: function(event, ui) {
          var id = $(this).attr("id").removePrefix("Playlist-");
          var uri = ui.draggable.data("uri");
          Dogvibes.addToPlaylist(id, uri);
        }
      });
      /* Remove-button */
      $('<span> remove </span>')
      .data("id", el.id)
      .attr("title", "remove this playlist")
      .click(function() {
        if(confirm("Do you want to remove this playlist?")) {
          var id = $(this).data("id");
          Dogvibes.removePlaylist(id, "Playlist.fetchAll");
          /* FIXME: solve this nicer */
          if(id == Playlist.selectedList) {
            location.hash = "#home";
          }
        }
      }).appendTo(item);
      /* Double click to start playing */
      item.dblclick(function() {
        id = $(this).data("id");
        Dogvibes.playTrack(0, id);
      });
      Playlist.ui.list.addItem(el.id, item);
    });
    Playlist.setPage();
  },

  handleResponse: function(json) {
    if(json.error !== 0) {
      alert("Couldn't get playlist");
      return;
    }
    Playlist.table.items = json.result;
    Playlist.table.display();    
    Playlist.set();
    $(function() {
      $(Playlist.table.ui.items).sortable(Config.sortableOptions);
    });     
  },
  playItem: function(id) {
    var nbr = parseInt(id, 10);
    if(!isNaN(nbr)) {
      Dogvibes.playTrack(id, Playlist.selectedList);
    }
  },
  set: function() {  
    Playlist.table.clearHighlight();
    $('li', Playlist.ui.list.ul).removeClass('playing');    
    if(Dogvibes.status.state == "playing") {
      $("#Playlist-"+Dogvibes.status.playlist_id).addClass('playing');
      if(Dogvibes.status.playlist_id == Playlist.selectedList) {    
        Playlist.table.highlightItem(Dogvibes.status.index);
      }
    }
  } 
};

var Search = {
  ui: {
    form:    "#Search-form",
    input:   "#Search-input",
    section: "#Search-section",
    page   : "#search"
  },
  searches: [],
  param: "",
  table: false,
  init: function() {
    /* Init search navigation section */
    Search.ui.list = new NavList.Section(Search.ui.section,'search');
    $(document).bind("Page.search", Search.setPage);
    
    /* Handle offline/online */
    $(document).bind("Server.error", function() {
      $(Search.table.ui.content).hide();
      $(Search.ui.page).removeClass();
      $(Search.ui.page).addClass("disconnected");
    });
    $(document).bind("Server.connected", function() {
      Search.setPage();
      $(Search.table.ui.content).show();
      $(Search.ui.page).removeClass("disconnected");
    });

    $(Search.ui.form).submit(function(e) {
      var val = $("#Search-input").val();
      if(val != "") {
        Search.doSearch($("#Search-input").val());
      }
      e.preventDefault();
      return false;
    });
    
    /* Create result table */
    Search.table = new ResultTable(
    {
      name: "Search",
      idTag: "uri",
      sortable: true,
      dblclick: function() {
        var uri = $(this).data("id");
        Dogvibes.queue(uri);
        Search.table.deselectAll();
        $(this).effect("highlight");
        $(this).addClass("queued");
      },
      callbacks: {
        popularity: function(element) {
          var value = element.text();
          var bar = $('<div></div>').css('width', (value*60)+"px");
          element.contents().wrap(bar);
        }
      }
    });
  
    /* Load searches from cookie */
    var temp;
    for(var i = 0; i < 6; i++){
      if((temp = getCookie("Dogvibes.search" + i)) != "") {
        Search.searches[i] = temp;
      }
    }
    Search.draw();
  },
  setPage: function() {
    if(Dogbone.page.id != "search") { return; }
    /* See if search parameter has changed. If so, reload */
    if(Dogvibes.server.connected &&
       Dogbone.page.param != Search.param) {
      Search.param = Dogbone.page.param;
      Search.searches.push(Search.param);
      Search.table.empty();
      $(Search.ui.page).addClass("loading");
      Search.addSearch(Search.param);
      
      Dogvibes.search(Search.param, "Search.handleResponse");
    }
    Search.setTitle();    
    Search.ui.list.selectItem(Dogbone.page.param);
  },
  addSearch: function(keyword) {
    var tempArray = Array();
    tempArray.unshift($.trim(keyword));
    $.each(Search.searches, function(i, entry){
      if($.trim(keyword) != entry){
        tempArray.push(entry);
      }
    });
    if(tempArray.length > 6){
      tempArray.pop();
    }
    Search.searches = tempArray;
    for(var i = 0; i < tempArray.length; i++) {
      setCookie("Dogvibes.search" + i, tempArray[i]);
    }
    Search.draw();  
  },
  draw: function() {
    Search.ui.list.empty();
    $(Search.searches).each(function(i, el) {
      Search.ui.list.addItem(el,"<li class='"+el+"'><a href='#search/"+el+"'>"+el+"</a></li>");
    });
  },
  setTitle: function() {
    $(UI.titlebar).empty();
    $(UI.titlebar).append($("<li class='selected'>Search</li>"));
    $(UI.titlebar).append($("<li class='keyword'>"+Search.param+"</li>"));    
  },
  doSearch: function(keyword) {
    window.location.hash = "#search/"+keyword;
  },
 
  handleResponse: function(json) {
    $(Search.ui.page).removeClass("loading");  
    if(json.error !== 0) {
      alert("Search error!");
      return;
    }
    Search.table.items = json.result;
    Search.table.display();
    $(function() {
      $(Search.table.ui.items + " tr").draggable(Config.draggableOptions);
    });    
  }
};


/* FIXME: correct artist/album handler in future */
var Artist = {
  albums: [],
  album: [],
  currentArtist: "",
  init: function() {
    $(document).bind("Page.artist", Artist.setPage);
    $(document).bind("Page.album", function() { Artist.setPage(); });
    $(document).bind("Server.connected", function() { Artist.setPage(); });    
  },
  setPage: function() {
    Titlebar.set(Dogbone.page.title);
    if(!Dogvibes.server.connected) { return; }
    if(Dogbone.page.title == "Album") {
      var album = Dogbone.page.param;
      /* FIXME: need a way of getting single album info */
      var entry = {
        uri: album,
        artist: "Jularbo",
        name: "none",
        released: "1981",
      };
      $("#album").empty();
      Dogvibes.getAlbum(entry.uri, "Artist.setAlbum");
    }
    else if(Dogbone.page.title == "Artist" && Artist.currentArtist != Dogbone.page.param){
      Artist.currentArtist = Dogbone.page.param;
      /* Reset and fetch new data */
      Artist.albums = [];
      $('#artist').empty().append('<h2>'+Dogbone.page.param+'</h2>');
      Dogvibes.getAlbums(Dogbone.page.param, "Artist.display");
    }
  },
  setAlbum: function(data) {
    Artist.album = new AlbumEntry(data);
    $("#album").append(Artist.album.ui);
  },
  display: function(data) {
    if(data.error > 0) { return false; }
    var other = false;
    var artist = Dogbone.page.param;
    /* FIXME: will this always work? */
    if(artist == data.result[0].artist) {
      $('<h3></h3>').text("Albums").appendTo('#artist');
    }
    $(data.result).each(function(i, element) {
      if(!other && element.artist != artist) {
        other = true;
        $('<h3></h3>').text("Appears on").appendTo('#artist');
      }
      var idx = Artist.albums.length;
      Artist.albums[idx] = new AlbumEntry(element);
      $('#artist').append(Artist.albums[idx].ui);
      
      /* Get tracks for album, since we don't get them directly */
      /* FIXME: solve context problem nicer */
      Dogvibes.getAlbum(element.uri, "Artist.albums["+idx+"].set", Artist.albums[idx]);
    });
  }
};

var AlbumEntry = function(entry) {
  var self = this;
  this.ui = 
    $('<div></div>')
    .addClass('AlbumEntry');
  var title = 
    $('<h4></h4>')
    .appendTo(this.ui)    
    .text(entry.name + ' ('+entry.released+')');
  var art = 
    $('<div></div>')
    .addClass('AlbumArt')
    .appendTo(this.ui);
  var artimg = 
    $('<img></img>')
    .attr('src', Dogvibes.albumArt(entry.artist, entry.name, 130))
    .appendTo(art);
  var table =  
    $('<table></table>')
    .attr('id', entry.uri+"-content")
    .data('self', this)
    .addClass('theme-tracktable')
    .appendTo(this.ui);
  var items = $('<tbody></tbody>').attr('id', entry.uri+'-items').appendTo(this.table);
  
  this.resTbl = new ResultTable({ name: entry.uri, fields: [ 'title', 'duration' ] });
  /* Show the tracks if we have them */
  if(typeof(entry.tracks) != "undefined") { 
    self.resTbl.items = entry.tracks;
    self.resTbl.display();
  }
  this.set = function(data) {
    if(data.error > 0) { return; }
    /* XXX: compensate for different behaviours in AJAX/WS */
    var self = typeof(this.context) == "undefined" ? this : this.context;
    self.resTbl.items = data.result;
    self.resTbl.display(); 
  }
  
};

/***************************
 * Keybindings 
 ***************************/
 
/* CTRL+s for searching */ 
$(document).bind("keyup", "ctrl+s", function() {
  $(Search.ui.input).focus();
});

$(document).bind("keyup", "ctrl+p", function() {
  PlayControl.toggle();
});

$(document).dblclick(function() {
  var sel;
  if(document.selection && document.selection.empty){
    document.selection.empty() ;
  } else if(window.getSelection) {
    sel=window.getSelection();
  }
  if(sel && sel.removeAllRanges) {
    sel.removeAllRanges();
  }
});

/***************************
 * Startup 
 ***************************/
$(document).ready(function() {
  
  /* Zebra stripes for all tables */
  $.tablesorter.defaults.widgets = ['zebra'];

  Dogbone.init("content");
  ConnectionIndicator.init();
  PlayControl.init();
  TrackInfo.init();
  /* Init in correct order */
  Playqueue.init();
  Main.init();
  Search.init();
  Playlist.init();
  Artist.init();
  /* Start server connection */
  Dogvibes.init(Config.defaultProtocol, Config.defaultServer, Config.defaultUser);
  
  /****************************************
   * Misc. behaviour. Application specific
   ****************************************/
   
  /* FIXME:  */
  $(UI.trackinfo).click(function() {
    $(UI.navigation).toggleClass('fullHeight');
    $(UI.currentsong).toggleClass('minimized');
  });
  
  /* Splitter */
  $("#separator").draggable( {
    containment: [150, 0, 300, 0],
    axis: 'x',
    drag: PanelSplit.drag
  });
  
}); 

var PanelSplit = {
  left: 180,
  drag: function(event, ui) {
    PanelSplit.set(ui.position.left);
  },
  set: function(left) {
    $(".resizable-right").css("width", left+"px");
    $(".resizable-left").css("left", left+"px");
    $(".resizable-top").each(function(i, el) {
      var height = $(el).height();
      $(el).height(height + (left - PanelSplit.left));
    });    
    $(".resizable-bottom").each(function(i, el) {
      var height = $(el).css("bottom");
      height = parseInt(height.substring(0, height.indexOf("px")), 10);
      $(el).css("bottom", (height + (left - PanelSplit.left)) + "px");
    });
    PanelSplit.left = left;
  }
};
