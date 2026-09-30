require([
    "underscore",
    "jquery",
    "splunkjs/mvc",
    "splunkjs/mvc/searchmanager",
    "splunkjs/mvc/simplexml/ready!"
], function(_, $, mvc, SearchManager) {
    "use strict";

    function submitted() {
        return mvc.Components.get("submitted");
    }

    $("#start_time_picker").datetimepicker({
        dateFormat: "yy-mm-dd",
        timeFormat: "HH:mm z",
        controlType: "select",
        onClose: function() {
            var date = $("#start_time_picker").datetimepicker("getDate");
            if (date) {
                submitted().set("StartTimeToken", date.getTime() / 1000);
            }
        }
    });

    $("#end_time_picker").datetimepicker({
        dateFormat: "yy-mm-dd",
        timeFormat: "HH:mm z",
        controlType: "select",
        onClose: function() {
            var date = $("#end_time_picker").datetimepicker("getDate");
            if (date) {
                submitted().set("EndTimeToken", date.getTime() / 1000);
            }
        }
    });

    var updateTimesSM = new SearchManager({
        id: "updateTimesSM",
        app: "SA-ctf_scoreboard_admin",
        cache: false,
        autostart: false,
        search: "| makeresults"
    });

    submitted().set("somethingchanged", Date.now().toString());

    document.getElementById("submit_button").onclick = function() {
        var ctfId = submitted().get("ctf_id");
        var start = submitted().get("StartTimeToken");
        var end = submitted().get("EndTimeToken");

        if (!ctfId || ctfId === "__NO_CTF_SELECTED__") {
            document.getElementById("update_results").innerHTML =
                "Select a CTF event before changing question times.";
            return;
        }
        if (!start || !end) {
            document.getElementById("update_results").innerHTML =
                "Select both a start and end time.";
            return;
        }
        if (Number(end) <= Number(start)) {
            document.getElementById("update_results").innerHTML =
                "End time must be later than start time.";
            return;
        }

        document.getElementById("update_results").innerHTML = "Starting search...";

        var escaped = String(ctfId).replace(/"/g, '\\"');
        var searchString =
            '| inputlookup ctf_questions ' +
            '| eval StartTime=if(ctf_id="' + escaped + '",' + start + ',StartTime) ' +
            '| eval EndTime=if(ctf_id="' + escaped + '",' + end + ',EndTime) ' +
            '| outputlookup ctf_questions';

        updateTimesSM.settings.set("search", searchString);
        updateTimesSM.startSearch();

        updateTimesSM.on("search:failed", function() {
            document.getElementById("update_results").innerHTML = "Failed.";
        });

        updateTimesSM.on("search:progress", function(properties) {
            document.getElementById("update_results").innerHTML =
                "In progress with " + properties.content.eventCount + " events...";
        });

        updateTimesSM.on("search:done", function() {
            document.getElementById("update_results").innerHTML =
                "Done. Verify the selected CTF below.";
            submitted().set("somethingchanged", Date.now().toString());
        });
    };
});
