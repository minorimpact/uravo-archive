#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;

my $uravo = new Uravo;

my $filterList = "<option>default</option><option>all</option>";
foreach my $row (@{$uravo->{db}->selectall_arrayref("SELECT * FROM filter ORDER BY id", {Slice=>{}})}) {
    $filterList .= "<option>$row->{id}</option>";
}
print qq(Content-type: text/html

  <html>
    <head>
        <meta charset="utf-8">
        <title>Alerts</title>
        <link rel="stylesheet" type="text/css" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
        <link rel="stylesheet" type="text/css" href="/js/jquery/jquery.dataTables-1.9.4.css"> 
        <link rel="stylesheet" type="text/css" href="/js/jquery/TableTools.css"> 
        <link rel="stylesheet" type="text/css" href="/bb.css"> 
        <link rel="stylesheet" type="text/css" href="/js/jquery/jquery.contextMenu.css">

        <script src="/js/jquery/jquery-1.9.1.js"></script>
        <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
        <script src="/js/jquery/jquery.dataTables-1.9.4.js" type="text/javascript"></script>
        <script src="/js/jquery/TableTools-2.1.4.js" type="text/javascript"></script>
        <script src="/js/jquery/ZeroClipboard-1.0.4.js" type="text/javascript"></script>
        <script src="/js/jquery/dataTables.fnReloadAjax.js" type="text/javascript"></script>
        <script src="/js/jquery/jquery.contextMenu-1.6.5.js" type="text/javascript"></script>
        <script src="/js/jquery/dataTables.ColReorderWithResize.js" type="text/javascript"></script>

        <script type="text/javascript">
            var oTable;
            var oTableTools;
            var url_clicked;
            var last_update = new Date();
            var next_update = 1;
            var rollups = {};
            var control = 0;
            var clip = '';

            function tableTimer(reset) {
                var last_update_string = last_update.toString().replace(/ GMT.*\$/,'');
                last_update_string = last_update_string.replace(/^[A-Za-z]+ /,'');
                var events = oTableTools.fnGetSelected();
                if ((events.length  > 0 || \$(".context-menu-list").length) && !reset) {
                    \$("div.sDomInfo").html("<b>" + last_update_string + "</b> auto refresh in <b>--</b>");
                } else {
                    next_update = next_update - 1;
                    if (reset) { next_update = 0; }
                    if (next_update < 1) {
                        oTable.fnReloadAjax();
                        last_update = new Date();
                        next_update = 15;
                        \$.getJSON("API/event.cgi?filter=rollups", function (data) {
                            rollups = {};
                            for (var i=0; i<data.length; i++) {
                                var Identifier = data[i].Identifier;
                                var Summary = data[i].Summary;
                                var key = 'assigntorollup' + i;
                                rollups[key] = { name: Summary, Identifier: Identifier };
                            }
                        });
                    }
                    \$("div.sDomInfo").html("<b>" + last_update_string + "</b> auto refresh in <b>" + next_update + "</b>");
                }
            }

            function action(name, serial_list) {
                \$.get("alert_action.cgi?action="+ name + "&Serial=" + serial_list, function(data) { 
                    tableTimer(1);
                });
            }

            function contextMenuCallback(key, options) {
                var selected = oTableTools.fnGetSelected();
                var first_serial = '';
                var serial_list = '';

                if (selected.length > 0) {
                    for (var i = 0; i<selected.length; i++) {
                        var s = \$(selected[i]);
                        serial_list = serial_list + "," + s.attr('id');
                        if (first_serial == '') { first_serial = s.attr('id'); }
                    }
                    serial_list = serial_list.replace(/^,/,'');
                } else {
                    serial_list = \$(this).attr('id');
                }

                if (key == 'ack' || key == 'createticket' || key == 'deleteevent' || key == 'hide' || key == 'removeticket' || key == 'removenote') {
                    action(key, serial_list);
                } else if (key == 'assignticket') {
                    var Ticket = prompt("Ticket ID");
                    if (Ticket) {
                        \$.get("alert_action.cgi?action=assignticket&Serial=" + serial_list + "&Ticket=" + encodeURI(Ticket), function(data) { 
                            tableTimer(1);
                        });
                    }
                } else if (key.indexOf("assigntorollup") == 0) {
                    var Identifier = rollups[key].Identifier;
                    if (Identifier) {
                        \$.get("alert_action.cgi?action=assigntorollup&Serial=" + serial_list + "&ParentIdentifier=" + encodeURI(Identifier), function (data) {
                        });
                    }
                } else if (key == 'combine') {
                    var new_summary = prompt("Event Summary", clip);
                    if (new_summary) {
                        \$.get("alert_action.cgi?action=combine&Serial=" + serial_list + "&new_summary=" + encodeURI(new_summary), function(data) { 
                        });
                        clip = '';
                    }
                } else if (key == 'history') {
                    var history = window.open("historical_report.cgi?report=noform&journal=1&serial=" + serial_list);
                } else if (key == 'info') {
                    var info = window.open("alert.cgi?popup=1&Serial=" + serial_list,'','width=600,height=700,scrollbars=1');
                } else if (key == 'journal') {
                    var journal = window.open("alert_journal.cgi?popup=1&Serial=" + serial_list,'','width=600,height=700,scrollbars=1');
                } else if (key == 'server') {
                    var server_id = \$(this).find("td.server_id").text();
                    showServerEvents(server_id);
                } else if (key == 'clip') {
                    clip = \$("#" + first_serial).find("td.Summary").text();
                } else if (key == 'updatenote') {
                    var Note = prompt("Update Note on Event");
                    if (Note) {
                        \$.get("alert_action.cgi?action=updatenote&Serial=" + serial_list + "&Note=" + encodeURI(Note), function(data) { 
                        });
                    }
                }
                oTableTools.fnSelectNone();
                tableTimer(1);
            }

            function menuItems() {
                var items = {
                    "ack": { name: "Acknowledge (a)" },
                    "assignticket": { name: "Assign Existing Ticket" },
                    "assigntorollup": { name: "Assign to Exising Rollup", items: rollups },
                    "clip": { name: "Copy Summary to memory (c)" },
                    "createticket": { name: "Create Jira Ticket (t)" },
                    "deleteevent": { name: "Delete Event" },
                    "hide": { name: "Hide Event" },
                    "history": { name: "Historical Report (h)" },
                    "info": { name: "Information (i)" },
                    "journal": { name: "Journal (j)" },
                    "removeticket": { name: "Remove Jira Ticket" },
                    "removenote": { name: "Remove Note" },
                    "server": { name: "All Server Events" },
                    "updatenote": { name: "Update Note" }
                };
                if ( \$.isEmptyObject(rollups)  || rollups.length < 1) {
                    delete items['assigntorollup'];
                }
                if (oTableTools.fnGetSelected().length > 1) {
                    delete items['clip'];
                    delete items['history'];
                    delete items['info'];
                    delete items['journal'];
                    delete items['server'];
                    items['sep1'] = "-------";
                    items['combine'] = { name: "Combine Selected Events (c)" };
                }
                return items;
            }

            \$(function() {
                \$.contextMenu({
                    selector: '#event_list_table tr',
                    build: function (\$trigger, e) {
                        var selected = oTableTools.fnGetSelected();
                        if (selected.length == 0) {
                            var serial = \$trigger.attr('id');
                            oTableTools.fnSelect(\$("#" + serial));
                        }
                        return {
                            callback: contextMenuCallback,
                            items: menuItems(),
                        };
                    }
                });

		\$.fn.dataTableExt.sErrMode = 'throw';
                oTable = \$('#event_list_table').dataTable({
                    //"sDom": 'RT<"clear"><"sDomLink"><"sDomFilter"><"sDomInfo"><"bordered",f>ti',
                    //"sDom": 'RT<"clear"><"sDomLink"><"sDomFilter"><"sDomInfo"><"bordered",f>tipr',
                    "sDom": 'RT<"clear"><"sDomLink"><"sDomFilter"><"sDomInfo"><"bordered",f><"clear">iptr',
                    //"bScrollInfinite": true,
                    "bScrollCollapse": true,
                    //"sScrollY": \$(window).height() - 100,
                    "sAjaxSource": "API/event.cgi",
                    "sAjaxDataProp": "",
                    "asStripClasses": [],
                    "iDisplayLength": 100,
                    "fnRowCallback": function (nRow, aData, iDisplayIndex, iDisplayIndexFull ) { 
                        var serial = aData.Serial;
                        \$(nRow).attr('id', aData.Serial); 
                        \$(nRow).removeClass('odd');
                        \$(nRow).removeClass('even');
                        if (aData.Acknowledged == 1) {
                            \$(nRow).addClass('acked');
                        }

                        if (aData.Severity == '5') {
                            \$(nRow).addClass("critical");
                        } else if (aData.Severity == '4') {
                            \$(nRow).addClass("major");
                        } else if (aData.Severity == '3') {
                            \$(nRow).addClass("minor");
                        } else if (aData.Severity == '2') {
                            \$(nRow).addClass("warning");
                        } else if (aData.Severity == '1') {
                            \$(nRow).addClass("indeterminate");
                        } else if (aData.Severity == '0') {
                            \$(nRow).addClass("clear");
                        }

                        //var Depth = \$(nRow).find("td.Depth").html();
                        var Depth = aData.Depth;
                        if (Depth > 0) {
                            Identifier = aData.Identifier;
                            \$(nRow).find("td.Depth").html("<a href='javascript:showSuppressed(\\"" + Identifier + "\\");'>" + Depth + "</a>");
                        }

                        //var Ticket = \$(nRow).find("td.Ticket").html();
                        var Ticket = aData.Ticket;
                        if (Ticket) {
                            \$(nRow).find("td.Ticket").html("<a href='" + Ticket + "' target='_new'>" + Ticket + "</a>");
                        }

                        var server_id = aData.server_id;
                        if (server_id != '' && server_id != 'Not Found') {
                            \$(nRow).find("td.server_id").html("<a href='server.cgi?server_id=" + server_id + "' target='_new'>" + server_id + "</a>");
                            if (aData.Action == 1 || aData.Action == 3) { \$(nRow).find("td.server_id").append("&nbsp;<b>J</b>"); }
                            if (aData.Action == 2) { \$(nRow).find("td.server_id").append("&nbsp;<b>N</b>"); }
                            if (aData.Action == 4) { \$(nRow).find("td.server_id").append("&nbsp;<b>R</b>"); }
                        }

                        var cluster_id = aData.cluster_id;
                        if (cluster_id != '' && cluster_id != 'Not Found' && cluster_id != null) {
                            \$(nRow).find("td.cluster_id").html("<a href='cluster.cgi?cluster_id=" + cluster_id + "' target='_new'>" + cluster_id + "</a>");
                        }

                        var type_id = aData.type_id;
                        if (type_id != '' && type_id != 'Not Found' && type_id != null) {
                            \$(nRow).find("td.type_id").html("<a href='type.cgi?type_id=" + type_id + "' target='_new'>" + type_id + "</a>");
                        }

                        var AlertGroup = aData.AlertGroup;
                        if (AlertGroup == 'timeout') {
                            \$(nRow).addClass('purple');
                        }

                        var Summary = aData.Summary;
                        var SummaryLength = Summary.length;
                        if (SummaryLength > 75) {
                            Summary = Summary.substring(0,75) + "...";
                            \$(nRow).find("td.Summary").html(Summary);
                        }

                        var lo = new Date(aData.LastOccurrence * 1000);
                        var LastOccurrence= (lo.getMonth() + 1) + "/" + lo.getDate() + "/" + lo.getFullYear().toString().replace(/^20/,'') + " " + lo.toTimeString().replace(/ GMT.*\$/, '');
                        \$(nRow).find("td.LastOccurrence").html(LastOccurrence);
                    },
                    "oTableTools": {
                        "sRowSelect": "multi",
                        "aButtons": [], //"aButtons": [ "select_none"],
                        "fnPreRowSelect": function (e) {
                             if( !e ) e = window.event;
                             var srcEl = e.target||e.srcElement;
                             if (srcEl.nodeName.toLowerCase() === 'a') {
                                 return false;
                             }
                             return true;
                         }
                    },
                    "aaSorting": [[10, "desc"],[0,"asc"],[1,"asc"],[2,"asc"]],
                    "aoColumns": [
                        { "mDataProp": "server_id",
                          "sWidth": 130,
                           "sClass": "server_id"
                        },
                        { "mDataProp": "cluster_id",
                          "sWidth": 130,
                           "sClass": "cluster_id"
                        },
                        { "mDataProp": "type_id",
                          "sWidth": 130,
                          "sClass": "type_id"
                        },
                        { "mDataProp": "AlertGroup",
                          "sWidth": 150,
                          "sClass": "AlertGroup"
                        },
                        { "mDataProp": "Summary",
                           "sClass": "Summary",
                        },
                        { "mDataProp": "Ticket",
                          "sWidth": 75,
                          "sClass": "Ticket"
                        },
                        { "mDataProp": "Tally",
                          "sWidth": 50,
                          "sClass": "Count"
                        },
                        { "mDataProp": "Note",
                          "sClass": "Note"
                        },
                        { "mDataProp": "Depth",
                          "sWidth": 50,
                          "sClass": "Depth"
                        },
                        { "mDataProp": "LastOccurrence",
                          "sWidth": 130,
                          "sClass": "LastOccurrence"
                        },
                        { "mDataProp": "Severity",
                          "sWidth": 50,
                          "sClass": "Severity"
                        }
                    ]
                });
                oTableTools = TableTools.fnGetInstance('event_list_table');
                resizeTable();
                \$(window).resize(function() { resizeTable();});

                \$("div.sDomLink").html("");
                \$("div.sDomFilter").html("&nbsp;Filter <select id=filter onchange=\\"oTable.fnReloadAjax('API/event.cgi?filter=' + this.value); oTableTools.fnSelectNone();\\">$filterList</select>");

                \$(document).keyup(function (e) {
                    var selected = oTableTools.fnGetSelected();
                    if (selected.length > 0 && \$(document.activeElement).attr('type') != 'text') {
                        if (selected.length == 1 && e.which == 67) { // C
                            contextMenuCallback('clip');
                            return;
                        } else if (selected.length == 1 && e.which == 73) { // I
                            contextMenuCallback('info');
                            return;
                        } else if (selected.length == 1 && e.which == 72) { // H
                            contextMenuCallback('history');
                            return;
                        } else if (selected.length == 1 && e.which == 74) { // J
                            contextMenuCallback('journal');
                            return;
                        }
                        if (e.which == 65) { // A
                            contextMenuCallback('ack');
                        }
                        if (e.which == 67) { // C
                            contextMenuCallback('combine');
                        }
                        if (e.which == 84) { // T
                            contextMenuCallback('createjiraticket');
                        }
                    } 
                });
            });

            window.setInterval(tableTimer,1000);

            function showServerEvents(server_id) {
                if (server_id) {
                    \$("div.sDomLink").html("<a href='javascript:showSuppressed(\\"\\");'>Show All Events</a>");
                } else {
                    \$("div.sDomLink").html("");
                }
                // Also pass the filter, since server_id is blank when we return to the default page.
                var url = "API/event.cgi?server_id=" + encodeURI(server_id) + "&filter=" + \$("#filter").val();
                oTable.fnReloadAjax(url);
            }

            function showSuppressed(Identifier) {
                if (Identifier) {
                    \$("div.sDomLink").html("<a href='javascript:showSuppressed(\\"\\");'>Show All Events</a>");
                } else {
                    \$("div.sDomLink").html("");
                }
                // Also pass the filter, since Identifier is blank when we return to the default page.
                var url = "API/event.cgi?ParentIdentifier=" + encodeURI(Identifier) + "&filter=" + \$("#filter").val();
                oTable.fnReloadAjax(url);
            }

            function resizeTable() {
                var width = \$(window).width();
                //console.log(width);
                if (width < 1800) {
                    oTable.fnSetColumnVis( 10, false );
                } else {
                    oTable.fnSetColumnVis( 10, true );
                }
                if (width < 1750) {
                    oTable.fnSetColumnVis( 9, false );
                } else {
                    oTable.fnSetColumnVis( 9, true );
                }
                if (width < 1200) {
                    oTable.fnSetColumnVis( 5, false );
                    //\$('body').css('font-size', 'large');
                } else {
                    oTable.fnSetColumnVis( 5, true );
                    //\$('body').css('font-size', 'medium');
                }
                if (width < 1050) {
                    oTable.fnSetColumnVis( 7, false );
                    //\$('body').css('font-size', 'x-large');
                } else {
                    oTable.fnSetColumnVis( 7, true );
                    //\$('body').css('font-size', 'large');
                }
                tableTimer(1);
            }
        </script>
    </head>

    <body>
        <div id=header>
            ${\ $uravo->menu(); }
        </div>
        <table id="event_list_table" class="display" width=100%>
            <thead>
                <tr>
                    <th>server_id</th>
                    <th>cluster</th>
                    <th>type</th>
                    <th>AlertGroup</th>
                    <th>Summary</th>
                    <th>Ticket</th>
                    <th>Count</th>
                    <th>Note</th>
                    <th>Depth</th>
                    <th>LastOccurrence</th>
                    <th>Severity</th>
                </tr>
            </thead>
            <tbody>
            </tbody>
        </table>
        <div id=debug></div>
  </body>
</html>
);
