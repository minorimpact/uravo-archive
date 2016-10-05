#!/usr/bin/perl

use lib '/usr/local/uravo/lib';
use Uravo;

use Getopt::Long;

my $uravo = new Uravo;
my @args;
my $delim   = "\n";

GetOptions("delim=s", \$delim,
           "help", sub { usage(); },
           "flat", sub { $delim=' ' },
         ) || usage();


eval { &main(); };
print "$@\n" if ($@);
exit;


sub main {
    my $action  = shift @ARGV;
    my $params;

    $params->{id_only} = 1;

    foreach my $param (@ARGV)  {
        if ($param =~ /^(\w+)=(\S+)$/) {
            $params->{$1}  = $2;
        } else {
            push @args, $param;
        }
    }
    eval "do_$action(\$params, \@args);";
    print "$@\n" if ($@);
    print "\n";
}

sub do_list {
    my $params  = shift;
    if (!defined($params->{silo}) && !defined($params->{silo_id})) {
        $params->{all_silos} = 1;
    }

    foreach my $arg (@_) {
        if ($arg eq "clusters") {
            print join($delim, $uravo->getClusters($params, {id_only=>1}));
        }
        if ($arg eq "servers" ) {
            print join($delim, $uravo->getServers($params, {id_only=>1}));
        }
        if ($arg eq "types" ) {
            print join($delim, $uravo->getTypes($params, {id_only=>1}));
        }
    }
}

sub usage {
    my $error       = shift;
    $0              =~/([^\/]+)$/;
    my $shortname   = $1 || $0;

    print "$error" if ($error);
    print "\n" unless (!$error || $error =~/\n$/);
    print <<USAGE;
usage: $shortname [options] <command> [parameter [...] ]

OPTIONS
    --flat          Print the results horizontally (space delimited) rather than
                    vertically (\\n delimited).
    --help          Display this message.

COMMANDS
    One of the following must be passed to $shortname:
        list servers    
        list clusters
        list types

PARAMETERS
    Parameters can be passed to various commands in the form of a 'name=value' pairs.
    See the following examples.

EXAMPLES
    Print a list of clusters:
        $ $shortname list clusters
        cluster_id_1
        cluster_id_2

    Print a list of servers for a given cluster:
        $ $shortname list servers cluster=cluster_id_1
        server_id_1
        server_id_2

    Print a list of all servers, horizontally:
        $ $shortname --flat list servers 
        server_id_1 server_id_2 server_id_3 server_id_4

    Show all the servers of a particular type in a particular cluster:
        $ $shortname list servers type=type_id_1 cluster=cluster_id_2
        server_id_3

    Display the servers that are not of a certain type:
        $ $shortname list servers type=\!type_id_1
        server_id_1
        server_id_2
        server_id_4

       (Note the backslash to escape the '!' character.  Shells do weird things with
        '!'s.)


USAGE
    exit;
}
