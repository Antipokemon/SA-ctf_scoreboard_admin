require([
    "jquery",
    "splunkjs/mvc",
    "splunkjs/mvc/simplexml/ready!"
], function($, mvc) {
    "use strict";

    var defaultTokens = mvc.Components.get("default");
    var submittedTokens = mvc.Components.get("submitted");
    var endpoint = "/en-US/splunkd/__raw/servicesNS/nobody/SA-ctf_registration/ctf_registration/admin/events";

    function setToken(name, value) {
        defaultTokens.set(name, value);
        if (submittedTokens) {
            submittedTokens.set(name, value);
        }
    }

    function requestedCtfId() {
        try {
            return new URLSearchParams(window.location.search).get("ctf_id") || "";
        } catch (e) {
            return "";
        }
    }

    function chooseEvent(events) {
        var requested = requestedCtfId();
        if (requested) {
            for (var i = 0; i < events.length; i++) {
                if (events[i].ctf_id === requested) {
                    return events[i];
                }
            }
        }

        var active = events.filter(function(event) {
            return event.event_state === "IN_PROGRESS";
        });
        if (active.length) {
            return active[0];
        }

        var upcoming = events.filter(function(event) {
            return event.event_state === "UPCOMING";
        });
        if (upcoming.length) {
            return upcoming[0];
        }

        return events.length ? events[0] : null;
    }

    function installSelector(events, selected) {
        if ($("#ctf-admin-event-picker").length) {
            return;
        }

        var wrapper = $("<div>")
            .attr("id", "ctf-admin-event-picker")
            .css({
                "display": "flex",
                "align-items": "center",
                "gap": "10px",
                "padding": "10px 16px",
                "margin": "10px 0",
                "border": "1px solid rgba(255,255,255,.18)",
                "border-radius": "6px"
            });

        $("<strong>").text("CTF Event").appendTo(wrapper);

        var select = $("<select>")
            .attr("id", "ctf-admin-event-select")
            .css({"min-width": "300px"});

        events.forEach(function(event) {
            $("<option>")
                .attr("value", event.ctf_id)
                .prop("selected", selected && event.ctf_id === selected.ctf_id)
                .text(
                    (event.name || event.ctf_id) +
                    " [" + (event.event_state || "UNKNOWN") + "]"
                )
                .appendTo(select);
        });

        select.on("change", function() {
            var params = new URLSearchParams(window.location.search);
            params.set("ctf_id", $(this).val());
            window.location.search = params.toString();
        });

        wrapper.append(select);

        var target = $(".dashboard-body").first();
        if (!target.length) {
            target = $(".dashboard").first();
        }
        if (target.length) {
            target.prepend(wrapper);
        }
    }

    function fail(message) {
        setToken("ctf_id", "__NO_CTF_SELECTED__");
        setToken("ctf_event_name", "No CTF selected");
        setToken("ctf_admin_context_ready", "0");

        var box = $("<div>")
            .css({
                "padding": "12px",
                "margin": "10px 0",
                "border": "1px solid #d9534f"
            })
            .text(message);

        $(".dashboard-body").first().prepend(box);
    }

    $.ajax({
        url: endpoint,
        method: "GET",
        dataType: "json",
        cache: false
    }).done(function(data) {
        var events = data.events || [];
        var selected = chooseEvent(events);

        if (!selected) {
            fail("No CTF events exist. Create one in Capture the Flag Registration first.");
            return;
        }

        setToken("ctf_id", selected.ctf_id || "");
        setToken("ctf_event_name", selected.name || selected.ctf_id || "");
        setToken("ctf_event_starts", selected.event_starts || "");
        setToken("ctf_event_ends", selected.event_ends || "");
        setToken("ctf_registration_state", selected.registration_state || "");
        setToken("ctf_event_state", selected.event_state || "");
        setToken("ctf_admin_context_ready", "1");

        installSelector(events, selected);
    }).fail(function(xhr) {
        fail(
            "Unable to load CTF events from Capture the Flag Registration: " +
            (xhr.responseText || xhr.statusText)
        );
    });
});
