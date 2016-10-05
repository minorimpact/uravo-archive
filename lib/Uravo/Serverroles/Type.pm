package Uravo::Serverroles::Type;

use strict;
use lib "/usr/local/uravo/lib";
use Uravo;
use Data::Dumper;

my $uravo;

sub new {
    my $self	    = {};
    my $package	    = shift || return;
    my $type_id     = shift || return;

    $uravo ||= new Uravo;

    my $type_data = $uravo->{db}->selectrow_hashref("SELECT * FROM type WHERE type_id=?", undef, ( $type_id )) || return;
    return unless ($type_data);

    foreach my $key (keys %{$type_data}) {
        $self->{type_fields}  .= "$key ";
        $self->{$key} = $type_data->{$key};
    }

    my $proc_data = $uravo->{db}->selectall_arrayref("SELECT * FROM type_process WHERE type_id=?", {Slice=>{}}, ( $type_id )) || die ($uravo->{db}->errstr);
    foreach my $proc (@$proc_data) {
        $self->{procs}{$proc->{process_id}} = $proc;
    }
    $self->{object_type} =  'type';
    bless $self;
    return $self;
}

sub add {
    my $params = shift || return;
    my $changelog = shift || {note=>'Uravo::Serverroles::Type::add()', user=>$0};

    my $type_id = $params->{type_id} || return;


    $uravo ||= new Uravo;
    my $insert_type = $uravo->{db}->do("insert into type (type_id, create_date) values (?, now())",undef, ($type_id)) || die($uravo->{db}->errstr);
    $uravo->changelog({object_type=>'type',object_id=>$type_id,field_name=>'New type.',new_value=>$type_id},$changelog);

    return new Uravo::Serverroles::Type($type_id);
}


sub getServers {
    my $self    = shift || return;
    my $params  = shift;


    my $local_params;
    map { $local_params->{$_}   = $params->{$_} } keys %{$params};
    $local_params->{type_id} = $self->id();
    $local_params->{all_silos} = 1;
    return $uravo->getServers($local_params);
}

sub getClusters {
    $uravo->log("Uravo::Serverroles::Type::getClusters()", 5);
    my $self    = shift || return;
    my $params  = shift || {};

    my $local_params;
    map { $local_params->{$_}   = $params->{$_} } keys %{$params};
    $local_params->{type_id} = $self->id();
    $local_params->{all_silos} = 1;
    return $uravo->getClusters($local_params);
}

sub _list {
    my $params	= shift || {};

    $uravo ||= new Uravo;
    $uravo->log("Uravo::Serverroles::Type::_list()",5);
    my $type_id = ($params->{type} || $params->{type_id});
    my $cluster_id = ($params->{cluster} || $params->{cluster_id});
    my $silo_id = ($params->{silo} || $params->{silo_id});

    my $list = $uravo->getCache("Type:_list:$type_id:$cluster_id:$silo_id");
    return keys %$list if ($list);

    my $where	= "where t.type_id is not null";
    if ($type_id) { $where .= " and sr.type_id='$type_id'"; }
    if ($cluster_id) { $where .= " and server.cluster_id='$cluster_id'"; }
    if ($silo_id) { $where .= " AND silo.silo_id = '$silo_id'"; }

    my $sql= "select distinct(t.type_id) from type t left join server_type st on (t.type_id=st.type_id) left join server on (st.server_id=server.server_id) left join cluster on (server.cluster_id=cluster.cluster_id) left join silo on (cluster.silo_id=silo.silo_id) $where";
    $uravo->log("$sql",9);
    my $types    = $uravo->{db}->selectall_arrayref($sql, {Slice=>{}}) || die("Can't get a list of types:" . $uravo->{db}->errstr);
    foreach my $type (@$types) { 
        my $id = $type->{type_id};
        next unless ($id);
        $list->{$id}++;
    }

    $uravo->setCache("Type:_list:$type_id:$cluster_id:$silo_id", $list);
    return keys %$list;
}

sub set {
    my $self        = shift || return;
    my $field       = shift || return;
    my $value       = shift;

    return $self->update($field, $value);
}

sub getProcesses {
    my $self = shift || return;

    return $uravo->{db}->selectall_hashref("SELECT p.*, tp.yellow, tp.red FROM process p, type_process tp where p.process_id=tp.process_id and tp.type_id=?", "process_id", {Slice=>{}}, $self->id()) || die($self->{db}->errstr);
}

sub update {
    my $self            = shift || return;
    my $field           = shift || return;
    my $value           = shift;
    my $changelog       = shift;

    if (!$changelog && ref($value) eq 'HASH' && ref($field) eq 'HASH') {
        $changelog = $value;
    } elsif (!$changelog) {
        $changelog = { user=>'unknown'};
    }

    if (ref($field) eq 'HASH') {
        foreach my $f (keys %$field) {
            $self->update($f, $field->{$f}, $changelog);
        }
        return $changelog;
    }

    if ($field eq 'procs') {
        my $proclist = $uravo->getProcesses();
        my $type_process = $uravo->{db}->selectall_arrayref("SELECT process_id as proc_id, red from type_process WHERE type_id=?", {Slice=>{}}, ($self->id()));
        # Scan the database for process to delete.
        foreach my $dbproc (@$type_process) {
            my $done = 0;
            foreach my $proc ( @$value ) {
                if ($proc->{proc_id} eq $dbproc->{proc_id}) {
                    $done = 1;
                }
            }
            if (!$done) {
                $uravo->{db}->do("delete from type_process where type_id=? and process_id=?", undef, ($self->id(), $dbproc->{proc_id}));
                $uravo->changelog({object_type=>$self->{object_type},object_id=>$self->id(),field_name=>'deleted process', old_value=>$proclist->{$dbproc->{proc_id}}{name}},$changelog);
            }
        }

        # Scan the databse for new processes to add.
        foreach my $proc ( @$value ) {
            my $done = 0;
            foreach my $dbproc (@$type_process) {
                if ($proc->{proc_id} eq $dbproc->{proc_id}) {
                    $done = 1;
                    if ($proc->{red} ne $dbproc->{red}) {
                        $uravo->{db}->do("update type_process set red=? where type_id=? and process_id=?", undef, ($proc->{red}, $self->id(), $proc->{proc_id}));
                        $uravo->changelog({object_type=>$self->{object_type},object_id=>$self->id(),field_name=>"updated ${\ $proclist->{$proc->{proc_id}}{name};} threshold", old_value=>$dbproc->{red},new_value=>$proc->{red}},$changelog);
                    }

                }
            }
            if (!$done) {
                $uravo->{db}->do("insert into type_process (type_id, process_id, red)  values (?, ?, ?)", undef, ($self->id(), $proc->{proc_id}, $proc->{red}));
                $uravo->changelog({object_type=>$self->{object_type},object_id=>$self->id(),field_name=>'added process', new_value=>$proclist->{$proc->{proc_id}}{name}},$changelog);
            }
        }

        return $changelog;
    }

    if ($field eq 'modules') {
        my $type_module = $uravo->{db}->selectall_arrayref("SELECT module_id,enabled from type_module WHERE type_id=?", {Slice=>{}}, ($self->id())) || die($uravo->{db}->errstr);
        # Scan the database for modules to delete.
        foreach my $dbmodule (@$type_module) {
            my $done = 0;
            foreach my $module_id ( keys %$value ) {
                if ($module_id eq $dbmodule->{module_id}) {
                    if ($value->{$module_id} != $dbmodule->{enabled}) {
                        $uravo->{db}->do("UPDATE type_module SET enabled=? WHERE type_id=? and module_id=?", undef, ($value->{$module_id}, $self->id(), $module_id)) || die($uravo->{db}->errstr);
                    }
                    $done = 1;
                    last;
                }
            }
            if (!$done) {
                $uravo->{db}->do("delete from type_module where type_id=? and module_id=?", undef, ($self->id(), $dbmodule->{module_id})) || die($uravo->{db}->errstr);
                $uravo->changelog({object_type=>$self->{object_type},object_id=>$self->id(),field_name=>'deleted module', old_value=>$dbmodule->{module_id}},$changelog);
            }
        }

        # Scan the databse for new modules to add.
        foreach my $module_id ( keys %$value ) {
            my $done = 0;
            foreach my $dbmodule (@$type_module) {
                if ($module_id eq $dbmodule->{module_id}) {
                    $done = 1;
                    if ($value->{$module_id} != $dbmodule->{enabled}) {
                        $uravo->{db}->do("UPDATE type_module SET enabled=? WHERE type_id=? and module_id=?", undef, ($value->{$module_id}, $self->id(), $module_id)) || die($uravo->{db}->errstr);
                    }
                    last;
                }
            }
            if (!$done) {
                $uravo->{db}->do("insert into type_module (type_id, module_id, enabled)  values (?, ?, ?)", undef, ($self->id(), $module_id, $value->{$module_id})) || die($uravo->{db}->errstr);
                $uravo->changelog({object_type=>$self->{object_type},object_id=>$self->id(),field_name=>'added module', new_value=>$module_id},$changelog);
            }
        }

        return $changelog;
    }

    if ($field eq 'logs') {
        my @ids;
        foreach my $log_id (keys %$value) {
            my $log = $value->{$log_id};
            my $detail = $log->{detail};
            next unless (ref($detail) eq 'ARRAY' && scalar(@$detail));
            if ($log_id && $log_id =~/^\d+$/) {
                $uravo->{db}->do("UPDATE type_log SET log_file=? WHERE id=?", undef, ($log->{log_file}, $log_id));
            } else {
                $uravo->{db}->do("INSERT INTO type_log (log_file, type_id, create_date) VALUES(?, ?, NOW())", undef, ($log->{log_file}, $self->id()));
                $log_id = $uravo->{db}->{mysql_insertid};
            }
            push(@ids, $log_id);

            my @dids;
            foreach my $d (@$detail) {
                if ($d->{id} && $d->{id} =~/^\d+$/) {
                    $uravo->{db}->do("UPDATE type_log_detail SET regex=? WHERE id=?", undef, ($d->{regex}, $d->{id}));
                } else {
                    $uravo->{db}->do("INSERT INTO type_log_detail (type_log_id, regex, create_date) VALUES(?, ?, NOW())", undef, ($log_id, $d->{regex}));
                    $d->{id} = $uravo->{db}->{mysql_insertid};
                }
                push(@dids, $d->{id});
            }
            $uravo->{db}->do("DELETE FROM type_log_detail WHERE type_log_id=? AND id NOT IN (" . join(",", @dids) . ")", undef, ($log_id));
        }
        $uravo->{db}->do("DELETE FROM type_log WHERE type_id=? AND id NOT IN (" . join(",", @ids) . ")", undef, ($self->id())) if (scalar(@ids));
        return $changelog;
    }

    my $old_value =  $self->{$field};
    if ($old_value ne $value) {
        $uravo->changelog({object_type=>$self->{object_type},object_id=>$self->id(),field_name=>$field, old_value=>$old_value,new_value=>$value},$changelog);
    }

    $uravo->{db}->do("UPDATE type SET $field=? WHERE type_id=?", undef, ( $value, $self->id() )) || die($uravo->{db}->errstr);
    $self->{$field} = $value;
    return $changelog;
}

sub getProcs {
    $uravo->log("Uravo::Serverroles::Type::getProcs()", 8);
    my $self        = shift || return;
    my $params	    = shift;
    my $proc_list;

    my $type_id = $self->id();
    my $results = $uravo->{db}->selectall_arrayref('SELECT p.name, tp.red FROM process p, type_process tp WHERE p.process_id = tp.process_id AND tp.type_id=?', {Slice=>{}}, ($type_id));
    foreach my $result (@$results) {
        $proc_list->{$result->{name}} = $result->{red};
    }

    return $proc_list;
}
        
sub link {
    my $self        = shift || return;
    my $links       = shift || 'default';
    my $ret;
    my $image_base  = '/images';

    $links          = " $links ";
    $links          =~s/\s+default\s+/ config graphs /;

    while ($links =~/\s?-(\w+)\s?/g) {
        $links          =~s/\s?-?$1\s?/ /g;
    }

    foreach my $link (split(/\s+/, $links)) {
        if ($link eq 'config') {
            $ret    .= "<a href='/cgi-bin/edittype.cgi?type_id=${\ $self->id(); }' title='Configure ${\ $self->name(); }'><img name='${\ $self->id(); }-$link' src=$image_base/config-button.gif width=15 height=15 border=0></a>\n";
        }
        if ($link eq 'graphs' ) {
            $ret    .= "<a href='/cgi-bin/graph.cgi?type_id=${\ $self->id(); }&server_id=all' title='View graphs for ${\ $self->name(); }'><img src=$image_base/graph-button.gif width=15 height=15 border=0></a>\n";
        }
    }
    return $ret || $self->link();
}

sub get {
    my ($self, $name) = @_;

    return $self->{$name};
}

sub changelog {
    my $self = shift || return;

    return $uravo->changelog({object_id=>$self->id(), object_type=>$self->type()});
}

sub getModules {
    my $self = shift || return;
    my $params = shift || {};

    my $tmp_params; 
    map { $tmp_params->{$_} = $params->{$_} } keys %{$params};
    $tmp_params->{type_id} = $self->id();

    return $uravo->getModules($tmp_params);
}

sub getLogs {
    my $self = shift || return;

    my $logFileData = $uravo->{db}->selectall_hashref("SELECT * FROM type_log WHERE type_id=?", "id", undef, ($self->id()));
    foreach my $id (keys %$logFileData) {
        $logFileData->{$id}->{detail} = $uravo->{db}->selectall_arrayref("SELECT * FROM type_log_detail WHERE type_log_id=?", {Slice=>{}}, ($id));
    }
    return $logFileData;
}

sub delete {
    my $params = shift || return;
    my $changelog = shift || {};

    my $type_id = $params->{type_id} || return;

    $uravo ||= new Uravo;

    $uravo->{db}->do("update server_type set type_id='unknown' where type_id=?", undef, ($type_id)) || die($uravo->{db}->errstr);
    $uravo->{db}->do("delete from type_process where type_id=?", undef, ($type_id)) || die($uravo->{db}->errstr);
    $uravo->{db}->do("delete from changelog, changelog_detail using changelog inner join changelog_detail where changelog.object_id=? and changelog.object_type='type' and changelog.id=changelog_detail.changelog_id", undef, ($type_id)) || die($uravo->{db}->errstr);
    $uravo->{db}->do("delete from changelog where object_id=? and object_type='type'", undef, ($type_id)) || die($uravo->{db}->errstr);
    $uravo->{db}->do("delete from type where type_id=?", undef, ($type_id)) || die($uravo->{db}->errstr);

    return;
}

sub data {
    my $self = shift || return;
    my $data = {};

    foreach my $field (split(/ /, $self->{type_fields})) {
        $data->{$field} = $self->{$field};
    }
    return $data;
}

# Misc info functions.
sub id		{ my ($self) = @_; return $self->{type_id}; }
sub name	{ my ($self) = @_; return $self->{name} || $self->id(); }
sub type    { my ($self) = @_; return $self->{object_type}; }

1;
