#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;
use Data::Dumper;


eval { &main(); };
print "Content-type: text/html\n\n$@" if ($@);
exit;

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $save = $form->{"save"};

    if ($save) {
        foreach my $key (keys %$form) {
            if ($key =~ /^(primary|secondary|tertiary)_(email|pager)_([^_]+)$/) {
                my $field = "$1_$2";
                my $group = $3;
                $uravo->{db}->do("UPDATE contacts SET $field=? where contact_group=?", undef, ($form->{$key}, $group)) || die ($uravo->{db}->errstr); 
            }
            if ($key =~ /^default_contact_group$/) {
                $uravo->{db}->do("UPDATE contacts SET default_group=0 where default_group=1") || die ($uravo->{db}->errstr);
                $uravo->{db}->do("UPDATE contacts SET default_group=1 where contact_group=?", undef, ($form->{$key})) || die ($uravo->{db}->errstr); 
            }
            if ($key =~ /^new_contact_group$/ && $form->{$key}) {
                $uravo->{db}->do("INSERT INTO contacts (contact_group, create_date) values (?, now())", undef, ($form->{$key}))  || die ($uravo->{db}->errstr);
            }
        }
    }

    print "Content-type: text/html\n\n";
    print <<HEAD;
<head>
    <title>Contacts</title>
    <link rel="stylesheet" type=text/css href="/uravo.css">
</head>
HEAD

    print $uravo->menu();
    print <<DATA;
<div id=links>
    <ul>
        <li><a href=settings.cgi>Settings</a></li>
        <li><a href=thresholds.cgi>Thresholds</a></li>
        <li><a href=escalations.cgi>Escalations</a></li>
        <li><a href=processes.cgi>Processes</a></li>
        <li><a href=rootcause.cgi>Root Causes</a></li>
        <li><a href=actions.cgi>Actions</a></li>
        <li><a href=networks.cgi>Networks</a></li>
        <li><a href=filters.cgi>Filters</a></li>
    </ul>
</div>
<div id=content>
<form method='POST'>
<table cellspacing="0" cellpadding="3">
    <tr>
        <td></td>
        <td>&nbsp;</td>
        <td colspan="2" align="center" bgcolor="salmon"><b>Primary</b></td>
        <td>&nbsp;</td>
        <td colspan="2" align="center" bgcolor="green"><b>Secondary</b></td>
        <td>&nbsp;</td>
        <td colspan="2" align="center" bgcolor="blue"><b>Tertiary</b></td>
    </tr>
    <tr>
        <td><b>Contact Group</td>
        <td>&nbsp;</td>
        <td align="center" bgcolor="salmon"><b>email</b></td>
        <td align="center" bgcolor="salmon"><b>pager</b></td>
        <td>&nbsp;</td>
        <td align="center" bgcolor="green"><b>email</b></td>
        <td align="center" bgcolor="green"><b>pager</b></td>
        <td>&nbsp;</td>
        <td align="center" bgcolor="blue"><b>email</b></td>
        <td align="center" bgcolor="blue"><b>pager</b></td>
    </tr>
DATA
    my $contact_data = $uravo->{db}->selectall_arrayref("SELECT * FROM contacts", {Slice=>{}});
    my $default_contact_group_options = "<option value='NONE'>NONE</option>\n";
    my $color_modifier = "dark";
    foreach my $data (sort { lc($a->{contact_group}) cmp lc($b->{contact_group}) } @$contact_data) {
        my $contact_group = $data->{contact_group};
        $default_contact_group_options .= "<option value='$contact_group'";
        if ($data->{'default_group'} && $data->{'default_group'} == 1 ) { $default_contact_group_options .= " selected"; }
        $default_contact_group_options .= ">$contact_group</option>\n";

        print <<FORM;
    <tr>
        <td bgcolor="${\ $color_modifier}gray"><a href=deletecontactgroup.cgi?contact_group=$contact_group><img src=/images/delete.png></a>&nbsp;$contact_group</td>
        <td bgcolor="${\ $color_modifier}gray">&nbsp;</td>
        <td bgcolor="${\ $color_modifier}salmon"><input type="text" maxlength="50" value="$data->{'primary_email'}" name="primary_email_$contact_group" /></td>
        <td bgcolor="${\ $color_modifier}salmon"><input type="text" maxlength="50" value="$data->{'primary_pager'}" name="primary_pager_$contact_group"/></td>
        <td bgcolor="${\ $color_modifier}gray">&nbsp;</td>
        <td bgcolor="${\ $color_modifier}green"><input type="text" maxlength="50" value="$data->{'secondary_email'}" name="secondary_email_$contact_group"/></td>
        <td bgcolor="${\ $color_modifier}green"><input type="text" maxlength="50" value="$data->{'secondary_pager'}" name="secondary_pager_$contact_group"/></td>
        <td bgcolor="${\ $color_modifier}gray">&nbsp;</td>
        <td bgcolor="${\ $color_modifier}blue"><input type="text" maxlength="50" value="$data->{'tertiary_email'}" name="tertiary_email_$contact_group"/></td>
        <td bgcolor="${\ $color_modifier}blue"><input type="text" maxlength="50" value="$data->{'tertiary_pager'}" name="tertiary_pager_$contact_group"/></td>
    </tr>
FORM

    }
    print <<FOOTER;
    </table>
        <td colspan='10'>
        <p>
            <label for=default_contact_group>
                Default Contact Group
                <span class=fielddesc>Any alerts that aren't defined will be emailed to the default contact group.</span>
            </label>
            <select name='default_contact_group'>$default_contact_group_options</select>
        </p>

        <p>
            <label for=new_contact_group>
                New Contact Group
                <span class=fielddesc>Add a new contact group.</span>
            </label>
            <input type=text name=new_contact_group id=new_contact_group>
        </p>

        <p>
            <button id="save-changes" name=save value=1>Save Changes</button>
        </p>

        <p>
            Notifications will be sent on the following schedule:<br />
            First and second alerts: <b>primary email</b><br />
            Third and fourth alerts: <b>primary email & pager, secondary email</b><br />
            Fifth and sixth alerts: <b>primary email & pager, secondary email & pager, tertiary email</b><br />
            Seventh and remaining alerts: <b>primary email & pager, secondary email & pager, tertiary email & pager</b><br />
        </p>
</form>
</div>
FOOTER
}

