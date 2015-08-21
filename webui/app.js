
$( document ).ready(function() {
    var serverUrl = "http://localhost:8000";
    getLedStatus();
    $(document).on("click", ".button-container input", function() {
        var new_setting = $(this).val();
        $.ajax({
            method: 'POST',
            url:serverUrl + "/settings",
            data: {"intensity_mode": new_setting},
            dataType: 'json',
            success:function(result) {
                $(".button-container label").removeClass("active");
                $(".button-container label input").attr("checked", "undefined");
                setButtons(new_setting);
            },
            error: function(e) {
                alert("Error :(")
            }
        });

    });

    getPatternList();

    $(document).on("click", "#patternListBox input", function(){
      setNewPattern($(this).parent().find('input[type="radio"]').val());
    })



    function getLedStatus() {
        $.ajax({
            url:serverUrl + "/settings",
            dataType: 'json',
            success:function(result) {
                setButtons( result['intensity_mode']);
            },
            error: function(e) {
                alert("Error :(");
            }
        });
    }

    function setButtons(status) {
        status = status.toLowerCase();
        var activeElement = $("input[value='" + status + "']");
        activeElement.attr("checked", "checked");
        activeElement.parent().addClass('active');
    }

    function getPatternList(){
      $.ajax ({
        url: serverUrl + "/settings",
        dataType: 'json',
        success: function(result) {
          $.each(result['all_presets'], function(i, obj) {
              var radioBtnData = "<p><label><input type=\"radio\" id=\" " + i + "\" name=\"patternGroup\" value=\"" + obj + "\" /> " + obj + "</label></p>";
              $("#patternListBox").append(radioBtnData);
              });
          setActualPattern();
       }
     });
    }

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
