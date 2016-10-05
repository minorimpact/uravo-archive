#!/usr/bin/perl -w 

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;


eval { &main(); };
print "Content-type: text/html\n\n$@" if ($@);
exit;

sub main {
    my $uravo = new Uravo;

    print <<HTML;
Content-type: text/html

<!DOCTYPE HTML>
<html>
<head>
    <link rel="stylesheet" type="text/css" href="/header.css" />
    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <title>Serverroles</title>
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
    <script src="/js/jquery/jquery.isotope-1.5.25.js"></script>
    <script src="/js/jquery/jquery.cookie-1.3.1.js"></script>
    <script src="/js/serverroles.js"></script>

    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <style>
        body { height: 100%; font-family:Sans-serif; }
        #wrapper { min-height: 100%; position:relative; }
        #menu { position: relativel height:100%; padding-top: 50px; }
        #container { position: relative; height: 100%; padding-bottom: 20px;  }
        #header { width:100%; position:fixed; top:0px; margin:auto; z-index:100000; height: 50px; background-color:rgba(255,255,255,0.7);} 
        #footer { width:95%; position:fixed; bottom:0; height: 20px; background-color:rgba(255,255,255,0.7); }
        #tip-dialog { font-size:x-small; }

        #header a { font-weight:bold; }
        .tip-link { font-size:x-small; font-style:block; font-weight:bold; }
        .dim { color:grey; }
        .view_title { font-weight: bold; margin-top:10px; margin-bottom: 10px; font-size:x-large; }
        .sub_view { width: 250px; margin-bottom: 15px }
        .sub_view_title { font-weight: bold; margin-bottom: 2px; font-size:large; }
        .menu_item { width: 175px; font-size:x-small; background-color: ${\ $uravo->color('menu'); }; margin:1px; padding:2px; }
        .menu_item_highlight { background-color: yellow; font-weight:bold; }
        .server_highlight { background-color: yellow; font-weight:bold; }
        .hidden { display: none; }
    </style>
</head>
<body>
    <div align='center' id='wrapper'>
        <div id="header">
            ${\ $uravo->menu(); }
            <table border=0>
                <tr>
                    <td><div id="debug"></div></td>
                    <td><select id=bu_id></select></td>
                    <td><select id=silo_id></select></td>
                    <td align='center' valign='top'><a href='addserver.cgi'>Add New Server</a> &nbsp;</td>
                    <td align='center' valign='top'><a id=bulkupdate href='bulkupdate.cgi'>Edit Servers</a> &nbsp;</td>
                    <td align='center' valign='top'><a href='index_classic.cgi' id='showall'>Show All clusters</a> &nbsp;</td>
                    <td align='center' valign='top'><a href='javascript:regroup();' id='regroup'>Regroup</a> &nbsp;</td>
                    <td><input name='find_server' id='find_server' onblur='if (this.value == "") { this.value = find_server_default; \$(this).addClass("dim"); }' onfocus='if (this.value==find_server_default) { this.value=""; } \$(this).removeClass("dim");'></td>
                    <td><div class=tip-link><input type=checkbox id=compress checked>Compress Servers</div></td>
                    <td><div id=tip-link class=tip-link>?:Show Tips</div></td>
                </tr>
            </table>
        </div>

        <div id='menu'></div>
        <div class='title' id='title'></div>
        <div class='view' id='container'></div>
        <div id='loading'><img src=/images/loading.gif></div>
    </div>
    <div id='footer' align="right"><div>

    <div id="tip-dialog" title="Tips">
        <b>Keyboard Shortcuts</b><br />
        <b>f</b>: jump to search box. From the search box, start typing...<br />
        &nbsp;&nbsp;&nbsp;a server id to jump to that server.<br />
        &nbsp;&nbsp;&nbsp;a cluster/type id to jump to that cluster/type.<br />
        &nbsp;&nbsp;&nbsp;<b>enter</b> to jump to the next matching server<br />
        <b>r</b>: regroup by cluster/type.<br />
        <b>a</b>: show all clusters/types.<br />
        <b>+</b>: Add a new server.<br />
        <b>pgup/pgdown</b>: If you're at the top or bottom of the page, use PageUp or PageDown to skip to the previous or next cluster/type.<br />
        &nbsp;&nbsp;&nbsp;<br />
        Move your mouse over a server to see more information in the lower right corner of your window.<br />
        &nbsp;&nbsp;&nbsp;<br />
        Uncheck "Compress Servers" to add white space to force type/clusters into an evenly spaced grid.
        
    </div>

    <script type="text/javascript">
    var view;
    var sub_view;
    var view_id;
    var control;
    var attop;
    var atbottom;
    var menu_items;
    var search_id;
    var search_index = 0;
    var search_result = [];
    var search_server;
    var search_done = 0;
    var loading = 0;

    var find_server_default = 'search for id or ip';

    \$(function() {
        \$("#compress").on('click',
            function() {
                \$("#view-" + view_id).isotope('destroy');
                if (\$(this).is(":checked")) {
                    \$("#view-" + view_id).isotope({ itemSelector: '.sub_view' }).isotope('reLayout');
                } else {
                    \$("#view-" + view_id).isotope({ itemSelector: '.sub_view', layoutMode: 'fitRows' }).isotope('reLayout');
                }
            }
        );

        \$("#tip-dialog").dialog({
            autoOpen: false,
            height: 250,
            width: 400,
            modal: true,
            addClass: "tip-dialog"
        });
        
        \$("#tip-link").click(function() {
            \$("#tip-dialog").dialog("open");
        });

        if (\$.cookie('search_id')) {
            \$("#find_server").val(\$.cookie('search_id'));
        } else {
            \$("#find_server").val(find_server_default);
        }

        \$("#menu").isotope({
            itemSelector: '.menu_item'
        });

        if (\$.cookie('search_id')) {
            setSearchBox(\$.cookie('search_id'));
        } else {
            setSearchBox();
        }

        if (\$.cookie("view")) {
            view = \$.cookie("view");
        } else {
            view = 'cluster';
        }

        if (view == 'type') {
            sub_view = 'cluster';
            \$("#bulkupdate").addClass("hidden");
        } else {
            sub_view = 'type';
            \$("#bulkupdate").removeClass("hidden");
        }

        \$(document).keydown(function (e) {
            if (e.which == 17 || e.which == 91) {
                control = 1;
             }
        });

        \$("#find_server").keydown(function (e) {
            if (e.which == 33 || e.which==34) {
                \$("#find_server").blur();
            }
            if (e.which == 70) {
                return;
            }
            if (e.which == 13) {
                if (search_result.length > 1) {
                    search_index = search_index + 1;
                    if (search_index >= search_result.length) {
                        search_index = 0;
                    }
                    search_server = null;
                }
            }
        });

        \$(document).keyup(function (e) {
            //\$("#debug").html(e.which);
            if (e.which == 17 || e.which == 91) {
               control = 0;
            }
            if (\$(document.activeElement).attr('id') != 'find_server') {
                if (e.which == 70) {
                    \$("#find_server").focus().removeClass("dim").val('');
                }
                if (e.which == 191) {
                    \$("#tip-dialog").dialog("open");
                }
                if (e.which == 82) {
                    regroup();
                }
                if (e.which == 187) {
                    location = "addserver.cgi";
                }
                if (e.which == 65) {
                    location = "index_classic.cgi";
                }
            } else if (\$(document.activeElement).attr('id') == 'find_server') {
                if (e.which == 27) {
                    setSearchBox('');
                }
            }

            if (e.which == 33) {
                if (attop) {
                    setSearchBox();
                    var prev;
                    for (i=menu_items.length - 1; i>=0; i--) {
                        if (menu_items[i] == view_id) {
                            prev = 1;
                        } else if (prev) {
                            getData(menu_items[i]);
                            return;
                        }
                    }
                    getData(menu_items[menu_items.length - 1]);
                }
            }

            if (e.which == 34) {
                if (atbottom) {
                    setSearchBox();
                    var next;
                    for (i=0; i<menu_items.length; i++) {
                        if (menu_items[i] == view_id) {
                            next = 1;
                        } else if (next) {
                            getData(menu_items[i]);
                            return;
                        }
                    }
                    getData(menu_items[0]);
                }
            }
        });

        \$(window).scroll(function() {
            if((\$(window).scrollTop() + \$(window).height()) == getDocHeight()) {
                atbottom = 1;
            } else {
                atbottom = 0;
            }
            if (\$(window).scrollTop() == 0) {
                attop = 1;
            } else {
                attop = 0;
            }
        });

        \$("#container").on("mouseenter","div.server",
            function() {
                var server_id = this.id.substring(7,this.id.length);
                \$.getJSON("API/server.cgi?server_id=" + server_id, updateServerInfoStatus);
            }
        );
        
        \$("#bu_id").change(function() {
            \$.cookie('view_id','');
            \$.cookie('silo_id','');
            \$.cookie('bu_id',\$(this).val());
            setSearchBox('');
            \$.getJSON("API/silo.cgi?bu_id=" + \$(this).val(),loadSiloData);
        });

        \$("#silo_id").change(function() {
            \$.cookie('view_id','');
            \$.cookie('silo_id',\$(this).val());
            setSearchBox('');
            loadMenu();
        });

        \$("#regroup").html('Regroup by ' + sub_view);
        \$("#container").html('');
        search_result.length = 0;
        search_server = null;
        search_done = 0;
        \$.cookie('search_id','');

        \$.getJSON("API/bu.cgi",loadBUData);
            
    });

    function loadBUData(data) {
        var default_bu_id = \$.cookie('bu_id');
        for (var i=0; i<data.length; i++) {
            var value = data[i];
            if (!default_bu_id  && i==0 && value != '') {
                default_bu_id = value;
            }
            var option = "<option value=" + value;
            if (default_bu_id == value) {
                option = option + " selected";
            }
            option = option + ">" + value + "</option>";
            \$("#bu_id").append(option);
        }
        \$.getJSON("API/silo.cgi?bu_id=" + default_bu_id,loadSiloData);
    }

    function loadSiloData(data) {
        var default_silo_id = \$.cookie('silo_id');
        \$("#silo_id").html('');
        for (var i=0; i<data.length; i++) {
            var value = data[i];
            if (!default_silo_id && i==0 && value != '') {
                default_silo_id = value;
            }
            var option = "<option value=" + value;
            if (default_silo_id == value) {
                option = option + " selected";
            }
            option = option + ">" + value + "</option>";
            \$("#silo_id").append(option);
        }
        loadMenu();
    }

    function loadMenu() {
        //loading = loading + 1;
        \$.getJSON("API/" + view + ".cgi?silo_id=" + \$("#silo_id").val(),
            function(data) {
                menu_items = data;
                \$("#menu").isotope('destroy');
                \$("#menu").html('');
                \$("#menu").isotope({ itemSelector: '.menu_item' });
                for (var i=0; i<data.length; i++) {
                    var id = data[i];
                    var \$menu_item = \$("<div class='menu_item' id='menu_item-" + id + "'><a href='javascript:setSearchBox();getData(\\"" + id + "\\");'>" + id + "</a></div>");
                    \$("#menu").isotope('insert', \$menu_item);
                    if (\$.cookie('view_id') && id == \$.cookie('view_id')) {
                        getData(id);
                    } else if (!\$.cookie('view_id') && i == 0) {
                        getData(id);
                    }
                };
                \$("#menu").isotope('reLayout');
                //loading = loading - 1;
            }
        );
    }

    function regroup() {
        if (view == 'type') {
            view = 'cluster';
        } else {
            view = 'type';
        }
        \$.cookie('view_id','');
        \$.cookie('view',view);

        location.reload();
    }

    window.setInterval(function() {
        var search = \$("#find_server").val();

        if (search.length < 3) {
            \$(".server_highlight").removeClass("server_highlight");
            search_result.length = 0;
            search_server = null;
            search_done = 0;
            search_id = search;
            \$.cookie('search_id', search_id);
        } else if ( search != find_server_default && search.length >= 3 && search != search_id) {
            \$(".server_highlight").removeClass("server_highlight");
            search_result.length = 0;
            search_server = null;
            search_done = 0;
            search_id = search;
            \$.cookie('search_id', search_id);
            if (search_id.match(/^[0-9]+\./)) {
                \$.getJSON("API/server.cgi?search=" + search_id,
                    function(data) {
                        search_index = 0;
                        search_result = [data.server_id];
                    }
                );
            } else {
                \$.getJSON("API/server.cgi?text_string=" + search_id,
                    function(data) {
                        search_index = 0;
                        search_result = data;
                    }
                );
            }
        } else if (search_result.length > 0 && Object.size(search_server)==0) {
            \$.getJSON("API/server.cgi?server_id=" + search_result[search_index], function(data) {
                if (data.bu_id != \$("#bu_id").val() || data.silo_id !=\$("#silo_id").val()) {
                    \$.cookie('bu_id', data.bu_id);
                    \$.cookie('silo_id', data.silo_id);
                    if (view == 'cluster' && data.cluster_id) {
                        \$.cookie('view_id',data.cluster_id);
                    } else if (view == 'type' && data.type_id) {
                        \$.cookie('view_id',data.type_id);
                    }
                    \$("#bu_id").val(data.bu_id);
                    \$.getJSON("API/silo.cgi?bu_id=" + data.bu_id,loadSiloData);
                } else {
                    if (view == 'cluster' && data.cluster_id) {
                        getData(data.cluster_id);
                    } else if (view == 'type' && data.type_id) {
                        getData(data.type_id);
                    }
                }
                search_server = data;
                search_done = 0;
            });
        } else if (Object.size(search_server) > 0 && ((view == 'cluster' && search_server.cluster_id == view_id) || (view == 'type' && search_server.type_id == view_id)) && !search_done) {
            \$(".server_highlight").removeClass("server_highlight");
            var s = search_server.server_id.replace(/\\./g,"\\\\.");
            var server_div = \$("#server-" + s);
            if (server_div.length) {
                server_div.addClass("server_highlight");
                \$('html, body').animate({ scrollTop: server_div.offset().top - 50 }, 500);
                updateServerInfoStatus(search_server);
                search_done = 1;
            }
        }
    }, 250);

    function getData(id) {
        if (view_id == id) {
            return;
        }
        \$('.menu_item_highlight').removeClass('menu_item_highlight');
        \$("#menu_item-" + id).addClass('menu_item_highlight');
        \$("#container").html('');
        \$("#container").hide();
        \$("#loading").show();

        if (view == 'cluster') {
            \$("#bulkupdate").attr('href','bulkupdate.cgi?cluster_id=' + id);
        }

        view_id = id;
        \$.cookie('view_id',id);

        var view_div = \$("#view-" + id);

        if (view_div.length) {
            \$('html, body').animate({ scrollTop: \$("#view_title-" + id).offset().top - 50 }, 500);
            return;
        } else {
            \$("#container").append("<div id=view_title-" + id + " class=view_title><a href=" + view + ".cgi?" + view + "_id=" + id + ">" + id + "</a> <a href=graph.cgi?" + view + "_id=" + id + "><img src=/images/graph-button.gif border=0></a></div>");
            \$("#container").append("<div id=view-" + id + " class=view></div>");
            if (\$("#compress").is(":checked")) {
                \$("#view-" + id).isotope({ itemSelector: '.sub_view' });
            } else {
                \$("#view-" + id).isotope({ itemSelector: '.sub_view', layoutMode: 'fitRows' });
            }
        }
        \$("#footer").html('');

        loading = loading + 1;
        \$.getJSON("API/" + sub_view + ".cgi?" + view + "_id=" + id + "&silo_id=" + \$("#silo_id").val(),
            function(data) {
                if (data.length == 0) {
                    \$("#view-" + id ).html('No ' + sub_view + 's found.');
                } else {
                    \$.each(data, 
                        function(i, sub_id) { 
                            // Build cluster list
                            var \$sub_view_div = \$("<div id='sub_view-" + id + "-" + sub_id + "' class='sub_view'><div id=sub_view_title-" + id + "-" + sub_id + " class='sub_view_title'><a href=" + sub_view +".cgi?" + sub_view + "_id=" + sub_id + ">" + sub_id + "</a> <a href=graph.cgi?" + view + "_id=" + id + "&" + sub_view + "_id=" + sub_id + "><img src=/images/graph-button.gif border=0></a></div></div>");
                            \$("#view-" + id).isotope('insert', \$sub_view_div);
                            loading = loading + 1;
                            \$.getJSON("API/server.cgi?" + view + "_id=" + id + "&" + sub_view + "_id=" + sub_id,
                                function(data) {
                                    // Build type list
                                    var servers = '';
                                    for (var i=0; i<data.length; i++) {
                                        var server_id =  data[i];
                                        servers = servers + "<div class='server' id='server-" + server_id + "'>"  + (i + 1) + ". " + "<a href=server.cgi?server_id="  + server_id + ">" + server_id + "</a> <a href=graph.cgi?server_id=" + server_id + "&graph_id=all><img src=/images/graph-button.gif border=0></a></div>";
                                    }
                                    \$("#sub_view-" +id + "-"  + sub_id).append(servers);

                                    if(\$(window).height() >= getDocHeight()) {
                                        atbottom = 1;
                                    } else {
                                        atbottom = 0;
                                    }
                                    attop = 1;
                                    loading = loading - 1;
                                    if (loading == 0) {
                                        \$("#loading").hide();
                                        \$("#container").show();
                                        \$("#view-" + id).isotope('reLayout');
                                    }
                                }
                            );
                        }
                    );
                }
                loading = loading - 1;
            }
        );
    }

    function updateServerInfoStatus(data) {
        var status = "<b>" + data.server_id + "</b>";
        if (data.server_model) { status = status + " model:<b>" + data.server_model + "</b>"; }
        if (Object.size(data.diskinfo)>0) {
            var totaldisk = 0;
            for (key in data.diskinfo) {
                totaldisk = totaldisk + parseInt(data.diskinfo[key].size);
            }
            status = status + " disk:<b>" + totaldisk + "GB</b>";
        }
        if (data.mem > 0) { 
            var mem = parseInt(data.mem/1000000);
            status = status + " mem:<b>" + mem + "GB</b>"; 
        }
        if (data.kickstart_name) { status = status + " ks:<b>" + data.kickstart_name + "</b>"; }
                
        \$("#footer").html(status);
    }

    function setSearchBox(val) {
        if (val) {
            \$("#find_server").focus().removeClass("dim").val(val);
        } else {
            \$("#find_server").blur().addClass("dim").val(find_server_default);
            search_id = '';
            \$.cookie("search_id",'');
        } 
    }
    </script>
</body>
</html>
HTML
}
 

