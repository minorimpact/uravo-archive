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
    my $uravo  = new Uravo({loglevel=>0});
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;
    my $user = $ENV{'REMOTE_USER'} || die "INVALID USER";

    my $type_id	        = $form->{type_id};

    my $type = $uravo->getType($type_id);
    if (!$type) {
        print "Location: types.cgi\n\n";
        exit;
    }
            
    if ($form->{save}) {
        my %modules;
        foreach my $key (keys %$form) { 
            next unless ($key =~ /^(module|override)_(.*)$/);
            my $module_id = $2;
            $modules{$module_id} = ($form->{"override_$module_id"}?0:1);
        }

        my @procs = ();
        my @modules = ();
        my %log_files;
        #print "Content-type: text/plain\n\n";
        foreach my $key (sort keys %$form) { 
            if ($key =~ /^module_(.*)$/) {
                my $module_id = $1;
                push @modules, $module_id;
            } elsif ($key =~ /^procs_([0-9]+)$/) {
                my $proc_id = $1;
                my $red = $form->{"red_$proc_id"} || '';
                $red =~s/&gt;/>/;
                $red =~s/&lt;/</;
                push @procs, { proc_id=>$proc_id,
                            red=> $red};
            } elsif ($key =~/^logfile_([^_]+)$/) {
                next unless ($form->{$key});
                my $id = $1;
                $log_files{$id}->{log_file} = $form->{$key};
            } elsif ($key =~/^regex_([^_]+)_([^_]+)$/) {
                next unless ($form->{$key});
                my $log_id = $1;
                my $regex_id = $2;
                if (exists($log_files{$log_id})) {
                    push(@{$log_files{$log_id}->{detail}}, {id=>$regex_id, type_log_id=>$log_id, regex=>$form->{$key}});
                }
            }
        }
        my $changelog = {user=>$user, ticket=>$form->{ticket}, note=>$form->{note}};

        $type->update({procs=> \@procs, comments=> $form->{comments}, auto_id_type=>$form->{auto_id_type}, auto_id_source=>$form->{auto_id_source}, auto_id_text=>$form->{auto_id_text}, modules=>\%modules, community=>$form->{community}, logs=>\%log_files},$changelog);

        print "Location: type.cgi?type_id=$type_id\n\n";
        exit;
    }
    print "Content-type: text/html\n\n";
    
    my $auto_id_type_select = "<select name=auto_id_type>\n";
    $auto_id_type_select .= "<option></option>";
    $auto_id_type_select .= "<option value=file " . ($type->get('auto_id_type') eq 'file'?' selected':'') . ">file</option>";
    $auto_id_type_select .= "<option value=http " . ($type->get('auto_id_type') eq 'http'?' selected':'') . ">http</option>";
    $auto_id_type_select .= "<option value=snmp " . ($type->get('auto_id_type') eq 'snmp'?' selected':'') . ">snmp</option>";
    $auto_id_type_select .= "</select>";

    my $procLimitSelect = "<select name='red_PROC'>\n";
    $procLimitSelect    .= "<option value='>0'>at least one\n";
    $procLimitSelect    .= "<option value='=0'>none\n";
    $procLimitSelect    .= "<option value='=1'>one\n";
    $procLimitSelect    .= "<option value='>=5'>at least five\n";
    $procLimitSelect    .= "<option value='>=10'>at least ten\n";
    $procLimitSelect    .= "</select>\n";

    my $processes = $uravo->getProcesses();
    my $proclist;
    foreach my $proc_id (sort { uc($processes->{$a}{name}) cmp uc($processes->{$b}{name}); } keys %{$processes}) {
        $proclist   .=  "<p><label for=procs_$proc_id>$processes->{$proc_id}{name}</label><input type=checkbox name='procs_$proc_id' value='$proc_id'";
        $proclist   .= (( defined($type->{procs}{$proc_id}))?" checked":"");
        $proclist   .= ">";

        my $select  = $procLimitSelect;
        $select     =~s/PROC/$proc_id/;
        $select     =~s/'$type->{procs}{$proc_id}{red}'/'$type->{procs}{$proc_id}{red}' selected/;
        $proclist   .= "$select";
        $proclist .= "</p>\n";
            
    }

    my %modules = map{$_->id()=>$_} $type->getModules();
    my $localModuleList;
    foreach my $module_id ($uravo->getModules({remote=>0,id_only=>1})) {
        my $module = $modules{$module_id};
        my $enabled = 0;
        $enabled = $module->enabled($type_id) if ($module);
        $localModuleList .= "<p><label for=module_$module_id>$module_id</label><input type=checkbox name=module_$module_id ${\ (($enabled)?'checked':''); }><input type=checkbox name=override_$module_id ";
        if ($module && !$enabled) {
            $localModuleList .= " checked";
        }
        $localModuleList .= "></p>\n";
    }
    my $remoteModuleList;
    foreach my $module_id ($uravo->getModules({remote=>1,id_only=>1})) {
        my $module = $modules{$module_id};
        my $enabled = 0;
        $enabled = $module->enabled($type_id) if ($module);
        $remoteModuleList .= "<p><label for=module_$module_id>$module_id</label><input type=checkbox name=module_$module_id ${\ (($enabled)?'checked':''); }><input type=checkbox name=override_$module_id ";
        if ($module && !$enabled) {
            $remoteModuleList .= " checked";
        }
        $remoteModuleList .= "></p>\n";
    }

    my $logFiles;
    my $logs = $type->getLogs();
    foreach my $log_id (keys %$logs) {
        my $log = $logs->{$log_id};
        $logFiles .= "<p>
            <label for=logfile_$log_id>Log File</label>
            <div class=log><input type=text class=logfile name=logfile_$log_id value='$log->{log_file}' /><div class=log_detail>\n";
        foreach my $detail (@{$log->{detail}}) {
            my $detail_id = $detail->{id};
            $logFiles .= "<input type=text name=regex_$log_id\_$detail_id value='$detail->{regex}' class=regex />\n";
        }
        $logFiles .= "<input type=text name=regex_$log_id\_new placeholder='New regex' class=regex /></div></div>\n";
        $logFiles .= "</p>\n";
    }
    $logFiles .= "<p><label>New Log File</label><div class=log> <input class=logfile type=text name=logfile_new value='' placeholder='New logfile'/><div class=log_detail><input type=text name=regex_new_new value='' placeholder='New regex' class=regex /></div></div></p>\n";

    print <<HEAD;
<head>
    <title>Edit Type: $type_id</title>
    <link rel="stylesheet" href="/js/jquery/ui/1.10.1/themes/base/jquery-ui.css" />
    <link rel="stylesheet" href="/uravo.css">
    <script src="/js/jquery/jquery-1.9.1.js"></script>
    <script src="/js/jquery/ui/1.10.1/jquery-ui.js"></script>
    <script type="text/javascript">
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
                        \$( "#edittype").submit();
                    },
                    Cancel: function() {
                      \$( this ).dialog( "close" );
                    }
                }
            });
 
            \$( "#save-changes").button().click(function() {
                \$("#save-dialog").dialog("open");
            });
            \$( "#delete-type").button().click(function() {
                if(confirm('Are you sure you want to delete $type_id?')) { 
                    self.location='deletetype.cgi?type_id=$type_id';
                }
            });
        });
    </script>
</head>
HEAD
    print $uravo->menu();
    print <<FORM;
<div id=links>
    <ul>
        <li><a href=types.cgi>All Types</a></li>
    </ul>
</div>
<div id=content>
    <h1>$type_id</h1>
    <form method='POST' id='edittype'>
        <input type='hidden' name='type_id' value='$type_id'>
        <input type='hidden' name='save' id='save' value=1>
        <input type='hidden' name='_ticket' id='ticket'>
        <input type='hidden' name='note' id='note'>

        <p>
            <label for=comments>
                Comments
                <span class=fielddesc></span>
            </label>
            <textarea name=comments cols=50 rows=7>${\ $type->get('comments');}</textarea>
        </p>
        <p>
            <label for=auto_id_type>
                Auto ID Type
                <span class=fielddesc></span>
            </label>
            $auto_id_type_select
        </p>
        <p>
            <label for=auto_id_source>
                Auto ID Source
                <span class=fielddesc></span>
            </label>
            <input type=text name=auto_id_source value="${\ $type->get('auto_id_source');}" />
        </p>
        <p>
            <label for=auto_id_text>
                Auto ID text
                <span class=fielddesc></span>
            </label>
            <input type=text name=auto_id_text value="${\ $type->get('auto_id_text');}" />
        </p>
        <p>
            <label for=cummunity>
                SNMP Community String
                <span class=fielddesc>The community string for connecting to SNMP devices.</span>
            </label>
            <input type=text name=community value="${\ $type->get('community');}" />
        </p>
        <h2>Local Modules</h2>
        $localModuleList
        <h2>Remote Modules</h2>
        $remoteModuleList
        <h2>Processes</h2>
        $proclist
        <h2>Log Files</h2>
        <div id=log_files>
            $logFiles
        </div>
        <p>
            <button id="save-changes">Save Changes</button>
            <button id="delete-type">Delete this Type</button>
        </p>
</div>

<div id="save-dialog" title="Save Changes">
    <form>
        <fieldset>
            <lable for="save-dialog-ticket">Jira Ticket</label>
            <input type="text" name="save-dialog-ticket" id="save-dialog-ticket" value="" class="text ui-widget-content ui-corner-all" />
            <lable for="save-dialog-note">Note</label>
            <input name="save-dialog-note" id="save-dialog-note" value="" class="text ui-widget-content ui-corner-all" maxlength=50/>
        </fieldset>
    </form>
</div>
</body>
</html>
FORM

}

