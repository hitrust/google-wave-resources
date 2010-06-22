var sharedMap;
var waveMode, oldWaveMode;
var key = "ABQIAAAAzr2EBOXUKnm_jVnk0OJI7xSosDVG8KKPE1-m51RBrvYughuyMxQ-i1QfUnH94QxWIa6N4U6MouMmBA";
var stateCallbacks = 0;

/** Initialises the Gadget, initialises all of the global variables, sets
 *  the state according to the UserPrefs, adds all of the required panels
 *  to the map, registers all of the initial even hiandlers.
 */
function initialize() {
  wave.setStateCallback(receiveState, this);
  wave.setModeCallback(receiveMode, this);
  gadgets.window.adjustHeight(410);
  wave.ui.loadCss();
}

function receiveState(state) {
  var initialCallback;

  if (!sharedMap) {
    initialCallback = true;
    sharedMap = new SharedMap("map_canvas");
    modeSwitch();
  }

  var maptypes = {'m': G_NORMAL_MAP, 'k': G_SATELLITE_MAP, 'h': G_HYBRID_MAP, 'p': G_PHYSICAL_MAP};
  var maptype = getState('maptype');
  if (maptype) {
    var maptypeConstant = maptypes[maptype];
    sharedMap.sharedMapType = maptypeConstant;
    if (sharedMap.map.getCurrentMapType() != maptypeConstant) {
       sharedMap.map.setMapType(maptypeConstant);
    }
  }

  // sync overlays
  var allKeys = state.getKeys();
  for (var i = 0; i < allKeys.length; i++) {
    var key = allKeys[i];
    if (key.indexOf("overlay") > -1) {
      var geometryData = JSON.parse(state.get(key));
      if (sharedMap.geometries[key]) { // already placed, just update
        // update
        // only update if data has changed
        var geometry = sharedMap.geometries[key];
        // Something changed
        if (geometry.getName() != geometryData.name) {
          geometry.setName(geometryData.name);
          geometry.updateNameField(geometryData.name);
        }
        if (geometry.getDescription() != geometryData.description) {
          geometry.setDescription(geometryData.description);
          geometry.updateDescriptionField(geometryData.description);
        }
        if (geometry.isPoint()) {
          if (JSON.stringify(geometry.getCoordinatesArray()) != JSON.stringify(geometryData.coordinates)) {
            var latlng = new GLatLng(geometryData.coordinates[0].lat, geometryData.coordinates[0].lng);
            geometry.getOverlay().setLatLng(latlng);
            geometry.updateCoordinatesFromOverlay();
          }
        } else {
          // If not being edited at the time, re-create overlay
          if (JSON.stringify(geometry.getCoordinatesArray()) != JSON.stringify(geometryData.coordinates)) {
            if (!geometry.getEditable()) {
              sharedMap.map.removeOverlay(geometry.getOverlay());
              geometry.createOverlay();
              geometry.updateCoordinatesFromOverlay();
            }
          }
        }  
      } else {
        sharedMap.createGeometryFromData(key, geometryData);
      }
    }
  }

  // Remove deleted overlays
  for (geometryKey in sharedMap.geometries) {
    var geometry = sharedMap.geometries[geometryKey]; 
    if (!state.get(geometryKey) & geometry.notSavedYet == false) {
      sharedMap.map.removeOverlay(geometry.getOverlay());
      sharedMap.geometries[geometryKey] = null;
    }
  }

  if (allKeys.length == 0) {
    var dialogDiv = document.getElementById('dialog');
    wave.ui.makeDialog(dialogDiv, 'Welcome!');
    dialogDiv.style.display = 'block';
    var lat = null;
    var lng = null;
    if (google.loader.ClientLocation) {
      lat = google.loader.ClientLocation.latitude;
      lng = google.loader.ClientLocation.longitude;
    } else {
      lat = geoplugin_latitude();
      lng = geoplugin_longitude();
    }
    if (lat && lng && !sharedMap.sharedCenter_) {
      if (sharedMap.statusControl) {
        sharedMap.statusControl.setText('<a href="http://www.geoplugin.com/" target="_blank">Geolocation by geoPlugin</a>');
      }
      sharedMap.map.setCenter(new GLatLng(lat, lng), 12);
      sharedMap.saveCenter();
    }
  }

  var center = getState('center'); 
  if (center) {
    center = JSON.parse(center);
    sharedMap.sharedCenter_ = new GLatLng(center[0], center[1]);
    sharedMap.sharedZoom_ = parseInt(JSON.parse(getState('zoom')), 10);
    if (sharedMap.geometries.length == 0) { 
      sharedMap.map.setCenter(sharedMap.sharedCenter_, sharedMap.sharedZoom_);
    }
  }
  if (initialCallback) { 
    sharedMap.zoomAll_();
  }
}

function log(string) {
  if (wave.log) {
    wave.log("FROM MAPS GADGET " + string);

  }
}

Geometry = function () {
  this.name = '';
  this.description = '';
  this.coordinates = [];
  this.type = null;
  this.userId = null;
  this.map = null;
};

Geometry.prototype.setName = function(name) {
  this.name = name;
}

Geometry.prototype.getName = function() {
  return this.name;
}

Geometry.prototype.setDescription = function(description) {
  this.description = description;
}

Geometry.prototype.getDescription = function() {
  return this.description;
}

Geometry.prototype.setCoordinates = function(coordinates) {
  this.coordinates = coordinates;
}

Geometry.prototype.addCoordinates = function(latlng) {
  this.coordinates.push(latlng);
}

Geometry.prototype.getCoordinates = function() {
  return this.coordinates;
}

Geometry.prototype.setType = function(type) {
  this.type = type;
}

Geometry.prototype.getType = function(type) {
  return this.type;
}

Geometry.prototype.setUserId = function(userId) {
  this.userId = userId;
}

Geometry.prototype.getUserId = function() {
  return this.userId;
}

Geometry.prototype.setKey = function(key) {
  this.key = key;
}

Geometry.prototype.getKey = function() {
  return this.key;
}

Geometry.prototype.createKey = function() {
 var newDate = new Date();
 this.key = "overlay-" + newDate.getTime();
}

Geometry.prototype.getCoordinatesArray = function() {
  var coordinates = [];
  for (var i = 0; i < this.getCoordinates().length; i++) {
    var coord = {lat: this.getCoordinates()[i].lat(),
                 lng: this.getCoordinates()[i].lng()}
    coordinates.push(coord);
  }
  return coordinates;
}

Geometry.prototype.getDataString = function() {
  var data = {
    'name': this.getName(),
    'description': this.getDescription(),
    'coordinates': this.getCoordinatesArray(),
    'type': this.getType(),
    'userId': this.getUserId()
  }
  return JSON.stringify(data);
}

Geometry.TYPE_POINT = 'point';
Geometry.TYPE_LINE = 'line';
Geometry.TYPE_POLY = 'poly';
Geometry.COLOR_EDIT = '#188629';
Geometry.COLOR_VIEW = '#0000ff';
Geometry.MARKER_EDIT = 'http://chart.apis.google.com/chart?cht=mm&chs=32x32&chco=21b631,21c739,FFFFFF&ext=.png';
Geometry.MARKER_VIEW = 'http://chart.apis.google.com/chart?cht=mm&chs=32x32&chco=77D5F7,0078AE,77D5F7&ext=.png';

Geometry.prototype.setSharedMap = function(map) {
  this.map = map;
}


Geometry.prototype.getSharedMap = function() {
  return this.map;
}

Geometry.prototype.getOverlay = function() {
  return this.overlay;
}

Geometry.prototype.createOverlay = function() {
  var overlay;
  var me = this;
  if (this.isPoint()) {
    var icon = new GIcon(G_DEFAULT_ICON);
    icon.image = Geometry.MARKER_VIEW;
    icon.iconSize = new GSize(32, 32);
    icon.shadowSize = new GSize(51, 32);
    icon.iconAnchor = new GPoint(16, 32);
    icon.infoWindowAnchor = new GPoint(16, 2);
    icon.infoShadowAnchor = new GPoint(18, 25);
    if (this.getEditable()) {
      icon.image = Geometry.MARKER_EDIT;
    }
    overlay = new GMarker(this.getCoordinates()[0], {draggable: true, icon: icon});
    overlay.disableDragging();
    GEvent.addListener(overlay, 'dragstart', function() {
      me.updateDataFromFields();
      me.getSharedMap().map.closeInfoWindow();
    });
    GEvent.addListener(overlay, 'dragend', function() {
      me.updateCoordinatesFromOverlay();
      me.showInfoWindow();
    });
  } else {
    var latlngs = [];
    for (var i = 0; i < this.getCoordinates().length; i++) {
      latlngs.push(this.getCoordinates()[i]);
    }
    var color = Geometry.COLOR_VIEW;
    if (this.getEditable()) {
      color = Geometry.COLOR_EDIT;
    }
    if (this.getType() == Geometry.TYPE_LINE) {
      overlay = new GPolyline(latlngs, color);
    } else {
      overlay = new GPolygon(latlngs, color, 2, 1.0, color, .2);
    }
    GEvent.addListener(overlay, 'endline', function() {
      me.updateCoordinatesFromOverlay();
      me.getSharedMap().lineBeingEditedNow = false;
      me.showInfoWindow();
      me.saveData();  
      GEvent.trigger(me.getSharedMap().editControl, 'view');
    });
    GEvent.addListener(overlay, 'lineupdated', function() {
      me.updateCoordinatesFromOverlay();
      var sharedMap = me.getSharedMap();
      if (sharedMap.mode == 'line' || sharedMap.mode == 'poly') {
        sharedMap.statusControl.setText('Click on the final point to finish the line.');
      }
      me.saveData();
     });
  }
  GEvent.addListener(overlay, 'click', function() {
    me.showInfoWindow();
  });
  this.overlay = overlay;
}


Geometry.prototype.getData = function() {
  return this.data;
}

Geometry.prototype.getType = function() {
  return this.type;
}

Geometry.prototype.setEditable = function(editable) {
  this.editable = editable;
}

Geometry.prototype.getEditable = function() {
  return this.editable;
}

Geometry.prototype.updateLatLng = function(lat, lng) {
  if (this.getType() != Geometry.TYPE_POINT) {
    return;
  } 
  this.getOverlay().setLatLng(new GLatLng(lat, lng));
}

Geometry.prototype.isPoint = function() {
  return this.getType() == Geometry.TYPE_POINT;
}

Geometry.prototype.isPoly = function() {
  if (this.getType() == Geometry.TYPE_LINE || this.getType() == Geometry.TYPE_POLY) {
    return true;
  } else {
    return false;
  }
}

Geometry.prototype.startEditingOverlay = function() {
  this.setEditable(true);
  if (this.isPoly()) {
    if (this.getOverlay().getVertexCount() == 1) {
      this.getOverlay().enableDrawing();
    }  else {
      this.getOverlay().enableEditing();
    }
    this.getOverlay().setStrokeStyle({color: Geometry.COLOR_EDIT});
    if (this.getType() == Geometry.TYPE_POLY) {
      this.getOverlay().setFillStyle({color: Geometry.COLOR_EDIT});
    }
  } else {
    this.getOverlay().enableDragging();
    this.getOverlay().setImage(Geometry.MARKER_EDIT);
    this.showInfoWindow();
  }
}

Geometry.prototype.disableEditingOverlay = function() {
  this.setEditable(false);
  if (this.isPoint()) {
    this.getOverlay().disableDragging();
    this.getOverlay().setImage(Geometry.MARKER_VIEW);
  } else {
    this.getSharedMap().lineBeingEditedNow = false;
    this.getOverlay().disableEditing();  
    this.getOverlay().setStrokeStyle({color: Geometry.COLOR_VIEW});
    if (this.getType() == Geometry.TYPE_POLY) {
      this.getOverlay().setFillStyle({color: Geometry.COLOR_VIEW});
    }
    GEvent.clearListeners(this.getOverlay(),  'mouseover');
    GEvent.clearListeners(this.getOverlay(),  'mouseout');
  }
}

Geometry.prototype.getFieldId = function(label, suffix) {
  return this.key + (label) + (suffix || '_input');
}

Geometry.prototype.updateNameField = function(name) {
  var fieldId = this.getFieldId('name');
  if (document.getElementById(fieldId)) {
    document.getElementById(fieldId).value = name;
  }
}

Geometry.prototype.updateDescriptionField = function(description) {
  var fieldId = this.getFieldId('description');
  if (document.getElementById(fieldId)) {
    document.getElementById(fieldId).value = description;
  }
}

Geometry.prototype.updateNameFromField = function() {
  var fieldId = this.getFieldId('name');
  var fieldValue = document.getElementById(fieldId).value;
  this.setName(fieldValue);
}

Geometry.prototype.updateDescriptionFromField = function() {
  var fieldId = this.getFieldId('description');
  var fieldValue = document.getElementById(fieldId).value;
  this.setDescription(fieldValue);
}

Geometry.prototype.updateCoordinatesFromOverlay = function() {
  if (this.isPoint()) {
    this.setCoordinates([this.getOverlay().getLatLng()]);
  } else {
    this.setCoordinates([]);
    for (var i = 0; i < this.getOverlay().getVertexCount(); i++) {
      this.addCoordinates(this.getOverlay().getVertex(i));
    }
  }
}


Geometry.prototype.updateDataFromFields = function() {
  this.updateNameFromField();
  this.updateDescriptionFromField();
}

Geometry.prototype.saveData = function(deleteIt) {
  if (deleteIt) {
    saveState(this.getKey(), null);
  } else {
    saveState(this.getKey(), this.getDataString());
  }
}

Geometry.prototype.saveAndClose = function () {
  this.updateDataFromFields();
  this.saveData();
  this.disableEditingOverlay();
  this.setEditable(false);
  this.getSharedMap().map.closeInfoWindow();
}

Geometry.prototype.getLatLng = function() {
  if (this.isPoly()) {
    return this.getOverlay().getBounds().getCenter();
  } else {
    return this.getOverlay().getLatLng();
  }
}

Geometry.prototype.showInfoWindow = function() {
  // close info window
  if (this.getEditable()) {
    this.showEditWindow();
  } else {
    this.showViewWindow();
  }
}

Geometry.prototype.showEditWindow = function() {
  var me = this;
  var div = document.createElement('div');
  div.style.width = '200px';
  var formDiv = this.createForm();
  div.appendChild(formDiv);
  this.openInfoWindow(div);
}

Geometry.prototype.showViewWindow = function() {
  var me = this;
  var div = document.createElement('div');
  div.style.width = '200px';
  var viewDiv = this.createView();
  div.appendChild(viewDiv);

  var editButton = SharedMap.createButton('Edit');
  GEvent.addDomListener(editButton, 'click', function() {
    me.startEditingOverlay();
    me.showEditWindow();
  });
  div.appendChild(editButton);
  this.openInfoWindow(div);
}


Geometry.prototype.openInfoWindow = function(div) {
  if (this.isPoint()) {
    this.getOverlay().openInfoWindow(div);
  } else {
    this.getSharedMap().map.openInfoWindow(this.getLatLng(), div);
  }
}

SharedMap = function(id) {
  this.map = null;
  this.mapDiv = document.getElementById(id);
  this.geometries = {};
  this.createMap();
};


SharedMap.prototype.createMap = function() {
  var me = this;
  var opts = 
    {showOnLoad: true,
     onGenerateMarkerHtmlCallback: function(marker, html, result) {
         return me.extendMarker(me, marker, html, result);
       }
     };
  this.map = new GMap2(this.mapDiv, {googleBarOptions: opts});
  this.map.setCenter(new GLatLng(37, -122));
  this.map.addControl(new GMapTypeControl());
  this.map.addControl(new GSmallZoomControl());
  
  //TODO: Add button for zoom all

  GEvent.addListener(this.map, 'click', function(overlay, latlng) {
    if (overlay) {
      return;
    }
    if (me.mode == 'view') {
      return;
    }
    if (me.lineBeingEditedNow) {
      return;
    }
    // Disable any lines still in edit mode
    me.processGeometries(function(geometry) {
      geometry.disableEditingOverlay();
    });
    // Create either a new marker or a new line, depending on mode
    var geometry = new Geometry();
    geometry.setSharedMap(me);
    geometry.setUserId(wave.getViewer().getId());
    geometry.setType(me.mode);
    geometry.createKey();
    geometry.setCoordinates([latlng]);
    geometry.setEditable(true);
    geometry.createOverlay();
    me.map.addOverlay(geometry.getOverlay());
    me.geometries[geometry.getKey()] = geometry;
    if (geometry.isPoly()) {
      me.lineBeingEditedNow = true;
    } 
    geometry.startEditingOverlay();
  });

  GEvent.addListener(this.map, 'zoomend', function() {
    if (inEditing() && me.geometries.length == 0) {
      var state = wave.getState();
      state.submitDelta({'center': JSON.stringify([me.map.getCenter().lat(), me.map.getCenter().lng()]),
       'zoom': me.map.getZoom() + ""});
    }
   });

  GEvent.addListener(this.map, 'dragend', function() {
    if (inEditing() && me.geometries.length == 0) {
      me.saveCenter();
    }
  });
  GEvent.addListener(this.map, 'maptypechanged', function() {
     if (inEditing()) {
       var state = wave.getState();
       state.submitDelta({'maptype': me.map.getCurrentMapType().getUrlArg()});
     }
  });

  modeSwitch();
};

SharedMap.prototype.zoomAll_ = function() {
  var me = this;
  var bounds = me.getBoundsForAll_();
  if (!bounds.isEmpty()) {
    me.map.setCenter(bounds.getCenter());
    me.map.setZoom(me.map.getBoundsZoomLevel(bounds)-1);
  }
}

SharedMap.prototype.getBoundsForAll_ = function() {
  var me = this;
  var bounds = new GLatLngBounds();
  for (var geometryKey in me.geometries) {
    var geometry = me.geometries[geometryKey];
    if (geometry.isPoint()) {
      bounds.extend(geometry.getOverlay().getLatLng());
    } else {
      bounds.extend(geometry.getOverlay().getBounds().getSouthWest());
      bounds.extend(geometry.getOverlay().getBounds().getNorthEast());
    }
  }
  return bounds;
}


SharedMap.prototype.saveCenter = function() {
  var me = this;
  var state = wave.getState();
  state.submitDelta({'center': JSON.stringify([me.map.getCenter().lat(), me.map.getCenter().lng()]),
       'zoom': me.map.getZoom() + ""});
}

SharedMap.prototype.removeEditingUI_ = function() {
  var me = this;
  if (this.editControl) {
    this.map.removeControl(this.editControl);
    this.editControl = null;
  }
  if (this.statusControl) {
    this.map.removeControl(this.statusControl);
  }
  this.statusControl = new StatusControl();
  this.map.addControl(this.statusControl, new GControlPosition(G_ANCHOR_BOTTOM_LEFT, new GSize(65, 5)));
  this.statusControl.setText('Now in view mode. To edit, place blip in edit mode (CTRL+E).');

  this.map.disableGoogleBar();
  this.processGeometries(function(geometry) {
    geometry.disableEditingOverlay();
  });
}

SharedMap.prototype.addEditingUI = function() {
  var me = this;

  if (this.statusControl) {
    this.map.removeControl(this.statusControl);
  }
  this.editControl = new EditControl();
  this.map.addControl(this.editControl);
  this.statusControl = new StatusControl();
  this.map.addControl(this.statusControl);
  editControl = this.editControl;
  this.map.enableGoogleBar();
  GEvent.addListener(editControl, 'view', function() {
    me.mode = 'view';
    me.editingNow = false;
    me.resetStatusText();
    editControl.highlightButton(me.mode);
  });
  GEvent.addListener(editControl, 'point', function() {
    me.mode = 'point';
    me.editingNow = false;
    me.resetStatusText();
    editControl.highlightButton(me.mode);
  });
  GEvent.addListener(editControl, 'line', function() {
    me.mode = 'line';
    me.editingNow = false;
    me.resetStatusText();
    editControl.highlightButton(me.mode);
  });
  GEvent.addListener(editControl, 'poly', function() {
    me.mode = 'poly';
    me.editingNow = false;
    me.resetStatusText();
    editControl.highlightButton(me.mode);
  });
  GEvent.trigger(editControl, 'view');
}

SharedMap.prototype.resetStatusText = function() {
  var me = this;
  switch (me.mode) {
    case 'view':
      me.statusControl.setText(null);
      break;
    case 'point':
      me.statusControl.setText('Click on the map to create a new marker.');
      break;
    case 'line':
      me.statusControl.setText('Click on the map to start creating a new line.');
      break;
    case 'poly':
      me.statusControl.setText('Click on the map to start creating a new filled poly.');
      break;
  }
};


SharedMap.prototype.processGeometries = function(fn) {
  for (var geometryKey in this.geometries) {
    fn.call(this, this.geometries[geometryKey]);
  }
}


Geometry.prototype.createTableRow = function(label, value, isFinal) {
  var me = this;
  var div = document.createElement('div');
  var labelEl = document.createElement('label');
  labelEl.className = 'label';
  labelEl.innerHTML = label;
  div.appendChild(labelEl);
  div.appendChild(document.createElement('br'));
  var valueInput = document.createElement('input');
  valueInput.type = 'text';
  valueInput.value = value;
  valueInput.id = this.getFieldId(label.toLowerCase(), '_input');

  valueInput.onblur = function() {
    me.updateDataFromFields();
  }

  if (isFinal) {
    valueInput.onkeypress = function(e) {
      var keycode;
      if (window.event) {
        keycode = window.event.keyCode;
      } else if (e) {
       keycode = e.which;
      }
      if (keycode == 13) {
        GEvent.trigger(me.getSharedMap().editControl, 'view');
      }
   };
  }
  valueInput.focus();
  div.appendChild(valueInput);
  return div;
}

Geometry.prototype.createView = function() {
  var html = [];
  var participant = wave.getParticipantById(this.getUserId());
  html.push('<div class="byline">');
  if (participant) {
    html.push('<img src="' + participant.getThumbnailUrl() + '" width="20" height="20">&nbsp;');
    html.push(participant.getDisplayName());
  } else {
    html.push(this.getUserId());
  }
  html.push(':</div>');
  html.push('<b><span id="' + this.getFieldId('name') + '">' + this.getName() + '</span></b><br>');
  html.push('<span id="' + this.getFieldId('description') + '">' + this.getDescription() + '</span><br>');
  html.push('<p>');
  if (this.isPoint()) {
    var title = this.getName();
    var latlng = this.getCoordinates()[0];
    var ll = latlng.lat() + ',' + latlng.lng();
    var ddUrl = 'http://maps.google.com/maps?saddr=&daddr=' + ll + '+(' + title + ')';
    html.push('<a target="_blank" href="' + ddUrl + '">Directions</a> | ');
    var cbUrl = 'http://maps.google.com/maps?cbll=' + ll + '&layer=c&cbp=12,180,,0,5';
    html.push('<a target="_blank" href="' + cbUrl + '">Street View</a> | ');
    html.push('<a target="_blank" href="javascript:sharedMap.map.setCenter(new GLatLng(' + ll + '), 18)">Zoom In</a>');
    html.push('</p>');
  }
  var div = document.createElement('div');
  div.className += ' sidebarview';
  div.innerHTML = html.join('');
  return div;
}

Geometry.prototype.createForm = function(parent_div) {
  var me = this;

  var div = document.createElement('div');
  div.className = 'sidebaredit';
  div.appendChild(me.createTableRow('Name', this.getName()));
  div.appendChild(me.createTableRow('Description', this.getDescription(), true));
 
  var saveButton = SharedMap.createButton('Done');
  saveButton.onclick = function() {
    me.saveAndClose();
    GEvent.trigger(me.getSharedMap().editControl, 'view');
  };
  div.appendChild(saveButton);
  div.appendChild(document.createTextNode(' '));
  var deleteButton = SharedMap.createButton('Delete');
  deleteButton.onclick = function() {
    me.saveData(true);
    me.disableEditingOverlay();
    me.getSharedMap().map.closeInfoWindow();
    me.getSharedMap().map.removeOverlay(me.getOverlay());
  };
  div.appendChild(deleteButton);
  div.appendChild(document.createElement('br'));
  div.appendChild(document.createElement('br'));
  var span = document.createElement('span');
  span.innerHTML = 'You can now drag the green marker to change the location.';
  div.appendChild(span);
  return div;
};

SharedMap.createButton = function(label) {
 var button = document.createElement('a');
 button.href = 'javascript:void(0)';
 button.innerHTML = label;
 wave.ui.makeButton(button);
 return button;
}

SharedMap.prototype.createGeometryFromData = function(key, data) {
  var me = this;
  var geometry = new Geometry();
  geometry.setName(unescape(data.name));
  geometry.setDescription(unescape(data.description));
  var coordinates = data.coordinates;
  for (var i = 0; i < coordinates.length; i++) {
    geometry.addCoordinates(new GLatLng(coordinates[i].lat, coordinates[i].lng));
  }
  geometry.setType(data.type);
  geometry.setUserId(data.userId);
  geometry.setSharedMap(me);
  geometry.setKey(key);
  geometry.createOverlay();
  me.map.addOverlay(geometry.getOverlay());
  me.geometries[geometry.getKey()] = geometry;
}

SharedMap.prototype.extendMarker = function(gs, marker, html, result) {
  var me = this;
  // extend the passed in html for this result
  // http://code.google.com/apis/ajaxsearch/documentation/reference.html#_class_GlocalResult
  var div = document.createElement('div');
  var button = SharedMap.createButton('Copy to map');
  button.onclick = function() {
    var geometry = new Geometry();
    geometry.setName(result.titleNoFormatting);
    if (result.titleNoFormatting != result.streetAddress) {
      geometry.setDescription(result.streetAddress);
    }
    geometry.setType(Geometry.TYPE_POINT);
    geometry.setUserId(wave.getViewer().getId());
    geometry.setSharedMap(me);
    geometry.createKey();
    geometry.addCoordinates(marker.getLatLng());
    geometry.createOverlay();
    me.map.addOverlay(geometry.getOverlay());
    me.geometries[geometry.getKey()] = geometry;
    marker.closeInfoWindow();
    marker.hide();
    geometry.showInfoWindow();
  };

  div.appendChild(html);
  div.appendChild(document.createElement('br'));
  div.appendChild(button);
  return div;
};
 
function EditControl() {
}

EditControl.prototype = new GControl();

EditControl.prototype.initialize = function(map) {
  var me = this;
  me.buttons = {};
 
  var controlDiv = document.createElement('div'); 
  var controlTable = document.createElement('table');
  var controlTR = document.createElement('tr');
  
  var viewOptions = {imgUrl: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bsu.png',
                 imgHoverUrl: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bsd.png',
                 id: 'view'};
  var viewButton = this.createButton(viewOptions);
  var viewTD = document.createElement('td');
  viewTD.appendChild(viewButton.img);

  var markerOptions = {imgUrl: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bmu.png',
                 imgHoverUrl: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bmd.png',
                 id: 'point', tooltip: 'Click on the map to create a new marker.'};
  var markerButton = this.createButton(markerOptions);
  var markerTD = document.createElement('td');
  markerTD.appendChild(markerButton.img);

  var lineOptions = {imgUrl: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Blu.png',
                 imgHoverUrl: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bld.png',
                 id: 'line', tooltip: 'Click on the map to start creating a new line.'};
  var lineButton = this.createButton(lineOptions);
  var lineTD = document.createElement('td');
  lineTD.appendChild(lineButton.img);

  var polyOptions = {imgUrl: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bpu.png',
                 imgHoverUrl: 'http://www.google.com/intl/en_us/mapfiles/ms/t/Bpd.png',
                 id: 'poly', tooltip: 'Click on the map to start creating a new filled poly.'};
  var poly_button = this.createButton(polyOptions);
  var polyTD = document.createElement('td');
  polyTD.appendChild(poly_button.img);

  controlTR.appendChild(viewTD);
  controlTR.appendChild(markerTD);
  controlTR.appendChild(lineTD);
  controlTR.appendChild(polyTD);
  controlTable.appendChild(controlTR);
  controlDiv.appendChild(controlTable);
  GEvent.trigger(viewButton.img, 'click');
  map.getContainer().appendChild(controlDiv);
  return controlDiv;
} 
 
EditControl.prototype.createButton = function(buttonOptions) {
  var me = this;
  var button = {};
  button.opts = buttonOptions;

  var buttonImg = document.createElement('img');
  buttonImg.style.cursor = 'pointer';
  buttonImg.width = '33';
  buttonImg.height = '33';
  buttonImg.border = '0';
  buttonImg.src = buttonOptions.imgUrl;
  buttonImg.id = buttonOptions.id + '_control';
  GEvent.addDomListener(buttonImg, 'click', function() { 
    me.highlightButton(buttonOptions.id);
    GEvent.trigger(me, buttonOptions.id);
  });  

  button.img = buttonImg;
  me.buttons[buttonOptions.id] = button;
  return button;
}

EditControl.prototype.highlightButton = function(selectedButtonId) {
  for (var buttonId in this.buttons) {
    this.buttons[buttonId].img.src = this.buttons[buttonId].opts.imgUrl;
  }
  this.buttons[selectedButtonId].img.src = this.buttons[selectedButtonId].opts.imgHoverUrl;
}

EditControl.prototype.getDefaultPosition = function() {
  return new GControlPosition(G_ANCHOR_BOTTOM_LEFT, new GSize(306, 0));
}

function StatusControl() {
}

StatusControl.prototype = new GControl();

StatusControl.prototype.initialize = function(map) {
  var me = this;
  var status_div = document.createElement('span');
  status_div.style.color = 'grey';
  status_div.style.backgroundColor = 'white';
  status_div.style.border = '1px solid grey';
  status_div.style.padding = '5px';
  status_div.style.fontSize = '11px';
  this.status_div = status_div;
  map.getContainer().appendChild(status_div);
  return this.status_div;
}

StatusControl.prototype.setText = function(text) {
  if (!text) {
    this.status_div.style.display = 'none';
  } else {
    this.status_div.style.display = 'block';
    this.status_div.innerHTML = text;
  }
}

StatusControl.prototype.getDefaultPosition = function() {
  return new GControlPosition(G_ANCHOR_BOTTOM_LEFT, new GSize(460, 5));
}
 
function saveState(key, value) {
  var state = wave.getState();
  var delta = {};
  delta[key] = value;
  state.submitDelta(delta); 
}

function getState(key) {
  var state = wave.getState();
  return state.get(key);
}

function receiveMode(mode) {
  oldWaveMode = waveMode;
  waveMode = mode;
  // Don't switch if were just going from edit to view or vice versa
  if ((oldWaveMode == wave.Mode.EDIT && waveMode == wave.Mode.VIEW) ||
      (oldWaveMode == wave.Mode.VIEW && waveMode == wave.Mode.EDIT) ||
      (!oldWaveMode)) {
    log('switching');
    log(oldWaveMode);
    log(waveMode);
    modeSwitch();
  }
}

function modeSwitch() {
  if (!waveMode || !sharedMap) return;
  switch (waveMode) {
    case wave.Mode.PLAYBACK:
      sharedMap.removeEditingUI_();
      break;
    case wave.Mode.EDIT:
      sharedMap.addEditingUI();
      break;
    case wave.Mode.VIEW:
      sharedMap.addEditingUI();
      break;
  }
}

function inEditing() {
  return waveMode != wave.Mode.PLAYBACK;
}

google.setOnLoadCallback(initialize);
//TODO: Reinstate GUnload once Chrome bug fixed
