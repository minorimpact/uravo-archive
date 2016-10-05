#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;
use Data::Dumper;

main();

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $save = $form->{"save"};
    my $form_AlertGroup = $form->{"AlertGroup"};
    my $form_AlertKey = $form->{"AlertKey"};
    my $error;

    print "Content-type: text/html\n\n";
    if ($save) {
        my %values = ();
        my $table;
        my $id;
        my $name;
        foreach my $key (keys %$form) {
            if ($key =~ /^([^_]+),([^_]+),(.+)$/) {
                $values{$1}{$2}{$3} = $form->{$key};
            }
        }

        my $sql = "update monitoring_default_values set yellow=?,red=?,disabled=? where id=?";
        my $insert = $uravo->{db}->prepare($sql);
        my $default_yellow;
        my $default_red;
        my $default_timeout;
        foreach my $id (keys %{$values{defaults}}) {
            $default_yellow = $values{defaults}{$id}{yellow};
            $default_red = $values{defaults}{$id}{red};
            $insert->execute($values{defaults}{$id}{yellow}, $values{defaults}{$id}{red}, ($values{defaults}{$id}{disabled} eq "on") ?1:0, $id) || die ($uravo->{db}->errstr);
        }

        my $update_sql = "update monitoring_values set yellow=?,red=?,disabled=? where id=?";
        my $update = $uravo->{db}->prepare($update_sql);
        my $delete_sql = "delete from monitoring_values where id=?";
        my $delete = $uravo->{db}->prepare($delete_sql);
        foreach my $id (keys %{$values{values}}) {
            my $yellow = $values{values}{$id}{yellow};
            my $red = $values{values}{$id}{red};
            my $disabled = $values{values}{$id}{disabled};

            if ($id =~/^[0-9]+$/) {
                if ($values{values}{$id}{delete}){
                    $delete->execute($id)  || die ($uravo->{db}->errstr);
                } else {
                    $update->execute($yellow, $red, ($disabled eq "on") ?1:0, $id) || die ($uravo->{db}->errstr);
                }
            } elsif ($id eq 'new') {
                my $type_id = $values{values}{$id}{type_id};
                my $cluster_id = $values{values}{$id}{cluster_id};
                my $server_id = $values{values}{$id}{server_id};

                if ($yellow && $red && ($default_yellow != $yellow || $default_red != $red  || $disabled) && (($cluster_id && $type_id) || $server_id)) {
                    $uravo->{db}->do("insert into monitoring_values (AlertGroup, AlertKey, cluster_id, type_id, server_id, yellow, red, disabled, create_date) values (?, ?, ?, ?, ?, ?, ?, ?, now())", undef, ($form_AlertGroup, $form_AlertKey, $cluster_id, $type_id, ($server_id || undef), $yellow, $red, ($disabled eq "on") ?1:0 ));
                }
            }
        }
    }

    print <<HEAD;
<head>
    <title>Thresholds</title>

    <link rel="stylesheet" type="text/css" href="/uravo.css">
    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />

    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
    <script src="/js/serverroles.js"></script>
    <script>
        \$(function() {
            \$("#cluster_id").change(loadTypes);
            \$("#type_id").change(serverList);

            loadClusters();
        });

        function loadClusters() {
            //\$("#cluster_id").html("<option value=''>any cluster</option>");
            \$("#cluster_id").html('');
            \$.getJSON("API/cluster.cgi",
                function(data) { 
                    for (var i=0; i<data.length; i++) {
                        var value = data[i];
                        var option = "<option value='" + value + "'>" + value + "</option>";
                        \$("#cluster_id").append(option);
                    };
                    loadTypes();
                }
            );
        }

        function loadTypes() {
            var cluster_id = \$("#cluster_id").val();
            //\$("#type_id").html("<option value=''>any type</option>");
            \$("#type_id").html('');
            \$.getJSON("API/type.cgi?cluster_id=" + cluster_id,
                function(data) {
                    for (var i=0; i<data.length; i++) {
                        var value = data[i];
                        var option = "<option value='" + value + "'>" + value + "</option>";
                        \$("#type_id").append(option);
                    }
                    serverList();
                }
            );
        }

        function serverList() {
            var cluster_id = \$("#cluster_id").val();
            var type_id = \$("#type_id").val();
            \$("#server_id").html("<option value=''>any server</option>");
            \$.getJSON("API/server.cgi?cluster_id=" + cluster_id + "&type_id=" + type_id,
                function(data) {
                    for (var i=0;i<data.length;i++) {
                        var value = data[i];
                        \$("#server_id").append("<option value='" + value + "'>" + value + "</option>");
                    }
                }
            );
        }
    </script>
</head>
HEAD

    print $uravo->menu();
    print qq(
<div id=links>
    <ul>
        <li><a href=settings.cgi>Settings</a></li>
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
    <h1>Thresholds</h1>
    <form method='POST'>
        <input type="hidden" name="AlertGroup" value="$form_AlertGroup" />
        <input type="hidden" name="AlertKey" value="$form_AlertKey" />
        <table>
            <tr>
                <th>&nbsp;</th>
                    <th colspan="3">check</th>
                    <th>yellow</th>
                    <th>&nbsp;</th>
                    <th>red</th>
                    <th>&nbsp;</th>
                    <th>disabled</th>
                    <th>&nbsp;</th>
                </tr>
    );
    my $monitoring_default_values_data = $uravo->{db}->selectall_arrayref("SELECT distinct(AlertGroup) FROM monitoring_default_values ORDER BY AlertGroup", {Slice=>{}});
    my $color_modifier = "dark";
    foreach my $data (@$monitoring_default_values_data) {
        my $AlertGroup = $data->{AlertGroup};

        $color_modifier = ($color_modifier eq "light")?"dark":"light";
        print qq(
            <tr>
                <td>&nbsp;</td>
                <td colspan="3"><a href="thresholds.cgi?AlertGroup=$AlertGroup">$AlertGroup</a></td>
                <td colspan="8">&nbsp;</td>
            </tr>
        );
        if ($AlertGroup eq $form_AlertGroup) {
            my $subcheck_monitoring_default_values_data = $uravo->{db}->selectall_arrayref("SELECT id, AlertKey, yellow, red, disabled, description FROM monitoring_default_values WHERE AlertGroup=? ORDER BY AlertKey", {Slice=>{}}, ($AlertGroup));
            foreach my $data (@$subcheck_monitoring_default_values_data) {
                my $id = $data->{id};
                my $AlertKey = $data->{AlertKey} || '';
                my $default_yellow = $data->{yellow};
                my $default_red = $data->{red};
                my $default_disabled = $data->{disabled};
                $color_modifier = ($color_modifier eq "light")?"dark":"light";
                print qq(
                    <tr>
                        <td>&nbsp;</td>
                        <td>&nbsp;</td>
                        <td colspan="2"><a href="thresholds.cgi?AlertGroup=$AlertGroup&AlertKey=$AlertKey">$AlertKey</a></td>
                        <td colspan="6">$data->{description}</td>
                    </tr>
                );
                if ($AlertKey eq $form_AlertKey) {
                    $color_modifier = ($color_modifier eq "light")?"dark":"light";
                    print qq(
                        <tr>
                            <td>&nbsp;</td>
                            <td>&nbsp;</td>
                            <td>&nbsp;</td>
                            <td><b>Default</b></td>
                            <td><input type="text" name="defaults,$id,yellow" value="$default_yellow"></td>
                            <td>&nbsp;</td>
                            <td><input type="text" name="defaults,$id,red" value="$default_red"></td>
                            <td>&nbsp;</td>
                            <td><input type="checkbox" name="defaults,$id,disabled" ${\ ($default_disabled?"checked":""); }></td>
                            <td>&nbsp;</td>
                        </tr>
                    );
                    my $monitoring_values_data = $uravo->{db}->selectall_arrayref("SELECT id, cluster_id, type_id, server_id, yellow, red, disabled FROM monitoring_values WHERE AlertGroup=? and AlertKey=?", {Slice=>{}}, ($AlertGroup, $AlertKey));
                    foreach my $data (@$monitoring_values_data) {
                        my $id = $data->{id};
                        print qq(
                            <tr>
                                <td><input type="checkbox" name="values,$id,delete"></td>
                                <td colspan=2>&nbsp;</td>
                                <td>
                        );
                        if ($data->{server_id} ne '') {
                            print "<a href='/cgi-bin/admin/serverroles/server.cgi?server_id=$data->{server_id}'>$data->{server_id}</a>";
                        } else {
                            print "$data->{cluster_id}/$data->{type_id}"; 
                        }
                        print qq(
                                </td>
                                <td><input type="text" name="values,$id,yellow" value="$data->{yellow}"></td>
                                <td>&nbsp;</td>
                                <td><input type="text" name="values,$id,red" value="$data->{red}"></td>
                                <td>&nbsp;</td>
                                <td><input type="checkbox" name="values,$id,disabled" ${\ ($data->{disabled}?"checked":""); }></td>
                                <td>&nbsp;</td>
                            </tr>
                        );
                    }

                    print qq(
                        <tr>
                            <td>&nbsp;</td>
                            <td>&nbsp;</td>
                            <td>&nbsp;</td>
                            <td>
                                <select id=cluster_id name="values,new,cluster_id"></select><select id=type_id name="values,new,type_id"></select><select id=server_id name="values,new,server_id"></select>
                            </td>
                            <td><input type="text" name="values,new,yellow" value=""></td>
                            <td>&nbsp;</td>
                            <td><input type="text" name="values,new,red" value=""></td>
                            <td>&nbsp;</td>
                            <td><input type="checkbox" name="values,new,disabled"></td>
                            <td>&nbsp;</td>
                        </tr>
                    );
                }
            }
        }
    }
    print qq(
            <tr>
                <td></td>
                <td colspan="9">${\ ($error?"<font color='red'>&nbsp;<b>$error</b></font>":''); }</td>
            </tr>
            <tr>
                <td colspan="10"><input type="submit" value="Save Changes" name="save"></td>
            </tr>
        </table>
        </form>
    </div>
    );
}

