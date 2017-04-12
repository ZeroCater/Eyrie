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
