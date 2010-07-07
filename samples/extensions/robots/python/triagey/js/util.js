function getFormData(form) {
  var getstr = "";
  for (i=0; i<form.getElementsByTagName("input").length; i++) {
    if (form.getElementsByTagName("input")[i].type == "text" || 
        form.getElementsByTagName("input")[i].type == "hidden") {
      getstr += form.getElementsByTagName("input")[i].name + "=" + 
                form.getElementsByTagName("input")[i].value + "&";
    }
    if (form.getElementsByTagName("input")[i].type == "checkbox") {
      if (form.getElementsByTagName("input")[i].checked) {
        getstr += form.getElementsByTagName("input")[i].name + "=" + 
                  form.getElementsByTagName("input")[i].value + "&";
      } else {
        getstr += form.getElementsByTagName("input")[i].name + "=&";
      }
    }
    if (form.getElementsByTagName("input")[i].type == "radio") {
      if (form.getElementsByTagName("input")[i].checked) {
        getstr += form.getElementsByTagName("input")[i].name + "=" + 
                  form.getElementsByTagName("input")[i].value + "&";
      }
    }
  }
  for (i = 0; i < form.getElementsByTagName("select").length; i++) {
     var sel = form.getElementsByTagName("select")[i];
     getstr += sel.name + "=" + sel.options[sel.selectedIndex].value + "&";
  }
  return getstr;
}
