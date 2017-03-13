/**
 * On document ready
 */
$(function() {
    $('html').removeClass('no-js');
    UPRIBOX.Main.init();
});
/**
 * upribox Modules
 */
// Namespace
var UPRIBOX = UPRIBOX || {};
/**
 * Main Module
 */
UPRIBOX.Main = (function($) {
    'use strict';
    /** Private */
    var pageIdentifier = null;
    var $x = 0;
    var xBound = 850;

    var pollingTimeout = 300;
    var wlanWarningTimeout = 30000;

    //Will be set to true if polling timeouts occur
    var upriboxUnreachable = false;

    /**  **/
    /**
     * Setup up event listeners
     */
    function initListeners() {
        /** open and close mobile menue **/
        $('body').on('click', '.js-menu', toggleMenu);
        $(window).resize(checkWindowSize);
        $('body').on('click', '.js-info-trigger', toggleInfo);
        $('body').on('click', '.js-info-trigger', toggleInfoCookie);


        $('body').on('click', '.js-edit-form', function(e) {
             e.preventDefault();
             var inputs = $('.js-form > fieldset > input');
             inputs.attr('disabled',false);
             inputs.first().focus();
             $(this).hide();
             $('.js-abort-form').show();
        });
        $('body').on('click', '.js-abort-form', function(e) {
             e.preventDefault();
             var inputs = $('.js-form > fieldset > input');
             inputs.attr('disabled',true);
             $(this).hide();
             $('.js-edit-form').show();
        });

        $('body').on('click', '.action-qr-show', function() {

            var qrimage = $(this).parent().children('.qr-image');
            var link = $(this).parent().find('a').text();
            qrimage.toggleClass('hidden');
            console.log(link);
            if(qrimage.children().length == 0){
                new QRCode(qrimage.get(0), link);
            }

        });
        $('body').on('click', '.js-delete-profile', function() {
            var href = $(this).attr('href');
            $(this).attr('disabled', true);

            $.ajax({
                url: href,
                dataType: 'json',
                type: 'post',
                context: this,
                data: {'csrfmiddlewaretoken': Cookies.get('csrftoken')},
                success: function (data) {
                    $(this).parents('.column').remove();
                },

            });
        });

        $('body').on('click', '.js-form-submit', function(e) {
            e.preventDefault();
            var href = $(this).attr('href');
            var form = $(this).closest('form');
            $(this).attr('disabled', true);
            updateMainContent(href, 'post', form);
        });

        $('body').on('click', '.js-toggle-button', toggleServiceState);

        $('body').on('click', '#button-vpn-generate', function(e) {
            e.preventDefault();
            $('.js-profile-placeholder').addClass('hidden');

            var href = $(this).attr('href');
            var form = $(this).closest('form');
            $(this).attr('disabled', true);
            $.ajax({
                url: href,
                dataType: 'html',
                data: form.serialize(),
                type: 'post',
                context: this,
                success: function (data) {
                    var response = $(data);
                    $(this).attr('disabled', false);
                    $('#id_profilename').val('');
                    $('#main-content').html($(data));
                    onAjaxUpdate();
                },

            });
        });

        $('body').on('click', '.js-vpn-link-generate', function(e) {
            e.preventDefault();

            var href = $(this).attr('href');
            $(this).attr('disabled', true);
            $.ajax({
                url: href,
                dataType: 'html',
                type: 'post',
                data: {'csrfmiddlewaretoken': Cookies.get('csrftoken')},
                context: this,
                success: function (data) {
                    $(this).parents('.column').replaceWith($(data))
                },

            });
        });

        $('#button-vpn-generate', function() {
            // spawn timer for link timeout countdown, but only if we are on the vpn page
            setInterval(function() {
                $('.js-vpn-timer').each( function(i, el) {
                    var timer = $(el);
                    var seconds = timer.attr('data-vpn-timeout');

                    if(seconds!='timed-out') {
                        if (seconds >= 0) {
                            timer.attr('data-vpn-timeout', seconds - 1);
                            timer.text(formatSeconds(seconds));
                        } else {
                            timer.attr('data-vpn-timeout', 'timed-out');

                            //update profile
                            var href = $(this).attr('data-link-update');
                            $.ajax({
                                url: href,
                                dataType: 'html',
                                type: 'post',
                                data: {'csrfmiddlewaretoken': Cookies.get('csrftoken')},
                                context: this,
                                success: function (data) {
                                    $(this).parents('.column').replaceWith($(data))
                                },

                            });
                        }
                    }
                });
            }, 1000);
        });

        $('body').on('click', '.js-modal-close', clearJobStatus);
    }

    function updateChart() {

        if($('.ct-chart').length ) {
            var href = '/statistics/get';

            $(".loading").show();
            $(".ct-pies").hide();
            $(".ct-chart").hide();
            $(".legend").hide();
            $(".lists").hide();

            $.ajax({
                url: href,
                dataType: 'json',
                data: {'csrfmiddlewaretoken': Cookies.get('csrftoken')},
                type: 'post',

                success: function (chartdata) {
                    var chart_str = JSON.stringify(chartdata, null, 4);
                    console.log(chart_str);

                    drawChart(chartdata);
                    var ol = $('.js-filtered-sites').find('ol');
                    ol.empty();
                    for(var i=0;i<chartdata.filtered_pages.length;i++){
                        var li = $('<li></li>');
                        li.text(chartdata.filtered_pages[i]['url'] + ' - ' + chartdata.filtered_pages[i]['count']);
                        ol.append(li);
                    }
                    var ol = $('.js-blocked-sites').find('ol');
                    ol.empty();
                    for(var i=0;i<chartdata.blocked_pages.length;i++){
                        var li = $('<li></li>');
                        li.text(chartdata.blocked_pages[i]['url'] + ' - ' + chartdata.blocked_pages[i]['count']);
                        ol.append(li);
                    }

                    $(".loading").hide();
                    $(".ct-pies").fadeIn();
                    $(".ct-chart").fadeIn();
                    $(".legend").fadeIn();
                    $(".lists").fadeIn();

                }

            });
        }
    }
    /**
     * Draw Chartist charts
     * @param chartdata
     */
    function drawChart(chartdata) {
        //Chartist js-library (https://gionkunz.github.io/chartist-js/)

        var padding = 15;
        var y_axis_width = Math.max.apply( Math, chartdata.bar_data.series[0].concat(chartdata.bar_data.series[1] ) ).toString().length;
        if (y_axis_width > 4) {
            padding = (y_axis_width - 3) * 10;
        }

        var bar_options = {
            stackBars: true,
            chartPadding: padding,
            axisY: {
                onlyInteger: true
            }
        };

        new Chartist.Bar('.ct-chart', chartdata.bar_data, bar_options);

        var pie1_percentage = 0;
        if (chartdata.pie1_data.series[0] + chartdata.pie1_data.series[1] > 0) {
            pie1_percentage = Math.round((chartdata.pie1_data.series[1] / (chartdata.pie1_data.series[0] + chartdata.pie1_data.series[1]) * 100) * 100) / 100;
        }

        var pie2_percentage = 0;
        if (chartdata.pie2_data.series[0] + chartdata.pie2_data.series[1] > 0) {
            pie2_percentage = Math.round((chartdata.pie2_data.series[1] / (chartdata.pie2_data.series[0] + chartdata.pie2_data.series[1]) * 100) * 100) / 100;
        }

        var pie1_options = {
            donut: true,
            donutWidth: 60,
            width: '300px',
            hight: '300px',
            labelInterpolationFnc: function(value) {
                return value;
            },
            plugins: [
                Chartist.plugins.fillDonut({
                    items: [{
                        content: '<i class="fa fa-tachometer"></i>',
                        position: 'bottom',
                        offsetY : 10,
                        offsetX: -2
                    }, {
                        content: '<h3>' + pie1_percentage + '%<br><span class="small">blocked</span></h3>'
                    }]
                })
            ],
        };

        var pie2_options = {
            donut: true,
            donutWidth: 60,
            width: '300px',
            hight: '300px',
            labelInterpolationFnc: function(value) {
                return value;
            },
            plugins: [
                Chartist.plugins.fillDonut({
                    items: [{
                        content: '<i class="fa fa-tachometer"></i>',
                        position: 'bottom',
                        offsetY : 10,
                        offsetX: -2
                    }, {
                        content: '<h3>' + pie2_percentage + '%<br><span class="small">blocked</span></h3>'
                    }]
                })
            ],
        };

        new Chartist.Pie('.ct-pie1', chartdata.pie1_data, pie1_options);
        new Chartist.Pie('.ct-pie2', chartdata.pie2_data, pie2_options);

        // var options = {
        //     scaleMinSpace: 1000,
        //     showPoint: false,
        //     lineSmooth: false,
        //     axisX: {
        //         showGrid: true,
        //         showLabel: true
        //     },
        //     axisY: {}
        // };
        // new Chartist.Line('.ct-chart', data, options);
    }

    /**
     * Enables or disables a service
     * @param url
     * @param state
     */
    function toggleServiceState(e){
        e.preventDefault();
        var href = $(this).attr('href');
        var state = $(this).attr('data-state-enabled');
        $(this).attr('disabled', true);
        $.ajax({
            url: href,
            dataType: 'html',
            data: {'enabled': state, 'csrfmiddlewaretoken': Cookies.get('csrftoken')},
            type: 'post',
            context: this,
            success: function (data) {
                $('body').append($(data));
                onAjaxUpdate();
                $(this).attr('disabled', false);
            },

        });
    }
    /**
     * Updates the main content with AJAX
     * @param {string} the url to load
     * @param {string} the type (post or get)
     * @param {Object} form data (optional)
     */
    function updateMainContent(href, type, form) {
        $.ajax({
            url: href,
            dataType: 'html',
            data: form? form.serialize(): null,
            type: type,
            success: function (data) {
                $('#main-content').html($(data));
                onAjaxUpdate();
            },

        });
    }

    /**
     * Should be called whenever the site is updated via AJAX (but not from inside pollJobStatus)
     * Also gets executed once on page load
     */
    function onAjaxUpdate() {
        checkInfoCookie();
        pollJobStatus();
    }

    function triggerWlanWarning() {
        //show message if button is still disabled
        if(upriboxUnreachable && $('.js-modal-close').attr('disabled')) {
            $('.js-connection-warning').removeClass('hidden');
        }
    }
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
                var refreshUrl = $(this).attr('data-refresh-url');
                if(refreshUrl){
                    updateMainContent(refreshUrl, 'get');
                }
                console.log('messages cleared')
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

        var href= $('body').attr('data-poll-url');

        $.ajax({
            url: href,
            dataType: 'json',
            data: {'csrfmiddlewaretoken': Cookies.get('csrftoken')},
            type: 'post',

            success: function (data) {
                console.log("queue " + href + " status: " + data.status);
                upriboxUnreachable = false;

                //we received data - hide warning again if visible
                $('.js-connection-warning').addClass('hidden');
                if(data.message){
                    var tag = $('.message').find('ul').first();
                    tag.empty();
                    for(var i=0;i<data.message.length;i++) {
                        var litag = $('<li class="success-message"></li>');
                        tag.append(litag.html(data.message[i]));
                    }
                }

                if(data.status === 'done'){
                    $('.js-modal-close').attr('disabled', false);
                    var tag = $('.message').find('ul').first();
                    var litag = $('<li class="success-message hidden"></li>');
                    tag.append(litag);;
                }else{
                    setTimeout(pollJobStatus, pollingTimeout);
                }
            },
            error: function(jqXHR, textStatus, errorThrown){

                console.log("queue check request failed: " + textStatus);

                //if we are not logged in, we get redirected to /login
                //in this case, stop retrying
                if(jqXHR.status == 200 && errorThrown instanceof SyntaxError){
                    //show warning to user
                    $('.js-session-lost-warning').removeClass('hidden');
                    //if the modal dialog is currently being show and the close button is disabled,
                    //enable it
                    var closebutton = $('.js-modal-close');
                    if(closebutton.attr('disabled')){
                        closebutton.attr('disabled', false);
                        //add a on click listener that reloads the page so the user
                        //gets redirected to the login site
                        closebutton.on('click', function() {
                            location.reload();
                        })
                    }
                    return
                }
                if(!upriboxUnreachable){
                    //Show WLAN switching message after timeout
                    setTimeout(triggerWlanWarning, wlanWarningTimeout);
                }
                upriboxUnreachable = true;
                setTimeout(pollJobStatus, pollingTimeout);
            }

        });
    }

    /**
     * Show/Hide menu in responsive design
     */
    function toggleMenu() {
        $('#site-header nav').toggle();
        $('.js-menu').toggleClass('is-open');
    }
    /**
     * Fallback, if windows gets resized and menu is not visible
     */
    function checkWindowSize() {
        $x = $(window).width();
        if ($x > xBound) $('#site-header nav').show();
    }
    /**
     * Toggle information panel
     * @param {Boolean} true to show, false to hide
     * @returns {Boolean} False to prevent default
     */
    function toggleInfo(state) {
        $('.js-col-2-main').first().toggleClass('is-expanded', state);
        $('.js-col-2-info').last().toggleClass('is-expanded', state);
        $('.i-arrow').toggleClass('is-flipped', state);
        return false;
    }
    /**
     * Check cookies on every page
     *
     */
    function checkInfoCookie() {
        var cookie = Cookies.get(pageIdentifier);
        if (cookie === undefined || cookie === 'true') {
            toggleInfo(true);
        }else{
            toggleInfo(false);
        }
    }
    /**
     * Toggle cookie to hide infobox
     */
    function toggleInfoCookie() {
        var cookie = Cookies.get(pageIdentifier);
        if(cookie == 'true') {
            cookie = false;
        } else {
            cookie = true;
        }
        Cookies.set(pageIdentifier, cookie);
    }

    /**
     * Formats the given seconds as hh:mm:ss
     * @param secs
     * @returns {string}
     */
    function formatSeconds(secs) {
        var sec_num = Math.round(parseInt(secs, 10)); // don't forget the second param
        var hours   = Math.floor(sec_num / 3600);
        var minutes = Math.floor((sec_num - (hours * 3600)) / 60);
        var seconds = sec_num - (hours * 3600) - (minutes * 60);

        if (hours   < 10) {hours   = "0"+hours;}
        if (minutes < 10) {minutes = "0"+minutes;}
        if (seconds < 10) {seconds = "0"+seconds;}
        var time    = minutes+':'+seconds;
        if(hours > 0){
            time = hours+':' + time;
        }
        return time;
    }
    /**
     * Create hash code
     *
     * @param   {string}
     * @returns {Number|string} Number 0 or hashed string.
     *
     * @see {@link http://erlycoder.com/49/javascript-hash-functions-to-convert-string-into-integer-hash|Erly Coder}
     */
    function hashCode(str) {
        var hash = 0;
        if (str.length == 0) return hash;
        for (var i = 0; i < str.length; i++) {
            var char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return hash;
    }

    /** Public */
    return {
        /**
         * Initialize
         * Call DOM preparation and call event listener setup
         */
        init: function() {
            pageIdentifier = 'id-' + hashCode(window.location.pathname).toString();
            initListeners();
            checkInfoCookie();
            pollJobStatus();
            updateChart();
        }
    }
}(jQuery));