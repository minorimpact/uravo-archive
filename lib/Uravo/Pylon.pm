package Uravo::Pylon;

use Socket;
use Data::Dumper;

sub pylon {
    my $params = shift || return;

    my $command = $params->{command} || return;
    my $remote = $params->{remote} || "localhost";
    my $port = $params->{port} || 5555;

    my ($iaddr, $paddr, $proto);

    $iaddr   = inet_aton($remote) || die "no host: $remote";
    $paddr   = sockaddr_in($port, $iaddr);

    $proto   = getprotobyname('tcp');
    socket(SOCK, PF_INET, SOCK_STREAM, $proto) || die "socket: $!";
    connect(SOCK, $paddr) || die "connect: $!";

    select(SOCK);
    $| = 1;
    select(STDOUT);
    my $strlen = length($command);
    print SOCK "$command|EOF\n";

    my $response = '';
    while (my $line = <SOCK>) {
        if ($line eq "\n") {
            last;
        }
        $response .= $line;
    }
    #$response = <SOCK>;
    close(SOCK);

    return $response;
}

1;
