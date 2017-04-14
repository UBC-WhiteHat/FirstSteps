package NVD;

#  Extract vulnerability records from the XML files provided by NIST in their
#  public data feed at: https://nvd.nist.gov/download.cfm
#
#  This module supports only the NVD XML version 1.2.1 schema. The version 2.0
#  schema is not supported.

use strict;
use warnings;

use XML::LibXML;

use DBI;





sub extract {
    my $fname = shift
        or warn("please provide the XML file to load\n"),
        return;

    my $xml;
    eval {
        $xml = XML::LibXML->load_xml(location => $fname);
    };

    if($@) {
        return ();
    }

    my( $nvd ) = $xml->nonBlankChildNodes;

    my @vuln;
    my %vuln;
    for my $entry ($nvd->nonBlankChildNodes) {
        my %value;
        %value = parse_nvd_entry($entry);

        for my $attr ($entry->attributes) {
            $value{$attr->nodeName} = $attr->nodeValue;
        }

        # rename 'name' to 'cve_id'
        my $cve_id = $value{cve_id} = delete $value{name};

        $vuln{$cve_id} = \%value;
    }

    return %vuln;
}

sub save2db {
    my $refvuln = shift
        or warn("You have to provide outputs from extract().\n"),
        return;
    my $table_identifier = shift
        or warn("Please provide a table identifier.\n"),
        return;
    my $dsn = shift
        or warn("Please provide a database.\n"),
        return;
    my $username = shift
        or warn("Please provide a username for database.\n"),
        return;
    my $password = shift;


    # Connect to MySQL database
    my %attr = (PrintError=>0, RaiseError=>1);
    my $dbh = DBI->connect($dsn,$username,$password,\%attr);
    print "Connected to database successfully.\n";

    my $table_name = "cve_$table_identifier";
    my $table2_name = "02cve_$table_identifier";

    # Create a new table
    my @ddl = (
       "CREATE TABLE $table_name(
           published DATE,
           modified DATE,
           severity VARCHAR(15),
           cve_id VARCHAR(20) NOT NULL PRIMARY KEY);"
    );

    for my $sql(@ddl) {
        $dbh->do($sql);
    }

    my @ddl_1 = (
       "CREATE TABLE $table2_name(
           name   VARCHAR(30),
           id int NOT NULL AUTO_INCREMENT,
           vendor VARCHAR(20),
           cve_id VARCHAR(20) NOT NULL,
           PRIMARY KEY (id,cve_id));"
    );

    for my $sql(@ddl_1) {
        $dbh->do($sql);
    }


    print "Created tables successfully.\n";

    # Insert data into the tables
    my $sql = "INSERT INTO $table_name(cve_id,published,modified,severity)
        VALUES(?,?,?,?)";
    my $stmt = $dbh->prepare($sql);

    while (my ($cve_id, $value) = each (%{$refvuln}))
    {
        #print($value->{severity}, $value->{modified}, $value->{published});
        $stmt->execute($cve_id, $value->{published}, $value->{modified}, $value->{severity});
    }
    $stmt->finish();

    my $sql2 = "INSERT INTO $table2_name(cve_id,name,vendor)
        VALUES(?,?,?)";
    my $stmt2 = $dbh->prepare($sql2);

    while (my ($cve_id, $value) = each (%{$refvuln}))
    {

        foreach my $vulndetail ($$value{vuln_soft}{prod}) {
            if (ref($vulndetail) eq 'ARRAY') {
                next;
            } else {
                #print($value->{name}, $value->{vendor});
                $stmt2->execute($cve_id, $vulndetail->{name}, $vulndetail->{vendor});
            }
        }
    }
    $stmt2->finish();

    # Disconnect from the MySQL database
    $dbh->disconnect();

}
sub parse_nvd_entry {
    my $entry = shift;

    my %entry;
    for my $node ($entry->nonBlankChildNodes) {
        my $name = $node->nodeName;
        my $value = $node->textContent;
        $value =~ s/^\s+|\s+$//g;

        if ($node->nodeName eq '#text') {
            # The node content is held in an element called: '#text'. This is
            # returned by the call to the method: textContent. As we recurse
            # through the document, we rename it to "body".

            $name = "body";
        }

        if ($node->hasChildNodes) {
            my %value = parse_nvd_entry($node);
            $value = \%value;
        }

        if (defined $entry{$name}) {
            # This node name is reused within the same parent node
            my $existing_entry = $entry{$name};

            $value = {$name, $value};
            if (ref $existing_entry eq "ARRAY") {
                push @$existing_entry, $value;
            } else {
                $entry{$name} = [$existing_entry, $value];
            }

        } else {
            $entry{$name} = $value;
        }

        if ($node->hasAttributes) {
            my %attr ;
            for my $attr ($node->attributes) {
                $attr{$attr->nodeName} = $attr->nodeValue;
            }

            if (ref $value eq "HASH") {
                @$value{keys %attr} = values %attr;
            } else {
                $entry{$name} = {$name => $value, %attr};
            }
        }
    }

    return %entry;
}


1;
