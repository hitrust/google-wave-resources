var youtubePlayer = null;
var pickerOverlay = null;
var videoState = null;
var preloadingNow = false;
var progressInterval = null;

var DEBUG = true;

/** Timing related constants **/
var SECONDS_PRELOAD = 3;
var SECONDS_WAITING = 0;

var DEFAULT_VOLUME = 60;

/** DOM elements **/
var DOM = {
  PICKER: null,
  PICKERRESULTS: null,
  PICKERTRIGGER: null,
  SEARCHBUTTON: null,
  SEARCHINPUT: null,
  PLAYER: null,
  PLAYINGNOW: null,
  PLAYTIME: null,
  CONTROL: null,
  PROGRESSBAR: null,
  ELAPSEDBAR: null
};

/** Time diffs allowed **/
var DIFF = {
  PLAYLAG: 1,
  PAUSELAG: 1,
  PRELOAD: 1
};

/** Keys + key prefixes **/
var KEY = {
  ID: 'video-id',
  STATUS: 'video-status:',
  DATA: 'video-data:',
  PLAYTIME: 'video-playtime:',
  TIMESTAMP: 'video-timestamp:',
  MODIFIER: 'video-modifier:'
};

/** Status of video, as set by participants **/
var STATUS = {
  SELECTED: 'selected',
  PLAYING: 'playing',
  PAUSED: 'paused',
  ENDED: 'ended'
};

/** State of YouTube player, as specified by Youtube API **/
var PLAYERSTATE = {
  UNSTARTED: -1,
  ENDED: 0,
  PLAYING: 1,
  PAUSED: 2,
  BUFFERING: 3,
  CUED: 5
};

/**
 * Object for managing state for a selected video.
 */
function VideoState(id) {
  this.id = id;
}

VideoState.prototype.saveSelection = function(data) {
  var delta = {};
  delta[KEY.ID] = this.id;
  delta[KEY.DATA + this.id] = JSON.stringify(data);
  delta[KEY.STATUS + this.id] = 'selected';
  wave.getState().submitDelta(delta);
};

VideoState.prototype.saveStatus = function(status, playtime, timestamp) {
  log("saveStatus(" + status + ", " + playtime + ", " + timestamp +")")
  var delta = {};
  delta[KEY.STATUS + this.id] = status;
  if (playtime == null || playtime == undefined) {
    playtime = youtubePlayer.getCurrentTime();
  }
  delta[KEY.PLAYTIME + this.id] = playtime;
  delta[KEY.TIMESTAMP + this.id] = timestamp || new Date();
  delta[KEY.MODIFIER + this.id] = wave.getViewer().getId();
  wave.getState().submitDelta(delta);
};

VideoState.prototype.deleteState = function() {
  var delta = {};
  var keys = [KEY.DATA, KEY.STATUS, KEY.PLAYTIME, KEY.TIMESTAMP, KEY.MODIFIER];
  for (var i = 0; i < keys.length; i++) {
    delta[keys[i] + this.id] = null;
  }
  wave.getState().submitDelta(delta);
};

VideoState.prototype.getId = function() {
  return this.id;
};

VideoState.prototype.getModifier = function() {
  return wave.getState().get(KEY.MODIFIER + this.id);
};

VideoState.prototype.getData = function() {
  var data = wave.getState().get(KEY.DATA + this.id);
  if (data) {
    data = JSON.parse(data);
    return data;
  }
  return null;
};

VideoState.prototype.getTitle = function() {
  var data = this.getData();
  if (data) {
    return data.title;
  }
  return null;
};

VideoState.prototype.getDuration = function() {
  var data = this.getData();
  if (data) {
    return data.duration;
  }
  return null;
}

VideoState.prototype.getStatus = function() {
  return wave.getState().get(KEY.STATUS + this.id);
}

VideoState.prototype.getPlaytime = function() {
  var playtime = wave.getState().get(KEY.PLAYTIME + this.id);
  if (playtime != null) {
    return parseFloat(playtime);
  } else {
    return null;
  }
}

VideoState.prototype.getTimestamp = function() {
  var timestamp = wave.getState().get(KEY.TIMESTAMP + this.id);
  if (timestamp) {
    return new Date(timestamp);
  } else {
    return null;
  }
}

/**
 * Get the actual playtime which is the shared playtime plus the time elapsed
 * since the shared playtime was updated.
 */
VideoState.prototype.getComputedPlaytime = function() {
  if (this.getPlaytime() == null) return null;
  var timeElapsed = new Date() - this.getTimestamp();
  var currentPlaytime = this.getPlaytime() + (timeElapsed/1000);
  return currentPlaytime;
}

function log(message) {
  if (DEBUG) {
    if (window.console && console.log) {
      console.log(message);
    }
  }
}

/**
 * Handles state callbacks.
 */
function onStateChange(state, changedState) {
  log("State change:");
  log(state);
  log(changedState);
  // If no video has been selected, show picker + featured vids
  if (!state.get(KEY.ID)) {
    pickerOverlay.load();
    DOM.PICKER.addClass('start');
    showFeatured();
    return;
  }

  // If the video changed
  if (changedState[KEY.ID]) {
    pickerOverlay.close();
    videoState = new VideoState(state.get(KEY.ID));
    if (videoState.getStatus() == STATUS.ENDED) {
      showEnded();
    } else {
      prepVideo();
    }
    return;
  }

  // If video is same but status changed
  var statusKey = (KEY.STATUS + videoState.getId());
  if (videoState && changedState[statusKey]) {
    controlVideo();
  }
}


/*** PICKER RELATED FUNCTIONALITY ***/

function showSearch(query) {
  var searchUrl = 'http://gdata.youtube.com/feeds/api/videos';
  var params = {
    'v': '2',
    'alt': 'jsonc',
    'format': '5',
    'q': query
  }
  DOM.PICKERRESULTS.empty();
  DOM.PICKERRESULTS.append('<div class="picker-divider">Search Results:</div>');
  JSONP.get(searchUrl, params, null, function(json) {
    handleSearchResults(json);
  });
}

function showRelated(id) {
  var feedUrl = 'http://gdata.youtube.com/feeds/api/videos/' + id + '/related';
  var params = {
    'v': '2',
    'alt': 'jsonc',
    'format': '5'
  }
  DOM.PICKERRESULTS.empty();
  DOM.PICKERRESULTS.append('<div class="picker-divider">Related Videos:</div>');
  JSONP.get(feedUrl, params, null, function(json) {
    handleFeedResults(json);
  });
}


function showFeatured() {
  var feedUrl = 'http://gdata.youtube.com/feeds/api/standardfeeds/recently_featured';
  var params = {
    'v': '2',
    'alt': 'jsonc',
    'format': '5'
  };
  DOM.PICKERRESULTS.empty();
  DOM.PICKERRESULTS.append('<div class="picker-divider">Featured Videos:</div>');
  JSONP.get(feedUrl, params, null, function(json) {
    handleFeedResults(json);
  });
}


function numberWithCommas(x) {
  return x.toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ",");
}


function handleFeedResults(json) {
  DOM.PICKERRESULTS.removeClass('search').addClass('feed');
  var results = json.data.items || [];
  var resultsArea = $('<div></div>');
  for (var i = 0; i < Math.min(14, results.length); i++) {
    addFeedResult(results[i], resultsArea);
  }
  DOM.PICKERRESULTS.append(resultsArea);
}


function addFeedResult(result, resultsArea) {
  var resultBlock= $('<div></div>').appendTo(resultsArea);
  resultBlock.click(function() {
    selectVideo(result);
  });
  resultBlock.addClass('result');
  var image = $('<img src="' + result.thumbnail.sqDefault + '">').appendTo(resultBlock);
  var linkBlock = $('<div class="title"><a href="javascript:void(0)">' + truncate(result.title, 37) + '</div>').appendTo(resultBlock);
  var infoBlock = $('<div class="info"></div>').appendTo(resultBlock);
  infoBlock.append('by ' + result.uploader);
  if (result.viewCount) {
    var views = numberWithCommas(result.viewCount);
    infoBlock.append('<br>' + views + ' views');
  }
}


function handleSearchResults(json) {
  DOM.PICKERRESULTS.removeClass('feed').addClass('search');
  var results = json.data.items || [];
  var resultsTable = $('<table></table>');
  for (var i = 0; i < results.length; i++) {
    addSearchResult(results[i], resultsTable);
  }
  DOM.PICKERRESULTS.append(resultsTable);
}

function addSearchResult(result, resultsTable) {
  var row = $('<tr></tr>').appendTo(resultsTable);
  var imageCell = $('<td width="140"></td>').appendTo(row);
  imageCell.click(function() {
    selectVideo(result);
  });
  var image = $('<img src="' + result.thumbnail.sqDefault + '">').appendTo(imageCell);
  var infoCell = $('<td></td>').appendTo(row);
  infoCell.click(function() {
    selectVideo(result);
  });
  var linkBlock = $('<div class="title"><a href="javascript:void(0)">' + result.title + '</a></div>').appendTo(infoCell);
  infoCell.append('<p>' + truncate(result.description, 140) + '<br>');
  var uploaded = new Date(result.uploaded).toRelativeTime();
  var views = numberWithCommas(result.viewCount);
  infoCell.append('by ' + result.uploader + ' | ' + uploaded + ' | ' + views + ' views</p>');
}

/*** PICKER -> PLAYER TRANSITION FUNCTIONALITY ***/

function selectVideo(result) {
  stopVideo();
  pickerOverlay.close();
  if (videoState) {
    videoState.deleteState();
    videoState = null;
  }
  videoState = new VideoState(result.id);
  videoState.saveSelection(result);
}


/*** PLAYER RELATED FUNCTIONALITY ***/

function prepVideo() {
  DOM.PLAYER.show();
  DOM.PLAYINGNOW.html('Now playing: ' + videoState.getTitle());
  if (!youtubePlayer) {
    var params = { allowScriptAccess: "always", wmode: 'transparent' };
    var atts = { id: "myytplayer" };
    swfobject.embedSWF('http://www.youtube.com/e/' + videoState.getId() + '?enablejsapi=1&playerapiid=ytplayer',
                       'player-ytapiplayer', '100%', '80%', '8', null, null, params, atts);
  } else {
    stopVideo();
    youtubePlayer.cueVideoById(videoState.getId());
    preloadVideo();
  }
}

function onYouTubePlayerReady(playerId) {
  youtubePlayer = document.getElementById('myytplayer');
  log("YouTube player ready: " + youtubePlayer);
  youtubePlayer.addEventListener('onStateChange', 'onYouTubePlayerStateChange');
  youtubePlayer.setVolume(DEFAULT_VOLUME);
  preloadVideo();
}

function preloadVideo() {
  // Handle easy cases where video is paused or
  // video was playing but is now past the end time
  if (videoState.getStatus() == STATUS.PAUSED) {
    pauseWithPreload();
    return;
  } else if (videoState.getStatus() == STATUS.PLAYING && videoState.getComputedPlaytime() >= videoState.getDuration()) {
    stopVideo();
    DOM.PLAYINGNOW.html('Last played: ' + videoState.getTitle());
    DOM.PICKERLINK.click();
    return;
  }
  log('Preloading');
  preloadingNow = true;
  var currentPlaytime = videoState.getComputedPlaytime();
  if (!currentPlaytime) {
    // The video was selected but hasn't been played by anyone yet
    currentPlaytime = 0;
  }
  youtubePlayer.style.visibility = 'hidden';
  youtubePlayer.mute();
  if (currentPlaytime > 0) {
    log('Seeking to ' + currentPlaytime);
    youtubePlayer.seekTo(currentPlaytime);
  } else {
    log('Playing video for preloading purposes.');
    youtubePlayer.playVideo();
  }

  var preloadPlaytime = currentPlaytime + SECONDS_PRELOAD;
  var checkInterval = window.setInterval(function() {
    var timeDiff = Math.abs(youtubePlayer.getCurrentTime() - preloadPlaytime);
    if (youtubePlayer.getPlayerState() == PLAYERSTATE.PLAYING && timeDiff <= DIFF.PRELOAD) {
     window.clearInterval(checkInterval);
     youtubePlayer.pauseVideo();
     preloadingNow = false;
     almostPlayVideo();
    }
  }, 30);
}

function almostPlayVideo() {
  log('Almost playing video');
  if (isParticipant()) {
    if (videoState.getStatus() == STATUS.SELECTED) {
      log('Noone else started playing it, Ill start playing in ' + SECONDS_WAITING + ' seconds');
      var predictedTimestamp = new Date();
      predictedTimestamp.setMilliseconds(predictedTimestamp.getMilliseconds() + (SECONDS_WAITING * 1000));
      window.setTimeout(function() {
        playVideo(0);
      }, 1000 * SECONDS_WAITING);
      // Only do this if we're a participant. Otherwise we'd auto-join the space.
        videoState.saveStatus(STATUS.PLAYING, 0, predictedTimestamp);
    } else if (videoState.getStatus() == STATUS.PLAYING) {
      var currentPlaytime = videoState.getComputedPlaytime();
      log('Someone else is already playing it, Im starting at ' + currentPlaytime);
      if (currentPlaytime < videoState.getDuration()) {
        playVideo(currentPlaytime);
      }
    }
  }
}


function playVideo(playtime) {
  if (preloadingNow) return;
  youtubePlayer.style.visibility = 'visible';
  youtubePlayer.unMute();
  if (playtime != undefined) {
    log('Seeking to ' + playtime);
    youtubePlayer.seekTo(playtime);
  }
  youtubePlayer.playVideo();
  log('Playing from ' + playtime + ' at ' + (new Date()));

  progressInterval = window.setInterval(updateProgress,1000);
}

function updateProgress() {
  if (!youtubePlayer || !youtubePlayer.getCurrentTime) return;
  DOM.ELAPSEDBAR.width(((youtubePlayer.getCurrentTime()/videoState.getDuration())*100)+'%');
  if (DEBUG) {
    DOM.PLAYTIME.text(youtubePlayer.getCurrentTime());
  }
}

function pauseVideo() {
  log('Pausing video');
  // If the video is currently playing, pause it:
  youtubePlayer.pauseVideo();
  window.clearInterval(progressInterval);
}


function stopVideo() {
  if (!youtubePlayer) return;
  youtubePlayer.stopVideo();
}

/**
 * How long time does it take to buffer. Every time we lag we increase this.
 */
var justBuffered = false;
var bufferStart = null;
var bufferTimeEstimation = 1;

function onYouTubePlayerStateChange(state) {
  logState(state);
  if (preloadingNow) {
    log('Preloading now, dont care about state change.');
    return;
  }
  switch (state) {
    case PLAYERSTATE.UNSTARTED:
      DOM.CONTROL.removeClass('loading play pause').addClass('replay');
      break;
    case PLAYERSTATE.ENDED:
      videoState.saveStatus(STATUS.ENDED);
      showEnded();
      break;
    case PLAYERSTATE.PLAYING:
      videoState.saveStatus(STATUS.PLAYING);
      if (bufferStart) {
        bufferTimeEstimation = (new Date().getTime() / 1000) - bufferStart;
      }
      if (justBuffered) {
        catchupOnLag(state);
      }
      DOM.CONTROL.removeClass('loading play replay').addClass('pause');
      justBuffered = false;
      break;
    case PLAYERSTATE.PAUSED:
      videoState.saveStatus(STATUS.PAUSED);
      DOM.CONTROL.removeClass('loading pause replay').addClass('play');
      updateProgress();
      break;
    case PLAYERSTATE.BUFFERING:
      DOM.CONTROL.removeClass('play pause replay').addClass('loading');
      bufferStart = new Date().getTime() / 1000;
      break;
    case PLAYERSTATE.CUED:
      DOM.CONTROL.removeClass('play pause replay').addClass('loading');
      break;
    default:
      break;
  }
}

function showEnded() {
  DOM.CONTROL.removeClass('loading play pause').addClass('replay');
  DOM.PLAYINGNOW.html('Last played: ' + videoState.getTitle());
  pickerOverlay.load();
  showRelated(videoState.getId());
}

function catchupOnLag() {
  // If we'd been buffering, let's see if we need to catch up
  if (videoState.getStatus() == STATUS.PLAYING) {
    var timeDiff = videoState.getComputedPlaytime() - youtubePlayer.getCurrentTime();
    if (Math.abs(timeDiff) > DIFF.PLAYLAG) {
      var newTime = Math.min(youtubePlayer.getDuration(),
          videoState.getComputedPlaytime() + bufferTimeEstimation);
      log('Skipping from ' + youtubePlayer.getCurrentTime() + ' to ' + newTime +
          ". Buffering time estimation is: " + bufferTimeEstimation);
      playVideo(newTime);
    }
  }
}

function logState(state) {
  var logInfo = [];
  logInfo.push('currentTime: ' + youtubePlayer.getCurrentTime());
  logInfo.push('videoBytesLoaded: ' + youtubePlayer.getVideoBytesLoaded());
  switch(state) {
    case PLAYERSTATE.UNSTARTED:
      logInfo.push('state: unstarted');
      break;
    case PLAYERSTATE.ENDED:
      logInfo.push('state: ended');
      break;
    case PLAYERSTATE.PLAYING:
      logInfo.push('state: playing');
      break;
    case PLAYERSTATE.PAUSED:
      logInfo.push('state: paused');
      break;
    case PLAYERSTATE.BUFFERING:
      logInfo.push('state: buffering');
      break;
    case PLAYERSTATE.CUED:
      logInfo.push('state: cued');
      break;
  }
  log(logInfo.join(','));
}


function pauseWithPreload() {
  preloadingNow = true;
  var playtime = videoState.getPlaytime();
  youtubePlayer.seekTo(playtime, true);
  var checkInterval = window.setInterval(function() {
    var timeDiff = Math.abs(youtubePlayer.getCurrentTime() - playtime);
    if (youtubePlayer.getPlayerState() == PLAYERSTATE.PLAYING && timeDiff <= DIFF.PRELOAD) {
      window.clearInterval(checkInterval);
      preloadingNow = false;
      youtubePlayer.pauseVideo();
    }
  }, 30);
}

function controlVideo() {
  if (!youtubePlayer || !youtubePlayer.pauseVideo) return;
  var status = videoState.getStatus();
  var modifier = videoState.getModifier();
  switch(status) {
    case STATUS.PAUSED:
      var timeDiff = Math.abs(youtubePlayer.getCurrentTime() - videoState.getPlaytime());
      if (modifier != wave.getViewer().getId() && timeDiff >= DIFF.PAUSELAG) {
        log('Pausing because ' + modifier + ' told me to and time diff is ' + timeDiff);
        pauseWithPreload();
      }
      if (youtubePlayer.getPlayerState() == PLAYERSTATE.PLAYING) {
        log('Pausing because I was playing before');
        pauseWithPreload();
      }
      break;
    case STATUS.PLAYING:
      console.log('playing now');
      var timeDiff = Math.abs(youtubePlayer.getCurrentTime() - videoState.getComputedPlaytime());
      // Sync only play requests from other user that are more than X seconds diff
      if (modifier != wave.getViewer().getId() && timeDiff > DIFF.PLAYLAG) {
        log('Playing because ' + modifier + ' told me to and timeDiff is ' + timeDiff);
        playVideo(videoState.getComputedPlaytime() + bufferTimeEstimation);
      }
      if (youtubePlayer.getPlayerState() == PLAYERSTATE.PAUSED) {
        log('Playing because I was paused before');
        playVideo(videoState.getComputedPlaytime());
      }
      break;
  }
}

function isParticipant() {
  // If the thumbnailUrl is an empty string we've not joined the wave.
  return !!wave.getViewer().thumbnailUrl_;
}

function mute() {
  window.console.log('mute');
  var state = gadgetAV.getState();
  state.mic = false;
  gadgetAV.setState(state)
}

function unmute() {
  window.console.log('unmute');
  var state = gadgetAV.getState();
  state.mic = true;
  gadgetAV.setState(state)
}

/**
 * Sets up state callback and initializes UI elements.
 */
$(function() {
  gadgets.window.adjustHeight(-1);

  gadgetAV.setStateChangedCallback(function(state) {
    window.console.log('AV state changed: %o', state)
  });

  var spaceDown = false;
  $(document).keydown(function(evt) {
    // Space
    if (evt.keyCode == 32) {
      // We get continous keydown events while the key is down but we should only mute once.
      if (!spaceDown) {
        unmute();
        spaceDown = true;
      }
    }
  });
  $(document).keyup(function(evt) {
    // Space
    if (evt.keyCode == 32) {
      mute();
      spaceDown = false;
    }
  });
  mute();

  DOM.PICKER = $('#picker');
  DOM.PICKERTRIGGER = $('#picker-trigger');
  DOM.PICKERRESULTS = $('#picker-results');
  DOM.SEARCHBUTTON = $('#search-button');
  DOM.SEARCHINPUT = $('#search-input');
  DOM.PLAYER = $('#player');
  DOM.PLAYINGNOW = $('#player-nowplaying');
  DOM.PLAYTIME = $('#player-time');
  DOM.PICKERLINK = $('#player-link');
  DOM.CONTROL = $('#player-control');
  DOM.PROGRESSBAR = $('#player-progressbar');
  DOM.ELAPSEDBAR = $('#player-elapsedbar');
  DOM.VOLUME = $('#player-volume');

  DOM.PICKERTRIGGER.overlay({target: DOM.PICKER});
  pickerOverlay = DOM.PICKERTRIGGER.data('overlay');

  DOM.SEARCHBUTTON.click(function() {
    showSearch(DOM.SEARCHINPUT.val());
  });

  DOM.SEARCHINPUT.keypress(function(event) {
    if (event.which == '13') {
      showSearch(DOM.SEARCHINPUT.val());
      event.preventDefault();
    }
  });

  DOM.PICKERLINK.click(function() {
    pickerOverlay.load();
    DOM.PICKER.removeClass('start');
    showRelated(videoState.getId());
  });

  DOM.PROGRESSBAR.click(function(e){
    var ratio = (e.pageX-DOM.PROGRESSBAR.offset().left)/DOM.PROGRESSBAR.outerWidth();
    DOM.ELAPSEDBAR.width(ratio*100+'%');
    var playtime = videoState.getDuration()*ratio;
    youtubePlayer.seekTo(playtime, true);
    videoState.saveStatus(STATUS.PLAYING, playtime);
    return false;
  });

  DOM.CONTROL.click(function(){
    if (youtubePlayer.getPlayerState() == PLAYERSTATE.PAUSED) {
      playVideo();
      log('Saving the playing state');
      videoState.saveStatus(STATUS.PLAYING);
    } else if (youtubePlayer.getPlayerState() == PLAYERSTATE.PLAYING) {
      pauseVideo();
      log('Saving the pause state');
      videoState.saveStatus(STATUS.PAUSED);
    }
  });

  DOM.PROGRESSBAR.hide();
  DOM.VOLUME.hide();
  DOM.PLAYER.hover(
    function() {
      DOM.PROGRESSBAR.fadeIn();
      DOM.VOLUME.fadeIn();
    },
    function() {
      DOM.PROGRESSBAR.fadeOut();
      DOM.VOLUME.fadeOut();
    }
  );

  DOM.VOLUME.height(300);
  DOM.VOLUME.slider({
    orientation: "vertical",
    range: "min",
    min: 0,
    max: 100,
    value: DEFAULT_VOLUME,
    slide: function( event, ui ) {
      youtubePlayer.setVolume(parseInt(ui.value));
    }
  });

  wave.setStateCallback(onStateChange);
});
