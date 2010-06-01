// Copyright 2009 Google Inc.
function setStars(selectedStar) {
  return;
  var state = wave.getState();
  showStars(selectedStar);

  var viewerId = wave.getViewer().getId()
  state.submitValue(viewerId + '-vote', selectedStar);
}

function showStars(numStars) {
  var viewerId = wave.getViewer().getId();
  var viewerVote = viewerId + '-vote';
  // If no stars are specified (i.e. this is onmouseover),
  // just show number of stars for the viewer
  if (!numStars && wave && wave.getState().get(viewerVote)) {
    numStars = parseInt(wave.getState().get(viewerVote));
  }
  var _rating_star_names = [ '','Poor','Below average','Average','Above average','Excellent!' ];
  var img_rate_star_on = 'http://mashable-submitty.appspot.com/img/star_on.png';
  var img_rate_star_off = 'http://mashable-submitty.appspot.com/img/star_off.png';

  if (!numStars) {
    numStars = 0;
  }
  for (var i = 1; i <= 5; ++i) {
    var star_elem = _gel('star'+i);
    if (!star_elem) {
      continue;
    }
    if (numStars >= i) {
      star_elem.src = img_rate_star_on;
    } else {
      star_elem.src = img_rate_star_off;
    }
  }
  var star_name = _gel('star_name');
  if (star_name && numStars >= 0 && numStars < _rating_star_names.length) {
    star_name.innerHTML = _rating_star_names[numStars];
  }
}

function stateChanged() {
  showStars();
  var keys = wave.getState().getKeys();
  var totalVotes = 0;
  var starVotes = {};
  for (var i = 0; i < keys.length; i++) {
    var key = keys[i];
    if (key.indexOf('-vote') > 0) {
      // its a vote
      totalVotes++;
      var value = wave.getState().get(key);
      if (starVotes[value]) {
        starVotes[value]++
      } else {
        starVotes[value] = 1;
      }
    }
  }

  if (totalVotes > 0) {
    updateStarVotes('1', starVotes, totalVotes);
    updateStarVotes('2', starVotes, totalVotes);
    updateStarVotes('3', starVotes, totalVotes);
    updateStarVotes('4', starVotes, totalVotes);
    updateStarVotes('5', starVotes, totalVotes);
  }
}

function updateStarVotes(star, starVotes, totalVotes) {
  var percentElem = document.getElementById('percent' + star);
  var tdElem = document.getElementById('td' + star);
  var divElem = document.getElementById('div' + star);
  var parenElem = document.getElementById('paren' + star);
  if (starVotes[star]) {
    var numVotes = parseInt(starVotes[star])
    starPercentage = (numVotes/totalVotes) * 100;
    starPercentage = starPercentage.toFixed(2);
    percentElem.innerHTML = starPercentage + '%';
    tdElem.title = starPercentage + '%';
    divElem.style.width = starPercentage + '%';
    parenElem.innerHTML = '(' + starVotes[star] + ')';
  } else {
    percentElem.innerHTML = '';
    tdElem.title = '';
    divElem.style.width = '0%';
    parenElem.innerHTML = '';
  }
}

function main() {
  if (wave && wave.isInWaveContainer()) {
    wave.setStateCallback(stateChanged);
  }
}
gadgets.util.registerOnLoadHandler(main);
