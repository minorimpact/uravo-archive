#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

main();

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;
    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $rack_id = $form->{"rack_id"};
    my $save = $form->{"save"};

    my $rack = $uravo->getRack($rack_id);
    unless ($rack_id && $rack) {
        print "Location: racks.cgi\n\n";
        exit;
    }

    if ($save) {
        my $changelog = {note=>'', user=>$user, ticket=>''};
        $rack->update({x_pos=>$form->{x_pos}, y_pos=>$form->{y_pos}}, $changelog);

        print "Location: rack.cgi?rack_id=$rack_id\n\n";
        exit;
    }
    
    print "Content-type: text/html\n\n";

    my $cage_id = $rack->get('cage_id');
    my @servers = $rack->getServers({id_only=>1});

    print <<HEAD;
<head>
    <title>Edit Rack: $rack_id</title>
    <link rel="stylesheet" href="/uravo.css" />
</head>
HEAD
    print $uravo->menu();
    print <<DATA;
<div id=links>
</div>
    <div id=content>
    <h1>$rack_id</h1>
    <form method='POST'>
    <input type="hidden" name="rack_id" value="$rack_id" />
    <fieldset>
        <label for=x_pos>
            X Position
            <span class="fielddesc">The x position of this rack on a grid.</span>
        </label>
        <input type="text" name="x_pos" value="${\ $rack->get('x_pos'); }" maxlength="3" size="3" placeholder="X Position" />

        <label for y_pos>
            Y Position
            <span class="fielddesc">The Y position of this rack on a grid.</span>
        </label>
        <input type="text" name="y_pos" value="${\ $rack->get('y_pos'); }" maxlength="3" size="3" placeholder="Y Position" />

        <button class=submit type="submit" name=save value=1>Save Changes</button>
DATA
        print qq(<button onClick="if(confirm('Are you sure you want to delete $rack_id?')) { self.location='deleterack.cgi?rack_id=$rack_id' } return false;">Delete this Rack</button>) unless (scalar(@servers)) ;
        print qq(
    </fieldset>
</form>
</div>);

}

