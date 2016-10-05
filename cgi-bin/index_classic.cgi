#!/usr/bin/perl -w 

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

my $uravo = new Uravo;
my $script_name = 'index.cgi';

eval { &main(); };
print "Content-type: text/html\n\n$@" if ($@);
exit;

sub main {
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    print "Content-type: text/html\n\n";
    print <<HEAD;
<head>
    <title>All Servers</title>
    <link rel="stylesheet" href="/uravo.css">
</head>
HEAD
    print "<div align=center>\n";
    print "<font face='helvetica'>\n"; #;arial;sans-serif'>\n";

    my $view            = $$form{'view'} || 'cluster';
    my $query_cluster   = $$form{'query_cluster'} || '';
    my $query_type      = $$form{'query_type'} || '';

    my $params          = {type=>$query_type, cluster=>$query_cluster, all_silos=>1};

    $| = 0;

    my  @data   = sort { lc($a->id()) cmp lc($b->id()) } (($view eq 'type') ? $uravo->getTypes($params):$uravo->getClusters($params));
    my $menu        = makeMenu($view, $params, $form , \@data);
    print "$menu<br>\n<table><td width=100% align=center valign=top>";

    my $master_server_list = ();
    foreach my $server ($uravo->getServers($params)) {
        foreach my $type_id ($server->getTypes({id_only=>1}))  {
            if ($view && $view eq 'cluster') {
                push( @{ $master_server_list->{$server->cluster_id()}{$type_id} }, $server);
            } else {
                push( @{ $master_server_list->{$type_id}{$server->cluster_id()} }, $server);
            }
        }
    }
    listServers($params, \@data, $master_server_list);
    
    print "</table>\n";
}
 
sub makeMenu {
    my $view = shift || 'cluster';
    my $params = shift;
    my $form = shift;
    my $clusters_data = shift;

    my $cluster_options;
    my $menu   = $uravo->menu();
    
    $menu .= "<div id=links>";
    $menu .= "<ul>\n";
    if ($clusters_data->[0]) {
        my $data_type   = $clusters_data->[0]->type();
        my $sub_type    = ($data_type eq 'cluster')?'type':'cluster';
        $menu   .= "<li><a href=index_classic.cgi?view=$sub_type>Regroup by $sub_type</a></li>\n";
    }
    $menu .= "</ul></div>\n";
    $menu .= "<table width=100%>";
    $menu .= "<tr>\n";
    my $c   = 0;
    foreach my $data ( @{ $clusters_data } ) {
        my $name    = $data->id();
        $name       =~s/ /&nbsp;/g;
        $menu       .= "<td align=center nowrap bgcolor=" . $uravo->color('menu') . "><a href='#" . $data->id() . "'><font size=-2>$name</a></a>\n";
        if (++$c>6) {
            $menu   .= "<tr>";
            $c      = 0;
        }
        $cluster_options.=sprintf "<option>%s (all)\n",$data->id();

        my $data_type   = $data->type();
        my $sub_type    = ($data_type eq 'cluster')?'type':'cluster';
        my @subs        = ($sub_type eq 'cluster')?$data->getClusters($params):$data->getTypes($params);
        foreach my $sub ( sort { $a->id() cmp $b->id() } @subs) {
            $cluster_options.=sprintf "<option value=%s.%s>  - %s\n",$data->id(),$sub->id(),$sub->id();
        }
    }
    $menu .= "</table>\n";

}

sub listServers {
    my $params = shift;
    my $data = shift;
    my $master_server_list = shift;
	my $style       = " style=\"color: black;\"";
    my $max_cols    = 4;
    
    foreach my $data (@{ $data }) {
        my $col_count   = 1;
        my $name        = $data->id();
        my $id          = $data->id();
        my $data_type   = $data->type();
        my $sub_type    = ($data_type eq 'cluster')?'type':'cluster';

        my @subs        = ($sub_type eq 'cluster')?$data->getClusters($params):$data->getTypes($params);
        next unless (scalar(@subs));

        # title
        print "<a name=$id>\n";
        print "<table width=100%><tr bgcolor=" . $uravo->color('header') . "><td align=center>\n";
        print "<table cellpadding=0 cellspacing=0><tr><td align=center><font size=+1><b>$name</b></font>\n";
        print $data->link('default -graphs');
        print "<a href=graph.cgi?$data_type\_id=$id><img src=/images/graph-button.gif border=0></a>\n";
        print "<tr><td align=center>v<b>" .  $data->version() if ($data_type eq 'cluster' && $data->version());
        print "</table>\n";

        # controls
        print "<table cellspacing=0><tr><td align=center><font size=-2>";
        if (!$params->{$data_type} && !$params->{$sub_type}) {
            print "<a href=$script_name?query_$data_type=$id&view=$data_type><img src='/images/focus-button.gif' border=0 title='view $name only'></a>";
        } 
        if (!$params->{$data_type} && $params->{$sub_type}) { 
            print " &nbsp; view <a href='$script_name?view=$data_type'><b>all ${sub_type}s</b></a> &nbsp; "; 
            print " &nbsp; view <a href='$script_name?query_$data_type=$id&query_$sub_type=$params->{$sub_type}&view=$data_type'><b>$name</b></a> only &nbsp; "; 
        }
        if ($params->{$data_type} && !$params->{$sub_type}){
            print "&nbsp; view <a href=$script_name?view=$data_type><b>all ${data_type}s</b></a> &nbsp; ";
        }
        if ($params->{$data_type} && $params->{$sub_type}){
            print "&nbsp; view <a href=$script_name?query_$sub_type=$params->{$sub_type}&view=$data_type><b>all ${data_type}s</b></a> &nbsp; ";
            print "&nbsp; view <a href=$script_name?query_$data_type=$id&view=$data_type><b>all ${sub_type}s</b></a> &nbsp; ";
        }
        print "</table></table>";
        print "<table align=center border=1>";

        foreach my $sub ( sort { $a->id() cmp $b->id() } @subs) {
            my $sub_name = $sub->id();
            my $sub_id = $sub->id();
            print "<td align=center valign=top>";
            print "<table width=100% height=100%><tr>";
            print "<td bgcolor=" . $uravo->color('subheader') . " align=center valign=center>";
            print $sub_name;
            print $sub->link('default -graph');
            print "<a href=graph.cgi?$data_type\_id=$id&server_id=all&$sub_type\_id=${\ $sub->id(); }><img src=/images/graph-button.gif border=0></a>\n";
            print "<br>v<b>" .  $sub->version() if ($sub_type eq 'cluster' && $sub->version());
            print "<tr height=100%><td align=center height=100%>";
            my $tmp_params;
            map { $tmp_params->{$_}   = $params->{$_} } keys %{$params};
            $tmp_params->{$sub_type} = $sub->id();
            print "<table cellpadding=0 cellspacing=0>";
            if (ref($master_server_list->{$id}{$sub_id}) eq 'ARRAY') {
                my $cnt = 1;
                foreach my $server (sort { $a->id() cmp $b->id() } @{ $master_server_list->{$id}{$sub_id} }) {
                    print "<tr><td align=right>$cnt. &nbsp; </td><td> <a href=server.cgi?server_id="  . $server->id() . ">" . $server->id() . "</a>&nbsp;\n";
                    print "<td>" . $server->link("graphs") . "</td>\n";
                    $cnt ++;
                } # each server
            }
            print "</table>";
            print "</table>";
            if ( $col_count++ > $max_cols ) { $col_count = 1 ; print "</tr></tr>"; }
        } # each sub type/cluster
        print "</table>";

        print "<br>\n";
        print "<br>\n";
    } # each cluster/type
}

