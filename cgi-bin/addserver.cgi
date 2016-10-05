#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Serverroles::Server;
use CGI;

main();

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $server_id	= $form->{server_id};
    my $warning	= "";

    if ($server_id) {
        $server_id = lc($server_id);
        if ($server_id =~/^([a-z]+)0([0-9]+)-([0-9]+)$/) {
            $server_id = "$1$2-$3";
        }
        my $hostname	= $server_id;

        if ($server_id && ($uravo->getServer($server_id))) {
            $warning	= "'<a href=server.cgi?server_id=$server_id>$server_id</a>' already exists.\n";
        } 
        if ($server_id =~/[^a-z0-9_\.-]/) {
            $warning = "Server ID can only contain letters, numbers, underlines, periods or dashes.";
        }
        if (!$warning) {
            my $changelog = {user=>$user, note=>'Added server ' . $server_id};
            eval {
                Uravo::Serverroles::Server::add({server_id=>$server_id}, $changelog);
            };

            if ($@) {
                $warning = $@;
            } else {
                print "Location: editserver.cgi?server_id=$server_id\n\n";
                exit;
            }
        }
    }
    print "Content-type: text/html\n\n";
    print <<HEAD;
<head>
    <title>Add Server</title>
    <link rel=stylesheet href=/uravo.css />
</head>
HEAD
    print $uravo->menu();
    print <<FORM;
<div id=links>
</div>
<div id=content>
    <h1>Add New Server</h1>
    <h2 class=warning>$warning</h2>
    <form method=post name="addserver">
        <fieldset>
            <p>
                <label for=server_id>
                    New Server ID
                </label>
                <input type=text id=server_id name=server_id value="$server_id">
            </p>
                
            <p>
                <button type=submit value=1>Add Server</button>
            </p>
        </fieldset>
    </form>
</div>
FORM
}
