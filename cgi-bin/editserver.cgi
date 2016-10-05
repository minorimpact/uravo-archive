#!/usr/bin/perl

use strict;
use lib "/usr/local/uravo/lib";
use CGI;
use Uravo;
use Data::Dumper;

eval { &main(); };
print "Content-type: text/html\n\n$@\n" if ($@);
exit;

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;
    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $server_id       = $form->{server_id};
    my $save            = $form->{save};

    my $server = $uravo->getServer($server_id);
    if (!$server_id || !$server ) {
        print "Location: index.cgi\n\n";
        return;
    }

    if ($save) {
        my $changelog = {user=>$user,ticket=>$form->{ticket}, note=>$form->{note}};
        $server->update({position=>$form->{position},
                         check_conn=>($form->{check_conn})?1:0,
                         serial_number=>$form->{serial_number},
                         comments=>$form->{comments},
                         server_model=>$form->{server_model},
                         type_id=>[ split(/\0/, $form->{type_id})],
                         cluster_id=>$form->{cluster_id},
                         asset_tag=>$form->{asset_tag},
                         rack_id=>$form->{rack_id},
                         hostname=>$form->{hostname},
        },$changelog);

        foreach my $param (keys %$form) {
            next unless ($form->{$param});

            # Add new interface
            if ($param =~ /^int_network_new$/) {
                my @interface_alias = ();
                foreach my $interface_alias (split(/\0/, $form->{interface_alias_new})) {
                    next unless ($interface_alias && $interface_alias ne 'new DNS alias');
                    my $server = $uravo->getServer($interface_alias);
                    push(@interface_alias, $interface_alias) unless ($server);
                }

                if ($form->{'int_network_new'} && ($form->{int_ip_new} || $form->{int_mac_new})) {
                    $server->addInterface({ip=>$form->{'int_ip_new'}, network=>$form->{'int_network_new'}, netblock_id=>$form->{'int_netblock_id'}, mac=>$form->{'int_mac_new'}, name=>$form->{'int_name_new'}, main=>$form->{'int_main_new'}, icmp=>$form->{'int_icmp_new'}, interface_alias=>\@interface_alias}, $changelog);
                }
            }

            # Edit interfaces.
            if ($param =~ /^int_network_([0-9]+)$/) {
                my $interface_id = $1;
                my $interface = $server->getInterface($interface_id);
                my @interface_alias = ();
                foreach my $interface_alias (split(/\0/, $form->{"interface_alias_$interface_id"})) {
                    next unless ($interface_alias && $interface_alias ne 'new DNS alias');
                    my $server = $uravo->getServer($interface_alias);
                    push(@interface_alias, $interface_alias) unless ($server);
                }
                if ($interface) {
                    $interface->update({main=>$form->{"int_main_$interface_id"},
                                    icmp=>$form->{"int_icmp_$interface_id"},
                                    ip=>$form->{"int_ip_$interface_id"},
                                    mac=>$form->{"int_mac_$interface_id"},
                                    netblock_id=>$form->{"int_netblock_$interface_id"},
                                    network=>$form->{"int_network_$interface_id"},
                                    name=>$form->{"int_name_$interface_id"},
                                    interface_alias=>\@interface_alias},$changelog);
                }
            }

            # Delete interfaces.
            if ($param =~ /^int_delete_([0-9]+)$/) {
                $server->deleteInterface({interface_id=>$1},$changelog);
            }
        }

        print "Location: server.cgi?server_id=$server_id\n\n";
        return;
    }

    print "Content-type: text/html\n\n";
    my %checkboxes = ();
    $checkboxes{check_conn} = ($server->get('check_conn'))?"checked":"";
    $checkboxes{check_snmp} = ($server->get('check_snmp'))?"checked":"";
    
    my $cluster_id = $server->cluster_id();
    my $clusterSelect;
    foreach my $id (sort { lc($a) cmp lc($b); } $uravo->getClusters({id_only=>1, all_silos=>1})) {
        $clusterSelect   .= "<option value='$id'";
        $clusterSelect   .= " selected" if ($id eq $cluster_id);
        $clusterSelect   .= ">$id</option>\n";
    }

    my $rack_id = $server->get('rack_id');
    my $rackSelect;
    foreach my $id (sort { lc($a) cmp lc($b); } $uravo->getRacks({id_only=>1})) {
        $rackSelect .= "<option value='$id'";
        $rackSelect .= " selected" if ($id eq $rack_id);
        $rackSelect .= ">$id</option>\n";
    }

    my %types = map { $_=>1; } $server->getTypes({id_only=>1});
    my $typeOptions;
    foreach my $type_id (sort $uravo->getTypes({id_only=>1})) {
            $typeOptions   .= "<option value='$type_id'";
            $typeOptions   .= " selected" if ($types{$type_id});
            $typeOptions   .= ">$type_id</option>\n";
    }

    my $server_models_data = $uravo->{db}->selectall_arrayref("SELECT * FROM hardware_detail ORDER BY id", {Slice=>{}});
    my $server_model_select = "<select name='server_model'><option></option>\n";
    foreach my $data (@$server_models_data) {
        $server_model_select .= "<option " . (($server->get('server_model') eq $data->{id})?" selected":'') . ">" . $data->{id} . "</option>\n";
    }
    $server_model_select .= "</select>\n";

    print <<HEAD;
<head>
    <title>Edit Server:$server_id</title>
    <link rel="stylesheet" href="/uravo.css">
    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>

    <script>
        var newip;

        function add_new_interface() {
            \$("#add_new_interface").show();
            \$("#add_new_interface_alias").show();
            \$("#add_new_interface_link").hide();
        }

        \$(function () {
            \$( "#save-dialog" ).dialog({
                autoOpen: false,
                height: 350,
                width: 375,
                modal: true,
                buttons: {
                    "Save Changes": function() {
                        \$("#note").val(\$( "#save-dialog-note").val());
                        \$("#ticket").val(\$( "#save-dialog-ticket").val());
                        \$( this ).dialog( "close" );
                        \$( "#editserver").submit();
                    },
                    Cancel: function() {
                        \$( this ).dialog( "close" );
                    }
                }
            });
            \$( "#save-changes").button().click(function(e) {
                e.preventDefault();
                \$("#save-dialog").dialog("open");
            });

            \$( "#newip-dialog" ).dialog({
                autoOpen: false,
                height: 350,
                width: 375,
                modal: true,
                buttons: {
                    "Add IP": function() {
                        var interface_id = \$(this).data('interface_id');
                        var address_field = \$("#int_ip_" + interface_id);
                        address_field.val(newip);
                        \$("#int_network_" + interface_id).val(\$( "#newip-dialog-network").val());
                        \$("#int_netblock_" + interface_id).val(\$( "#newip-dialog-netblock").val());
                        \$( this ).dialog( "close" );
                    },
                    Cancel: function() {
                        \$( this ).dialog( "close" );
                    }
            }});
 
            \$( ".newip-button").button().click(function(e) {
                e.preventDefault();
                \$("#newip-dialog-network").html('');
                \$("#newip").html('');
                \$.getJSON("API/network.cgi",function(data) {
                    for (var i=0; i<data.length; i++) {
                        var network = data[i];
                        \$("#newip-dialog-network").append("<option>" + network + "</option>");
                    }
                    loadNetblocks();
                });

                var id = \$(this).attr('id');
                var re = /_([^_]+)\$/;
                var match = re.exec(id);
                if (!match) {
                    return;
                }
                var interface_id = match[1];
                \$("#newip-dialog").data('interface_id',interface_id).dialog("open");
            });

            \$("#newip-dialog-network").change(loadNetblocks);
            \$("#newip-dialog-netblock").change(getNewip);

            \$( "#delete-server").button().click(function(e) {
                e.preventDefault();
                if(confirm('Are you sure you want to delete $server_id?')) { 
                    self.location='deleteserver.cgi?server_id=$server_id';
                }
            });

            \$( ".interface_alias_cell").on( {
                keyup: function() {
                    var name = \$(this).attr("name");
                    var re = /_([^_]+)\$/;
                    var match = re.exec(name);
                    if (!match) {
                        return;
                    }
                    var interface_id = match[1];

                    var blank = 0;
                    \$(this).closest("td").find("input").each(function() {
                        if (\$(this).val() == '' || \$(this).val() == 'new DNS alias') {
                            blank++;
                            if (blank > 1) {
                                \$(this).remove();
                                blank--;
                            }
                        }
                    });
                    if (!blank) {
                        \$(this).closest("td").append("<input type=text name='interface_alias_" + interface_id + "' value='' style='float:left;'>");
                    }
                }
            }, 'input');

            \$("input.dim").one('focus', function() {
                \$(this).removeClass(\"dim\");
                \$(this).val(\"\");
            });


            \$("select.int_network").change(function () {
                var id = \$(this).attr('id');
                var network = \$(this).val();
                var re = /_([^_]+)\$/;
                var match = re.exec(id);
                if (!match) {
                    return;
                }
                var interface_id = match[1];
                \$("#int_netblock_" + interface_id).html('');
                if (!network) {
                    return;
                }
                \$.getJSON("/serverroles/API/netblock?server_id=$server_id&available=1&network=" + network, function(data) {
                    for (var i=0; i<data.length; i++) {
                        var netblock_id = data[i];
                        \$.getJSON("/serverroles/API/netblock?netblock_id=" + netblock_id, function(netblock_data) {
                            \$("#int_netblock_" + interface_id).append("<option value='" + netblock_data.netblock_id + "'>" + netblock_data.address + "</option>");
                        });
                    }
                });
            });

            // Prevent the backspace key from navigating back.
            \$(document).unbind('keydown').bind('keydown', function (event) {
                var doPrevent = false;
                if (event.keyCode === 8) {
                    var d = event.srcElement || event.target;
                    if ((d.tagName.toUpperCase() === 'INPUT' && (d.type.toUpperCase() === 'TEXT' || d.type.toUpperCase() === 'PASSWORD' || d.type.toUpperCase() === 'FILE')) || d.tagName.toUpperCase() === 'TEXTAREA') {
                        doPrevent = d.readOnly || d.disabled;
                    } else {
                        doPrevent = true;
                    }
                }

                if (doPrevent) {
                    event.preventDefault();
                }
            });
            \$("#add_new_interface").hide();
            \$("#add_new_interface_alias").hide();
        });

        function loadNetblocks() {
            \$("#newip-dialog-netblock").html('');
            var network = \$("#newip-dialog-network").val();
            \$.getJSON("API/netblock.cgi?network=" + network + "&server_id=$server_id&available=1",function(data) {
                for (var i=0; i<data.length; i++) {
                    var netblock = data[i];
                    \$("#newip-dialog-netblock").append("<option>" + netblock + "</option>");
                }
                getNewip();
            });
        }

        function getNewip() {
            var netblock = \$("#newip-dialog-netblock").val();
            \$.getJSON("API/newip.cgi?netblock_id=" + netblock, function(data) { \$("#newip").html("ip:" + data[0]); newip=data[0]; });
        }
    
    </script>
</head>
HEAD

    my $row = 1;
    print $uravo->menu();
    print <<DATA;
<div id=links>
</div>
<div id=content>
    <h1>$server_id</h1>
    <form method=POST name="editserver" id="editserver">
    <input type="hidden" value="$server_id" name="server_id">
    <input type="hidden" id="ticket" name="ticket">
    <input type="hidden" id="save" name="save" value="1">
    <input type="hidden" id="note" name="note">
    <fieldset>
        <p>
        <label for=hostname>
            Hostname
            <span class="fielddesc">Actual hostname of the server.</span>
        </label>
        <input type=text name=hostname id=hostname value="${\ $server->get('hostname'); }">
        </p>

        <p>
        <label for=comments>
            Comments
            <span class="fielddesc">Notes and information specific to this device.</span>
        </label>
        <textarea name=comments id=comments rows=5 cols=55>${\ $server->get('comments'); }</textarea>
        </p>

        <p>
        <label for=rack_id>
            Rack
            <span class="fielddesc">Where does this device live?</span>
        </label>
        <select name=rack_id id=rack_id>$rackSelect</select>
        </p>

        <p>
        <label for=position>
            Position
            <span class="fielddesc">Rack position.</span>
        </label>
        <input type=text id=position name=position value="${\ $server->get('position'); }" maxlength=2 size=3>
        </p>

        <p>
        <label for=asset_tag>
            Asset Tag
            <span class="fielddesc"></span>
        </label>
        <input type=text id=asset_tag name=asset_tag value="${\ $server->get('asset_tag'); }">
        </p>

        <p>
        <label for=serial_number>
            Serial Number
            <span class="fielddesc"></span>
        </label>
        <input type=text id=serial_number name=serial_number value="${\ $server->get('serial_number'); }">
        </p>

        <p>
        <label for=cluster_id>
            Cluster
            <span class="fielddesc"></span>
        </label>
        <select name=cluster_id id=cluster_id>$clusterSelect</select>
        </p>

        <p>
            <label for=type_id>
                Types
                <span class=fielddesc>Use CMD or ALT to select multiple types.</span>
            </label>
            <select name=type_id id=type_id multiple=multiple>$typeOptions<select>
        </p>

        <h2>Monitoring</h2>
        <p>
        <label for=chech_conn>
            Check ICMP?
            <span class="fielddesc">Override ping checking for this server.</span>
        </label>
        <input type=checkbox name=check_conn $checkboxes{check_conn}>
        </p>

        <p>
        <label for=check_snmp>
            Check SNMP?
            <span class="fielddesc">Override SNMP monitoring for this server.</span>
        </label>
        <input type=checkbox name=check_snmp $checkboxes{check_snmp}>
        </p>

        <h2>Hardware</h2>
        <p>
            <label for=server_model>
                Server Model
                <span class=fielddesc></span>
            </label>
            $server_model_select
        </p>

        <h2>Interfaces</h2>
            <table>
                <tr>
                    <th></th>
                    <th>IP</th>
                    <th></th>
                    <th>MAC</th>
                    <th>Name</th>
                    <th>Network</th>
                    <th>Main</th>
                    <th>ICMP</th>
                </tr>
DATA

    my @interfaces = $server->getInterfaces();
    foreach my $interface (@interfaces) {
        my $interface_id = $interface->id();
        print "<input type=hidden id=int_netblock_$interface_id name=int_netblock_$interface_id>\n";
        print "<tr>\n";
        print "<td><input type='checkbox' name='int_delete_$interface_id' id='int_delete_$interface_id'/></td>\n";
        print "<td><input type='text' value='" . $interface->get('ip') . "' maxlength='15' size='15' name='int_ip_$interface_id' id='int_ip_$interface_id'/></td>\n";
        print "<td><button id=int_newip_$interface_id class='newip-button'>New IP</button></td>\n";
        print "<td><input type='text' value='" . $interface->get('mac') . "' maxlength='17' size='17' name='int_mac_$interface_id' id='int_mac_$interface_id'/></td>\n";
        print "<td><input type='text' value='" . $interface->get('name') . "' name='int_name_$interface_id' id='int_name_$interface_id'/></td>\n";
        print "<td><select id=int_network_$interface_id name=int_network_$interface_id>";
        foreach my $network (sort {lc($a->{network}) cmp lc($b->{network})} $uravo->getNetworks()) {
            print "<option value='$network->{network}'";
            print " selected" if ($network->{network} eq $interface->get('network'));
            print ">$network->{network}</option>\n";
        }
        print "</select></td>\n";
        print "<td><input type='checkbox' " . ($interface->get('main')?"checked":"") . " name='int_main_$interface_id' id='int_main_$interface_id'/></td>\n";
        print "<td><input type='checkbox' " . ($interface->get('icmp')?"checked":"") . " name='int_icmp_$interface_id' id='int_icmp_$interface_id'/></td>\n";
        print "</tr>\n";
        print "<tr><td></td><td colspan=7 class=interface_alias_cell>\n";
        foreach my $alias ($interface->interface_alias()) {
            print "<input type=text name=interface_alias_$interface_id value='$alias' style='float:left;'>\n";
        }
        print "<input type=text value='new DNS alias' name='interface_alias_$interface_id' class=dim style='float:left;'>\n";
        print "</td></tr>\n";
    }

    print qq(<tr id='add_new_interface'>
                    <td></td>
                    <td><input type='text' value='' maxlength='15' size='15' name='int_ip_new' id='int_ip_new'/></td>
                    <td><button id=int_newip_new class='newip-button'>New IP</button></td>
                    <input type=hidden id=int_netblock_new name=int_netblock_new>
                    <input type=hidden id=int_network_new name=int_network_new>
                    <td><input type='text' value='' maxlength='17' size='17' name='int_mac_new' /></td>
                    <td><input type='text' value='' name='int_name_new' maxlength='50'/></td>
                    <td></td>
                    <td><input type='checkbox' name='int_main_new' /></td>
                    <td><input type='checkbox' name='int_icmp_new' /></td>
                </tr>
                <tr id='add_new_interface_alias'>
                    <td></td>
                    <td colspan=7 class=interface_alias_cell><input type=text name=interface_alias_new class=dim value='new DNS alias'></td>
                </tr>

                <tr>
                    <td valign='top' align='right'>
                        <img src='/images/delete_arrow.png'>
                    </td>
                    <td>
                        Delete Selected
                    </td>
                    <td colspan='2'>
                        <a id='add_new_interface_link' href="javascript:add_new_interface();">Add New Interface</a>
                    </td>
                </tr>
            </table>

        <p>
            <button id="save-changes">Save Changes</button>
            <button id="delete-server">Delete this Server</button>
        </p>
    </fieldset>
</form>
</div>

<div id="save-dialog" title="Save Changes">
    <form>
        <fieldset>
            <label for="save-dialog-ticket">Ticket</label>
            <input type="text" name="save-dialog-ticket" id="save-dialog-ticket" value="" class="text ui-widget-content ui-corner-all" />
            <label for="save-dialog-note">Note</label>
            <input name="save-dialog-note" id="save-dialog-note" value="" class="text ui-widget-content ui-corner-all" maxlength=50/>
        </fieldset>
    </form>
</div>

<div id="newip-dialog" title="New IP">
    <form>
        <fieldset>
            <label for="newip-dialog-network">Network</label>
            <select id='newip-dialog-network' name="newip-dialog-network" class="select ui-widget-content ui-corner-all"><option></option></select>
            <label for="newip-dialog-netblock">Netblock</label>
            <select id='newip-dialog-netblock' name="newip-dialog-netblock" class="select ui-widget-content ui-corner-all"><option></option></select>
        </fieldset>
    </form>
    <span id=newip class=newip></span>
</div>

</body>
</html>);
}
