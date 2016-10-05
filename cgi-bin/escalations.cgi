#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Data::Dumper;
use CGI;


eval { &main(); };
print "Content-type: text/html\n\n$@" if ($@);
exit;

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $save = $form->{"save"};
    my $sort = $form->{'sort'} || "id";
    my $error;

    if ($save) {
        my %new_escalation = ();
        foreach my $key (keys %$form) {
            if ($key =~ /^new_(.*)$/) {
                $new_escalation{$1} = $form->{$key};
            }
            if ($key =~ /^delete_([0-9]+)$/) {
                my $id = $1;
                my $sql = "delete from escalations where id=?";
                $uravo->{db}->do($sql, undef, ( $id )) || die ($uravo->{db}->errstr);
            }
        }
        my $field_list = '';
        my @values = ();
        foreach my $field (keys(%new_escalation)) {
            next if ($new_escalation{$field} eq '*' || $new_escalation{$field} eq '');
            $field_list .= "$field, ";
            push(@values, $new_escalation{$field});
        }

        if (scalar(@values) && !$new_escalation{'contact_group'}) {
            $error .= "You must specify a contact group.<br />\n";
        } elsif (scalar(@values) == 1) {
        } elsif (scalar(@values)) {
            $field_list =~s/, *$//;

            my $value_list;
            for (my $i = 0; $i < scalar(@values); $i++) {
                $value_list .= "?, ";
            }
            $value_list =~s/, *$//;

            my $sql = "insert into escalations ($field_list, mod_date, create_date) values ($value_list, now(), now())";
            $uravo->{db}->do($sql, undef, @values);
        }
    }

    print "Content-type: text/html\n\n";
    print <<HEAD;
<head>
    <link rel="stylesheet" type="text/css" href="/uravo.css">
    <title>Escalations</title>
</head>
HEAD
    print $uravo->menu();
    my $cluster_option_list = "<option value='*'>*</option>\n";
    foreach my $cluster_id (sort { lc($a) cmp lc($b) } $uravo->getClusters({id_only=>1})) {
        $cluster_option_list .= "<option value='$cluster_id'>$cluster_id</option>\n";
    }

    my $type_option_list = "<option value='*'>*</option>\n";
    foreach my $type_id ( sort { lc($a) cmp lc($b) } $uravo->getTypes({id_only=>1})) {
        $type_option_list .= "<option value='$type_id'>$type_id</option>\n";
    }

    my $check_data = $uravo->{db}->selectall_arrayref("SELECT distinct(AlertGroup) as AlertGroup FROM alert_summary ORDER BY AlertGroup", {Slice=>{}});
    my $check_option_list = "<option value='*'>*</option>\n";
    foreach my $check (@$check_data) {
        $check_option_list .= "<option value='$check->{AlertGroup}'>$check->{AlertGroup}</option>\n";
    }

    my $contact_data = $uravo->{db}->selectall_arrayref("SELECT * FROM contacts", {Slice=>{}});
    my $group_option_list = "<option value='NONE'>NONE</option>\n";
    foreach my $data (@$contact_data) {
        my $contact_group = $data->{contact_group};
        $group_option_list .= "<option value='$contact_group'>$contact_group</option>\n";
    }

    print <<DATA;
<div id=links>
    <ul>
        <li><a href=settings.cgi>Settings</a></li>
        <li><a href=thresholds.cgi>Thresholds</a></li>
        <li><a href=contacts.cgi>Escalation Contacts</a></li>
        <li><a href=processes.cgi>Processes</a></li>
        <li><a href=rootcause.cgi>Root Causes</a></li>
        <li><a href=actions.cgi>Actions</a></li>
        <li><a href=networks.cgi>Networks</a></li>
    </ul>
</div>
<div id=content>
    <form method='POST'>
<table cellspacing="0" cellpadding="3">
    <tr>
        <td><b>delete</b></td>
        <td>&nbsp;</td>
        <td><b><a href="escalations.cgi?sort=cluster_id">cluster</a></b></td>
        <td>&nbsp;</td>
        <td><b><a href="escalations.cgi?sort=type_id">type</a></b></td>
        <td>&nbsp;</td>
        <td><b><a href="escalations.cgi?sort=AlertGroup">check</a></b></td>
        <td>&nbsp;</td>
        <td><b><a href="escalations.cgi?sort=contact_group">Contact Group</a></b></td>
    </tr>
DATA
    my $escalation_data = $uravo->{db}->selectall_arrayref("SELECT * FROM escalations ORDER BY $sort", {Slice=>{}}) || die($uravo->{db}->errstr);
    my $color_modifier = "dark";
    foreach my $data (@$escalation_data) {
        $color_modifier = ($color_modifier eq "light")?"dark":"light";
        my $cluster_id = $data->{'cluster_id'};
        my $type_id = $data->{'type_id'};
        my $AlertGroup = $data->{'AlertGroup'};
        print <<FORM;
    <tr>
        <td bgcolor="${\ $color_modifier}gray"><input type='checkbox' name='delete_$data->{id}'></td>
        <td bgcolor="${\ $color_modifier}gray">&nbsp;</tb>
        <td bgcolor="${\ $color_modifier}gray">${\ ($cluster_id?$cluster_id:'*'); }</td>
        <td bgcolor="${\ $color_modifier}gray">&nbsp;</tb>
        <td bgcolor="${\ $color_modifier}gray">${\ ($type_id?$type_id:'*'); }</td>
        <td bgcolor="${\ $color_modifier}gray">&nbsp;</tb>
        <td bgcolor="${\ $color_modifier}gray">${\ ($AlertGroup?$AlertGroup:'*'); }</td>
        <td bgcolor="${\ $color_modifier}gray">&nbsp;</tb>
        <td bgcolor="${\ $color_modifier}gray">$data->{'contact_group'}</td>
    </tr>
FORM
    }
    print <<FOOTER;
    <tr>
        <td></td>
        <td>&nbsp;</tb>
        <td><select name="new_cluster_id">$cluster_option_list</select></td>
        <td>&nbsp;</tb>
        <td><select name="new_type_id">$type_option_list</select></td>
        <td>&nbsp;</tb>
        <td><select name="new_AlertGroup">$check_option_list</select></td>
        <td>&nbsp;</tb>
        <td><select name="new_contact_group">$group_option_list</select></td>
        <td>&nbsp;</tb>
    </tr>
    <tr>
        <td></td>
        <td colspan="9">${\ ($error?"<font color='red'><b>$error</b></font>":''); }<br /><br /></td>
    </tr>
    <tr>
        <td colspan="3"><input type="submit" value="Save Changes" name="save"></td>
    </tr>
    <tr>
        <td colspan='10'>
        <h2>Notes</h2>
        <p>
        This page defines which <a href='contacts.cgi'>contact group</a> will receive
        nagios alerts based upon the cluster the server a member of, the type of server it is, and the
        particular check generating the alert.
        </p>
        <p>In addition to the various contact groups, there are two Contact Group settings that will
        prevent notifications.  <b>NONE</b> will simply prevent nagios from sending out notification
        emails.  
        <p>
        For escalation definitions that may overlap, the general rule of precedence is <b>cluster</b>, 
        then <b>type</b>, then <b>check</b>- most specific to least specific. In the case of notifications
        that have been disabled, the rules are evaluated from least specific to most specific, and any
        criteria match that's been disabled will not result in an escalation.
        </p>
        <p>
        For example: If all escalations for servers in the database cluster go to DBA, and all disk
        checks go to DCTech, then an alert for a full disk will go to the DBA group. However, if a third
        rule is added that states all memory checks are NONE, then a database server with a memory
        error will not be sent to anyone.
        </p>
        <p>
        If all notifications have been disabled for a server, then "host-down" notifications will NOT be
        sent out.  If any alerts are not disabled,  notifications will still go out to the contact 
        group specified as the 'Host Down' contact group on the 
        <a href='contacts.cgi'>contact group</a> page.
        </p>
        <p>
        To delete an item, check the box(es) in the column marked 'delete', and click 'Save Changes'.
        </p>
        <p>
        It will take up to 15 minutes for changes on this page to be reflected in nagios.
        </p>
        <p>

        </p>
        </td>
    </tr>
</table>
</form>
</div>
FOOTER
}

