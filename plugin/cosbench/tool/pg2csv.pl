#!/usr/bin/perl

$iostatfile = "$ARGV[0]";
$CSVFILE = "$ARGV[1]";
print $iostatfile

# --------------------------------------------------------------------
# This reads through the entire IOSTAT log file, builds a list of unique
# device names (devicelist), a list of unique counter name (counterlist), 
# and builds a list of rawdata (rawdatalist)with device:::value.
# --------------------------------------------------------------------

open(IOSTATFILE, $iostatfile) || die "Unable to open $iostatfile!\n";

while(<IOSTATFILE>) {
	chomp;
	if ($_ =~ /ceph/) {
		@datalist = split(" ", $_);
		foreach $i (0..$#datalist) {
			push (@rawdatalist, $datalist[$i]);
		}
      }
}
close(IOSTATFILE);

# --------------------------------------------------------------------
# Now merge all data into a single csv file
# --------------------------------------------------------------------

open(CSVFILE, ">$CSVFILE") || die "Unable to open $CSVFILE!\n";

$linecount = 120;
$colcount = 2;
# the follow each line
for ($i = 0; $i < $linecount; $i++) {
	for($j = 0; $j < $colcount; $j++){
		print CSVFILE shift(@rawdatalist);
		print CSVFILE ",";
	}
	print CSVFILE "\n";
}

close(CSVFILE);
