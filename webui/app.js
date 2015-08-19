$( document ).ready(function() {
    var serverUrl = "http://localhost:8000";
    getLedStatus();
    $(".button-container input").on("click", function() {
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

    function getLedStatus() {
        $.ajax({
            url:serverUrl + "/settings",
            dataType: 'json',
            success:function(result) {
                setButtons( result['intensity_mode']);
            },
            error: function(e) {
                alert("Error :(")
            }
        });
    }
    function setButtons(status) {
        status = status.toLowerCase()
        var activeElement = $("input[value='" + status + "']");
        activeElement.attr("checked", "checked");
        activeElement.parent().addClass('active');
    }

    function getPatternList(){
      
    }
});
