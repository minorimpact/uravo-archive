package Uravo::Config;

my $config_file = "/etc/uravo.conf";

sub new {
    my $self = {};

    open(CONFIG, $config_file);
    while(<CONFIG>) {
        chomp($_);
        next if ($_ eq '');
        next if (/^\s?#/);
        if (my ($key, $value) = (/^([^=]+)=(.*)$/)) {
            $key =~s/^\s+//;
            $key =~s/\s+$//;
            $value =~s/^\s+//;
            $value =~s/\s+$//;
            if ($value =~/^"(.+)"$/) {
                $value = $1;
            }
            my @values = split(/,/, $value);
            $self->{$key} = $values[int(rand(scalar(@values)))] || $value;
        }
    }

    bless($self);
    return $self;
}



