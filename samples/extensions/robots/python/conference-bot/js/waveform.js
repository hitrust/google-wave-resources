waveform = {}

waveform.getFormData = function(form) {
  var formData = {};
  for (i = 0; i < form.getElementsByTagName('input').length; i++) {
    elem = form.getElementsByTagName('input')[i];
    if (elem.type == 'text' || elem.type == 'hidden') {
      formData[elem.name] = elem.value;
    }
    if (elem.type == 'checkbox') {
      if (elem.checked) {
        formData[elem.name] = 'on';
      } else {
        formData[elem.name] = '';
      }
    }
    if (elem.type == 'radio') {
      if (elem.checked) {
        formData[elem.name] = elem.value;
      }
    }
    if (elem.type == 'button') {
      if (elem.clicked) {
        var key = elem.name || elem.id;
        formData[key] = 'on';
      }
    }
  }
  for (i = 0; i < form.getElementsByTagName('select').length; i++) {
     var sel = form.getElementsByTagName('select')[i];
     formData[sel.name] = sel.options[sel.selectedIndex].value;
  }
  return formData;
}

waveform.waveEnableForm = function(form) {
  function handleButtonClick(input) {
    input.onclick = function() {
      var key = input.name || input.id || 'button';
      var delta = {}
      // Indicate its been clicked atleast once
      delta[key] = 'clicked';
      // Track each time its clicked
      var key2 = key + '-clicked';
      var clickedBefore = wave.getState().get(key2);
      delta[key2] = (clickedBefore) ? (clickedBefore+1) : 1;
      wave.getState().submitDelta(delta);
    }
  }

  for (i = 0; i < form.getElementsByTagName('input').length; i++) {
    var input = form.getElementsByTagName('input')[i];
    if (input.type == 'button') {
      handleButtonClick(input);
    } else {
      input.onchange = function() {
        waveform.submitFormDelta(form);
      }
    }
  }
  for (i = 0; i < form.getElementsByTagName('select').length; i++) {
    var select = form.getElementsByTagName('select')[i];
    select.onchange = function() {
      waveform.submitFormDelta(form);
    }
  }

  for(j=0, elements = form.elements; j < elements.length; j++) {
    if( /^text/.test(elements[j].type)) {
      elements[j].hasFocus= false;
      elements[j].onfocus = function(){this.hasFocus=true;};
      elements[j].onblur = function(){this.hasFocus=false;};
    }
  }
};

waveform.updateForm = function(form) {
  var keys = wave.getState().getKeys();
  for (var i = 0; i < keys.length; i++) {
    var key = keys[i];
    var elems = document.getElementsByName(key);
    if (elems.length > 0) {
      var elem = elems[0];
      var newValue = wave.getState().get(key)
      if (elem.value != newValue && !elem.hasFocus) {
        elem.value = newValue;
        if (elem.type == 'checkbox' && newValue == 'on') {
          elem.checked = true;
        }
      }
    }
  }
}

waveform.submitFormDelta = function(form) {
  formData = waveform.getFormData(form);
  changedFormData = {}
  for (formName in formData) {
    formValue = wave.getState().get(formName);
    if (formValue != formData[formName]) {
      changedFormData[formName] = formData[formName];
    }
  }
  wave.getState().submitDelta(changedFormData);
}
