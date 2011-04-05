selected = "false"

function showWriteCommentsForm() {
  document.getElementById('write_comment').style.display = 'block';
  document.getElementById('write_comment_link').style.display = 'none';
  document.getElementById('errmsg').style.display = "block";
}

function clearReviewForm() {
  document.getElementById('write_comment').style.display = 'none';
  document.getElementById('write_comment_link').style.display = 'block';
  selected = "false"
  for (var i=1; i <= 5; i++ ) {
       var img_id = "star" + i;
       document.getElementById(img_id).src = "/static/img/small_star_off.gif";
  }
  document.getElementById('errmsg').style.display = "none";
}

function setStars(num_stars) {
  document.getElementById('star_value').value = num_stars;
  selected ="true";
  for (var i=1; i <= num_stars; i++ ) {
      var img_id = "star" + i;
      document.getElementById(img_id).src = "/static/img/small_star_on.gif";
  }
  
  for (var j = 5; j > num_stars; j--) {
     var img_id = "star" + j;
     document.getElementById(img_id).src = "/static/img/small_star_off.gif";
  }
}

function showStars(num_stars) {
  if (num_stars == '0' && selected == "false") {
     for (var i=1; i <= 5; i++ ) {
       var img_id = "star" + i;
       document.getElementById(img_id).src = "/static/img/small_star_off.gif";
     }
  }
  else if (selected == "false") {
    for (var i=1; i <= num_stars; i++ ) {
      var img_id = "star" + i;
      document.getElementById(img_id).src = "/static/img/small_star_on.gif";
    }
  }
}

function updateCommentAuthor(){
  document.getElementById('nickname').value = "Anonymous";
}

function updateEditStatus(type){
  
  if (type == "thumbnail") {
    document.getElementById('updatethumb').value = "True";
  }
  else if (type == "ss") {
    document.getElementById('updatess').value = "True"; 
  }
}
  
function share () {
  var a=document, b=a.createElement('script'),w=window,g={};g.altWindow=w.open('','_blank','height=370px,width=720px,toolbar=no,directories=no,status=no,menubar=no,scrollbars=no,resizable=no');setTimeout(function(){g.altWindow.focus()},1000);function f(o){try{var d=new google.share.EmailWidget(g);d.display()}catch(e){if(o>20)return;setTimeout(function(){f(o+1)},o<10?1<<o:1000)}};b.src='http://www.google.com/s2/sharing/js?script=socialsharing&key=AAAAJ--gdtJYHC_fJptEAHT5Bf3CyVkKtkTsgXiSRui1pjdmzEX0QZeihel6NJ-1FJBvOg';a.body.appendChild(b);f(0)}

