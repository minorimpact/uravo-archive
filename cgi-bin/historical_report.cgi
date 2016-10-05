#!/usr/bin/perl

use strict;

use lib "/usr/local/uravo/lib";
use Uravo;
use Uravo::Util;
use DBI;
use CGI;
use JSON;
use Time::Local;
use Data::Dumper;

my $uravo = new Uravo;

my $script_name = "historical_report.cgi";

eval { 
    main(); 
};
print "Content-type:text/html\n\n$@\n" if ($@);

sub main {
    my $query = CGI->new();
    my %vars = $query->Vars;
    my $form = \%vars;

    if ($form->{server_id} || $form->{serial} || $form->{jira} || $form->{cluster}) {
        $form->{report} = 'eventhistory' if (!$form->{report} || $form->{report} eq 'noform');
    }

    my $report = $form->{report};

    # If we didn't come in with a startdate, see if we can figure that out
    if (!$form->{startdate}) {
        my $displace = 1;
        # If we were given a range, then assume that we want to start from today
        if ($form->{range}) {
            $displace = $form->{range};
            # if they left off range type, then assume hours
            if ($form->{range_type} eq 'days') {
                $displace = $displace * 24;
            } else {
                $form->{range_type} = 'hours';
            }
        }
        my $today = time - (60 * 60 * $displace);
        my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime($today);
        $form->{startdate} = sprintf('%02d/%02d/%4d', $mon+1, $mday, $year + 1900);
        $form->{starttime} = $hour;
    }

    my $errors = {};
    if ($report) {
        if (!$form->{range} || $form->{range_radio} eq 'now') {
            my ($startmonth, $startday, $startyear) = ($form->{startdate} =~ /^(\d{2})\/(\d{2})\/(\d{4})$/);
            my $then = timelocal(0,0,$form->{starttime},$startday,($startmonth-1),$startyear);
            my ($dy, $dm, $dd, $dh, $dmin, $ds) = Uravo::Util::dateDelta($then);
            # If this report is older than 30 days, we're probably not going to get much data anyway,
            if ($dy > 0 || $dm > 0) {
                $form->{range} = 30;
                $form->{range_type} = 'days';
            } else {
                if ($dd > 0) {
                    $form->{range} = $dd;
                    if ($dh > 0 || $dmin > 0 || $ds > 0) {
                        $form->{range} ++;
                    }
                    $form->{range_type} = 'days';
                } else {
                    $form->{range} = $dh;
                    if ($dmin > 0 || $ds > 0) {
                        $form->{range} ++;
                    } 
                    $form->{range_type} = 'hours';
                }
            }
        }

        # Now do the error checking
        if (!$form->{server_id} && $form->{focus} eq 'server') {
            $errors->{server_id} = 1;
        }
        if (!$form->{Ticket} && $form->{focus} eq 'Ticket') {
            $errors->{Ticket} = 1;
        }
        if ($form->{startdate} !~ /^\d{2}\/\d{2}\/\d{4}$/) {
            $errors->{startdate} = 1;
        }
        if ($form->{starttime} < 0 || $form->{starttime} > 23) {
            $errors->{starttime} = 1;
        }
        if ($form->{range} < 1) {
            $errors->{range} = 1;
        }
        if ($form->{range_type} ne 'hours' &&  $form->{range_type} ne 'days') {
            $errors->{range_type} = 1;
        }
    }

    if ($report eq 'ajaxreport') {
        my $report_data = get_report_data($form);
        ajax_send_data($report_data);
    } elsif ($report eq 'csv') {
        my $report_data = get_report_data($form);
        csv_send_data($report_data);
    } elsif (!$report || scalar (keys %$errors) > 0) {
        html_header();
        display_form($form, $errors);
        html_footer();
    } elsif ($report eq 'eventhistory') {
        html_header();
        ajax_result($form);
        html_footer();
    } 
}


sub html_header {
    print "Content-type: text/html\n\n";
    print qq[
    <html>
    <head>
        <title>Tivoli Historical Events Report</title>
        <style type='text/css'>
            /* the table (within the div) that holds the date picker calendar */
            .dpTable { font-family:Tahoma, Arial, Helvetica, sans-serif; font-size:12px; text-align:center; color:#505050; background-color:#FFFFFF; border:1px solid #999; }

            /* a table cell that holds a highlighted day (usually either today's date or the current date field value) */
            .dpDayHighlightTD { background-color:#CCCCCC; }

            /* highlight selected days, i.e. release dates */
            .dpDayReserveTD { background-color:#CCCCCC; }  

            /* the date number table cell that the mouse pointer is currently over (you can use contrasting colors to make it apparent which cell is being hovered over) */
            .dpTDHover { background-color:#CCFFCC; color:#000000; }
                                              
            /* a table cell that holds the names of days of the week (Mo, Tu, We, etc.) */
            .dpDayTD { background-color:#DCDCDC; border: 1px solid #CCCCCC; }
                                                      
            /* additional style information for the text that indicates the month and year */
            .dpTitleText { font-size:12px; color:#666666; font-weight:bold; }
                                                             
            /* additional style information for the cell that holds a highlighted day (usually either today's date or the current date field value) */
            .dpDayHighlight { color:#000000; font-weight: bold; }

            /* the forward/backward buttons at the top & "This Month" and "Close" buttons at the bottom */
            .dpButton, .dpTodayButton { font-family:Verdana, Tahoma, Arial, Helvetica, sans-serif; font-size:10px; color:#333333; background:#CCCCCC; font-weight:bold; padding:0px; }
        </style>
    </head>
    <body>
    <div id=header>
        ${\ $uravo->menu(); }
    </div>
    ];
}


sub get_report_data {
    my $form = shift;

    my $server_id = $form->{server_id};
    my $serial = $form->{serial};
    my $cluster = $form->{cluster};
    my $type = $form->{type};
    my ($month, $day, $year) = $form->{startdate} =~ /^(\d{2})\/(\d{2})\/(\d{4})$/;
    my $start = $form->{starttime};
    my $range = $form->{range};
    my $range_type = $form->{range_type};
    my $Ticket = $form->{Ticket};
    my $alertgroup = $form->{alertgroup};
    my $debug = $form->{debug};
    my $set = $form->{set} || 0;

    my $starttime = sprintf("%4d-%02d-%02d %02d:00:00", $year, $month, $day, $start);
    my $endtime = "(DATE_ADD('$starttime', interval $range " . ($range_type eq 'hours' ? 'HOUR' : 'DAY') . "))";


    my $maxcount = 50;

    my $dbh = $uravo->{db};

    my $new_events_sql = "SELECT * FROM historical_alert WHERE (FirstOccurrence >= '$starttime' AND FirstOccurrence < $endtime)";
    my $existing_events_sql = "SELECT * FROM historical_alert WHERE ((DeletedAt IS NULL OR (DeletedAt >= '$starttime' AND DeletedAt < $endtime)) AND FirstOccurrence < '$starttime') ";
    if ($alertgroup) {
        $new_events_sql .= " AND AlertGroup='$alertgroup'";
        $existing_events_sql .= " AND AlertGroup='$alertgroup'";
    }
    if ($server_id) {
        $new_events_sql .= " AND server_id='$server_id'";
        $existing_events_sql .= " AND server_id='$server_id'";
    } 
    if ($serial) {
        $new_events_sql .= "AND Serial='$serial'";
        $existing_events_sql .= "AND Serial='$serial'";
    }
    if ($Ticket) {
        $new_events_sql .= " AND Ticket='$Ticket'";
        $existing_events_sql .= " AND Ticket='$Ticket'";
    }

    if ($cluster && $cluster ne 'all') {
        $new_events_sql .= " AND cluster_id='$cluster'";
        $existing_events_sql .= " AND cluster_id='$cluster'";
    }

    if ($type && $type ne 'all') {
        $new_events_sql .= " AND type_id='$type'";
        $existing_events_sql .= " AND type_id='$type'";
    }

    my $events = $dbh->selectall_hashref($new_events_sql, 'Serial');
    my $existing_events = $dbh->selectall_hashref($existing_events_sql, 'Serial');

    foreach my $serial (keys %$existing_events) {
        $events->{$serial} = $existing_events->{$serial};
    }

    my %severity_map = ( 0 => 'Clear', 1 => 'Indeterminate', 2 => 'Warning', 3 => 'Minor', 4 => 'Major', 5 => 'Critical');
    my %severity_color = ( 0 => '#00CD00', 1 => '#CCCCCC', 2 => '#63B8FF', 3 => '#FFFF00', 4=> '#FFA500', 5 => '#FF0000');
    my %suppressed_map = ( 0 => 'Normal', 1 => 'Escalated', 2 => 'Escalated-Level 2', 3 => 'Escalated-Level 3', 4 => 'Suppressed', 5 => 'Hidden', 6 => 'Maintenance'); 

    my $report_data = { startdate  => $form->{startdate},
                        starttime  => $start,
                        range      => $range,
                        range_type => $range_type,
                        alertgroup => $alertgroup};

    if ($debug) {
        $report_data->{new_query} = $new_events_sql;
        $report_data->{existing_query} = $existing_events_sql;
    }

    my $count = 0;

    foreach my $serial (sort { $a <=> $b } keys %$events) {
        my $row = $events->{$serial};
        clean_row($row);

        $count++;
        if ($set > 0 && $count < ($set * $maxcount)) {
            next;
        }
        if ($count - ($set * $maxcount) > $maxcount) {
            $report_data->{next_set} = $set + 1;
            last;
        }

        $report_data->{data}{$serial} = { server_id        => $row->{server_id},
                                          firstoccurrence  => $row->{FirstOccurrence},
                                          statechange      => $row->{StateChange},
                                          deletedat        => $row->{DeletedAt},
                                          alertgroup       => $row->{AlertGroup},
                                          alertkey         => $row->{AlertKey},
                                          summary          => $row->{Summary},
                                          deletedby        => $row->{DeletedBy},
                                          originalseverity => $row->{original_Severity},
                                          identifier       => $row->{Identifier} };

        my $history;

        my $severity_sql = "SELECT * FROM historical_Severity WHERE Serial='$row->{Serial}' ORDER BY create_date";
        my $severity_history = $dbh->selectall_arrayref($severity_sql, { Slice => {}});
        foreach my $severity_row (@$severity_history) {
            clean_row($severity_row);
            $history->{$severity_row->{create_date}.'severity'}{date} = $severity_row->{create_date};
            $history->{$severity_row->{create_date}.'severity'}{field} = "Severity";
            $history->{$severity_row->{create_date}.'severity'}{value} = $severity_map{$severity_row->{Severity}};
            $history->{$severity_row->{create_date}.'severity'}{raw_value} = $severity_row->{Severity};
        }

        my $suppressed_sql = "SELECT * FROM historical_SuppressEscl WHERE Serial='$row->{Serial}' ORDER BY create_date";
        my $suppressed_history = $dbh->selectall_arrayref($suppressed_sql, {Slice=>{}});
        foreach my $suppressed_row (@$suppressed_history) {
            clean_row($suppressed_row);
            $history->{$suppressed_row->{create_date}.'escalation'}{date} =  $suppressed_row->{create_date};
            $history->{$suppressed_row->{create_date}.'escalation'}{field} = "Escalation";
            $history->{$suppressed_row->{create_date}.'escalation'}{value} = $suppressed_map{$suppressed_row->{SuppressEscl}};
        }

        my $parent_sql = "SELECT * FROM historical_ParentIdentifier WHERE Serial='$row->{Serial}' ORDER BY create_date";
        my $parent_history = $dbh->selectall_arrayref($parent_sql, { Slice => {}});
        my $first = 1;
        foreach my $parent_row (@$parent_history) {
            clean_row($parent_row);
            if (!$parent_row->{ParentIdentifier} && $first) {
                $first = 0;
                next;
            }
            $history->{$parent_row->{create_date}.'parent'}{date} = $parent_row->{create_date};
            $history->{$parent_row->{create_date}.'parent'}{field} = "Parent";
            $history->{$parent_row->{create_date}.'parent'}{value} = ($parent_row->{ParentIdentifier} || '-');
        }

        my $ticket_sql = "SELECT * FROM historical_Ticket WHERE Serial='$row->{Serial}' ORDER BY create_date";
        my $ticket_history = $dbh->selectall_arrayref($ticket_sql, { Slice => {}});
        $first = 1;
        foreach my $ticket_row (@$ticket_history) {
            clean_row($ticket_row);
            if (!$ticket_row->{Ticket} && $first) {
                $first = 0;
                next;
            }
            $history->{$ticket_row->{create_date}.'ticket'}{date} = $ticket_row->{create_date};
            $history->{$ticket_row->{create_date}.'ticket'}{field} = "Ticket";
            $history->{$ticket_row->{create_date}.'ticket'}{value} = $ticket_row->{Ticket};
        }

        my $summary_sql = "SELECT * FROM historical_Summary WHERE Serial='$row->{Serial}' ORDER BY create_date";
        my $summary_history = $dbh->selectall_arrayref($summary_sql, { Slice => {}});
        $first = 1;
        foreach my $summary_row (@$summary_history) {
            clean_row($summary_row);
            if ($first) {
                $report_data->{data}{$serial}{summary} = $summary_row->{Summary};
                $first = 0;
                next;
            }
            $history->{$summary_row->{create_date}.'summary'}{date} = $summary_row->{create_date};
            $history->{$summary_row->{create_date}.'summary'}{field} = "Summary";
            $history->{$summary_row->{create_date}.'summary'}{value} = $summary_row->{Summary};
        }

            my $journal_sql = "SELECT * FROM alert_journal WHERE Serial='$row->{Serial}' ORDER BY create_date";
            my $journal_history = $dbh->selectall_arrayref($journal_sql, { Slice => {}});
            foreach my $journal_row (@$journal_history) {
                clean_row($journal_row);
                $history->{$journal_row->{create_date}.'journal'}{date} = $journal_row->{create_date};
                $history->{$journal_row->{create_date}.'journal'}{field} = "Action";
                $history->{$journal_row->{create_date}.'journal'}{value} = $journal_row->{entry};
            }

        $report_data->{data}{$serial}{history} = $history;
    }

    return $report_data;
}


sub ajax_send_data {
    my $report_data = shift;

    print "Content-Type: text/plain\n\n";
    print JSON->new->pretty(1)->encode($report_data);
}


sub csv_send_data {
    my $report_data = shift;
    print "Content-Type: text/csv\n";
    print "Content-Disposition: attachment;filename=\"report.csv\"\n\n";

    # Headers
    print "Date/Time, Deleted, Server ID, Alert Group, Alert Key, Summary, Deleted By, Identifier, Severity, Escalation, Parent, Jira Ticket, Action\n";
    
    my @fields1 = qw/deletedat server_id alertgroup alertkey/;
    my @fields2 = qw/deletedby identifier/;
    my @hfields = qw/date field value/;
    foreach my $serial (sort { $a <=> $b } keys %{$report_data->{data}}) {
        my $entry1;
        my $entry2;
        my $date;
        my %audits;
        foreach my $f (@fields1) {
            $entry1 .= "\"$report_data->{data}{$serial}{$f}\",";
        }
        foreach my $f (@fields2) {
            $entry2 .= "\"$report_data->{data}{$serial}{$f}\",";
        }
        $audits{Summary} = $report_data->{data}{$serial}{summary};
        foreach my $his (sort keys %{$report_data->{data}{$serial}{history}}) {
            if ($date && $date ne $report_data->{data}{$serial}{history}{$his}{date}) {
                print "\"$date\", $entry1 \"$audits{Summary}\", $entry2";
                print "\"$audits{Severity}\",\"$audits{Escalation}\",\"$audits{Parent}\",\"$audits{'Jira Ticket'}\",\"$audits{Action}\"\n";
                $audits{Action} = '';
            }
            $date = $report_data->{data}{$serial}{history}{$his}{date};
            $audits{$report_data->{data}{$serial}{history}{$his}{field}} = $report_data->{data}{$serial}{history}{$his}{value};
        }
        # Our final pass through the above loop won't print, so print final version
        print "\"$date\", $entry1 \"$audits{Summary}\", $entry2";
        print "\"$audits{Severity}\",\"$audits{Escalation}\",\"$audits{Parent}\",\"$audits{'Jira Ticket'}\",\"$audits{Action}\"\n";
   }
            
}


sub ajax_result {
    my $form = shift;

    print qq^
        <style tyle='text/css'>
            #wait { text-align: center;}
            #header a { color: #000; }
        </style>
        <script type='text/javascript'>
            var xmlhttp;
            var report_data;
            var sort_by = 'date';
            var sort_order = 'down';
            var base_url = '/cgi-bin/$script_name?report=ajaxreport';
                base_url += '&server_id=$form->{server_id}';
                base_url += '&serial=$form->{serial}';
                base_url += '&cluster=$form->{cluster}';
                base_url += '&type=$form->{type}';
                base_url += '&startdate=$form->{startdate}';
                base_url += '&starttime=$form->{starttime}';
                base_url += '&range=$form->{range}';
                base_url += '&range_type=$form->{range_type}';
                base_url += '&alertgroup=$form->{alertgroup}';
                base_url += '&debug=$form->{debug}';
                base_url += '&jira=$form->{jira}';
            if (window.XMLHttpRequest) {
                xmlhttp = new XMLHttpRequest();
            } else {
                xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
            }

            function process_report() {
                report_data = eval('(' + xmlhttp.responseText + ')');
                var report = document.getElementById('report');
                document.getElementById('status').innerHTML = 'Processing data...';
                create_table_body(report);
                if (report_data.next_set > 0) {
                    document.getElementById('status').innerHTML = 'Retrieved Data Set ' + report_data.next_set + '; Please wait...';
                    request_more(report_data.next_set); 
                } else {
                    create_csv();
                    document.getElementById('status').innerHTML = '';
                    document.getElementById('display_button').style.display = '';
                    document.getElementById('download_button').style.display = '';
                }
            }

            function process_more_report() {
                var new_data = eval('(' + xmlhttp.responseText + ')');
                document.getElementById('status').innerHTML = 'Processing data...';

                // Merge new data into report_data, kill old table
                for (var d in new_data.data) {
                    report_data.data[d] = new_data.data[d];
                }
                var report = document.getElementById('report');
                var current_length = report.rows.length - 1;
                for (var i = current_length; i > 1; i--) {
                    report.deleteRow(i);
                }

                create_table_body(report);
                if (new_data.next_set > 0) {
                    document.getElementById('status').innerHTML = 'Retrieved Data Set ' + new_data.next_set + '; Please wait...';
                    request_more(new_data.next_set);
                } else {
                    create_csv();
                    document.getElementById('status').innerHTML = '';
                    document.getElementById('display_button').style.display = '';
                    document.getElementById('download_button').style.display = '';
                }
                
            }

            function request_more(set) {
                xmlhttp.onreadystatechange=function()
                {
                    if (xmlhttp.readyState == 4) {
                        if (xmlhttp.status == 200) {
                            process_more_report();
                        } else if (xmlhttp.status == 500) {
                            display_error();
                        }
                    }
                };
                var url = base_url + '&set=' + set;
                url += '&t=' + Math.random();
                xmlhttp.open("GET", url, true);
                xmlhttp.send();
            }

            function request_report() {
                xmlhttp.onreadystatechange=function()
                {
                    if (xmlhttp.readyState == 4) {
                        if (xmlhttp.status == 200) {
                            process_report();
                        } else if (xmlhttp.status == 500) {
                            display_error();
                        }
                    }
                };
                var url = base_url + '&t=' + Math.random();
                xmlhttp.open("GET", url, true);
                xmlhttp.send();
            }

            function display_error() {
                var report = document.getElementById('report');
                document.getElementById('status').innerHTML = 'Server Error retrieving report';
            }

            function download_csv() {
                var url = '$script_name?report=csv';
                url += '&server_id=$form->{server_id}';
                url += '&serial=$form->{serial}';
                url += '&cluster=$form->{cluster}';
                url += '&type=$form->{type}';
                url += '&startdate=$form->{startdate}';
                url += '&starttime=$form->{starttime}';
                url += '&range=$form->{range}';
                url += '&range_type=$form->{range_type}';
                url += '&alertgroup=$form->{alertgroup}';
                url += '&debug=$form->{debug}';
                url += '&jira=$form->{jira}';
                window.open(url, "_blank");
            }

            function display_csv() {
                document.getElementById('csv').style.display = '';
            }

            function create_csv() {
                var csv = 'Date/Time, Deleted, Server ID, Alert Group, Alert Key, Summary, Deleted By, Identifier, Severity, Escalation, Parent, Jira Ticket, Action\\n\\r';
                for (d in report_data.data) {
                    var entry1 = '';
                    var entry2 = '';
                    var date = '';
                    var audits = new Object();
                    audits.severity = '';
                    audits.escalation = '';
                    audits.parent = '';
                    audits.jira = '';
                    audits.action = '';
                    audits.summary = '';

                    entry1 += '"' + report_data.data[d].deletedat + '",';
                    entry1 += '"' + report_data.data[d].server_id + '",';
                    entry1 += '"' + report_data.data[d].alertgroup + '",';
                    entry1 += '"' + report_data.data[d].alertkey + '",';
                    audits.summary += '"' + report_data.data[d].summary + '",';
                    entry2 += '"' + report_data.data[d].deletedby + '",';
                    //entry2 += '"' + report_data.data[d].identifier + '",';
                    entry2 += '"' + report_data.data[d].statechange + '",';
                    // Sort our history rows
                    var audit = new Array();
                    var a = 0;
                    for (h in report_data.data[d].history) {
                        audit[a] = h;
                        a++;
                    }
                    audit.sort();
                    for (a = 0; a < audit.length; a++) {
                        if (date != '' && date != report_data.data[d].history[audit[a]].date) {
                            csv += '"' + date + '",' + entry1 + audits.summary + entry2;
                            csv += '"' + audits.severity + '",';
                            csv += '"' + audits.escalation + '",';
                            csv += '"' + audits.parent + '",';
                            csv += '"' + audits.jira + '",';
                            csv += '"' + audits.action + '"\\n\\r';
                            audits.action = '';
                        }
                        date = report_data.data[d].history[audit[a]].date;
                        if (report_data.data[d].history[audit[a]].field == 'Severity') {
                            audits.severity = report_data.data[d].history[audit[a]].value;
                        } else if (report_data.data[d].history[audit[a]].field == 'Escalation') {
                            audits.escalation = report_data.data[d].history[audit[a]].value;
                        } else if (report_data.data[d].history[audit[a]].field == 'Parent') {
                            audits.parent = report_data.data[d].history[audit[a]].value;
                        } else if (report_data.data[d].history[audit[a]].field == 'Jira Ticket') {
                            audits.jira = report_data.data[d].history[audit[a]].value;
                        } else if (report_data.data[d].history[audit[a]].field == 'Action') {
                            audits.action = report_data.data[d].history[audit[a]].value;
                        } else if (report_data.data[d].history[audit[a]].field == 'Summary') {
                            audits.summary = '"' + report_data.data[d].history[audit[a]].value + '",';
                        }
                    }
                    csv += '"' + date + '",' + entry1 + audits.summary + entry2;
                    csv += '"' + audits.severity + '",';
                    csv += '"' + audits.escalation + '",';
                    csv += '"' + audits.parent + '",';
                    csv += '"' + audits.jira + '",';
                    csv += '"' + audits.action + '"\\n\\r';
                }
                document.getElementById('csv').value = csv;
            }

            function create_table_body(table) {
                table.deleteRow(1);
                var rowcount = 1;
                var colormap = new Array();
                colormap[0] = '#00CD00';
                colormap[1] = '#CCCCCC';
                colormap[2] = '#63B8FF';
                colormap[3] = '#FFFF00';
                colormap[4] = '#FFA500';
                colormap[5] = '#FF0000';

                // Sort our primary rows out
                var sorted = new Array();
                var s = 0;
                for (d in report_data.data) {
                    var entry = new Object();
                    entry.index = d;
                    if (sort_by == 'date') {
                        entry.value = report_data.data[d].firstoccurrence;
                    } else if (sort_by == 'deleted') {
                        entry.value = report_data.data[d].deletedat;
                    } else if (sort_by == 'server') {
                        entry.value = report_data.data[d].server_id;
                    } else if (sort_by == 'group') {
                        entry.value = report_data.data[d].alertgroup;
                    } else if (sort_by == 'key') {
                        entry.value = report_data.data[d].alertkey;
                    } else if (sort_by == 'summary') {
                        entry.value = report_data.data[d].summary;
                    } else if (sort_by == 'dby') {
                        entry.value = report_data.data[d].deletedby;
                    } else if (sort_by == 'ident') {
                        entry.value = report_data.data[d].identifier;
                    } else if (sort_by == 'lastmod') {
                        entry.value = report_data.data[d].lastmodifier;
                    }
                    sorted[s] = entry;
                    s++;
                }
                sorted.sort(function(a, b) {
                    var valueA = a.value.toLowerCase();
                    var valueB = b.value.toLowerCase();
                    if (valueA < valueB) {
                        return -1;
                    } else if (valueA > valueB) {
                        return 1;
                    } else {
                        return 0;
                    }
                });
                if (sort_order == 'up') {
                    sorted.reverse();
                }

                // for (d in report_data.data) {
                for (s = 0; s < sorted.length; s++) {
                    var row = table.insertRow(rowcount);
                    row.style.backgroundColor = '#CCC';
                    var cell = row.insertCell(0);
                    cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].firstoccurrence));
                    cell = row.insertCell(1);
                    cell.style.whiteSpace = 'nowrap';
                    if (report_data.data[sorted[s].index].deletedat) {
                        cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].deletedat));
                    } else {
                        cell.appendChild(document.createTextNode(' '));
                    }
                    cell = row.insertCell(2);
                    cell.style.whiteSpace = 'nowrap';

                    var anchor = document.createElement('A');
                    anchor.setAttribute('target', '_blank');
                    anchor.setAttribute('href', '/cgi-bin/$script_name?report=eventhistory&server_id=' +
                                                    report_data.data[d].server_id + '&startdate=' + report_data.startdate + '&starttime=' + report_data.starttime +
                                                    '&alertgroup=' + report_data.alertgroup + '&range=' + report_data.range + '&range_type=' + report_data.range_type);
                    anchor.setAttribute('alt', 'View report for Server' + report_data.data[sorted[s].index].server_id);
                    anchor.appendChild(document.createTextNode(report_data.data[sorted[s].index].server_id));
                    cell.appendChild(anchor);

                    cell = row.insertCell(3);
                    cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].alertgroup));
                    cell = row.insertCell(4);
                    cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].alertkey));
                    cell = row.insertCell(5);
                    cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].summary));
                    cell = row.insertCell(6);
                    if (report_data.data[sorted[s].index].deletedby) {
                        cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].deletedby));
                    } else {
                        cell.appendChild(document.createTextNode(' '));
                    }
                    cell = row.insertCell(7);
                    //cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].identifier));
                    cell.style.whiteSpace = 'nowrap';
                    cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].statechange));
                    rowcount++;
                    var color = report_data.data[sorted[s].index].originalseverity;
                    // Sort our history rows
                    var audit = new Array();
                    var a = 0;
                    for (h in report_data.data[sorted[s].index].history) {
                        audit[a] = h;
                        a++;
                    }
                    audit.sort();
                    for (a = 0; a < audit.length; a++) {
                        var colspan = 6;
                        if (report_data.data[sorted[s].index].history[audit[a]].field == 'Summary') {
                            continue;
                        }
                        if (report_data.data[sorted[s].index].history[audit[a]].field == 'Severity') {
                            color = report_data.data[sorted[s].index].history[audit[a]].raw_value;
                            if (a + 1 < audit.length && report_data.data[sorted[s].index].history[audit[a + 1]].field == 'Summary') {
                                colspan = 3;
                            }
                        }
                        row = table.insertRow(rowcount);
                        row.style.backgroundColor = colormap[color];
                        cell = row.insertCell(0);
                        cell.style.whiteSpace = 'nowrap';
                        cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].history[audit[a]].date));
                        cell = row.insertCell(1);
                        cell.style.whiteSpace = 'nowrap';
                        cell.style.textAlign = 'right';
                        cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].history[audit[a]].field));
                        cell = row.insertCell(2);
                        cell.style.backgroundColor = '#FFF';
                        cell.colSpan = colspan;
                        if (report_data.data[sorted[s].index].history[audit[a]].field == 'Jira Ticket') {
                            if (report_data.data[sorted[s].index].history[audit[a]].value) {
                                var anchor = document.createElement('A');
                                anchor.setAttribute('target', '_blank');
                                anchor.setAttribute('href', '' + report_data.data[sorted[s].index].history[audit[a]].value);
                                anchor.appendChild(document.createTextNode(report_data.data[sorted[s].index].history[audit[a]].value));
                                cell.appendChild(anchor);
                            } else {
                                cell.appendChild(document.createTextNode(' '));
                            }
                        } else {
                            cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].history[audit[a]].value));
                        }
                        if (a + 1 < audit.length && report_data.data[sorted[s].index].history[audit[a + 1]].field == 'Summary') {
                            cell = row.insertCell(3);
                            cell.style.backgroundColor = '#FFF';
                            cell.colSpan = colspan;
                            cell.appendChild(document.createTextNode(report_data.data[sorted[s].index].history[audit[a + 1]].value));
                        }
                        rowcount++;
                    }
                }
                // If we get here with no increase in rowcount, then our data set was empty
                if (rowcount == 1) {
                    var row = table.insertRow(rowcount);
                    var cell= row.insertCell(0);
                    cell.colSpan = 8;
                    cell.style.textAlign = 'center';
                    cell.style.fontWeight = 'bold';
                    cell.appendChild(document.createTextNode('No Data Found'));
                }
            }

            var columns = new Array("date", "deleted", "server", "group", "key", "summary", "dby", "ident", "lastmod");
            function sort_data(column) {
                var i;
                for (i = 0; i < columns.length; i++) {
                    var arrow = document.getElementById(columns[i] + '_arrow');
                    if (columns[i] == column) {
                        if (sort_by == column) {
                            if (sort_order == 'down') {
                                sort_order = 'up';
                            } else {
                                sort_order = 'down';
                            }
                        } else {
                            sort_by = column;
                            sort_order = 'down';
                        }
                        arrow.setAttribute('src', '/images/arrow' + sort_order + '.gif');
                        arrow.style.display = 'block';
                    } else {
                        arrow.style.display = 'none';
                    }
                }

                var report = document.getElementById('report');
                var report_size = report.rows.length;
                for (i = 1; i < report_size; i++) {
                    report.deleteRow(1);
                }
                var row = report.insertRow(1);
                var cell = row.insertCell(0);
                cell.colSpan = 8;
                cell.style.textAlign = 'center';
                cell.appendChild(document.createTextNode('Re-sorting Report Data'));
                create_table_body(report);
            }
        </script>
    ^;

    my ($month, $day, $year) = $form->{startdate} =~ /^(\d{2})\/(\d{2})\/(\d{4})$/;
    my $starttime = sprintf("%4d-%02d-%02d %02d:00:00", $year, $month, $day, $form->{starttime});

    print "<h2>Report on ";
    if ($form->{server_id}) {
        print "<a href='/cgi-bin/server.cgi?server_id=$form->{server_id}' target='_blank'>$form->{server_id}</a> ";
    } 
    if ($form->{serial}) {
        print "Serial: $form->{serial} ";
    }
    if ($form->{jira}) {
        print "Jira Ticket: $form->{jira} ";
    } 

    if ($form->{cluster} && $form->{cluster} ne 'all') {
        print "cluster <a href='/cgi-bin/cluster.cgi?cluster_id=$form->{cluster}' target='_blank'>$form->{cluster}</a> ";
    }
    if ($form->{type} && $form->{type} ne 'all') {
        print "type <a href='/cgi-bin/serverroles/type.cgi?type_id=$form->{type}' target='_blank'>$form->{type}</a> ";
    }
    if ($form->{alertgroup}) {
        print " (Alertgroup Filter: $form->{alertgroup})";
    }
    print "<br />Starting at $starttime, Range: $form->{range} $form->{range_type}</h2>";
    print "<div id='status' style='font-weight: bold; color: #F00; text-align: center;'>Retrieving Data; Please wait...</div>";
    print "<div style='text-align: right;' id='buttons'><button type='button' id='display_button' style='display: none' onclick='display_csv();'>Display .CSV</button> <button type='button' id='download_button' onclick='download_csv();' style='display: none;'>Download as .CSV</button></div>";
    print "<textarea id='csv' style='font-family: monospace; display: none' rows=20 cols=200 readonly></textarea>";
    print qq[
        <table id='report' width='100%' border=1>
            <thead>
                <tr id='header'>
                    <td width='1%' align='center'>
                        <table>
                            <tr><th><a href='javascript:void(0);' onclick='sort_data("date");'>Date/Time</a></th><td><img id='date_arrow' src='/images/arrowdown.gif'/></td></tr>
                        </table>
                    </td>
                    <td width='1%' align='center'>
                        <table>
                            <tr><th><a href='javascript:void(0);' onclick='sort_data("deleted");'>Deleted</a></th><td><img id='deleted_arrow' src='/images/arrowup.gif' style='display: none;'/></td></tr>
                        </table>
                    </td>
                    <td align='center'>
                        <table>
                            <tr><th><a href='javascript:void(0);' onclick='sort_data("server");'>Server ID</a></th><td><img id='server_arrow' src='/images/arrowup.gif' style='display: none;'/></td></tr>
                        </table>
                    </td>
                    <td align='center'>
                        <table>
                            <tr><th><a href='javascript:void(0);' onclick='sort_data("group");'>Alert Group</a></th><td><img id='group_arrow' src='/images/arrowup.gif' style='display: none;'/></td></tr>
                        </table>
                    </td>
                    <td align='center'>
                        <table>
                            <tr><th><a href='javascript:void(0);' onclick='sort_data("key");'>Alert Key</a></th><td><img id='key_arrow' src='/images/arrowup.gif' style='display: none;'/></td></tr>
                        </table>
                    </td>
                    <td align='center'>
                        <table>
                            <tr><th><a href='javascript:void(0);' onclick='sort_data("summary");'>Summary</a></th><td><img id='summary_arrow' src='/images/arrowup.gif' style='display: none;'/></td></tr>
                        </table>
                    </td>
                    <td align='center'>
                        <table>
                            <tr><th><a href='javascript:void(0);' onclick='sort_data("dby");'>Deleted By</a></th><td><img id='dby_arrow' src='/images/arrowup.gif' style='display: none;'/></td></tr>
                        </table>
                    </td>
                    <td align='center'>
                        <table>
                            <tr><th><a href='javascript:void(0);' onclick='sort_data("lastmod");'>Last Modified</a></th><td><img id='lastmod_arrow' src='/images/arrowup.gif' style='display: none;'/></td></tr>
                        </table>
                    </td>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td colspan=100% align='center'>Please wait; report is being generated in the background. Table will update when finished.</td>
                </tr>
            </tbody>
        </table>

        <script type='text/javascript'>
            request_report();
        </script>    
    ];
}

sub html_footer {
    print "</body></html>";
}

sub display_form {
    my $form = shift;
    my $errors = shift;
    my $server_id = $form->{server_id} || '';
    my $startdate = $form->{startdate} || 'mm/dd/yyyy';
    my $starttime = $form->{starttime};
    my $range = $form->{range} || 2;
    my $jira = $form->{jira};
    my $alertgroup = $form->{alertgroup} || '';
    my $focus = $form->{focus} || 'server';
    my $range_type = $form->{range_type};

    print_calendar_javascript();

    my @clusters = $uravo->getClusters();

    print "<script type='text/javascript'>\n";
    print "    var data = { \"clusters\": [\n";
    my $first_cluster = 1;
    foreach my $c ( sort { lc($a->id()) cmp lc($b->id()) } @clusters) {
        my @types = $c->getTypes();
        if ((scalar @types) == 0) {
            next;
        }
        if ($first_cluster) {
            $first_cluster = 0;
        } else {
            print ", \n";
        }
        print "        { \"name\": \"". $c->id() . "\",\n";
        print "          \"types\": [";

        my $first_type = 1;

        foreach my $t (sort { lc($a->id()) cmp lc($b->id()) } @types) {
            if ($first_type) {
                $first_type = 0;
            } else {
                print ", ";
            }
            print "\"" . $t->id() . "\"";
        }
        print "]}";
    }
    print "    \n]};\n";
            
    print qq[
        function dateCheck() { 
            var tocheck = document.report.startdate.value; 
            var returnval;
            if (tocheck == 'mm/dd/yyyy') { 
                 returnval = false; 
                 alert('Please select a start date.'); 
            } else { 
                 returnval = true; 
            } 
            return returnval; 
        }

        function change_focus() {
            var radio = document.getElementsByName('focus');
            var focus;
            for (var i = 0; i < radio.length; i++) {
                if (radio[i].checked) {
                    focus = radio[i].value;
                }
            }
            if (focus == 'cluster') {
                document.getElementById('cluster_select').disabled = false;
                document.getElementById('type_select').disabled = false;
                document.getElementById('server_id').disabled = true;
                document.getElementById('server_id').value = '';
                document.getElementById('jira').disabled = true;
                document.getElementById('jira').value='';
            } else if (focus == 'server') {
                document.getElementById('cluster_select').disabled = true;
                document.getElementById('type_select').disabled = true;
                document.getElementById('server_id').disabled = false;
                document.getElementById('jira').disabled = true;
                document.getElementById('jira').value='';
            } else if (focus == 'jira') {
                document.getElementById('cluster_select').disabled = true;
                document.getElementById('type_select').disabled = true;
                document.getElementById('server_id').disabled = true;
                document.getElementById('jira').disabled = false;
                document.getElementById('server_id').value = '';
            }
        }

        function update_types() {
            var cluster = document.getElementById('cluster_select');
            var type = document.getElementById('type_select');

            if (cluster.value == 'all') {
                type.value = 'all';
                type.disabled = true;
            } else {
                type.disabled = false;
                type.options.length = 0;
                var thiscluster;
                for (var c = 0; c < data.clusters.length; c++) {
                    if (data.clusters[c].name == cluster.value) {
                        thiscluster = data.clusters[c].types;
                        break;
                    }
                }
                var all = document.createElement('option');
                all.setAttribute('value', 'all');
                all.appendChild(document.createTextNode('All Types'));
                type.appendChild(all);
                for (var t = 0; t < thiscluster.length; t++) {
                    var newoption = document.createElement('option');
                    newoption.setAttribute('value', thiscluster[t]);
                    newoption.appendChild(document.createTextNode(thiscluster[t]));
                    type.appendChild(newoption);
                }
            }
        }

        function initialize_clusters() {
            var cluster=document.getElementById('cluster_select');
            for (var c = 0; c < data.clusters.length; c++) {
                var newoption = document.createElement('option');
                newoption.setAttribute('value', data.clusters[c].name);
                newoption.appendChild(document.createTextNode(data.clusters[c].name));
                cluster.appendChild(newoption);
            }
        }
    </script>

    <form name='report' action='$script_name'  onSubmit='return dateCheck()' method='get'>
        <input type='hidden' name='report' value='eventhistory'/>
        <table border=0>
            <tr>
                <td colspan=2 align=center><h3>Historical Event Report</h3></td>
            </tr>
    ];
    if (scalar (keys %$errors) > 0) {
        print "<tr><td colspan=3><div style='border: 1px solid #000; background-color: #FFFFAA; color: #EE0000; padding: 0px 10px 0px 10px;'><h3>Errors:</h3><ul>";
        if ($errors->{server_id}) {
            print "<li>Server ID required for 'By Server ID'</li>";
        }
        if ($errors->{ticket}) {
            print "<li>Ticket required for 'By Ticket'</li>";
        }
        if ($errors->{noform}) {
            print "<li>Report request error, please select options from form below</li>";
        }
        if ($errors->{startdate}) {
            print "<li>Start Date required, must be in format: mm/dd/yyyy</li>";
        }
        if ($errors->{starttime}) {
            print "<li>Start Time was incorrect; must be a value beween 0-23 (12:00AM -> 11:00PM)</li>";
        }
        if ($errors->{range}) {
            print "<li>Range must be at least 1</li>";
        }
        if ($errors->{range_type}) {
            print "<li>Range Type was missing; must be either 'hours' or 'days'</li>";
        }
        print "</ul></div></td></tr>";
    }
    print qq[
            <tr>
                <td valign='top'>
                    <table border=0>
                        <tr>
                            <td style='font-weight: bold; text-align: right;'><input type='radio' name='focus' value='server' 
    ];
    print ' checked ' if ($focus eq 'server');
    print qq[
                            onclick='change_focus();'> By Server ID:</td>
                            <td><input size=10 type='text' id='server_id' name='server_id' value='$server_id'/></td>
                        </tr>
                        <tr>
                            <td colspan=2><hr/></td>
                        </tr>
                        <tr>
                            <td style='font-weight: bold; text-align: right;'><input type='radio' name='focus' value='cluster' 
    ];
    print ' checked ' if ($focus eq 'cluster');
    print qq[
                            onclick='change_focus();'> By Cluster:</td>
                            <td><select name='cluster' id='cluster_select' onchange='update_types();'>
                                <option value='all' selected>All Clusters</option>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td style='font-weight: bold; text-align: right'>and Type:</td>
                            <td><select name='type' id='type_select'>
                                <option value='all' selected>All Types</option>
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td colspan=2><hr/></td>
                        </tr>
                        <tr>
                            <td style='font-weight: bold; text-align: right;'><input type='radio' name='focus' value='jira'
    ];
    print ' checked ' if ($focus eq 'jira');
    print qq[
                            onclick='change_focus();'> By Jira Ticket:</td>
                            <td><input type='text' size=10 name='jira' id='jira' value='$jira'/></td>
                        </tr>
                    </table>
                </td>
                <td valign='top' style='border-left: 1px solid #000'>
                    <table border=0>
                        <tr>
                            <td style='font-weight: bold; text-align: right'>Start Date:</td>
                            <td nowrap><input type='text' name='startdate' value='$startdate' size=10 onfocus="if(this.value=='mm/dd/yyyy') {this.value=''};" onblur="if(this.value==''){this.value='mm/dd/yyyy'};">
                                <a href="javascript: void(0);" onClick="displayDatePicker('startdate',this,null,null);"><img src="/images/cal.gif" border=0 alt="Click here for calendar"/></a></td>
                        </tr>
                        <tr>
                            <td style='font-weight: bold; text-align: right'>Start Time:</td>
                            <td>
                                <select name='starttime'>
    ];
    for (my $i = 0; $i < 24; $i++) {
        printf("<option value='\%d' \%s>%02d:00 \%s</option>", $i, ($i == $starttime ? 'selected' : ''), ($i % 12 == 0 ? 12 : $i % 12), ($i < 12 ? 'AM' : 'PM'));
    }
    print qq[
                                </select>
                            </td>
                        </tr>
                        <tr>
                            <td style='font-weight: bold; text-align: right' valign='top'>End Point:</td>
                            <td>
                                <table>
                                    <tr>
                                        <td><input type='radio' name='range_radio' value='now' checked/></td><td> Through Now, or</td>
                                    </tr>
                                    <tr>
                                        <td><input type='radio' name='range_radio' value='range'/></td><td> Specify Range:</td>
                                    </tr>
                                    <tr>
                                        <td>&nbsp;</td>
                                        <td><input type='text' name='range' value='$range' size=2/>
                                                <select name='range_type'>
    ];
    print "<option value='hours' " . ($range_type eq 'hours' || !$range_type ? 'selected' : '') . ">Hours</option>";
    print "<option value='days' " . ($range_type eq 'days' ? 'selected' : '') . ">Days</option>";
    print qq[
                                                </select>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        <tr>
                            <td style='font-weight: bold; text-align: right' nowrap>Filter by AlertGroup:</td>
                            <td><input type='text' size=15 name='alertgroup' value='$alertgroup'/></td>
                        </tr>
    ];

    print qq[
                    </table>
                </td>
            </tr>
            <tr>
                <td colspan=2 align=center><input type='submit' value='Generate Report'/></td>
            </tr>
        </table>
    </form>
    <script type='text/javascript'>
        initialize_clusters();
        change_focus();
    </script>
    ];
}


sub clean_row {
    my $row = shift || return;

    foreach my $key (keys %$row) {
        $row->{$key} =~s/ +$//;
        $row->{$key} =~s/\.000000$//;
    }
}

sub minutes_to_time {
    my $time = shift;

    my $hours = int($time / 60);
    my $minutes = $time % 60;

    return sprintf('%d hours', $hours);
}

sub print_calendar_javascript {
    print <<CALENDAR;
    <script type='text/javascript'>

    // Calendar formatting Info
    var datePickerDivID       = "datepicker";
    var iFrameDivID           = "datepickeriframe";
    var dayArrayShort         = new Array('Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa');
    var dayArrayMed           = new Array('Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat');
    var dayArrayLong          = new Array('Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday');
    var monthArrayShort       = new Array('Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec');
    var monthArrayMed         = new Array('Jan', 'Feb', 'Mar', 'Apr', 'May', 'June', 'July', 'Aug', 'Sept', 'Oct', 'Nov', 'Dec');
    var monthArrayLong        = new Array('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December');
    var defaultDateSeparator  = "/";     // common values would be "/" or "."
    var defaultDateFormat     = "mdy"    // valid values are "mdy", "dmy", and "ymd"
    var dateSeparator         = defaultDateSeparator;
    var dateFormat            = defaultDateFormat;

    var NS4 = (document.layers) ? 1 : 0;
    var IE4 = (document.all) ? 1 : 0;
    var DOM = ((document.getElementById) && (!IE4)) ? 1 : 0;
    var isOver = false;
    var timer = null;
    var comment_popup_elements = [];

    if (NS4) {
        origWidth = innerWidth;
        origHeight = innerHeight;
    }

    if (NS4) onresize = reDo;
    if (DOM) onload = InitObj;

    function reDo() {
        if (innerWidth != origWidth || innerHeight != origHeight) {
            location.reload();
        }
    }

    function InitObj() {
        keepGoing = 1;
        i = 1;
        while (keepGoing) {
            var whichEl = "menu" + i;
            if (DOM) {
                whichEl = document.getElementById(whichEl);
            } else if (NS4) {
                whichEl = document.layers[whichEl];
            } else if (document.all[whichEl]) {
                whichEl = document.all[whichEl].style;
            } else {
                whichEl = "";
            }
            if (whichEl) {
                whichEl.onmouseover = OverLayer;
                whichEl.onmouseout = OutLayer;
            } else {
                keepGoing = 0;
            }
            i++;
        }
    }

    function IndexPopupElement(element) {
        for(var i=0; i<comment_popup_elements.length;i++) {
            if(comment_popup_elements[i] == element) {
                return(i);
            }
        }
        comment_popup_elements[comment_popup_elements.length] = element;
        return(comment_popup_elements.length-1);
    }


    function ShowLayer(showEl, event,whichAnchor) {
        clearTimeout(timer);
        HideAllLayers();

        var whichEl;
        IndexPopupElement(showEl);
        if (DOM) {
            whichEl = document.getElementById(showEl);
        } else {
            if (NS4) {
                whichEl = document.layers[showEl];
            } else {
                whichEl = document.all[showEl].style;
            }
        }
        if(whichAnchor == null) {
           whichAnchor = showEl + "A";
        }
        menuTop = 0;
        menuLeft = 0;

        if (IE4) {
            if (document.all[whichAnchor]) {
                menuTop = findy(document.all[whichAnchor]) + 17;
                menuLeft = findx(document.all[whichAnchor]);
            }
        }
        if (NS4) {
            if (document.anchors[whichAnchor]) {
                menuTop = document.anchors[whichAnchor].y + 17;
                menuLeft = document.anchors[whichAnchor].x;
            }
        }
        if (DOM) {
            if (document.anchors[whichAnchor]) {
                menuTop = 17;
                menuLeft = -2;
                var myObject = document.anchors[whichAnchor];
                while (myObject.offsetParent) {
                    menuTop = menuTop + myObject.offsetTop;
                    menuLeft = menuLeft + myObject.offsetLeft;
                    myObject = myObject.offsetParent;
                }
            }
        }   
        if (whichEl) {
            if (DOM) {
                whichEl.style.visibility = "visible";
                whichEl.style.top = menuTop;
                whichEl.style.left = menuLeft + 25;
            } else {
                whichEl.visibility = "visible";
                whichEl.top = menuTop;
                whichEl.left = menuLeft + 25;
            }
        }
    }

    function findy(item) {
        if (item.offsetParent) {
            return item.offsetTop + findy(item.offsetParent);
        } else {
            return item.offsetTop;
        }
    }

    function findx(item) {
        if (item.offsetParent) {
            return item.offsetLeft + findx(item.offsetParent);
        } else {
            return item.offsetLeft;
        }   
    }

    function HideAllLayers() {
        for(var i=0; i<comment_popup_elements.length;i++) {
            var whichEl =comment_popup_elements[i];
            if (DOM) {
                whichEl = document.getElementById(whichEl);
            } else if (NS4) {
                whichEl = document.layers[whichEl];
            } else if (document.all[whichEl]) {
                whichEl = document.all[whichEl].style;
            } else {
                whichEl = "";
            }
            if (whichEl) {
                if (!isOver) {
                    if (DOM) {
                        whichEl.style.visibility = "hidden";
                    } else {
                        whichEl.visibility = "hidden";
                    }
                }
            } 
        }
    }

    function OverLayer() { clearTimeout(timer); isOver = true; }

    function OutLayer() {
        clearTimeout(timer);
        isOver = false;
        timer = setTimeout("HideAllLayers()",300);
    }

/**
This is a JavaScript library that will allow you to easily add some basic DHTML
drop-down datepicker functionality to your Notes forms. This script is not as
full-featured as others you may find on the Internet, but it's free, it's easy to
understand, and it's easy to change.

You'll also want to include a stylesheet that makes the datepicker elements
look nice. An example one can be found in the database that this script was
originally released with, at:

http://www.nsftools.com/tips/NotesTips.htm#datepicker

I've tested this lightly with Internet Explorer 6 and Mozilla Firefox. I have no idea
how compatible it is with other browsers.

version 1.5
December 4, 2005
Julian Robichaux -- http://www.nsftools.com

HISTORY
--  version 1.0 (Sept. 4, 2004):
Initial release.

--  version 1.1 (Sept. 5, 2004):
Added capability to define the date format to be used, either globally (using the
defaultDateSeparator and defaultDateFormat variables) or when the displayDatePicker
function is called.

--  version 1.2 (Sept. 7, 2004):
Fixed problem where datepicker x-y coordinates weren't right inside of a table.
Fixed problem where datepicker wouldn't display over selection lists on a page.
Added a call to the datePickerClosed function (if one exists) after the datepicker
is closed, to allow the developer to add their own custom validation after a date
has been chosen. For this to work, you must have a function called datePickerClosed
somewhere on the page, that accepts a field object as a parameter. See the
example in the comments of the updateDateField function for more details.

--  version 1.3 (Sept. 9, 2004)
Fixed problem where adding the <div> and <iFrame> used for displaying the datepicker
was causing problems on IE 6 with global variables that had handles to objects on
the page (I fixed the problem by adding the elements using document.createElement()
and document.body.appendChild() instead of document.body.innerHTML += ...).

--  version 1.4 (Dec. 20, 2004)
Added "targetDateField.focus();" to the updateDateField function (as suggested
by Alan Lepofsky) to avoid a situation where the cursor focus is at the top of the
form after a date has been picked. Added "padding: 0px;" to the dpButton CSS
style, to keep the table from being so wide when displayed in Firefox.

-- version 1.5 (Dec 4, 2005)
Added display=none when datepicker is hidden, to fix problem where cursor is
not visible on input fields that are beneath the date picker. Added additional null
date handling for date errors in Safari when the date is empty. Added additional
error handling for iFrame creation, to avoid reported errors in Opera. Added
onMouseOver event for day cells, to allow color changes when the mouse hovers
over a cell (to make it easier to determine what cell you're over). Added comments
in the style sheet, to make it more clear what the different style elements are for.
This is the main function you'll call from the onClick event of a button.
Normally, you'll have something like this on your HTML page:

Start Date: <input name="StartDate">
<input type=button value="select" onclick="displayDatePicker('StartDate');">

That will cause the datepicker to be displayed beneath the StartDate field and
any date that is chosen will update the value of that field. If you'd rather have the
datepicker display beneath the button that was clicked, you can code the button
like this:

<input type=button value="select" onclick="displayDatePicker('StartDate', this);">

So, pretty much, the first argument (dateFieldName) is a string representing the
name of the field that will be modified if the user picks a date, and the second
argument (displayBelowThisObject) is optional and represents an actual node
on the HTML document that the datepicker should be displayed below.

In version 1.1 of this code, the dtFormat and dtSep variables were added, allowing
you to use a specific date format or date separator for a given call to this function.
Normally, you'll just want to set these defaults globally with the defaultDateSeparator
and defaultDateFormat variables, but it doesn't hurt anything to add them as optional
parameters here. An example of use is:

<input type=button value="select" onclick="displayDatePicker('StartDate', false, 'dmy', '.');">

This would display the datepicker beneath the StartDate field (because the
displayBelowThisObject parameter was false), and update the StartDate field with
the chosen value of the datepicker using a date format of dd.mm.yyyy
*/

var __calendarHighlightDays = new Array();
function displayDatePicker(dateFieldName, displayBelowThisObject, dtFormat, dtSep, highlightDays)
{
  var targetDateField = document.getElementsByName (dateFieldName).item(0);

    try {
        if (highlightDays && highlightDays.length) {
            for (var i=0;i<highlightDays.length;i++) {
              __calendarHighlightDays[highlightDays[i]] = 1;
            }
        }
    }catch(e){}
 
  // if we weren't told what node to display the datepicker beneath, just display it
  // beneath the date field we're updating
  if (displayBelowThisObject)
    displayBelowThisObject = targetDateField;
 
  // if a date separator character was given, update the dateSeparator variable
  if (dtSep)
    dateSeparator = dtSep;
  else
    dateSeparator = defaultDateSeparator;
 
  // if a date format was given, update the dateFormat variable
  if (dtFormat)
    dateFormat = dtFormat;
  else
    dateFormat = defaultDateFormat;
 
  var x = displayBelowThisObject.offsetLeft;
  var y = displayBelowThisObject.offsetTop + displayBelowThisObject.offsetHeight ;
 
  // deal with elements inside tables and such
  var parent = displayBelowThisObject;
  while (parent.offsetParent) {
    parent = parent.offsetParent;
    x += parent.offsetLeft;
    y += parent.offsetTop ;
  }
 
  drawDatePicker(targetDateField, x, y);
}


/**
Draw the datepicker object (which is just a table with calendar elements) at the
specified x and y coordinates, using the targetDateField object as the input tag
that will ultimately be populated with a date.

This function will normally be called by the displayDatePicker function.
*/
function drawDatePicker(targetDateField, x, y)
{
  var dt = getFieldDate(targetDateField.value );
 
  // the datepicker table will be drawn inside of a <div> with an ID defined by the
  // global datePickerDivID variable. If such a div doesn't yet exist on the HTML
  // document we're working with, add one.
  if (!document.getElementById(datePickerDivID)) {
    // don't use innerHTML to update the body, because it can cause global variables
    // that are currently pointing to objects on the page to have bad references
    //document.body.innerHTML += "<div id='" + datePickerDivID + "' class='dpDiv'></div>";
    var newNode = document.createElement("div");
    newNode.setAttribute("id", datePickerDivID);
    newNode.setAttribute("class", "dpDiv");
    newNode.setAttribute("style", "visibility: hidden;");
    document.body.appendChild(newNode);
  }
 
  // move the datepicker div to the proper x,y coordinate and toggle the visiblity
  var pickerDiv = document.getElementById(datePickerDivID);
  pickerDiv.style.position = "absolute";
  pickerDiv.style.left = x + "px";
  pickerDiv.style.top = y + "px";
  pickerDiv.style.visibility = (pickerDiv.style.visibility == "visible" ? "hidden" : "visible");
  pickerDiv.style.display = (pickerDiv.style.display == "block" ? "none" : "block");
  pickerDiv.style.zIndex = 10000;
 
  // draw the datepicker table
  var html=refreshDatePicker(targetDateField.name, dt.getFullYear(), dt.getMonth(), dt.getDate());
}

/**
This is the function that actually draws the datepicker calendar.
*/
function refreshDatePicker(dateFieldName, year, month, day, xframe)
{
  // if no arguments are passed, use today's date; otherwise, month and year
  // are required (if a day is passed, it will be highlighted later)
  var thisDay = new Date();
 
  if ((month >= 0) && (year > 0)) {
    thisDay = new Date(year, month, 1);
  } else {
    day = thisDay.getDate();
    thisDay.setDate(1);
  }
 
  // the calendar will be drawn as a table
  // you can customize the table elements with a global CSS style sheet,
  // or by hardcoding style and formatting elements below
  var crlf = "\\r\\n";
  var TABLE = "<table cols=7 class='dpTable'>" + crlf;
  var xTABLE = "</table>" + crlf;
  var TR = "<tr class='dpTR'>";
  var TR_title = "<tr class='dpTitleTR'>";
  var TR_days = "<tr class='dpDayTR'>";
  var TR_todaybutton = "<tr class='dpTodayButtonTR'>";
  var xTR = "</tr>" + crlf;
  var TD = "<td class='dpTD' onMouseOut='this.className=\\"dpTD\\";' onMouseOver=' this.className=\\"dpTDHover\\";' ";    // leave this tag open, because we'll be adding an onClick event
  var TD_title = "<td colspan=5 class='dpTitleTD'>";
  var TD_buttons = "<td class='dpButtonTD'>";
  var TD_todaybutton = "<td colspan=7 class='dpTodayButtonTD'>";
  var TD_days = "<td class='dpDayTD'>";
  var TD_selected = "<td class='dpDayHighlightTD' onMouseOut='this.className=\\"dpDayHighlightTD\\";' onMouseOver='this.className=\\"dpTDHover\\";' ";    // leave this tag open, because we'll be adding an onClick event
  var TD_highlight = "<td class='dpDayReserveTD' onMouseOut='this.className=\\"dpDayReserveTD\\";' onMouseOver='this.className=\\"dpTDHover\\";' ";    // leave this tag open, because we'll be adding an onClick event
  var xTD = "</td>" + crlf;
  var DIV_title = "<div class='dpTitleText'>";
  var DIV_selected = "<div class='dpDayHighlight'>";
  var xDIV = "</div>";
 
  // start generating the code for the calendar table
  var html = TABLE;
  var i = 0;
 
  // this is the title bar, which displays the month and the buttons to
  // go back to a previous month or forward to the next month
  html += TR_title;
  if (!xframe) {
      html += TD_buttons + getButtonCode(dateFieldName, thisDay, -1, "&lt;") + xTD;
  } else {
      html += TD_buttons + '&nbsp;' + xTD;
  }
  html += TD_title + DIV_title + monthArrayLong[ thisDay.getMonth()] + " " + thisDay.getFullYear() + xDIV + xTD;
  if (xframe) {
      html += TD_buttons + getButtonCode(dateFieldName, thisDay, 0, "&gt;") + xTD;
  } else {
      html += TD_buttons + '&nbsp;' + xTD;
  }
  html += xTR;
 
  // this is the row that indicates which day of the week we're on
  html += TR_days;
  for(i = 0; i < dayArrayShort.length; i++)
    html += TD_days + dayArrayShort[i] + xTD;
  html += xTR;
 
  // now we'll start populating the table with days of the month
  html += TR;
 
  var wk_rows=0;
  // first, the leading blanks
  for (i = 0; i < thisDay.getDay(); i++)
    html += TD + '&nbsp;' + xTD;
 
  // now, the days of the month
  do {
    dayNum = thisDay.getDate();

    TD_onclick = " onclick=\\"updateDateField('" + dateFieldName + "', '" + getDateString(thisDay) + "');\\">";

    if (dayNum == day && !xframe)
      html += TD_selected + TD_onclick + DIV_selected + dayNum + xDIV + xTD;
    else if (__calendarHighlightDays[getDateString(thisDay)])
      html += TD_highlight + TD_onclick + DIV_selected + dayNum + xDIV + xTD;
    else
      html += TD + TD_onclick + dayNum +  xTD;
    
    // if this is a Saturday, start a new row
    if (thisDay.getDay() == 6) {
      html += xTR + TR;
      wk_rows += 1;
    }
    
    // increment the day
    thisDay.setDate(thisDay.getDate() + 1);
  } while (thisDay.getDate() > 1)
 
  // fill in any trailing blanks
  if (thisDay.getDay() > 0) {
    for (i = 6; i > thisDay.getDay(); i--)
      html += TD + '&nbsp;' + xTD;
    wk_rows += 1;
  }
  html += xTR;

  while (wk_rows < 6) {
    wk_rows += 1;
    html += TR;
    for (i = 6; i > 0; i--) {
       html += '<TD>&nbsp;</TD>';
    }
    html += xTR;
  }
 
  // add a button to allow the user to easily return to today, or close the calendar
  var today = new Date();
  var todayString = "Today is " + dayArrayMed[today.getDay()] + ", " + monthArrayMed[ today.getMonth()] + " " + today.getDate();
  html += TR_todaybutton + TD_todaybutton;
  if (!xframe) {
     html += "<button class='dpTodayButton' onClick='refreshDatePicker(\\"" + dateFieldName + "\\");'>this month</button> ";
  } else {
     html += "<button class='dpTodayButton' onClick='updateDateField(\\"" + dateFieldName + "\\");'>close</button>";
  }
  html += xTD + xTR;

  // and finally, close the table
  html += xTABLE;
  // draw the datepicker table
  var htmlx;
  if (xframe){
      return html;
  } else {
      htmlx = refreshDatePicker(dateFieldName, thisDay.getFullYear(), thisDay.getMonth(), thisDay.getDate(), 1);
  }
  var xhtml = "<table><tr><td>" + html + "</td><td>" + htmlx + "</td></tr></table>";
  document.getElementById(datePickerDivID).innerHTML = xhtml;
  // add an "iFrame shim" to allow the datepicker to display above selection lists
  adjustiFrame();
}

/**
Convenience function for writing the code for the buttons that bring us back or forward
a month.
*/
function getButtonCode(dateFieldName, dateVal, adjust, label)
{
  var newMonth = (dateVal.getMonth () + adjust) % 12;
  var newYear = dateVal.getFullYear() + parseInt((dateVal.getMonth() + adjust) / 12);
  if (newMonth < 0) {
    newMonth += 12;
    newYear += -1;
  }
 
  return "<button class='dpButton' onClick='refreshDatePicker(\\"" + dateFieldName + "\\", " + newYear + ", " + newMonth + ");'>" + label + "</button>";
}


/**
Convert a JavaScript Date object to a string, based on the dateFormat and dateSeparator
variables at the beginning of this script library.
*/
function getDateString(dateVal)
{
  var dayString = "00" + dateVal.getDate();
  var monthString = "00" + (dateVal.getMonth()+1);
  dayString = dayString.substring(dayString.length - 2);
  monthString = monthString.substring(monthString.length - 2);
 
  switch (dateFormat) {
    case "dmy" :
      return dayString + dateSeparator + monthString + dateSeparator + dateVal.getFullYear();
    case "ymd" :
      return dateVal.getFullYear() + dateSeparator + monthString + dateSeparator + dayString;
    case "mdy" :
    default :
      return monthString + dateSeparator + dayString + dateSeparator + dateVal.getFullYear();
  }
}


/**
Convert a string to a JavaScript Date object.
*/
function getFieldDate(dateString)
{
  var dateVal;
  var dArray;
  var d, m, y;
 
  try {
    dArray = splitDateString(dateString);
    if (dArray) {
      switch (dateFormat) {
        case "dmy" :
          d = parseInt(dArray[0], 10);
          m = parseInt(dArray[1], 10) - 1;
          y = parseInt(dArray[2], 10);
          break;
        case "ymd" :
          d = parseInt(dArray[2], 10);
          m = parseInt(dArray[1], 10) - 1;
          y = parseInt(dArray[0], 10);
          break;
        case "mdy" :
        default :
          d = parseInt(dArray[1], 10);
          m = parseInt(dArray[0], 10) - 1;
          y = parseInt(dArray[2], 10);
          break;
      }
      dateVal = new Date(y, m, d);
    } else if (dateString) {
      dateVal = new Date(dateString);
    } else {
      dateVal = new Date();
    }
  } catch(e) {
    dateVal = new Date();
  }
 
  return dateVal;
}


/**
Try to split a date string into an array of elements, using common date separators.
If the date is split, an array is returned; otherwise, we just return false.
*/
function splitDateString(dateString)
{
  var dArray;
  if (dateString.indexOf("/") >= 0)
    dArray = dateString.split("/");
  else if (dateString.indexOf(".") >= 0)
    dArray = dateString.split(".");
  else if (dateString.indexOf("-") >= 0)
    dArray = dateString.split("-");
  else if (dateString.indexOf("\\\\") >= 0)
    dArray = dateString.split("\\\\");
  else
    dArray = false;
 
  return dArray;
}

/**
Update the field with the given dateFieldName with the dateString that has been passed,
and hide the datepicker. If no dateString is passed, just close the datepicker without
changing the field value.

Also, if the page developer has defined a function called datePickerClosed anywhere on
the page or in an imported library, we will attempt to run that function with the updated
field as a parameter. This can be used for such things as date validation, setting default
values for related fields, etc. For example, you might have a function like this to validate
a start date field:

function datePickerClosed(dateField)
{
  var dateObj = getFieldDate(dateField.value);
  var today = new Date();
  today = new Date(today.getFullYear(), today.getMonth(), today.getDate());
 
  if (dateField.name == "StartDate") {
    if (dateObj < today) {
      // if the date is before today, alert the user and display the datepicker again
      alert("Please enter a date that is today or later");
      dateField.value = "";
      document.getElementById(datePickerDivID).style.visibility = "visible";
      adjustiFrame();
    } else {
      // if the date is okay, set the EndDate field to 7 days after the StartDate
      dateObj.setTime(dateObj.getTime() + (7 * 24 * 60 * 60 * 1000));
      var endDateField = document.getElementsByName ("EndDate").item(0);
      endDateField.value = getDateString(dateObj);
    }
  }
}

*/

function updateDateField(dateFieldName, dateString)
{
  var targetDateField = document.getElementsByName (dateFieldName).item(0);
  if (dateString)
    targetDateField.value = dateString;
 
  var pickerDiv = document.getElementById(datePickerDivID);
  pickerDiv.style.visibility = "hidden";
  pickerDiv.style.display = "none";
 
  adjustiFrame();
  targetDateField.focus();
 
  // after the datepicker has closed, optionally run a user-defined function called
  // datePickerClosed, passing the field that was just updated as a parameter
  // (note that this will only run if the user actually selected a date from the datepicker)
  if ((dateString) && (typeof(datePickerClosed) == "function"))
    datePickerClosed(targetDateField);
}


/**
Use an "iFrame shim" to deal with problems where the datepicker shows up behind
selection list elements, if they're below the datepicker. The problem and solution are
described at:

http://dotnetjunkies.com/WebLog/jking/archive/2003/07/21/488.aspx
http://dotnetjunkies.com/WebLog/jking/archive/2003/10/30/2975.aspx
*/
function adjustiFrame(pickerDiv, iFrameDiv)
{
  // we know that Opera doesn't like something about this, so if we
  // think we're using Opera, don't even try
  var is_opera = (navigator.userAgent.toLowerCase().indexOf("opera") != -1);
  if (is_opera)
    return;
  
  // put a try/catch block around the whole thing, just in case
  try {
    if (!document.getElementById(iFrameDivID)) {
      // don't use innerHTML to update the body, because it can cause global variables
      // that are currently pointing to objects on the page to have bad references
      //document.body.innerHTML += "<iframe id='" + iFrameDivID + "' src='javascript:false;' scrolling='no' frameborder='0'>";
      var newNode = document.createElement("iFrame");
      newNode.setAttribute("id", iFrameDivID);
      newNode.setAttribute("src", "javascript:false;");
      newNode.setAttribute("scrolling", "no");
      newNode.setAttribute ("frameborder", "0");
      document.body.appendChild(newNode);
    }
    
    if (!pickerDiv)
      pickerDiv = document.getElementById(datePickerDivID);
    if (!iFrameDiv)
      iFrameDiv = document.getElementById(iFrameDivID);
    
    try {
      iFrameDiv.style.position = "absolute";
      iFrameDiv.style.width = pickerDiv.offsetWidth;
      iFrameDiv.style.height = pickerDiv.offsetHeight ;
      iFrameDiv.style.top = pickerDiv.style.top;
      iFrameDiv.style.left = pickerDiv.style.left;
      iFrameDiv.style.zIndex = pickerDiv.style.zIndex - 1;
      iFrameDiv.style.visibility = pickerDiv.style.visibility ;
      iFrameDiv.style.display = pickerDiv.style.display;
    } catch(e) {
    }
 
  } catch (ee) {
  }
 
}
    </script>
CALENDAR

}
