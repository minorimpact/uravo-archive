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


    my $DB = $uravo->{db};

    my $cage_id = $form->{'cage'} || $form->{'cage_id'} || 'all';
    my @cages;
    if ($cage_id eq 'all') {
        @cages = $uravo->getCages();
    } else {
        @cages = map {$uravo->getCage($_); } split(/,/, $cage_id);
    }
    my $netblock_overlay = $form->{'netblock_overlay'};
    my $prefix = {$DB->selectrow_hashref("select prefix from cage where cage_id=?", undef, ($cage_id))}->{'prefix'};

    $| = 0;
    print "Content-type: text/html\n\n";
    print <<HEADER;
<head>
    <title>Racks</title>
    <link rel="stylesheet" href="/uravo.css" />
</head>
HEADER
    print $uravo->menu();
    print <<LINKS;
<div id=links>
    <ul>
        <li><a href="addrack.cgi">Add new Rack</a></li>
LINKS
    foreach my $cage (sort {lc($a->id()) cmp lc($b->id())} @cages) {
        my $id =$cage->id();
        print "<li>" . (($cage_id eq $id)?$id:"<a href='racks.cgi?cage=$id'>$id</a>") . "</li>\n";
    }
    print qq(
    </ul>
</div>
<div id=content>);

    foreach my $cage (sort {lc($a->id()) cmp lc($b->id())} @cages) {
        my $cage_id = $cage->id();
        my $max_pos = $DB->selectrow_hashref("select max(x_pos) as max_x_pos, max(y_pos) as max_y_pos from rack where cage_id=?", undef, ($cage_id));
        my $max_x_pos = $max_pos->{'max_x_pos'};
        my $max_y_pos = $max_pos->{'max_y_pos'};

        my @legend_colors = ('orange','grey','lightblue','salmon','lightgreen','yellow','sandybrown','purple');
        my %legend = ();

        my $netblockmap;
        my %rackmap = ();
        my %rackinfo = ();
        foreach my $rack ($uravo->getRacks({'cage'=>$cage_id})) {
            $rackmap{$rack->get('x_pos')}{$rack->get('y_pos')} = $rack;
            $rackinfo{$rack->id()} = $rack;
        }


        my $cage = $uravo->getCage($cage_id);

        print "<h1><a href='cage.cgi?cage_id=$cage_id'>$cage_id</a> " . $cage->link("default -info") . "</h1>\n";

        print "<table border='1'  cellpadding='1' cellspacing='3'>\n";
        print "<tr><td></td>\n";
        for (my $x = 1; $x<= $max_x_pos; $x++) {
            print "<td align='center'>$x</td>\n";
        }
        print "</tr>\n";

        my %servers = ();
        my $server_data = $DB->selectall_arrayref("select s.server_id, s.rack_id, s.position, s.server_model from server s, rack where rack.rack_id=s.rack_id and rack.cage_id=? order by s.position", {Slice=>{}}, ($cage_id));
        foreach my $server (@$server_data) {
            push(@{ $servers{$server->{'rack'}} }, $server);
        }
        my @racks = ();
        for (my $y = 1; $y<= $max_y_pos; $y++) {
            print "<tr>\n";
            print "<td>$y</td>\n";
            for (my $x = 1; $x<= $max_x_pos; $x++) {
                my $loop_rack_id;
                my $loop_rack;
                if ($rackmap{$x}{$y}) {
                    $loop_rack_id = $rackmap{$x}{$y}->id();
                    $loop_rack = $rackmap{$x}{$y};
                }
                if ($loop_rack_id) {
                    # This position has something in it.
                    print "<td";
                    if ($netblock_overlay && $legend{$loop_rack->get($netblock_overlay.'_netblock_id')}) {
                        print " bgcolor='" . $legend{$loop_rack->get($netblock_overlay.'_netblock_id')} . "'";
                    }
                    print ">";
                    push(@racks, $loop_rack_id);

                    my $server_count = 0;
                    if ($servers{$loop_rack_id}) {
                        $server_count = scalar(@{ $servers{$loop_rack_id} });
                    }
                    my $alt_server_count = 0;
                    if ($loop_rack_id =~ /^[a-z][a-z](\d+)$/ && $servers{$1}) {
                        $alt_server_count = scalar(@{$servers{$1}});
                    }
                    print "<h1 style='margin-bottom:0'><a href='rack.cgi?rack_id=$loop_rack_id' title='" . ($server_count + $alt_server_count) . " items'>$loop_rack_id</a></h1>";
                } else {
                    # this position is whitespace.
                    print "<td>&nbsp;";
                }
                print "</td>";
            }
            print "</tr>\n";
        }
        print "</table>\n";
    } # if ($cage)
}
print "</div>\n";

