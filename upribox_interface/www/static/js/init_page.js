/**
 * On document ready
 */
$(function() {
    INIT_JOBS.Main.init();
});
/**
 * upribox Modules
 */
// Namespace
var INIT_JOBS = INIT_JOBS || {};
/**
 * Main Module
 */
INIT_JOBS.Main = (function($) {
    'use strict';
    /** Private */

    var pollingTimeout = 300;

     /**
     * Gets executed when the user closes the modal dialog
     */
    function clearJobStatus(e) {

        if(e) {
            e.preventDefault();
        }
        var href= $('body').attr('data-clear-url');

        $.ajax({
            context: this,
            url: href,
            dataType: 'json',
            data: {'csrfmiddlewaretoken': Cookies.get('csrftoken')},
            type: 'post',

            success: function (data) {
                $(this).closest('.js-modal').remove();

                //reload main content if refesh url was given
                var refreshUrl = $(".init_jobs").attr('data-refresh-url');
                console.log(refreshUrl);
                window.location.replace(refreshUrl);
            },

            //retry in case of error
            error: function(jqXHR, textStatus, errorThrown){
                console.log("message clearing failed: " + textStatus)
                setTimeout(clearJobStatus, pollingTimeout);
            }

        });
    }
    /**
     * Poll the server for info about tasks in queue
     */
    function pollJobStatus() {

        var href= $('body').attr('data-poll-messages-url');

        $.ajax({
            url: href,
            dataType: 'json',
            data: {'csrfmiddlewaretoken': Cookies.get('csrftoken')},
            type: 'post',

            success: function (data) {
                if(data.status === 'done'){
                     clearJobStatus();
                }else{
                    setTimeout(pollJobStatus, pollingTimeout);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){
                var errorUrl = $(".init_jobs").attr('data-error-url');
                // window.location.replace(errorUrl);

                //if we are not logged in, we get redirected to /login
                //in this case, stop retrying
                if(jqXHR.status == 200 && errorThrown instanceof SyntaxError){
                    return
                }

                setTimeout(pollJobStatus, pollingTimeout);
            }

        });
    }

    /** Public */
    return {
        /**
         * Initialize
         * Call DOM preparation and call event listener setup
         */
        init: function() {
            pollJobStatus();
        }
    }
}(jQuery));
