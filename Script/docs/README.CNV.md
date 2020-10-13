Rules for DECoNoutput:


Screen for BF > 10 for all CNVs except DMD and SMN1
Screen for BF > 5 for all DMD and SMN1

CNV-Problem BF < 15 for all CNVs

if Reads.ratio <= 0.08: hom
if Reads.ratio > 0.29 and Reads.ratio < 0.71: het
if Reads.ratio >= 0.71 and Reads.ratio < 1.3: het CNV-Problem
if Reads.ratio >= 1.3 and Reads.ratio < 1.71: het


Big Del Boundaries Different as Reported for dels not SMN/DMD/CFTR: if exon first and exon last reported by DECoN are not in range of +- 1 exons as defined in annotation sheet targets.xlsx
