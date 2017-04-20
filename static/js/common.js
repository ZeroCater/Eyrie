$('a.ui.button:not(.link)').on('click', function(){
  $(this).addClass('loading');
});
$('#user_dropdown').dropdown();

function getParameterByName(name, url) {
  if (!url) {
    url = window.location.href;
  }
  name = name.replace(/[\[\]]/g, "\\$&");
  var regex = new RegExp("[?&]" + name + "(=([^&#]*)|&|#|$)"),
    results = regex.exec(url);
  if (!results) return null;
  if (!results[2]) return '';
  return decodeURIComponent(results[2].replace(/\+/g, " "));
}

jQuery.fn.highlight = function(pat) {
  function innerHighlight(node, pat) {
    var skip = 0;
    if (node.nodeType == 3) {
      var pos = node.data.toUpperCase().indexOf(pat);
      pos -= (node.data.substr(0, pos).toUpperCase().length - node.data.substr(0, pos).length);
      if (pos >= 0) {
        var spannode = document.createElement('span');
        spannode.className = 'highlight';
        var middlebit = node.splitText(pos);
        var endbit = middlebit.splitText(pat.length);
        var middleclone = middlebit.cloneNode(true);
        spannode.appendChild(middleclone);
        middlebit.parentNode.replaceChild(spannode, middlebit);
        skip = 1;
      }
    }
    else if (node.nodeType == 1 && node.childNodes && !/(script|style)/i.test(node.tagName)) {
      for (var i = 0; i < node.childNodes.length; ++i) {
        i += innerHighlight(node.childNodes[i], pat);
      }
    }
    return skip;
  }
  return this.length && pat && pat.length ? this.each(function() {
    innerHighlight(this, pat.toUpperCase());
  }) : this;
};
