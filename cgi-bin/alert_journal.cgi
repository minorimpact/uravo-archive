#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

eval {
    main();
}; 
print "Content-type: text/html\n\n$@\n" if ($@);

sub main {
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $uravo = new Uravo;

    my $Serial = $form->{Serial};
    my $popup = $form->{popup};

    print qq(Content-type: text/html

<!DOCTYPE html>
  <html>
    <head>
        <meta charset="utf-8">
        <title>Journal</title>
        <link rel="stylesheet" type="text/css" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
        <link rel="stylesheet" type="text/css" href=/js/jquery/jquery.dataTables-1.9.4.css"> 
        <link rel="stylesheet" type="text/css" href="/bb.css"> 

        <script src="/js/jquery/jquery-1.9.1.js"></script>
        <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>

        <script type="text/javascript">
            var popup = '$popup';
            \$(function() {
                if (!popup || popup == 0) {
                    \$("#header").html("${\ $uravo->menu(); }");
                }

                \$.getJSON("/cgi-bin/API/event.cgi?Serial=$Serial", function(data) {
                    var event = data[0];
                    \$("#title").append("<h2>" + event.Identifier + "</h2>");
                    \$("#title").append("<a href='alert.cgi?&popup=" + popup + "&Serial=" + event.Serial + "'>Information</a>&nbsp;<a href='javascript:window.opener.open(\\"/cgi-bin/historical_report.cgi?report=noform&serial=" + event.Serial + "\\");'>Historical</a>");
                    \$.getJSON("/cgi-bin/API/journal.cgi?Serial=$Serial", function(data) {
                        for (var i=0; i<data.length; i++) {
                            var value = data[i];
                            var entry = "<tr><td>" + value.create_date + "</td><td>" + value.entry + "</td></tr>";
                            \$("#journal tbody").append(entry);
                        }
                        \$("#journal").find("tr:odd").css("background-color", "#ccccff");
                    });

                });


            });

        </script>
    </head>

    <body>
        <div id='header'></div>
        <div id='title'></div>
        <table id='journal' width="100%" cellspacing=0>
            <tbody>
            </tbody>
        </table>
  </body>
</html>
);
}
