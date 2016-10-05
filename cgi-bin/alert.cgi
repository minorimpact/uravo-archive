#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

my $uravo  = new Uravo;
my $query = CGI->new();
my %vars = $query->Vars;
my $form = \%vars;

my $url;

if ($form->{Serial}) {
    $url = "API/event.cgi?Serial=" . $form->{Serial};
} elsif ($form->{Identifier}) {
    $url = "API/event.cgi?Identifier=" . $form->{Identifier};
}
my $popup = $form->{popup};
    
print qq(Content-type: text/html

<!DOCTYPE html>
  <html>
    <head>
        <meta charset="utf-8">
        <title>Information</title>
        <link rel="stylesheet" type="text/css" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
        <link rel="stylesheet" type="text/css" href="/js/jquery/jquery.dataTables-1.9.4.css"> 
        <link rel="stylesheet" type="text/css" href="/bb.css"> 

        <script src="/js/jquery/jquery-1.9.1.js"></script>
        <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>

        <script type="text/javascript">
            var Severity;
            var Acknowledged;
            var popup = '$popup';

            \$(function() {
                if (!popup || popup == 0) {
                    \$("#header").html("${\ $uravo->menu(); }");
                }
                \$("#header").h
                \$.getJSON("$url", function(alerts) {
                    if (alerts.length > 0) {
                        var data = alerts[0];

                        \$("#title").append("<h2>" + data.Identifier + "</h2>");
                        \$("#title").append("<a href='alert_journal.cgi?&popup=" + popup + "&Serial=" + data.Serial + "'>Journal</a>&nbsp;<a href='javascript:window.opener.open(\\"/cgi-bin/historical_report.cgi?report=noform&serial=" + data.Serial + "\\");'>Historical</a>");
                        var fields = new Array();
                        for (var property in data) {
                            fields.push(property);
                        }
                        fields.sort();
                        for(var i=0; i<fields.length; i++)  {
                            var property = fields[i];
                            var value = data[property];
                            if (property == 'Acknowledged') {
                                Acknowledged = value;
                                if (value == 1) {
                                    value = "YES";
                                } else {
                                    value = "NO";
                                }
                                Acknowledge = value;
                            }
                            if (property == 'AdditionalInfo' && value) {
                                var regex = /^http/;
                                if (regex.test(value)) {
                                    value = "<a href='javascript:window.opener.open(\\"" + value + "\\");'>" + value + "</a>";
                                }
                            }
                            if (property == 'cage_id' && value) {
                                value = "<a href=/cgi-bin/cage.cgi?cage_id=" + value + " target=_new>" + value + "</a>\\n";
                            }
                            if (property == 'cluster_id' && value && value != 'Not Found') {
                                value = "<a href=/cgi-bin/cluster.cgi?cluster_id=" + value + " target=_new>" + value + "</a>\\n";
                            }
                            if (property == "FirstOccurrence" || property == "StateChange" || property == "LastOccurrence" || property == "Timeout") {
                                value = new Date(value * 1000).toString().replace(/ GMT.*\$/, '');
                            }
                            if (property == 'Ticket' && value) {
                                value = "<a href='" + value + "' target='_new'>" + value + "</a>\\n";
                            }
                            if (property == 'ParentIdentifier' && value) {
                                value = "<a href='/cgi-bin/alert.cgi?popup=" + popup + "&Identifier=" + encodeURI(value) + "'>" + value + "</a>\\n";
                            }
                            if (property == 'rack_id' && value) {
                                value = "<a href=/cgi-bin/rack.cgi?rack_id=" + value + " target=_new>" + value + "</a>\\n";
                            }
                            if (property == 'server_id' && value && value != 'Not Found') {
                                value = "<a href=/cgi-bin/server.cgi?server_id=" + value + " target=_new>" + value + "</a>\\n";
                            }
                            if (property == 'Severity') {
                                Severity = value;
                            }
                            if (property == 'silo_id' && value) {
                                value = "<a href=/cgi-bin/silo.cgi?silo_id=" + value + " target=_new>" + value + "</a>\\n";
                            }
                            if (property == 'type_id' && value && value != 'Not Found') {
                                value = "<a href=/cgi-bin/type.cgi?type_id=" + value + " target=_new>" + value + "</a>\\n";
                            }

                            var entry = "<tr><td>" + property + "</td><td>" + value + "</td></tr>\\n";
                            \$("#info tbody").append(entry);
                        }

                        if (Severity == '5') {
                            \$("#info").find("tr").addClass("critical");
                        } else if (Severity == '4') {
                            \$("#info").find("tr").addClass("major");
                        } else if (Severity == '3') {
                            \$("#info").find("tr").addClass("minor");
                        } else if (Severity == '2') {
                            \$("#info").find("tr").addClass("warning");
                        }
                        if (Acknowledged == '1') {
                            \$("#info").find("tr").addClass("acked");
                        }
                    }
                });
            });
        </script>
    </head>

    <body>
        <div id=header></div>
        <div id='title'></div>
        <table id='info' cellspacing=0 border=1>
            <tbody>
            </tbody>
        </table>
  </body>
</html>
);
