#! /usr/bin/perl -w
#
#  Extract vulnerability records detailed in NIST NVD XML files. Save the
#  records into a database.

use strict;
use warnings;

use FindBin;
use lib qq($FindBin::Bin/../lib);

use NVD;
use Dumpvalue;


# The return value used at the end of the program.
my $ret = 0;

if (@ARGV < 1) {
    die "Extract NVD vulnerability records into a MySQL database file\n",
        "Usage:\n    $0 <NVD_XML_files>\n\n";
}


# MySQL database configuration
my $dsn = "DBI:mysql:perldb";
my $username = "root";
my $password = '';

foreach my $a (@ARGV) {
    if(-e $a) {
        if(-s _ == 0) {
                $ret += 1;
		print "Warning: file '$a' empty. Skipping.\n";
		next;
	}
    } else {
            $ret += 1;
	    print "Warning: File '$a' not found.\n";
	    next;
    }

    my %vuln = NVD::extract($a);
    my $match = $a;
    $match =~ m{(\d+)};
    my $id = $1;
    NVD::save2db(\%vuln, $id, $dsn, $username, $password);

    # The modified NVD module returns an empty hash on error.
    my $size = keys %vuln;
    if($size == 0) {
        $ret += 1;
        print "Error parsing file: '$a'. Skipping.\n";
        next;
    } else {
        my @sections = split('/', $a);
        my $sections_len = @sections;
        my $file_name = $sections[$sections_len - 1];
        my $new_file = "log/$file_name.log";

        open(my $fd, ">", "$new_file");

	if(not defined $fd) {
            $ret += 1;
            print "Error: Unable to open file 'log/$a.log'\n";
	    next;
	}

	select $fd;
        Dumpvalue->new->dumpValue(\%vuln);
	select STDOUT;

        close $fd;

        print "Wrote results to $new_file\n";
    }
}

exit $ret
