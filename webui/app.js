var serverUrl = window.location.origin;

// From underscore.js
// Returns a function, that, as long as it continues to be invoked, will not
// be triggered. The function will be called after it stops being called for
// N milliseconds. If `immediate` is passed, trigger the function on the
// leading edge, instead of the trailing.
function debounce(func, wait, immediate) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

function getSettings() {
    $.ajax ({
        url: serverUrl + "/settings",
        dataType: 'json',
        success: applySettings
    });
}

function applySettings(settings) {
    $.each(settings['all_presets'], function(i, obj) {
        var radioBtnData = "<p><label><input type=\"radio\" id=\" " + i + "\" name=\"patternGroup\" value=\"" + obj + "\" /> " + obj + "</label></p>";
        $("#patternListBox").append(radioBtnData);
    });

    $('#dimmerSlider').data('slider').setValue(settings.dimmer * 100);
}


$(document).ready(function() {
    $('#dimmerSlider').slider();
    getSettings();

    $('#dimmerSlider').on('change', debounce(function (e) {
        $.ajax({
            method: 'POST',
            url: serverUrl + '/settings',
            data: {dimmer: e.value.newValue / 100.0}
        });
    }, 100));

    $(document).on("click", ".button-container input", function() {
        var new_setting = $(this).val();
        $.ajax({
            method: 'POST',
            url:serverUrl + "/settings",
            data: {},
            dataType: 'json',
            success:function(result) {
                $(".button-container label").removeClass("active");
                $(".button-container label input").attr("checked", "undefined");
            },
            error: function(e) {
                alert("Error :(")
            }
        });

    });

    $(document).on("click", "#patternListBox input", function(){
      setNewPattern($(this).parent().find('input[type="radio"]').val());
    })


    function setNewPattern(newPattern){
      $.ajax({
          method: 'POST',
          url:serverUrl + "/settings",
          data: {"current_preset": newPattern},
          dataType: 'json',
          error: function(e) {
              alert("Error :(")
          }
      });
    }

    function setActualPattern() {
      $.ajax({
          url:serverUrl + "/settings",
          dataType: 'json',
          success:function(result) {
            var pattern = result['current_preset'];
            var activeElement = $("input[value='" + pattern + "']");
            activeElement.prop( "checked", true );
          },
          error: function(e) {
              alert("Error :(")
          }
      });
    }



});
