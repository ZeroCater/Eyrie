$('a.ui.button:not(.link)').on('click', function(){
    $(this).addClass('loading');
});
$('#user_dropdown').dropdown();
