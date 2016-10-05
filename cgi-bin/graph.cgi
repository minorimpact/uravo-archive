#!/usr/bin/perl

use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Serverroles::Graph;
use NetAddr::IP;
use Net::CIDR;
use Data::Dumper;
use GD::Graph::lines;
use CGI;

my @RANGES =  ('e-4h','e-48h', 'e-12d', 'e-48d', 'e-576d');
my $script_name = "graph.cgi";

eval { &main(); };
print "Content-type: text/html\n\n$@\n" if ($@);

sub main {
    my $uravo = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $g_obj  = new Uravo::Serverroles::Graph(1,1); #dummy object 

    my $cluster_id = $form->{cluster_id};
    my $type_id = $form->{type_id};
    my $server_id = $form->{server_id};
    my $rack_id = $form->{rack_id};
    my $cage_id = $form->{cage_id};
    my $netblock_id = $form->{netblock_id};
    my $graph_id = $form->{graph_id} || 'cpu,bandwidth';
    my $range = $form->{range} || "e-48h";
    my $aggregate = $form->{aggregate};
    my $aggregation_function = $form->{aggregation_function};
    my $cols = $form->{cols} || 3;
    my $height = $form->{height};
    my $width = $form->{width};
    my $groupby = $form->{groupby};

    my @server_ids;
    if ($cluster_id || $type_id || $cage_id || $rack_id || $netblock_id) {
        @server_ids = $uravo->getServers({cluster=>$cluster_id, type=>$type_id, cage=>$cage_id, rack=>$rack_id, netblock=>$netblock_id, id_only=>1, all_silos=>1});
    } else {
        @server_ids = split(/,/, $server_id);
    }


    my @graph_ids = split(/,/, $graph_id);

    my @ranges;
    if ($range eq 'all') {
        @ranges = @RANGES;
    } else {
        @ranges = split(/,/, $range);
    }
       
    print "Content-type: text/html\n\n";
    print $uravo->menu();
    my $aggregation_form = qq(
        <form>
            Aggregation: <select name="aggregate" OnChange="this.form.submit();">
                <option value=''>None</option>
                <option value='c' ${\ (($aggregate eq 'c')?'selected':''); }>Combined</option>
                <option value='s' ${\ (($aggregate eq 's')?'selected':''); }>Stacked</option>
                <option value='m' ${\ (($aggregate eq 'm')?'selected':''); }>Multiple</option>
            </select>
            <input type="hidden" name="cluster_id" value="$cluster_id">
            <input type="hidden" name="type_id" value="$type_id">
            <input type="hidden" name="server_id" value="$server_id">
            <input type="hidden" name="rack_id" value="$rack_id">
            <input type="hidden" name="cage_id" value="$cage_id">
            <input type="hidden" name="netblock_id" value="$netblock_id">
            <input type="hidden" name="range" value="$range">
            <input type="hidden" name="graph_id" value="$graph_id">
            <input type="hidden" name="height" value="$height">
            <input type="hidden" name="width" value="$width">
            <input type="hidden" name="cols" value="$cols">
        );
    if ($aggregate eq 's' || $aggregate eq 'm') {
        $groupby = 'type_id' unless ($groupby);
        $aggregation_form .= qq(group by <select name='groupby' OnChange="this.form.submit();">
            <option value='server_id' ${\ (($groupby eq 'server_id')?'selected':''); }>server</option>
            <option value='cluster_id' ${\ (($groupby eq 'cluster_id')?'selected':''); }>cluster</option>
            <option value='type_id' ${\ (($groupby eq 'type_id')?'selected':''); }>type</option>
            <option value='rack_id' ${\ (($groupby eq 'rack_id')?'selected':''); }>rack</option>
            <option value='cage_id' ${\ (($groupby eq 'cage_id')?'selected':''); }>cage</option>
            </select>\n);
    }
    if ($aggregate eq 'c') {
        $aggregation_function = 'sum' unless ($aggregation_function);
        $aggregation_form .= qq(<select name='aggregation_function' OnChange="this.form.submit();">
            <option value='sum' ${\ (($aggregation_function eq 'sum')?'selected':''); }>sum</option>
            <option value='avg' ${\ (($aggregation_function eq 'avg')?'selected':''); }>avg</option>
            </select>\n);
    }
    print $aggregation_form;
    print "<table>\n";
    if ($aggregate) {
        my $column = 0;
        my @local_graph_ids = ();
        if ($graph_ids[0] eq 'all') {
            foreach my $graph_id ($g_obj->graph_keys({ server_id => join(',', @server_ids)})) {
                push(@local_graph_ids, $graph_id);
            }

        } else {
            @local_graph_ids = @graph_ids;
        }
        foreach my $graph_id (sort @local_graph_ids) {
            $graph_id =~s/\//\./g;
            foreach my $range (@ranges) {
                if ($column >= $cols) {
                    print "</tr>\n";
                    $column = 0;
                }
                $column++;
                if ($column == 1) {
                    print "<tr>\n";
                }
                print "<td valign='top'>\n";
                if (scalar(@ranges) == 1) {
                    print "<a href='$script_name?graph_id=$graph_id&cluster_id=$cluster_id&server_id=$server_id&type_id=$type_id&aggregate=$aggregate&height=$height&width=$width&range=all&groupby=$groupby&rack_id=$rack_id&cage_id=$cage_id&netblock_id=$netblock_id&aggregation_function=$aggregation_function'>";
                } else {
                    print "<a href='graph_img.cgi?graph_id=$graph_id&cluster_id=$cluster_id&server_id=$server_id&type_id=$type_id&aggregate=$aggregate&height=$height&width=$width&range=$range&groupby=$groupby&rack_id=$rack_id&cage_id=$cage_id&netblock_id=$netblock_id&aggregation_function=$aggregation_function'>";
                }
                print "<img src='graph_img.cgi?graph_id=$graph_id&cluster_id=$cluster_id&server_id=$server_id&type_id=$type_id&aggregate=$aggregate&height=$height&width=$width&range=$range&groupby=$groupby&rack_id=$rack_id&cage_id=$cage_id&netblock_id=$netblock_id&aggregation_function=$aggregation_function' border='0'></a></td>\n";
            }
        }
        print "</tr>\n";
    } else {
        foreach my $server_id (sort @server_ids) {
            my $server = $uravo->getServer($server_id);
            print "<tr bgcolor='#AACCFF'><td colspan='$cols'><b>$server_id</b> ";
            print $server->link('default -graphs');
            print "</td></tr>\n";
            my @local_graph_ids = ();
            if ($graph_ids[0] eq 'all') {
                foreach my $graph_id ($g_obj->graph_keys({ server_id => $server_id})) {
                    push(@local_graph_ids, $graph_id);
                }
                push(@local_graph_ids, @aggregate_graph_ids);
            } else {
                @local_graph_ids = @graph_ids;
            }
            my $column = 0;
            foreach my $graph_id (sort @local_graph_ids) {
                $graph_id =~s/\//\./g;
                foreach my $range (@ranges) {
                    if ($server && $graph_id) {
                        if ($column >= $cols) {
                            print "</tr>\n";
                            $column = 0;
                        }
                        $column++;
                        if ($column == 1) {
                                print "<tr>\n";
                        }
                        print "<td valign='top'>\n";
                        if (scalar(@ranges) == 1) {
                            print "<a href='$script_name?server_id=$server_id&graph_id=$graph_id&range=all&height=$height&width=$width'>";
                        } else {
                            print "<a href='graph_img.cgi?server_id=$server_id&graph_id=$graph_id&range=$range&height=$height&width=$width&rack_id=$rack_id&cage_id=$cage_id&netblock_id=$netblock_id'>";
                        }
                        print "<img src='graph_img.cgi?server_id=$server_id&graph_id=$graph_id&range=$range&height=$height&width=$width' border='0'>";
                        print "</a>";
                        print "</td>\n";
                    }
                }
            }
            print "</tr>\n";
        }
    }
    print "</table>\n";
    print "</form>\n";
}

