#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

eval { 
    main(); 
};
print "Content-type: text/html\n\n$@" if ($@);
exit;

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my %info;
    $info{version} = $uravo->{version};
    $info{server_count} = $uravo->{db}->selectrow_hashref("SELECT COUNT(*) AS c FROM server")->{c};
    $info{alerts_per_min} = $uravo->{db}->selectrow_hashref("SELECT (COUNT(*)/60) AS c FROM historical_alert WHERE FirstOccurrence > NOW() - INTERVAL 1 HOUR")->{c};

    print "Content-type: text/html\n\n";
    print <<HEAD;
<html>
    <head>
        <title>Info</title>
        <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
        <link rel="stylesheet" href="/uravo.css">
        <script src="/js/jquery/jquery-1.9.1.js"></script>
        <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
        <script type="text/javascript">
            \$(function () {
            });
        </script>
    </head>
HEAD
    print $uravo->menu();
    print <<FORM;
    <body>
        <div id=links>
            <ul>
            </ul>
        </div>
        <div id=content>
            <h1>Info</h1>
            <div class=field>
                <span class=label>Version</span>
                <span class=data id=version>$info{version}</span>
            </div>
            <div class=field>
                <span class=label>Servers</span>
                <span class=data id=server_count>$info{server_count}</span>
            </div>
            <div class=field>
                <span class=label>Alerts/min</span>
                <span class=data id=alerts_per_min>$info{alerts_per_min}</span>
            </div>
        </div>
    </body>
</html>
FORM

}

