// Stop linting button

$('#delete_repo').api({
    action: 'delete_repo',
    on: 'click',
    method: 'DELETE',
    onSuccess: function() {
      // redirect user
      window.location = '/repos';
    },
    onFailure: function() {
      // Tell user it failed
      window.alert('An error occured while attempting to delete this repo.');
      $('#delete_repo').removeClass('loading');
    }
});

$('#default_branch').dropdown();
$('#settings_modal').modal({
  'autofocus': false,
  'onApprove': function() {
    $('#save_button').addClass('loading');
    $('#settings_form').submit().find('.field').addClass('disabled');
    return false;
  }
});
$('#settings').on('click', function(){
   $('#settings_modal').modal('show');
});
$('.build_row').on('click', function(){
  window.location = this.querySelector('.build_link').href;
});
$('.markdown-body h1, .markdown-body h2, .markdown-body h3, .markdown-body h4, .markdown-body h5, .markdown-body h6')
  .each(function(idx, value) {
    var anchor = '<a id="user-content-'+value.id+'" class="anchor" href="#'+value.id+'" aria-hidden="true"><svg aria-hidden="true" class="octicon octicon-link" height="16" version="1.1" viewBox="0 0 16 16" width="16"><path fill-rule="evenodd" d="M4 9h1v1H4c-1.5 0-3-1.69-3-3.5S2.55 3 4 3h4c1.45 0 3 1.69 3 3.5 0 1.41-.91 2.72-2 3.25V8.59c.58-.45 1-1.27 1-2.09C10 5.22 8.98 4 8 4H4c-.98 0-2 1.22-2 2.5S3 9 4 9zm9-3h-1v1h1c1 0 2 1.22 2 2.5S13.98 12 13 12H9c-.98 0-2-1.22-2-2.5 0-.83.42-1.64 1-2.09V6.25c-1.09.53-2 1.84-2 3.25C6 11.31 7.55 13 9 13h4c1.45 0 3-1.69 3-3.5S14.5 6 13 6z"></path></svg></a>';
    value.innerHTML = anchor + value.innerHTML;
});
$('.markdown-body img').each(function(idx, value) {
  var image_path = 'https://github.com/'+full_name+'/blob/'+branch+'/';
  // value.src is always a full path, even if the actual src is a relative path, so this should always work
  value.src = value.src.replace(base_url, image_path) + '?raw=true';
});
