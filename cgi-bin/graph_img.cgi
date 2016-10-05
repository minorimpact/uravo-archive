#!/usr/bin/perl

use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Serverroles::Graph;
use Data::Dumper;
use GD;
use GD::Graph::lines;
use GD::Graph::area;
use Time::HiRes qw(gettimeofday tv_interval);
use Storable qw(freeze thaw);
use Data::Dumper;
use Uravo::Pylon;
use CGI;

$| = 1;

my @days = ('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat');
my $y_labels = { bandwidth=>'bytes/second', conn=>'seconds', cpu=>'load average', cpu_util=>'% utilization', disk=>'% full', http=>'seconds', http_req_time=>'seconds', memory=>'% used',pylon_connections=>'connections/s',pylon_size=>'bytes',pylon_uptime=>'seconds', pylon_adds=>'adds/s', pylon_gets=>'gets/s', pylon_commands=>'commands/s', pylon_read_time=>'seconds', pylon_dumps=>'checks/s' };

my $default_height = 180;
my $default_width = 380;


eval { &main(); };
print "Content-type: text/html\n\n$@\n" if ($@);

sub main {
    my $uravo  = new Uravo({loglevel=>0});
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;


    my $total_start_time = [gettimeofday];
    my $cluster_id = $form->{cluster_id};
    my $type_id = $form->{type_id};
    my $server_id = $form->{server_id};
    my $cage_id = $form->{cage_id};
    my $rack_id = $form->{rack_id};
    my $aggregate = $form->{aggregate};
    my $graph_id = $form->{graph_id};
    my $range = $form->{range} || "e-48h";
    my $height = $form->{height} || $default_height;
    my $width = $form->{width} || $default_width;
    my $aggregation_function = $form->{aggregation_function};
    my $groupby = $form->{groupby};
    my $notitle = $form->{notitle};
    my $nofooter = $form->{nofooter};
    my $nolegend = $form->{nolegend};
    my $title = $form->{title};
    my $vrange = $form->{vrange};
    my $offset = $form->{offset} || time;
    my $rrd_graph = $form->{rrd_graph};
    my $source = $form->{source} || 'rrd';

    if ($offset =~/^([0-9]{4})-([0-9]{2})-([0-9]{2})$/) {
        use Time::Local;
        $offset = timelocal(59, 59, 23, $3, ($2-1),$1);
        $offset = time if ($offset > time);
    }


    my @server_ids;
    if ($cluster_id || $type_id || $cage_id || $rack_id) {
        @server_ids = $uravo->getServers({cluster=>$cluster_id, type=>$type_id, cage=>$cage_id, rack=>$rack_id, id_only=>1, all_silos=>1});
    } else {
        @server_ids = split(/,/, $server_id);
    }

    if (scalar(@server_ids) > 1 && !$aggregate) {
        $aggregate = "c"; 
    }

    if ($aggregate eq 'm' || $aggregate eq 's') {
        $groupby = 'type_id' unless ($groupby);
        $aggregation_function = 'sum';
    } elsif ($aggregate eq 'c') {
        $groupby = undef;
        $aggregation_function = 'sum' unless ($aggregation_function);
    }

    my $args;
    $args->{height} = $height;
    $args->{width} = $width;
    $args->{graph_id} = $graph_id;
    $args->{range} = $range;
    $args->{total_start_time} = $total_start_time;
    $args->{notitle} = $notitle;
    $args->{nofooter} = $nofooter;
    $args->{nolegend} = $nolegend;
    $args->{source} = $source;
    $args->{vrange} = $vrange if ($vrange);

    if ($aggregate) {
        $args->{title} = $graph_id;
        my $combined_graph_data;
        my %netblock = ();
        if (scalar(@server_ids) && $aggregate eq 'c' && $source eq 'pylon') {
            # We can pull a sum/avg for the same graph_id for multiple servers from pylon with (basically) a single command, which is 
            # much faster than pulling data for each individual server.

            $range =~s/^e-//;
            if ($range =~/([0-9]+)h$/) {
                $range = time() - ($1 * 3600) + 300;
            } elsif ($range =~/([0-9]+)d$/) {
                $range = time() - ($1 * 3600 * 24) + 300;
            }   

            foreach my $check_id (grep { /^($graph_id,|$graph_id$)/; } split(/\|/, Uravo::Pylon::pylon("checks|" . join("|", @server_ids)))) {
                my $sub_id = $graph_id;
                if ($check_id =~/$graph_id,(.+)/) {
                    $sub_id = $1;
                }

                my $command = (($aggregation_function eq "avg")?"avg":"get") . "|$check_id|$range|" . join("|", @server_ids);
            
                my $pylon = Uravo::Pylon::pylon($command);
                #print "Content-type: text/plain\n\n$graph_id,$command,$pylon\n";
                my @data = split(/\|/,$pylon);
                my $time = shift @data;
                my $size = shift @data;
                my $step = shift @data;

                foreach my $val (@data) {
                    if ($val =~/nan/) {
                        $combined_graph_data->{$time}{$sub_id} = undef;
                    } else {
                        $combined_graph_data->{$time}{$sub_id} = $val;
                    }
                    $time += $step;
                }
            }
            $args->{data} = $combined_graph_data;

        } elsif (scalar(@server_ids)) {
            # Pull the graph data for each server individually and combine it together in whatever way the user requested.
            my $smooth_start;
            my $smooth_interval;
            my %combined_graph_count = ();
            foreach my $server_id (@server_ids) {
                my $server = $uravo->getServer($server_id);
                if ($server && $graph_id) {
                    my $cluster_id = ${$server->{roles}}[0]->{cluster_id};
                    my $type_id = ${$server->{roles}}[0]->{type_id};
                    my $rack_id = $server->get('rack') || 'none';
                    my $cage_id = $server->get('cage') || 'none';

                    next if ($type_id eq 'aggregate');

                    my $server_graph_data;
                    my $graph_data = Uravo::Serverroles::Graph::ensmoothen_graph_data($server->graph_data({graph_id=>$graph_id,range=>$range,offset=>$offset,source=>$source}),$smooth_start,$smooth_interval);
                    unless ($smooth_start && $smooth_interval) {
                        my @times = sort keys %$graph_data;
                        $smooth_start = $times[0];
                        $smooth_interval = $times[1] - $times[0];
                    }
                    next unless ($graph_data && scalar(keys %$graph_data));
                    foreach my $time (keys %$graph_data) {
                        # Test to see if we have too much data to display.
                        #if ((scalar(@server_ids) * scalar(keys %{$graph_data->{$time}}))  > 2000 && $source ne "pylon") {
                        #    $args->{message} = "Too many data points.";
                        #    gd_error($args);
                        #    return;
                        #}
                        foreach my $sub_id (keys %{$graph_data->{$time}}) {
                            my $combined_sub_id = $sub_id;

                            if ($graph_id eq 'cpu' && $sub_id =~/^[0-9]+$/) {
                                $combined_sub_id = 'cpu';
                            }
                            if ($aggregate eq 'm' || $aggregate eq 's') {
                                if ($groupby eq 'server_id') {
                                    $combined_sub_id = "$server_id - $combined_sub_id";
                                } elsif ($groupby eq 'cage_id') {
                                    $combined_sub_id = "$cage_id - $combined_sub_id";
                                } elsif ($groupby eq 'rack_id') {
                                    $combined_sub_id = "$rack_id - $combined_sub_id";
                                } elsif ($groupby eq 'cluster_id') {
                                    $combined_sub_id = "$cluster_id - $combined_sub_id";
                                } elsif ($groupby eq 'type_id') {
                                    $combined_sub_id = "$type_id - $combined_sub_id";
                                }
                            }
                            $combined_graph_data->{$time}{$combined_sub_id} += $graph_data->{$time}{$sub_id}; 
                            $combined_graph_count->{$time}{$combined_sub_id}++;
                        }

                    }
                }
            }

            if ($aggregation_function eq 'avg') {
                foreach my $time (keys %$combined_graph_data) {
                    foreach my $sub_id (keys %{$combined_graph_data->{$time}}) {
                        $combined_graph_data->{$time}{$sub_id} = ($combined_graph_data->{$time}{$sub_id} / $combined_graph_count->{$time}{$sub_id});
                    }
                }
            }
            $args->{data} = $combined_graph_data;
        }

        if ($aggregate eq 's') {
            $args->{type} = 'area';
        }
    } elsif (scalar(@server_ids) > 0) {
        # If we somehow ended up here with multiple servers and no aggregation defined, just use the first one and screw
        # the rest.
        my $server = $uravo->getServer($server_ids[0]);
        if ($server && $graph_id) {
            my $type_id = ${$server->{roles}}[0]->{type_id};
            #next if ($type_id eq 'aggregate');
            my $graph_data = $server->graph_data({graph_id=>$graph_id,range=>$range,offset=>$offset,source=>$source});
            my $server_id = $server->id();
            $args->{title} = "$server_id - $graph_id";
            $args->{data} = $graph_data;
        }
    }

    $args->{title} = $title if ($title);
    gd_graph($args);
}

sub gd_error { 
    my $args = shift || return;

    $args->{width} ||= $default_width;
    $args->{height} ||= $default_height;

    my $im = new GD::Image($args->{width},$args->{height});

    # allocate some colors
    my $white = $im->colorAllocate(255,255,255);
    my $black = $im->colorAllocate(0,0,0);
    my $red = $im->colorAllocate(255,0,0);

    $im->transparent($white);
    $im->interlaced('true');

    $im->rectangle(0,0,($args->{width}-1 || 399),($args->{height} - 1 || 199),$red);
    $im->string(gdMediumBoldFont,2,10,$args->{title},$black);
    $im->string(gdSmallFont,2,25,$args->{message},$black);

    # Convert the image to PNG and print it on standard output
    print "Content-type: image/png\n\n";
    print STDOUT $im->png;
    return;
}


sub gd_graph {
    my $args = shift;

    if (!$args->{data} || !scalar(keys %{$args->{data}}) || $args->{blank}) {
        # Output a transparent 1x1 gif.
        my $img = "4749463839610100010080ff00c0c0c000000021f90401000000002c000000000100010040010132003b";
        $img =~ s/([a-fA-F0-9][a-fA-F0-9])/chr(hex($1))/eg;

        print "Content-type: image/gif\n\n";
        print $img;
        exit;
    }

    my $smooth_data = Uravo::Serverroles::Graph::ensmoothen_graph_data($args->{data});

    # Reparse the data into a graph-compatible structure.
    my @data = ();
    my %data_stats;
    my %subs = ();
    $label_width = 60;
    foreach my $time (sort keys %{$smooth_data}) {
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($time);
        if ($min =~/^[0-9]$/) { $min = "0$min"; }
        $mon++;
        $year -= 100;
        if ($args->{range} =~/h$/) {
            #push(@{$data[0]}, "$hour:$min");
            push(@{$data[0]}, $days[$wday] . " $hour:$min");
        } else {
            $label_width = 70;
            push(@{$data[0]}, "$mon/$mday/$year $hour:$min");
        }
        foreach my $sub_id (sort keys %{$smooth_data->{$time}}) {
            unless (defined($subs{$sub_id})) {
                $subs{$sub_id} = scalar(keys(%subs))+1;
                my $legend = $sub_id;
                if ($args->{graph_id} eq 'disk') {$legend =~s/\./\//g; }
                $args->{legend}->[$subs{$sub_id}-1] = $legend;
            }
            my $sub_count = $subs{$sub_id};
            my $value = $smooth_data->{$time}{$sub_id};
            if ($args->{vrange} && $value > $args->{vrange}) {
                $value = $args->{vrange};
            }

            push(@{$data[$sub_count]}, $value);

            $data_stats{$sub_count}{total} += $value;
            $data_stats{$sub_count}{count}++;
            if (!$data_stats{$sub_count}{max} || $value > $data_stats{$sub_count}{max}) {
                $data_stats{$sub_count}{max} = $value;
            }
            if (!$data_stats{$sub_count}{min} || $value < $data_stats{$sub_count}{min}) {
                $data_stats{$sub_count}{min} = $value;
            }
            $data_stats{$sub_count}{cur} = $value;
        }
    }

    foreach my $s_count (sort {$a <=> $b} keys %data_stats) {
        my $average = sprintf("%.1f", $data_stats{$s_count}{total}/$data_stats{$s_count}{count});
        my $min = sprintf("%.1f", $data_stats{$s_count}{min});
        my $max = sprintf("%.1f", $data_stats{$s_count}{max});
        my $cur = sprintf("%.1f", $data_stats{$s_count}{cur});

        $args->{legend}->[$s_count-1] .= "  Min: $min";
        $args->{legend}->[$s_count-1] .= "  Max: $max";
        $args->{legend}->[$s_count-1] .= "  Avg: $average";
        $args->{legend}->[$s_count-1] .= "  Cur: $cur";
        #print "" . ($s_count) . ": '" . $args->{legend}->[$s_count] . "'<br />\n";
    }

    # Build the graph.
    my $graph;
    my $height = $args->{height} || $default_height;
    my $width = $args->{width} || $default_width;
    my $legend_spacing = 2;
    # GD:Graph uses height to determing the height of the whole graph, legend included.  This increases
    # the height based on the number of lines, so the graph portion is always the same height.
    if (!$args->{nolegend}) {
        $height = $height + ((10 + $legend_spacing) * scalar(keys %subs)) + 15;
    }
    if ($args->{type} eq 'area') {
        $graph = GD::Graph::area->new($width, $height);
        $args->{cumulate} = 1;
    } else {
        $graph = GD::Graph::lines->new($width, $height);
    }

    $args->{y_label} = $y_labels->{$args->{graph_id}};

    my $skip = int(scalar(@{$data[0]} * $label_width)/($width - $label_width) + 1);
    $graph->set(
            x_label => '',
            b_margin => 15,
            x_label_skip => $skip,
            x_tick_offset => (scalar(@{$data[0]}) % $skip) ,
            y_number_format => \&y_number_format,
            fgclr => 'lgray',
            x_labels_vertical => 0,
            y_label => $args->{y_label},
            title => ($args->{notitle}?'':$args->{title}),
            cumulate => $args->{cumulate},
            legend_placement => 'BL',
            legend_spacing => $legend_spacing,
            lg_cols => 1,
            long_ticks => 1,
            transparent => 0,
            line_width=>3,
            skip_undef=>1,
            r_margin=> int($label_width/2)
        ) or die $graph->error;

    if (!$args->{nolegend}) {
        $graph->set_legend(@{$args->{legend}});
    }

    my $gd = $graph->plot(\@data);
    if (!$gd) {
        if ($graph->error =~/Vertical size too small/) {
            $args->{height} += 50;
            gd_graph($args);
            return;
        } else {
            die $graph->error;
        }
    }

    if (!$args->{nofooter}) {
        my $arch = `arch`;
        chomp($arch);
        my $total_elapsed = tv_interval($args->{total_start_time});
        my $footer = localtime(time) . " ($arch,$args->{source})";
        $gd->string(gdSmallFont,10,$height-15,$footer,$gd->colorAllocate(0,0,0));
        $footer = sprintf("%.4fs", $total_elapsed);
        $gd->string(gdSmallFont,$width-50,$height-15,$footer,$gd->colorAllocate(0,0,0));
    }

    print "Content-type: image/png\n\n";
    print STDOUT $gd->png;
    return;
}

sub y_number_format {
    my $value = shift;
    my $ret;
    my $suffix;

    my @big_suffixes = ('k','M','G','T','P');
    my @small_suffixes = ('m','u');

    if (abs($value) > 1) {
        while ( int($value/1000) == $value/1000) {
            $value = $value / 1000;
            $suffix = shift(@big_suffixes);
        }
    } elsif (abs($value) > 0) {
        while (abs($value) < 1) {
            $value = $value * 1000;
            $suffix = shift(@small_suffixes);
        }
    }
    return "$value$suffix";
}

