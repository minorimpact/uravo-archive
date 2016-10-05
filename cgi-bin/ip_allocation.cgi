#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

my $uravo = new Uravo;

main();

sub main {
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    print $uravo->menu();

    my $cage = $form->{'cage'};
    my @cages = $uravo->getCages();

    #$| = 0;
    my $db = $SERVERROLES::SRDB;

    print "<h2>SC-4 340</h2>\n";
    print "<table cellspacing='0' cellpadding='2'>\n";
    print "<tr><th>Netblock</th><th>Address</th><th>Reserved</th><th>Used</th><th>Free</th></tr>\n";
    foreach my $netblock ( sort { $a->id() <=> $b->id(); } $uravo->getNetblocks({'cage'=>9})) {
        print netblock($netblock);
    }
    print "</table>\n";

    print "<h2>Switch & Data</h2>\n";
    print "<table cellspacing='0' cellpadding='2'>\n";
    print "<tr><th>Netblock</th><th>Network</th><th>Reserved</th><th>Used</th><th>Free</th></tr>\n";
    foreach my $netblock ( sort { $a->id() <=> $b->id(); } $uravo->getNetblocks({'cage'=>11})) {
        print netblock($netblock);
    }
    print "</table>\n";
}

sub netblock {
    my $netblock = shift || return;

    my $netblock_id = $netblock->id();
    my $net = $netblock->get('address');


    my $total;
    my $reserved;
    my $where = 'where ';
    if ($net =~/^([0-9]+)\.([0-9]+)\.([0-9]+).0\/23$/) {
        $where .= "ip like '$1.$2.$3.%'";
        $where .= "or ip like '$1.$2." . ($3 + 1) . ".%'";
        $total = 512;
        $reserved = 67;
    } elsif ($net =~/^([0-9]+)\.([0-9]+)\.([0-9]+).0\/24$/) {
        $where .= "ip like '$1.$2.$3.%'";
        $total = 256;
        $reserved = 22;
    }

    my %ips = ();
    my $return;
    my $style;
    my $sql = "select ip from interface $where";
    print "Content-type: text/html\n\n$sql\n";
    my $res = $uravo->{db}->selectall_arrayref($sql, {Slice=>{}}) || die("Content-type:text/html\n\n$sql\n" . $uravo->{db}->errstr);
    foreach my $data (@$res) {
        $ips{$data->{'ip'}}++;
    }
    my $used = scalar(keys %ips);
    my $free = ($total - $reserved - $used);
    my $percent;
    if ($total - $reserved) {
       $percent = ($free / ($total - $reserved)) * 100;
    } else {
        $percent = 0;
    }
    if ($percent < 10) {
        $style = "font-weight:bold; background-color:red";
    }

    $return .= "<tr style='$style'>\n";
    $return .= "<td align='right'><a href=editnetblock.cgi?netblock_id=$netblock_id>$netblock_id</a></td>\n";
    $return .= "<td>$net</td>\n";
    $return .= "<td align='right'>$reserved</td>\n";
    $return .= "<td align='right'>$used</td>\n";
    $return .= "<td align='right'>$free</td>\n";
    $return .= "<td align='left'>(" . sprintf("%.2f", $percent) . "%)</td>\n";
    $return .= "</tr>\n";
    return $return;
}

    
