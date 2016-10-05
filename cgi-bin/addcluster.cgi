#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Serverroles::Cluster;
use CGI;

eval { &main(); };
print "Content-type: text/html\n\n$@" if ($@);
exit;

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;
    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $cluster_id	= $form->{cluster_id};
    my $silo_id = $form->{silo_id};
    my $warning	= "";

    if ($cluster_id) {
        my $changelog = {user=>$user, note=>'New cluster.'};

        my $original_cluster_id = $cluster_id;
        if ($cluster_id =~/[A-Z]/) {
            $cluster_id = lc($cluster_id);
            $warning .= "'$original_cluster_id' is invalid: contains uppercase letters.<br />\n";
            $warning .= "... changed to '$cluster_id'.<br>\n";
        }

        if (length($cluster_id) < 3) {
            $warning .= "'$cluster_id' is invalid: too short.  cluster_id needs to be at least 3 characters.<br />\n";
        }

        $original_cluster_id = $cluster_id;
        if ($cluster_id =~s/\W//g) {
            $warning .= "'$original_cluster_id' is invalid: contains invalid characters.<br />\n";
            $warning .= "... changed to '$cluster_id'.<br>\n";
        }

        unless ($cluster_id) {
            $warning	.= "'$cluster_id' is invalid.<br>\n";
        }

        if ($cluster_id && $uravo->getCluster($cluster_id)) {
            $warning	.= "'<a href='cluster.cgi?cluster_id=$cluster_id'>$cluster_id</a>' already exists.<br>\n";
        }

        unless ($warning) {
            Uravo::Serverroles::Cluster::add({cluster_id=>$cluster_id,silo_id=>$silo_id}, $changelog);
            print "Location: editcluster.cgi?cluster_id=$cluster_id\n\n";
            exit;
        }
    }

    print "Content-type: text/html\n\n";
print <<HEAD;
<head>
    <title>Add Cluster</title>
    <link rel=stylesheet href=/uravo.css />
</head>
HEAD
    my $siloSelect = "<select name=silo_id>";
    foreach my $silo (sort {$a cmp $b} $uravo->getSilos({id_only=>1,all_silos=>1})) {
        $siloSelect .= "<option value='$silo'" .(($silo eq $silo_id)?' selected':'') . ">$silo</option>\n";
    }
    $siloSelect .= "</select>";

    print $uravo->menu();

print <<FORM;
<div id=links>
    <ul>
        <li><a href=clusters.cgi>All Clusters</a></li>
    </ul>
</div>
<div id=content>
    <h2 class=warning>$warning</h2>
    <form method=post>
        <fieldset>
            <p>
                <label for=cluster_id>
                    New Cluster ID
                    <span class=fielddesc></span>
                </label>
                <input type=text name=cluster_id value="$cluster_id" maxlength=20><br />
            </p>
            <p>
                <label for=silo_id>
                    Network Silo
                    <span class=fielddesc></span>
                </label>
                $siloSelect
            </p>
            <p>
                <button>Add Cluster</button>
            </p>
        </fieldset>
    </form>
</div>
FORM
}


