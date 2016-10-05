#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;
use Data::Dumper;

eval {
    main();
};
print "Content-type: text/html\n\n$@" if ($@);

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    print "Content-type: text/html\n\n";
    if ($form->{save}) {
        delete($form->{save});
        if (defined($form->{record_clears})) {
            $form->{record_clears} = 1;
        } else {
            $form->{record_clears} = 0;
        }
        $uravo->update_settings($form);
    }

    print $uravo->menu();

    print <<DATA;
<head>
    <title>Settings</title>
    <link rel="stylesheet" type="text/css" href="/uravo.css">
</head>

<div id=links>
    <ul>
        <li><a href=thresholds.cgi>Thresholds</a></li>
        <li><a href=escalations.cgi>Escalations</a></li>
        <li><a href=contacts.cgi>Contacts</a></li>
        <li><a href=processes.cgi>Processes</a></li>
        <li><a href=rootcause.cgi>Root Causes</a></li>
        <li><a href=actions.cgi>Actions</a></li>
        <li><a href=networks.cgi>Networks</a></li>
        <li><a href=filters.cgi>Filters</a></li>
    </ul>
</div>
<div id=content>
    <h1>Settings</h1>
    <form method='POST'>
    <fieldset>
        <p>
            <label for=alert_timeout>
                Alert Timeout
                <span class="fielddesc">How long before a recurring alert will generate a 'purple' timeout alert, in minutes.</span>
            </label>
            <input type="text" name="alert_timeout" value="$uravo->{settings}->{alert_timeout}" placeholder="20" />
        </p>

        <p>
            <label for=record_clears>
                Record Clear Alerts
                <span class="fielddesc">Log 'green' alerts that don't clear an existing alert?</span>
            </label>
            <input type="checkbox" id=record_clears name="record_clears" ${\ ($uravo->{settings}->{record_clears}?'checked':''); }>
        </p>

        <p>
            <label for=minimum_severity>
                Minimum Severity
                <span class="fielddesc">Default alert minimum level to display on alerts page.</span>
            </label>
            <input type="text" name="minimum_severity" value="$uravo->{settings}->{minimum_severity}" placeholder="$uravo->{settings}->{minimum_severity}" />
        </p>

        <p>
            <label for=from_address>
                From Address
                <span class="fielddesc">Email notifications will come from this address.</span>
            </label>
            <input type="text" name="from_address" value="$uravo->{settings}->{from_address}" placeholder="$uravo->{settings}->{from_address}" />
        </p>

        <p>
            <label for=email_interval>
                Email Interval
                <span class="fielddesc">How often email notifications should go out, in minutes.</span>
            </label>
            <input type="text" name="email_interval" value="$uravo->{settings}->{email_interval}" placeholder="$uravo->{settings}->{email_interval}" />
        </p>

        <p>
            <label for=tsunami_level>
                Purple Tsunami Level
                <span class="fielddesc">How many 'purples' have to exist before a Tsunami alert is triggered.</span>
            </label>
            <input type="text" name="tsunami_level" value="$uravo->{settings}->{tsunami_level}" placeholder="$uravo->{settings}->{tsunami_level}" />
        </p>

        <p>
            <label for=history_to_keepl>
                History to Keep
                <span class="fielddesc">HOw many days of historical data to keep.</span>
            </label>
            <input type="text" name="history_to_keep" value="$uravo->{settings}->{history_to_keep}" placeholder="$uravo->{settings}->{history_to_keep}" />
        </p>

        <p>
            <button class=submit type="submit" name=save value=1>Save Changes</button>
        </p>
    </fieldset>
</form>

</div>
DATA
}

