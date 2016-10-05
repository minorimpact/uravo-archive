#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

eval {
    main();
};
print "Content-type: text/html\n\n$@" if ($@);

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    print "Content-type: text/html\n\n";
    if ($form->{alert}) {
        $uravo->alert({server_id=>$form->{server_id}, AlertGroup=>$form->{AlertGroup}, AlertKey=>$form->{AlertKey}, Summary=>$form->{Summary}, Severity=>$form->{Severity}});

    }

    my $serverSelect = "<select name=server_id>" . join('', map { "<option value=$_>$_</option>"; } sort { lc($a) cmp lc($b); } $uravo->getServers({id_only=>1, all_silos=>1})) . "</select>";
    print <<HEAD;
<head>
    <title>Test Alert</title>
    <link rel="stylesheet" href="/uravo.css">
</head>
HEAD
    print $uravo->menu();
    print <<FORM;
<div id=links>
</div>
<div id=content>
<h1>Test Alert</h1>
<form method='POST'>
    <fieldset>
        <p>
            <label for=server_id>
                server_id
                <span class="fielddesc"></span>
            </label>
            $serverSelect
        </p>
        <p>
            <label for=AlertGroup>
                AlertGroup
                <span class="fielddesc"></span>
            </label>
            <input type=text id=AlertGroup name=AlertGroup value="${\ ($form->{AlertGroup} || "test"); }"/>
        </p>
        <p>
            <label for=AlertKey>
                AlertKey
                <span class="fielddesc"></span>
            </label>
            <input type=text id=AlertKey name=AlertKey  value="${\ ($form->{AlertKey} || "test"); }"/>
        </p>
        <p>
            <label for=Summary>
                Summary
                <span class="fielddesc"></span>
            </label>
            <input type=text id=Summary name=Summary value="${\ ($form->{Summary} || "This is a test."); }" />
        </p>
        <p>
            <label for=Severity>
                Severity
                <span class="fielddesc"></span>
            </label>
            <input type=text id=Severity name=Severity  value="${\ ($form->{Severity} || "red"); }"/>
        </p>
        <p>
                <button id="alert" name=alert value=1>Generate Alert</button>
        </p>
    </fieldset>
</form>
</div>

FORM
}


