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

    my $cluster_id = $form->{'cluster_id'};
    my $type_id = $form->{'type_id'};

print <<HTML;
Content-type: text/html

<!DOCTYPE HTML>
<html>
<head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <title>Graph Picker</title>
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
    <script src="/js/serverroles.js"></script>

    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <style>
        #menu { position: relative; height:100%; padding-top: 50px; }
        #container { position: relative; height: 100%; padding-bottom: 20px; padding-top:50px; }
        #header { width:100%; position:fixed; top:0px; margin:auto; z-index:100000; height: 50px; background-color:rgba(255,255,255,0.7);} 
        #footer { width:95%; position:fixed; bottom:0; height: 20px; background-color:rgba(255,255,255,0.7); }

        body { height: 100%; font-family:Sans-serif; }
        label, input, textarea, checkbox { display:block; }
        label { margin-top: 15px; }
        input.text, input.textarea, input.checkbox { margin-bottom:12px; width:95%; padding: .4em; }
        fieldset { padding:0; border:0; margin-top:25px; }

        .server_list { border-spacing:0; }
        .server_list tr:nth-child(even) { background-color:${\ $uravo->color('menu'); };}
        .server_list td,th { padding-right:10px; }
        .menu_link { font-weight:bold; }
        .dim { color:grey; }
        .hidden { display:none; }
    </style>
</head>
<body>
    <div id='wrapper' style='width:100%; align:center;';>
        <div id="header">
            ${\ $uravo->menu(); }
        </div>
        <div id=graph_select style="width:20%; float:left; margin-top:50px; position:fixed;margin-left:0; text-align:left"></div>
        <div id='container' style="float:left; margin-left:20%;margin-right:20%; align:center;">
            <div id=server_data style='align:center;'>
                Select servers to graph:
                <div id=server_select></div>
                <button id='more_servers'>More Servers</button> 
                <button id='graph'>Graph</button> 
            </div>
        </div> 

        <div id=graph_options style="width:20%; position:fixed; float:left; padding-right:20px; margin-top:50px; margin-left:80%;">
            Set graphing options:
            <fieldset>
            <label for=width>Width</label>
            <input type=text name=width id=width maxlength=4>
            <label for=height>Height</label>
            <input type=text name=height id=height maxlength=4>
            <label for=range>Range</label>
            <select id=range><option>e-1h</option><option>e-2h</option><option>e-4h</option><option selected>e-48h</option><option>e-12d</option><option>e-48d</option><option>e-576d</option></select><br />

            <input type=checkbox id=split style="float:left; vertical-align:middle; margin-top:15px;"><label for=split>Split</label>
            <label for=columns>Columns</label>
            <input type=text name=columns id=columns>
            <label for=vrange>VRange</label>
            <input type=text name=vrange id=vrange>
            <label for=offset>End Date</label>
            <input type=text name=offset id=offset>
            </fieldset>
        </div>
    </div>

    <script>
        var default_cluster_id = "$cluster_id";
        var default_type_id = "$type_id";
        var server_select = 0;

        \$(function() {
            more_servers();

            \$("#more_servers").button().click(more_servers);
            \$(document).on("click",".server,.checkall", reload_graph_list);
            //\$("#graph").attr('disabled', true);
            \$("#graph").button().click(function() {
                var graph_url = "graph.cgi?server_id=" + serverListURL() + "&graph_id=" + graphListURL();
                if (\$("#width").val()) { graph_url = graph_url + "&width=" + \$("#width").val(); }
                if (\$("#range").val()) { graph_url = graph_url + "&range=" + \$("#range").val(); }
                if (\$("#height").val()) { graph_url = graph_url + "&height=" + \$("#height").val(); }
                if (\$("#vrange").val()) { graph_url = graph_url + "&vrange=" + \$("#vrange").val(); }
                if (\$("#offset").val()) { graph_url = graph_url + "&offset=" + \$("#offset").val(); }
                if (\$("#split").is(":checked")) { graph_url = graph_url + "&split=1"; }
                if (\$("#columns").val()) { graph_url = graph_url + "&columns=" + \$("#columns").val(); }
                //alert(graph_url);
                self.location = graph_url;
            });
            \$("#graph").button('disable');
            \$("#offset").datepicker({dateFormat: "yy-mm-dd"});
        });

        function graphListURL() {
            var graphList = ',';
            var fuck = \$("#graph_select input:checked");
            for (var i=0;i<fuck.length;i++) {
                var graph_id = \$(fuck[i]).closest("div").attr('id');
                graphList = graphList + ',' + graph_id;
                if (graph_id == 'all') {
                    continue;
                }
            }
            graphList = graphList.substr(2);
            return graphList;
        }

        function reload_graph_list() {
            var server_list_url = serverListURL();
            if (server_list_url) {
                \$.getJSON("API/graph_keys.cgi?server_id=" + server_list_url,
                    function(new_graph_list) {

                        var graphs = [];
                        var fuck = \$("#graph_select input:checked");
                        for (var i=0;i<fuck.length;i++) {
                            graphs[\$(fuck[i]).closest("div").attr('id')] = 1;
                        }


                        \$("#graph_select").html('');
                        if (new_graph_list.length > 0) {
                            \$("#graph_select").html('Select graphs:');
                            new_graph_list.unshift('all');
                        }

                        for (var i=0;i<new_graph_list.length;i++) {
                            var graph_id = new_graph_list[i];
                            \$("#graph_select").append("<div id=" + graph_id + "><input type=checkbox style='float:left'>" + graph_id + "</div>");
                            if (graphs[graph_id]) {
                                \$("#" + graph_id + " :checkbox").prop("checked", true);
                            } else if (graphs.length == 0) {
                                if (graph_id == 'cpu') { 
                                    \$("#" + graph_id + " :checkbox").prop("checked", true); 
                                    \$("#graph").button('enable'); 
                                }
                                if (graph_id == 'conn') { 
                                    \$("#" + graph_id + " :checkbox").prop("checked", true); 
                                    \$("#graph").button('enable'); 
                                }
                                if (graph_id == 'bandwidth') { 
                                    \$("#" + graph_id + " :checkbox").prop("checked", true); 
                                    \$("#graph").button('enable'); 
                                }
                            }
                            \$("#" + graph_id + " input").click(function() {
                                var graphList = graphListURL();
                                if (graphList.length > 0) {
                                    \$("#graph").button('enable');
                                } else {
                                    \$("#graph").button('disable');
                                }
                            });
                        }   
                    }
                );
            } else {
                \$("#graph_select").html('');
                \$("#graph").button('disable');
            }
        }

        function serverListURL() {
            var allServers = \$(".server");
            var serverList = ',';
            for (var i = 0; i<allServers.length; i++) {
                if (\$(allServers[i]).is(":checked")) {
                    var server_id = \$(allServers[i]).attr('id').substr(7);
                    serverList = serverList + "," + server_id;
                }
            }
            return serverList.substr(2);
        }

        function more_servers() {
            server_select = server_select + 1;
            \$('#server_select').append("<div><select id=cluster_id_" + server_select + " name='cluster_id'></select><select id=type_id_" + server_select + " name='type_id'></select><table id='server_list_" + server_select + "' border=0 class='server_list hidden'> <thead> <tr> <th><input class=checkall id=checkall_" + server_select + " type='checkbox'></th> <th><b>Server</b></th> <th><b>OS</b></th> <th><b>Model</b></th> </tr> </thead> <tbody> </tbody> </table> </div>");
            \$("#cluster_id_" + server_select + "").change(clusterChange);
            \$("#type_id_" + server_select + "").change(typeChange);
            \$("#checkall_" + server_select + "").on('click',
                function() {
                    \$(this).closest('table').find(":checkbox").prop("checked", this.checked);
                }
            );
            loadClusters(server_select);
        }

        function loadClusters(server_group) {
            \$.getJSON("API/cluster.cgi",
                function(data) { 
                    var cluster_id = data[0];
                    \$.each(data, function(id,value) {
                        var option = "<option value='" + value + "'";
                        if (value == default_cluster_id) {
                            option = option + " selected";
                        }
                        option = option + ">" + value + "</option>";
                        \$("#cluster_id_" + server_group).append(option);
                    });

                    loadTypes(server_group);
                }
            );
        }

        function clusterChange() {
            var server_group = \$(this).attr('id').substr(11);
            loadTypes(server_group);
        }

        function loadTypes(server_group) {
            \$("#type_id_" + server_group).html('');
            var cluster_id = \$("#cluster_id_" + server_group + "").val();
            \$.getJSON("API/type.cgi?cluster_id=" + cluster_id,
                function(data) {
                    \$.each(data, function(id,value) {
                        var option = "<option value='" + value + "'";
                        if (value == default_type_id) {
                            option = option + " selected";
                        }
                        option = option + ">" + value + "</option>";
                        \$("#type_id_" + server_group).append(option);
                    });
                    serverList(server_group);
                }
            );
        }

        function typeChange() {
            var server_group = \$(this).attr('id').substr(8);
            serverList(server_group);
        }

        function serverList(server_group) {
            var cluster_id = \$("#cluster_id_" + server_group + "").val();
            var type_id = \$("#type_id_" + server_group + "").val();
            \$("#checkall_" + server_group).prop("checked",false);
            \$("#server_list_" + server_group + " tbody").html('');
            \$("#server_list_" + server_group).removeClass("hidden");
            \$.getJSON("API/server.cgi?cluster_id=" + cluster_id + "&type_id=" + type_id,
                function(data) {
                    \$.each(data, 
                        function(id,value) {
                            \$.getJSON("API/server.cgi?server_id=" + value,
                                function(data) {
                                    \$("#server_list_" + server_group + " tbody").append("<tr><td><input class=server type=checkbox name=server_" + data.server_id + " id=server_" + data.server_id + "></td><td><a href=server.cgi?server_id=" + data.server_id + ">" + data.server_id + "</td><td>" + data.os_vendor + "/" + data.os_version + "</td><td>" + data.server_model + "</td></tr>");
                                }
                            );
                        }
                    );
                }
            );
        }
    </script>
</body>
HTML
}

