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

    var pollingTimeout = 900;
    var pollingTimeoutCounter = 700;
    var pollingTimeoutStatistics = 4000;
    var wlanWarningTimeout = 30000;

    //Will be set to true if polling timeouts occur
    var upriboxUnreachable = false;

    //forces continuous update of modal dialog (required when modal dialog is opened by user and we want to see new messages)
    var forceContinuousModalUpdate = false;

    //this pauses the counter from updating
    var pauseCounter = false;

    //stores in which mode the modal diaglog currently is
    var modalMode = null;

    //includes the template for a single device entry in device list
    var singleDeviceListHtmlTemplate = null;

    //a list which holds all devices, that are "in progress"
    var deviceInProgressList = {};

    //indicates if polling for devices in progress is running
    var pollingForDevicesInProgress = false;

    //ordered list for devices where the online status has to be checked (this is a queue)
    //var checkOnlineStatusList = {};
    var checkOnlineStatusList = [];


    //key value list for devices, which holds the index of each device from the list above
    //var checkOnlineStatusList = {};
    //var checkOnlineStatusIndexList = {};

    //sets how many devices are polled for their online status at once
    var onlineStatusPolling = 2;

    //sets the index of the last polling element
    var statOnlinePollingLastElementIndex = -1;

    //stores how many devices have already been checked completely for their online status
    var checkedDevicesForOnlineStatusCounter = 0;

    //holds data and layout for the statistics
    var statisticInformation = {
        data: [],
        layout: {}
    };

    //indicates how many weeks should be shown in the plot
    var totalWeeks = 5;

    //holds the calendar-weeks for the single links on the x axis of the plot
    var clickableWeeks = [];

    //holds the last week in the graphic (the one which is updated continuously
    var lastWeek;

    //the DOM Container which holds the plot graphic
    var gd;

    //indicates which week is currently selected
    var currentSelectedWeek = null;

    //indicates which week was clicked on -> when its clicked, it isn't yet the selected week (it becomes the selected week, when the package is received)
    var currentClickedWeek = null;

    //stores the timeout handler for making the tooltips invisible after some time, on mobile devices
    var makeTooltipsDisappearOnMobileTimeoutHandler;

    var refreshURL = false;

    //defining some urls for polling and html rendering-templates

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
            //  var inputs = $('.js-form > fieldset > input');
            var inputs = $(this).closest('.js-form').find('fieldset > input');
            inputs.attr('disabled',false);
            inputs.first().focus();
            $(this).hide();
            $(this).closest('.js-form').find('.js-abort-form').show();
            //  $('.js-abort-form').show();
        });
        $('body').on('click', '.js-abort-form', function(e) {
            e.preventDefault();
            //  var inputs = $('.js-form > fieldset > input');
            var inputs = $(this).closest('.js-form').find('fieldset > input');
            inputs.attr('disabled',true);
            $(this).hide();
            //  $('.js-edit-form').show();
            $(this).closest('.js-form').find('.js-edit-form').show();
        });

        $('body').on('click', '.action-qr-show', function() {

            var qrimage = $(this).parent().children('.qr-image');
            var link = $(this).parent().find('a').text();
            qrimage.toggleClass('hidden');
            //console.log(link);
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
            refreshURL = $("[data-refresh-url]").attr("data-refresh-url"); // || window.location.pathname
            var href = $(this).attr('href');
            var form = $(this).closest('form');
            $(this).attr('disabled', true);
            updateMainContent(href, 'post', form);
        });

        $('body').on('click', '.js-change-devicename', function(e){
            e.preventDefault();
            var href = $(this).attr('href');
            var form = $(this).closest('form');
            $(this).attr('disabled', true);
            var modal = $(this).closest('.js-modal');
            var slug = $(this).attr('data-slug');

            $.ajax({
                url: href,
                dataType: 'html',
                data: form? form.serialize(): null,
                type: 'post',
                success: function (data) {
                    modal.remove();
                    $("#" + slug + " .devname").text(data);
                    // onAjaxUpdate();
                },
                error: function(jqXHR){
                    // $('#main-content').html($(data));
                    $('.js-modal').replaceWith($(jqXHR.responseText));
                    // modal.replaceWith($(data));
                },

            });
        });

        $('body').on('click','label[name=changeName]', function(e) {
        // $('body').on('change','input[type=radio][name=changeName]', function(e) {
            if ($(this).attr("value") == 'chosenName') {
                $('input[type=text][name=chosenName]').prop('disabled', false);
                $('select[name=suggestion]').prop('disabled', true);

            }
            else if ($(this).attr("value") == 'suggestion') {
                $('input[type=text][name=chosenName]').prop('disabled', true);
                $('select[name=suggestion]').prop('disabled', false);
            }
        });

        $('body').on('click', '.js-toggle-button', toggleServiceState);
        $('body').on('change', '.js-toggle-box', toggleServiceState2);

        $('body').on('click', '.js-expand-button', function(e) {
            e.preventDefault();
            $('.js-static-ip-form').removeClass('hidden');
            $('.js-collapse-button').removeClass('hidden');
            $('.js-expand-button').addClass('hidden');
        });
        $('body').on('click', '.js-collapse-button', function(e) {
            e.preventDefault();
            $('.js-static-ip-form').addClass('hidden');
            $('.js-collapse-button').addClass('hidden');
            $('.js-expand-button').removeClass('hidden');
        });

        $('body').on('click', '.accordion', function(e) {
            this.classList.toggle("active");
            var panel = this.nextElementSibling;
            if (panel.style.maxHeight) {
                panel.style.maxHeight = null;
            } else {
                panel.style.maxHeight = panel.scrollHeight + "px";
            }
        });

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

        $('body').on('click', '.js-modal-close', //clearJobStatus);
        function(e){
                clearJobStatus.bind(this, e, function(){
                    if (refreshURL) {
                        if(refreshURL == window.location.pathname){
                            updateMainContent(refreshURL, 'get', undefined, true);
                        } else{
                            window.location.assign(refreshURL);
                        }
                        refreshURL = false;
                    }
                })();
        });

        $('body').on('click', '.js-modal-close-nojob', function(e){
            e.preventDefault();
            $(this).closest('.js-modal').remove();
        });

        var prevMode = undefined;

        $('body').on('click', '.radio_device', function(e) {
            this.caller = function () {
                var href = $(this).attr('data-href');
                var mode = $(this).val();
                var dev_id = $(this).attr('name');

                if(prevMode != mode){
                    // $(this).attr('disabled', true);
                    $(this).closest(".single-device-row").find(".radio_device").attr('disabled', true);
                    $.ajax({
                        url: href,
                        dataType: 'html',
                        data: {'mode': mode, 'dev_id': dev_id, 'csrfmiddlewaretoken': Cookies.get('csrftoken')},
                        type: 'post',
                        context: this,
                        success: function (data) {
                            setSingleDeviceAsInProgress(dev_id);
                            //$('body').append($(data));
                            //onAjaxUpdate();
                            // $(this).attr('disabled', false);
                        },
                        error: function () {
                            this.caller();
                        }
                    });
                }
                prevMode = undefined;
            }.bind(this);
            this.caller();
        });

        $(document).on('mousedown', '.dev_label', function(e) {
            // get the value of the current checked radio
            prevMode = $('.radio_device[name='+$(this).prev("input").attr('name')+']:checked').val();
        });

        $('body').on('click', '.devname', function(e) {
            e.preventDefault();
            var href = $(this).attr('href');
            $.ajax({
                url: href,
                dataType: 'html',
                data: {'csrfmiddlewaretoken': Cookies.get('csrftoken')},
                type: 'get',
                context: this,
                success: function (data) {
                    $('body').append($(data));
                    //onAjaxUpdate();
                    $(this).attr('disabled', false);
                },
            });
        });

        $('body').on('click', '.showpw', function(e) {
            var inputElement = $(this).prev('input');
            var spanElement = $(this);

            if(inputElement.attr("type")=="password"){
                inputElement.attr('type', 'text');
                $(this).removeClass("i-eye-open");
                $(this).addClass("i-eye-closed");
            } else {
                inputElement.attr('type', 'password');
                $(this).removeClass("i-eye-closed");
                $(this).addClass("i-eye-open");
            }

        });

        $("#changes-container").on('click', function () {
            showModal("message");
        });
        $("#error-container").on('click', function () {
            showModal("error");
        });


        $(document).ready(function ()  {
            pollForRequestedInformation({
                pollUrl: "data-poll-counter-url",
                domManipulator: updateUpriboxActionCount,
                errorHandler: errorUpriboxActionCount,
                pollIntervall: pollingTimeoutCounter,
                pollProxy: upriboxActionCountProxy
            });

            if ($('body').attr("data-template-single-device")) {
                checkProgressDevicesOnStart();
                getAllDevices();
            }

            if($('body').attr("data-poll-statistics-main-url")) {
                getStatistic();
            }

            if ($('.messages-to-show').length > 0) {
                showModal("message");
            }

            if ($('.statistics-content').length > 0) {
                $('.statistics-content').on("touchstart", function () {
                    clearTimeout(makeTooltipsDisappearOnMobileTimeoutHandler);
                    makeTooltipsDisappearOnMobileTimeoutHandler = setTimeout(function () {
                        $('.hoverlayer').empty();
                    }, 1500)
                })

            }

            initialisePasswordFields();

        });
    }

function initialisePasswordFields(){
    if ($("[type='password']").length > 0) {
        var pw1 = $("[name='password1']")[0];
        var pw2 = $("[name='password2']")[0];

        $("[type='password']").each(function(index, element) {
            $(element).bind("propertychange change click keyup input paste", function () {
                var result = zxcvbn(element.value);
                if (element.value == "")
                    result.score = -1;

                var passwordsMatch = null;
                var passwordLengthOk = null;
                var passwordLengthCheckRequired = ($("#string8to64needed").length > 0);

                var checkPasswordLength = function () {
                    if (passwordLengthCheckRequired) {
                        if (pw1.value.length >= 8 && pw1.value.length <=64) {
                            passwordLengthOk = true;
                        }
                        else {
                            passwordLengthOk = false;
                        }
                    }
                }

                if (element.name == "password1") {
                    passwordsMatch = (element.value == pw2.value && element.value != "");
                    checkPasswordLength();
                }
                if (element.name == "password2") {
                    passwordsMatch = (element.value == pw1.value && element.value != "");
                    checkPasswordLength();
                }

                if (passwordsMatch !== null && ((passwordLengthCheckRequired && passwordLengthOk !== null ) || !passwordLengthCheckRequired)) {
                    if (passwordsMatch && ((passwordLengthCheckRequired && passwordLengthOk === true) || !passwordLengthCheckRequired)) {
                        $("[name='submit']").removeAttr("disabled");
                        $("#passwordsDontMatch").css("display", "none");
                        if (passwordLengthCheckRequired) $("#string8to64needed").css("display", "none");
                    }
                    else {
                        if (!passwordsMatch) {
                            $("[name='submit']").attr("disabled", "disabled");
                            if (pw1.value != "" && pw2.value != "" ) $("#passwordsDontMatch").css("display", "block");
                            else if (pw1.value == "" || pw2.value == "") $("#passwordsDontMatch").css("display", "none");
                        }
                        else {
                            $("#passwordsDontMatch").css("display", "none");
                        }
                        if (passwordLengthCheckRequired && passwordLengthOk === true) {
                            $("#string8to64needed").css("display", "none");
                        }
                        else if (passwordLengthCheckRequired && passwordLengthOk === false) {
                            $("[name='submit']").attr("disabled", "disabled");
                            $("#string8to64needed").css("display", "block");
                        }

                    }
                }
                // Update the password strength meter
                $(".meter-container:eq(" + index + " )").attr("name", "meter-value" + (result.score + 1).toString());
            });
        });
    }
    }

    function toggleServiceState2(e){
        e.preventDefault();
        var href = $(this).attr('href');
        var state = this.checked ? 'yes' : 'no';
        // $(this).attr('disabled', true);
        refreshURL = $("[data-refresh-url]").attr("data-refresh-url");
        $.ajax({
            url: href,
            dataType: 'html',
            data: {'enabled': state, 'csrfmiddlewaretoken': Cookies.get('csrftoken')},
            type: 'post',
            context: this,
            success: function (data, textstatus, jqXHR) {
                //$('body').append($(data));
                onAjaxUpdate();
                // $(this).attr('disabled', false);
            },
            error: function(jqXHR, textStatus, errorThrown){
                if (jqXHR.status == 403){
                    window.location.replace(jqXHR.responseText);
                }
            },

        });
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
                initialisePasswordFields();
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
    function updateMainContent(href, type, form, prevent) {
        clearJobStatus(null, function () {
            modalMode = "default";
            $.ajax({
                url: href,
                dataType: 'html',
                data: form? form.serialize(): null,
                type: type,
                success: function (data) {
                    $('#main-content').html($(data));
                    initialisePasswordFields();
                    if (!prevent && $(".form-input-error").length < 1){
                        onAjaxUpdate();
                    }
                }
            });
        });
    }

    function showModal(type, lock) {
        if (typeof lock === 'undefined') {
            lock = false;
        }
        clearJobStatus(null, function () {
            $.ajax({
                url: $('body').attr("data-template-modal"),
                dataType: 'html',
                //data: form? form.serialize(): null,
                success: function(t) {
                    return function(data) {
                        forceContinuousModalUpdate = true;
                        pauseCounter = true;

                        $('#main-content').append($(data));
                        if (t === "message") {
                            modalMode = "default";
                            pollForRequestedInformation({
                                //pollOnce: true
                                pollProxy: modalUpdateProxy
                            });
                        }
                        else if (t === "error") {
                            modalMode = "error";
                            pollForRequestedInformation({
                                pollUrl: "data-poll-errors-url",
                                domManipulator: updateModal,
                                errorHandler: errorModal,
                                //pollOnce: true
                                pollProxy: modalUpdateProxy
                            });
                        }
                        if (lock){
                            $('.js-modal-close').attr('disabled', 'disabled');
                        }else{
                            $('.js-modal-close').attr('disabled', false);
                        }
                    }
                }(type, lock)
            });
        });
    }

    function checkProgressDevicesOnStart() {
        $(".single-device-row").each(function (index, element) {
            if ($(element).attr("data-changing") === "True") {
                setSingleDeviceAsInProgress($(element).attr("id"), true);
            }
        });
    }

    function setSingleDeviceAsInProgress(id, isAlreadyMarked) {
        if (!isAlreadyMarked) {
            $("#" + id).attr("data-changing", "True");
        }
        $("#" + id).find(".device-link").removeClass("i-connected").removeClass("i-notconnected").addClass("i-status");

        deviceInProgressList[id] = true;
        if (!pollingForDevicesInProgress) {
            pollForRequestedInformation({
                pollUrl: "data-poll-device-activeprogress-url",
                domManipulator: checkInProgressDevices,
                errorHandler: errorCheckInProgressDevices,
                stopPollingIfEmpty: true
            })
        }
    }

    function unsetSingleDeviceInProgress(id){
        delete deviceInProgressList[id];
        var entry = $("#" + id).find(".device-link");
        $("#" + id).attr("data-changing", "False");
        var onlineStat=entry.hasClass("is-online")?true:(entry.hasClass("is-offline")?false:null);
        if (onlineStat !== null)
            entry.removeClass("i-status").addClass(onlineStat?"i-connected":"i-notconnected");
        // $(".radio_device").attr("disabled", "false");
        $("#" + id).find(".radio_device").attr('disabled', false);
    }

    /**
     * Should be called whenever the site is updated via AJAX (but not from inside pollForRequestedInformation)
     * Also gets executed once on page load
     */
    function onAjaxUpdate() {
        checkInfoCookie();
        //alert(1);
        showModal("message", true);
        //pollForRequestedInformation();
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
    function clearJobStatus(e, cb, forceModalMode) {

        if(e) {
            e.preventDefault();
        }

        var href;

        if (!forceModalMode) {
            href = (modalMode==="error")?$('body').attr('data-clear-errors-url'):$('body').attr('data-clear-url');
            forceModalMode = modalMode;
        }
        else {
            href = (forceModalMode==="error")?$('body').attr('data-clear-errors-url'):$('body').attr('data-clear-url');
        }


        $.ajax({
            context: this,
            url: href,
            dataType: 'json',
            data: {'csrfmiddlewaretoken': Cookies.get('csrftoken')},
            type: 'post',

            success: function (mm) {
                return function (data) {
                    $(this).closest('.js-modal').remove();
                    modalMode = null;

                    if (mm === "error") {
                        if ($("#error-count").text() == "0")
                            $("#error-container").css("visibility", "hidden");
                    }
                    else {
                        if ($("#changes-count").text() == "0")
                            $("#changes-container").css("display", "none");
                    }
                    forceContinuousModalUpdate = false;
                    pauseCounter = false;
                    //reload main content if refesh url was given
                    // var refreshUrl = $(this).attr('data-refresh-url');

                    // if (refreshUrl) {
                    //     updateMainContent(refreshUrl, 'get');
                    // }
                    console.log('messages cleared')
                    if (cb) cb();
                }
            }(forceModalMode),

            //retry in case of error
            error: function(jqXHR, textStatus, errorThrown){
                console.log("message clearing failed: " + textStatus)
                setTimeout(function (c, mm) {
                    return function() {
                        clearJobStatus(null, c, mm);
                    }
                }(cb, forceModalMode), pollingTimeout);
            }

        });
    }

    function updateModal(data, pollRequest) {

        //console.log(data);
        if(data.message) {
            var tag = $('.message').find('ul').first();
            tag.empty();
            for (var i = 0; i < data.message.length; i++) {
                var messageClass = (data.message[i].status==="error")?"error-message":"success-message";//(modalMode==="error")?"error-message":"success-message";
                var litag = $('<li class="' + messageClass + '"></li>');
                if (!(modalMode !== "error" && data.message[i].status === "error")) {
                    tag.append(litag.html(data.message[i].message));
                    // data.message[i].message = $(".generalErrorText").text();
                    // $('.generalErrorText').removeClass('hidden');
                }
                // else{
                //     // data.message[i].message = $(".generalErrorText").text();
                //     // $('.generalErrorText').removeClass('hidden');
                // }
            }
        }
        if(data.status === "done" || data.status === "failed" ) { //|| forceContinuousModalUpdate
            $('.js-modal-close').attr('disabled', false);
        }
        var tag = $('.message').find('ul').first();
        if (data.status === "done" || data.status === "failed") {
            tag.addClass("all-done");
        }
        else {
            tag.removeClass("all-done");
        }
        /*if (forceContinuousModalUpdate) {
            setTimeout(function () {
                pollForRequestedInformation(pollRequest);
            }, pollingTimeout);
        }*/
        //var litag = $('<li class="success-message hidden"></li>');
        // tag.append(litag);
    }

    function modalUpdateProxy(cb) {
         if (forceContinuousModalUpdate) {
            setTimeout(function () {
                cb();
            }, pollingTimeout);
         }
    }

    function errorModal() {
        //alert(1);
        var closebutton = $('.js-modal-close');
        if(closebutton.attr('disabled')){
            closebutton.attr('disabled', false);
            //add a on click listener that reloads the page so the user
            //gets redirected to the login site
            closebutton.on('click', function() {
                location.reload();
            })
        }
    }

    function updateUpriboxActionCount(data) {
        if (parseInt(data.count)>0) {
            if (parseInt(data.count)==1) {
                $("#changes-text-plural").css("display", "none");
                $("#changes-text-singular").css("display", "inline");
            }
            else {
                $("#changes-text-singular").css("display", "none");
                $("#changes-text-plural").css("display", "inline");
            }
            $("#changes-count").text(data.count);
            $("#changes-container").css("display", "inline-block");
        }
        else {
            $("#changes-container").css("display", "none");
        }

        if (parseInt(data.errorcount)>0) {
            $("#error-count").text(data.errorcount);
            $("#error-container").css("visibility", "visible");
        }
        else {
            $("#error-container").css("visibility", "hidden");
        }
    }

    function upriboxActionCountProxy(cb) {
        if (!pauseCounter){
            setTimeout(cb, pollingTimeoutCounter);
        } else {
            setTimeout(function () {
                upriboxActionCountProxy(cb);
            }, pollingTimeoutCounter)
        }
    }
    function errorUpriboxActionCount() {

    }

    function getStatistic() {
        pollForRequestedInformation({
            pollUrl: "data-poll-statistics-main-url",
            domManipulator: completeStatistics,
            errorHandler: errorGetStatistics,
            pollOnce: true
        })
    }

    function completeStatistics(data) {

        var trace1 = {
            hoverinfo: "y",
            x: [/*'<a ><span class="kw-desc">KW </span>10</a>', '<a ><span class="kw-desc">KW </span>11</a>', '<a ><span class="kw-desc">KW </span>12</a>'*/],
            y: [/*20, 14, 23*/],
            width:[/*.6, .6, .6*/],
            marker: {color: '#007589'},
            name: 'gefiltert',
            type: 'bar'
        };
        var trace2 = {
            hoverinfo: "y",
            x: [/*'<a ><span class="kw-desc">KW </span>10</a>', '<a ><span class="kw-desc">KW </span>11</a>', '<a ><span class="kw-desc">KW </span>12</a>'*/],
            y: [/*12, 18, 29*/],
            width:[/*.6, .6, .6*/],
            marker: {color: '#47adc0'},
            type: 'bar',
            name: 'geblockt'
        };


        var trace3 = {
            hoverinfo: "none",
            x: [/*'<a ><span class="kw-desc">KW </span>10</a>', '<a ><span class="kw-desc">KW </span>11</a>', '<a ><span class="kw-desc">KW </span>12</a>', '<span class="kw-desc">KW </span>14', '<span class="kw-desc">KW </span>15'*/],
            y: [/*0,0,0,0,0*/],
            width:[/*.6, .6, .6*/],
            marker: {"color": "rgba(255, 255, 255, 0)"},
            /*width:[.75*(3/5), .75*(3/5), .75*(3/5),.75*(3/5), .75*(3/5)],*/
            name: 'dummy',
            type: 'bar'
        };

        var trace4 = {
            hoverinfo: "none",
            x: [/*'<a ><span class="kw-desc">KW </span>10</a>', '<a ><span class="kw-desc">KW </span>11</a>', '<a ><span class="kw-desc">KW </span>12</a>', '<span class="kw-desc">KW </span>14', '<span class="kw-desc">KW </span>15'*/],
            y: [/*0,0,0,0,0*/],
            width:[/*.6, .6, .6*/],
            marker: {"color": "rgba(255, 255, 255, 0)"},
            /*width:[.75*(3/5), .75*(3/5), .75*(3/5),.75*(3/5), .75*(3/5)],*/
            name: 'dummy',
            type: 'bar'
        };
        statisticInformation.data = [trace3, trace1, trace2, trace4];

        var layout = {
            xaxis: {
                autorange: true,
                showgrid: false,
                showline: true,
                fixedrange: true
            },
            yaxis: {
                autorange: true,
                showgrid: false,
                showline: true,
                showticklabels: false,
                fixedrange: true,
                zeroline: false
            },
            barmode: 'stack',
            showlegend: false,
            /*legend: {
             "x": "0",
             "margin.r": "120"
             },*/
            margin: {
                l: 22,
                r: 0,
                b: 50,
                t: 0,
                pad: 0
            },
            annotations: [
                /*{
                 x: 0,
                 y: trace1.y[0] + trace2.y[0],
                 xref: 'x',
                 yref: 'y',
                 text: '47049',
                 showarrow: true,
                 arrowcolor: "transparent",
                 arrowhead: 0,
                 ax: 0,
                 ay: -10
                 }*/
            ]
        };

        statisticInformation.layout = layout;

        initializeStatistics(data);

        /*trace1.y[0] =10;
         layout.annotations[0].y = trace1.y[0] + trace2.y[0];

         Plotly.Plots.resize(gd);*/
        // var week = $(".xtick").find("text").text;
        //console.log($(".xtick").find("text a"));
        //$(".xtick").find("text a").on("click", function () {alert(1)});
    }

    function initializeStatistics(data) {

        if (data[0].overallCount.bad == null)
            data[0].overallCount.bad = 0;
        if (data[0].overallCount.ugly == null)
            data[0].overallCount.ugly = 0;

        updateOverallCount(data[0].overallCount);
        updateLists(data[0].filtered.bad, data[0].filtered.ugly);

        var weeksToDo =  data.length;
        var dummyWeeksTodo =  totalWeeks - weeksToDo;

        var fillStatisticInformation = function (countBad, countUgly, week, index, onlyDummy, width) {
            if (!width)
                width = .6;
            var offset = onlyDummy?0:dummyWeeksTodo;
            var weekDomString = getWeekDomString(week, onlyDummy);
            if (!onlyDummy) {
                //statisticInformation.data[0].y[index] = countBad;
                statisticInformation.data[1].x[index] = weekDomString;
                statisticInformation.data[1].width[index] = width;

                //statisticInformation.data[1].y[index] = countUgly;
                statisticInformation.data[2].x[index] = weekDomString;
                statisticInformation.data[2].width[index] = width;

                statisticInformation.layout.annotations[index] = {
                    x: index + offset,
                    //y: countBad + countUgly,
                    xref: 'x',
                    yref: 'y',
                    text: '',
                    showarrow: true,
                    arrowcolor: "transparent",
                    arrowhead: 0,
                    ax: 0,
                    ay: -10
                }
                updateBarValue(index, countBad, countUgly, true);
            }
            statisticInformation.data[0].y[index + offset] = 0.0001; //this is added for the case all values are 0 - in this case the zero line would be placed in the vertical middle and the (zero indicating) annotations would also be in the vertical middle
            statisticInformation.data[0].x[index + offset] = weekDomString;
            statisticInformation.data[0].width[index + offset] = width;

            statisticInformation.data[3].y[index + offset] = 0.0013; //this is added for the case the values of the week are zero. thanks to this, the hover info stays at the bottom in that case
            statisticInformation.data[3].x[index + offset] = weekDomString;
            statisticInformation.data[3].width[index + offset] = width;
        }

        var getWeekDomString = function (week, dontCreateLink) {
            var calendarWeekShortText = $("#calendar-week-short-text").text();
            var defaultDomString = "<span>" + calendarWeekShortText + " </span>" + week;
            var retVal = dontCreateLink?defaultDomString:"<a id='week" + week + "'>" + defaultDomString + "</a>";
            return retVal;
        }

        var getWeekCountOfYear = function (prevYear) {
            /*according to
             https://de.wikipedia.org/w/index.php?title=Woche&oldid=167637426#Z.C3.A4hlweise_nach_ISO_8601
             and
             https://en.wikipedia.org/w/index.php?title=ISO_week_date&oldid=793798377#Weeks_per_year
             a common year has 53 Weeks, when it starts with a thursday and ends with a thursday
             and
             a leap year has 53 Weeks, when it starts with a Wednesday and ends with a Thursday or when it starts with a Thursday and ends with a Friday
             */
            var currentYear = new Date().getFullYear();
            if (prevYear) currentYear--;
            var isLeapYear = (new Date(currentYear, 1, 29).getMonth()==1);
            var has53Weeks = false;
            var yearsFirstDay = new Date(currentYear, 0, 1).getDay(); // 4 would be Thursday
            var yearsLastDay = new Date(currentYear, 11, 31).getDay(); // 4 would be Thursday
            if (!isLeapYear) {
                has53Weeks = (yearsFirstDay == 4 && yearsLastDay == 4);
            }
            else {
                has53Weeks = ((yearsFirstDay == 3 && yearsLastDay == 4) || (yearsFirstDay == 4 && yearsLastDay == 5));
            }
            return (has53Weeks?53:52);
        }

        for (var i = 0; i < totalWeeks; i++) {
            fillStatisticInformation(0, 0, "", i, true);
            clickableWeeks.push(0);
        }
        for (var i = 0; i < weeksToDo; i++) {
            fillStatisticInformation(0, 0, "", i);
        }
        for (var i = weeksToDo - 1; i >= 0; i--) {
            //for (var i = totalWeeks - 1; i >= dummyWeeksTodo; i--) {

            clickableWeeks[totalWeeks-i-1] = data[i].week;

            var bad = 0;
            var ugly = 0;
            if (i == 0) {
                lastWeek = data[i].week;
                currentClickedWeek = data[i].week;
                currentSelectedWeek = data[i].week;
                bad = parseInt(data[i].bad);
                ugly = parseInt(data[i].ugly);
                // for (var entry in data[i].filtered.bad) {
                //     bad += parseInt(data[i].filtered.bad[entry][1]);
                // }
                // for (var entry in data[i].filtered.ugly) {
                //     ugly += parseInt(data[i].filtered.ugly[entry][1]);
                // }
            }
            else {
                bad = parseInt(data[i].bad);
                ugly = parseInt(data[i].ugly);
            }
            //fillStatisticInformation(bad, ugly, data[i].week, totalWeeks-(i+1));
            fillStatisticInformation(bad, ugly, data[i].week, weeksToDo-1-i);

        }
        for (var i = 0; i < dummyWeeksTodo; i++) {
            //alert(1);

            /*var followWeek = (parseInt(data[0].week) + i + 1);
             var weeksInThisYear = getWeekCountOfYear();
             if (followWeek > weeksInThisYear)
             followWeek = weeksInThisYear - followWeek;
             fillStatisticInformation(0, 0, followWeek, i + weeksToDo, true);*/

            var prevWeek = (parseInt(data[data.length-1].week) - i - 1);
            var weeksInPrevYear = getWeekCountOfYear(true);
            if (prevWeek < 1)
                prevWeek = weeksInPrevYear + prevWeek;
            //fillStatisticInformation(0, 0, followWeek, i + weeksToDo, true);

            fillStatisticInformation(0, 0, prevWeek, dummyWeeksTodo - 1 - i, true);
        }
        var d3 = Plotly.d3;

        var WIDTH_IN_PERCENT_OF_PARENT = 73,
            HEIGHT_IN_PERCENT_OF_PARENT = 80;

        var gd3 = d3.select('#stats');
        /*.style({
         width: WIDTH_IN_PERCENT_OF_PARENT + '%',
         height: HEIGHT_IN_PERCENT_OF_PARENT + '%'
         });*/

        gd = gd3.node();
        window.onresize = function() {
            requestAnimationFrame(function() {
                Plotly.Plots.resize(gd);
                createLinksForWeeks();
            });
        };

        $(".loading").css("opacity", "0");
        $(".loading-text").css("opacity", "0");
        setTimeout(function () {
            $(".loading").css("display", "none");
            $(".loading-text").css("display", "none");
            $(".statistics-content").css("display", "block");
            $(".loading").detach().appendTo(".statistics-content .lists").addClass("update-weeks-statistik").css("visibility", "hidden").css("display", "block" );
            Plotly.newPlot(gd, statisticInformation.data, statisticInformation.layout, {displayModeBar: false});
            Plotly.Plots.resize(gd);
            setActiveWeekLink();
            createLinksForWeeks();
            $(".statistics-content").css("opacity", "1");
            setTimeout(function() {
                doStatisticsUpdate(lastWeek, true);
            }, 550);
        }, 450);
    }

    function createLinksForWeeks() {
        setTimeout(function() {
            $(".xtick").find("text").each(function (index, element) {
                $(element).find("a").on("click", function (ev) {
                    changeWeek(clickableWeeks[index]);
                });
            });
            //setActiveWeekLink();
        },200);
    }

    function changeWeek (week) {
        currentClickedWeek = week;
        setActiveWeekLink();
        addStatisticsWaitingSpinner();
        doStatisticsUpdate(week);
    }

    function addStatisticsWaitingSpinner() {
        $(".statistics-content .js-blocked-sites").css("visibility", "hidden");
        $(".statistics-content .js-filtered-sites").css("visibility", "hidden");
        $(".loading").css("visibility", "visible");
        $(".loading-text").css("visibility", "visible");
        $(".loading").css("opacity", "1");
        $(".loading-text").css("opacity", "1");
    }

    function removeStatisticsWaitingSpinner() {
        $(".loading").css("opacity", "0");
        $(".loading-text").css("opacity", "0");
        setTimeout(function () {
            $(".loading").css("visibility", "hidden");
            $(".loading-text").css("visibility", "hidden");
        }, 450);
        $(".statistics-content .js-blocked-sites").css("visibility", "visible");
        $(".statistics-content .js-filtered-sites").css("visibility", "visible");
    }
    function setActiveWeekLink() {
        /* $(".xtick").find("text").find("a").attr("class","");
         $(".xtick").find("text").find("a")[clickableWeeks.indexOf(currentSelectedWeek)].setAttribute("class", "activeWeekLink");
         console.log($(".xtick").find("text").find("a")[clickableWeeks.indexOf(currentSelectedWeek)]);*/
        $("body #statistic-details-calendar-week").text(currentClickedWeek);
        $("body #activePlotLinkStyle").remove();
        $("body").append("<style id='activePlotLinkStyle'>" +
            "\t.statistics-content #week" + currentClickedWeek + ", .statistics-content #week" + currentClickedWeek + ":active, .statistics-content #week" + currentClickedWeek + ":hover, .statistics-content #week" + currentClickedWeek + ":visited {" +
            "\t\tfill: rgb(0, 0, 0) !important;\n" +
            "\t\ttext-decoration: none !important;\n" +
            "\t\tpointer-events: none !important;\n" +
            "\t}\n" +
            "</style>");
    }

    function updateOverallCount(overallCount) {
        $("#total-blocked").text(overallCount.bad);
        $("#total-filtered").text(overallCount.ugly);
    }

    function updateLists(badList, uglyList) {
        $("#blocked-pages").empty();
        for (var detailUrl in badList) {
            $("#blocked-pages").append("<li>" + badList[detailUrl][0] + ": " + badList[detailUrl][1] + "</li>")
        }
        $("#filtered-pages").empty();
        for (var detailUrl in uglyList) {
            $("#filtered-pages").append("<li>" + uglyList[detailUrl][0] + ": " + uglyList[detailUrl][1] + "</li>")
        }
    }

    function updateBarValue (index, bad, ugly, ignoreRedraw) {
        // if (statisticInformation.data[0].y[index] == bad && statisticInformation.data[1].y[index] == ugly)
        //    return;
        statisticInformation.data[1].y[index] = bad;
        statisticInformation.data[2].y[index] = ugly;
        statisticInformation.layout.annotations[index].y = bad + ugly;
        statisticInformation.layout.annotations[index].text = bad + ugly;
        if (ignoreRedraw)
            return;
        Plotly.redraw(gd);
        Plotly.relayout(gd);
        createLinksForWeeks();
    }

    function errorGetStatistics() {

    }

    function doStatisticsUpdate(week, doInfinite) {
        pollForRequestedInformation({
            pollUrl: "data-poll-statistics-update-url",
            additionalUrl: week,
            domManipulator: updateStatistics,
            errorHandler: errorUpdateStatistics,
            pollOnce: !doInfinite,
            pollIntervall: pollingTimeoutStatistics
        })
    }

    function updateStatistics(data) {

        if (data.week == currentClickedWeek && currentClickedWeek != currentSelectedWeek) {
            currentSelectedWeek = currentClickedWeek;
            removeStatisticsWaitingSpinner();
        }
        if (data.overallCount.bad == null)
            data.overallCount.bad = 0;
        if (data.overallCount.ugly == null)
            data.overallCount.ugly = 0;
        var bad = 0;
        var ugly = 0;
        if (data.week == lastWeek) {
            bad = parseInt(data.bad);
            ugly = parseInt(data.ugly);
            // for (var entry in data.filtered.bad) {
            //     bad += parseInt(data.filtered.bad[entry][1]);
            // }
            // for (var entry in data.filtered.ugly) {
            //     ugly += parseInt(data.filtered.ugly[entry][1]);
            // }
            updateBarValue(statisticInformation.data[1].y.length-1, bad, ugly);
        }
        updateOverallCount(data.overallCount);
        if (data.week != currentSelectedWeek)
            return;
        updateLists(data.filtered.bad, data.filtered.ugly);
    }

    function errorUpdateStatistics() {

    }

    function getAllDevices() {
        $.ajax({
            url: $('body').attr("data-template-single-device"),
            dataType: 'html',
            //data: form? form.serialize(): null,
            success: function (data) {
                singleDeviceListHtmlTemplate = data;
                //console.log(singleDeviceListHtmlTemplate)
                pollForRequestedInformation({
                    pollUrl: "data-poll-device-list-url",
                    domManipulator: completeDeviceList,
                    errorHandler: errorGetDeviceList,
                    pollOnce: true
                });
            },
            error: function () {
                getAllDevices();
            }
        });
    }

    function completeDeviceList(data) {
        $("#device-sync-text1").addClass("device-sync-invisible-element");
        $("#device-sync-text2").removeClass("device-sync-invisible-element");

        if(data.length > 0) {
            $(".no-devices-row").remove();
        }
        else {
            $(".device-sync").css("display", "none");
            return;
        }

        for (var i = 0; i < data.length; i++) {
            //checkOnlineStatusList[data[i].slug] = true;
            checkOnlineStatusList.push(data[i].slug);
            //checkOnlineStatusIndexList[data[i].slug] = i;
            if ($("#" + data[i].slug).length>0)
                continue;
            var currentDeviceElement = $(singleDeviceListHtmlTemplate);
            $(currentDeviceElement).attr("id", data[i].slug);
            $(currentDeviceElement).find(".radio-" + data[i].mode).attr("checked", "checked");
            $(currentDeviceElement).find(".device-link").attr("href", data[i].name_url);
            $(currentDeviceElement).find(".device-link").text(data[i].name);
            $(".divTableBody").append(currentDeviceElement);
        }

        startCheckOnlineStatus();
    }

    function errorGetDeviceList() {

    }

    function checkInProgressDevices(data) {
        if (!data.length)
            data=[];

        for (var id in deviceInProgressList) {
            if (data.indexOf(id) == -1) {
                unsetSingleDeviceInProgress(id);
            }
        }
    }

    function errorCheckInProgressDevices() {

    }

    function startCheckOnlineStatus() {
        for (var i = 0; i < checkOnlineStatusList.length; i++) {
            //onlineStatusPolling
            checkOnlineStatus();
        }
    }

    function checkOnlineStatus(deviceId) {
        if (!deviceId) {
            statOnlinePollingLastElementIndex++;
            if (statOnlinePollingLastElementIndex  >= checkOnlineStatusList.length) {
                return;
            }
            deviceId = checkOnlineStatusList[statOnlinePollingLastElementIndex];
        }
        pollForRequestedInformation({
            pollUrl: "data-poll-device-online-state-url",
            pollOnce: true,
            domManipulator: updateOnlineStatus,
            errorHandler: errorCheckOnlineStatus,
            additionalUrl: deviceId
        });
    }

    function updateOnlineStatus(data) {
        // if ....  --> is there a scenario where you get a
        // "please request again, because I'm still checking the device..." response?
        // In this case call checkOnlineStatus(deviceId) from here and return.
        var id;
        var onlineStat;
        for (var key in data) {
            id = key;
            onlineStat = data[key];
        }
        var entry = $("#" + id).find(".device-link");
        entry.addClass(onlineStat?"is-online":"is-offline");
        if (onlineStat){
            var siblings = $(entry).parents('.single-device-row').prevAll('.single-device-row');
            $(entry).parents('.single-device-row').insertBefore(siblings[siblings.length-1]);
            // console.log($(entry).parents('.single-device-row').prevAll());
        }
        checkedDevicesForOnlineStatusCounter++;

        if ($("#" + id).attr("data-changing") !== "True")
            entry.removeClass("i-status").addClass(onlineStat?"i-connected":"i-notconnected");

        if (checkedDevicesForOnlineStatusCounter >= checkOnlineStatusList.length) {
            $(".device-sync").css("display", "none");
            return;
        }
        checkOnlineStatus();
    }

    function errorCheckOnlineStatus() {
    }

    /**
     * Poll the server for requested Information
     */
    function pollForRequestedInformation(pollRequest) {
        var additionalUrl = pollRequest&&pollRequest.additionalUrl?("/" + pollRequest.additionalUrl):"";
        var href = (pollRequest&&pollRequest.pollUrl?$('body').attr(pollRequest.pollUrl):$('body').attr('data-poll-messages-url')) + additionalUrl;
        var domManipulationCall = pollRequest&&pollRequest.domManipulator?pollRequest.domManipulator:updateModal;
        var pollErrorCall = pollRequest&&pollRequest.errorHandler?pollRequest.errorHandler:errorModal;
        var pollOnce = pollRequest&&pollRequest.pollOnce?pollRequest.pollOnce:false;
        var stopPollingIfEmpty = pollRequest&&pollRequest.stopPollingIfEmpty?pollRequest.stopPollingIfEmpty:false
        var intervallForPolling = pollRequest&&pollRequest.pollIntervall?pollRequest.pollIntervall:pollingTimeout;

        $.ajax({
            url: href,
            dataType: 'json',
            data: {'csrfmiddlewaretoken': Cookies.get('csrftoken')},
            type: 'post',

            success: function (pR) {
                return function (data) {
                    // console.log("queue " + href + " status: " + data.status);
                    upriboxUnreachable = false;
                    //we received data - hide warning again if visible
                    $('.js-connection-warning').addClass('hidden');

                    domManipulationCall(data, pR);

                    if  (pollRequest && pollRequest.pollProxy) {
                        pollRequest.pollProxy(function(p) {
                            return function() {
                                pollForRequestedInformation(p)
                            }
                        }(pR));
                    }
                    else if(data.status !== 'done' && data.status !== 'failed' && !pollOnce && (!stopPollingIfEmpty || (stopPollingIfEmpty && data.length && data.length > 0 ))) {
                        setTimeout(function ()  {
                            pollForRequestedInformation(pR)
                        }, intervallForPolling);
                    }
                }
            }(pollRequest),
            error: function(jqXHR, textStatus, errorThrown){

                console.log("queue check request failed: " + textStatus);

                //if we are not logged in, we get redirected to /login
                //in this case, stop retrying
                if(jqXHR.status == 200 && errorThrown instanceof SyntaxError){
                    //show warning to user
                    $('.js-session-lost-warning').removeClass('hidden');
                    //if the modal dialog is currently being show and the close button is disabled,
                    //enable it
                    pollErrorCall(pollRequest);
                    return;
                }
                if(!upriboxUnreachable){
                    //Show WLAN switching message after timeout
                    setTimeout(triggerWlanWarning, wlanWarningTimeout);
                }
                upriboxUnreachable = true;
                setTimeout(function (pr)
                {
                    return pollForRequestedInformation(pr);
                }(pollRequest), pollingTimeout);
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
            //pollForRequestedInformation();
            //updateChart();
        }
    }
}(jQuery));
