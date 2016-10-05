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
    my $script_name = "edithardware.cgi";


    my $save = $form->{"save"};
    my $error;

    if ($save) {
        my %new_escalation = ();
        foreach my $key (keys %$form) {
            if ($key =~ /^drac_([0-9]+)$/) {
                my $id = $1;
                my $drac = $form->{$key};
                next unless ($drac);
                $DB->do("UPDATE hardware_detail SET drac_version = ? WHERE id = ?", undef, ($drac, $id));
                if ($DB->errstr()) {
                    $error .= "sql: UPDATE hardware_detail SET drac_version = ? WHERE id = ?<br />\n";
                    $error .= "values: " . join(',', [$drac, $id]) . "<br />\n";
                    $error .= "errstr: " .  $DB->errstr() . "<br />\n";;
                }
            }
        }
    }

    print "Content-type: text/html\n\n";
    print $uravo->menu();
    print <<DATA;
<br /><br />
<form method='POST'>
<table cellspacing="0" cellpadding="3">
    <tr>
        <td><b>ID</b></td>
    </tr>
DATA
    my $hardware_data = $DB->selectall_arrayref("SELECT * FROM hardware_detail ORDER BY id", {Slice=>{}});
    my $color_modifier = "dark";
    foreach my $data (@$hardware_data) {
        $color_modifier = ($color_modifier eq "light")?"dark":"light";
        my $id = $data->{'id'};
        print <<FORM;
    <tr>
        <td bgcolor="${\ $color_modifier}gray">${\ ($id?$id:'*'); }</td>
    </tr>
FORM
    }
    print <<FOOTER;
    <tr>
    </tr>
    <tr>
        <td></td>
        <td colspan="9">${\ ($error?"<font color='red'><b>$error</b></font>":''); }<br /><br /></td>
    </tr>
    <tr>
        <td colspan="3"><input type="submit" value="Save Changes" name="save"></td>
    </tr>
</table>
</form>
FOOTER
}

