#!/usr/bin/perl 

use lib "/usr/local/uravo/lib";
use Uravo;
use CGI;

eval { &main(); };
print "Content-type: text/html\n\n$@" if ($@);
exit;

sub main {
    my $uravo  = new Uravo;
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $cluster_id = $form->{'cluster_id'};
    my $type_id = $form->{'type_id'};

    my $server_model_select = "<select name='server_model'><option></option>\n";
    my $server_models_data = $uravo->{db}->selectall_arrayref("SELECT * FROM hardware_detail ORDER BY id", {Slice=>{}});
    foreach my $data (@$server_models_data) {
        $server_model_select .= "<option value='" . $data->{id} . "'>" . $data->{id} . "</option>\n";
    }
    $server_model_select .= "</select>\n";

    if ($form->{'update'} && $cluster_id && $type_id) {
        my $new_cluster_id = $form->{'new_cluster_id'};
        my $new_type_id = $form->{'new_type_id'};
        foreach my $key (keys %$form) {
            if ($key =~/^server_(.+)$/) {
                my $server = $uravo->getServer($1);
                if ($server) {
                    my $comments = $server->get('comments');
                    if ($form->{comments}) {
                        $comments = $form->{comments} ."\n$comments";
                    }
                            
                    my $changelog = {user=>$user, ticket=>$form->{'ticket'}, note=>$form->{'note'}};
                    $server->update({cluster_id=>$new_cluster_id, type_id=>[$new_type_id], comments=>$comments,server_model=>$form->{'server_model'}},$changelog);
                }
            }
        }
        $cluster_id = $new_cluster_id;
        $type_id = $new_type_id;
    }

    print "Content-type: text/html\n\n";
    print <<HEAD;

<!DOCTYPE HTML>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="/uravo.css" />
    <title>Update Multiple Servers</title>
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
    <script src="/js/serverroles.js"></script>

    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <style>
        body { height: 100%; font-family:Sans-serif; }
        #wrapper { min-height: 100%; position:relative; }
        #menu { position: relativel height:100%; padding-top: 50px; }
        #container { position: relative; height: 100%; padding-bottom: 20px; padding-top:50px; }
        #header { width:100%; position:fixed; top:0px; margin:auto; z-index:100000; height: 50px; background-color:rgba(255,255,255,0.7);} 
        #footer { width:95%; position:fixed; bottom:0; height: 20px; background-color:rgba(255,255,255,0.7); }

        label, input, textarea { display:block; }
        input.text, input.textarea { margin-bottom:12px; width:95%; padding: .4em; }
        fieldset { padding:0; border:0; margin-top:25px; }
        .server_list { border-spacing:0; }
        .server_list tr:nth-child(even) { background-color:${\ $uravo->color('menu'); };}
        .server_list td,th { padding-right:10px; }
        .menu_link { font-weight:bold; }
        .dim { color:grey; }
        .hidden { display:none; }
    </style>
</head>
HEAD
    print $uravo->menu();
    print <<FORM;
    <div align='center' id='wrapper'>
        <div id='container'>
            <form id='serverlist' name='serverlist' method='POST'>
                <input type="hidden" id="ticket" name="ticket">
                <input type="hidden" id="note" name="note">
                <input type="hidden" name="update" value=1>

                Select cluster and type:<br />
                <select id=cluster_id name="cluster_id"></select>
                <select id=type_id name="type_id"></select>

                <table id="server_list" border=0 class="server_list hidden">
                    <thead>
                        <tr>
                            <th><input id=checkall type='checkbox'</th>
                            <th><b>Server</b></th>
                            <th><b>Frontnet&nbsp;IP</b></th>
                            <th><b>Backnet&nbsp;IP</b></th>
                            <th><b>OS</b></th>
                            <th><b>Model</b></th>
                            <th><b>Comments</b></th>
                        </tr>
                    </thead>
                    <tbody>
                    </tbody>
                </table>
                <br />
                        Update selected servers:<br />
                <table>
                    <tr>
                        <td align="right"> <b>New Cluster:</b> </td>
                        <td>
                            <select id=new_cluster_id name="new_cluster_id"></select>
                        </td>
                    </tr>
                    <tr>
                        <td align="right"> <b>New Type:</b> </td>
                        <td>
                            <select id=new_type_id name="new_type_id"></select>
                        </td>
                    </tr>
                    <tr>
                        <td align="right"> <b>Server Model:</b> </td>
                        <td>
                            $server_model_select
                        </td>
                    </tr>
                    <tr>
                        <td align="right" valign="top"> <b>Prepend Comments:</b> </td>
                        <td>
                            <textarea rows="4" cols="50" name="comments"></textarea>
                        </td>
                    </tr>
                </table>
            </form>
                        <button id='update'>Update</button> 
        </div> 
    </div>
    <div id="save-dialog" title="Save Changes">
        <form>
            <fieldset>
                <lable for="save-dialog-ticket">Ticket</label>
                <input type="text" name="save-dialog-ticket" id="save-dialog-ticket" value="" class="text ui-widget-content ui-corner-all" />
                <lable for="save-dialog-note">Note</label>
                <input name="save-dialog-note" id="save-dialog-note" value="" class="text ui-widget-content ui-corner-all" maxlength=50/>
            </fieldset>
        </form>
    </div>

<script>
    var default_cluster_id = "$cluster_id";
    var default_type_id = "$type_id";

    \$(function() {
        \$("#cluster_id").change(loadTypes);
        \$("#type_id").change(serverList);
        \$("#checkall").on('click',
            function() {
                \$(this).closest('table').find(":checkbox").prop("checked", this.checked);
            }
        );
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
                \$( "#serverlist").submit();
            },
            Cancel: function() {
              \$( this ).dialog( "close" );
            }
          }
        });
        \$( "#update").button().click(function() {
            \$("#save-dialog").dialog("open");
        });

        loadClusters();
    });
    
    function loadClusters() {
        \$.getJSON("/cgi-bin/API/cluster.cgi",
            function(data) { 
                var cluster_id = data[0];
                \$.each(data, function(id,value) {
                    var option = "<option value='" + value + "'";
                    if (value == default_cluster_id) {
                        option = option + " selected";
                    }
                    option = option + ">" + value + "</option>";
                    \$("#cluster_id").append(option);
                    \$("#new_cluster_id").append(option);
                });
                //default_cluster_id = '';

                \$.getJSON("/cgi-bin/API/type.cgi",
                    function(data) {
                        \$("#new_type_id").html('');
                        \$.each(data, function(id,value) {
                            var option = "<option value='" + value + "'";
                            if (value == default_type_id) {
                                option = option + " selected";
                            }
                            option = option + ">" + value + "</option>";
                            \$("#new_type_id").append(option);
                        });
                        //default_type_id = '';
                    }
                );
                loadTypes();
            }
        );
    }

    function loadTypes() {
        var cluster_id = \$("#cluster_id").val();
        \$("#new_cluster_id").val(cluster_id);
        \$.getJSON("/cgi-bin/API/type.cgi?cluster_id=" + cluster_id,
            function(data) {
                \$("#type_id").html('');
                \$.each(data, function(id,value) {
                    var option = "<option value='" + value + "'";
                    if (value == default_type_id) {
                        option = option + " selected";
                    }
                    option = option + ">" + value + "</option>";
                    \$("#type_id").append(option);
                });
                //default_type_id = '';
                serverList();
            }
        );
    }

    function serverList() {
        var cluster_id = \$("#cluster_id").val();
        var type_id = \$("#type_id").val();
        \$("#new_type_id").val(type_id);
        \$("#server_list tbody").html('');
        \$("#server_list").removeClass("hidden");
        \$.getJSON("/cgi-bin/API/server.cgi?cluster_id=" + cluster_id + "&type_id=" + type_id,
            function(data) {
                \$.each(data, 
                    function(id,value) {
                        \$.getJSON("/cgi-bin/API/server.cgi?server_id=" + value,
                            function(data) {
                                \$("#server_list tbody").append("<tr><td><input type=checkbox name=server_" + data.server_id + " id=server_" + data.server_id + "></td><td><a href=server.cgi?server_id=" + data.server_id + ">" + data.server_id + "</td><td>" + data.ip + "</td><td>" + data.backnet_ip + "</td><td>" + data.os_vendor + "/" + data.os_version + "</td><td>" + data.server_model + "</td><td>" + data.comments + "</td></tr>");
                            }
                        );
                    }
                );
            }
        );
    }
</script>
FORM
}

