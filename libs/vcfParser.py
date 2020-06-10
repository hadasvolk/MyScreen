'''pseudocode
1.  load in genome vcf as pandas. "filter out alt with ."
2.  load in candidate as csv file
3.  loop through candidate vcf chr/pos, get the record from pandas
4.  If no <M>, then just print out the record with "ForcedReport"
5.  If block with <M>, then gather all the alt, keep record where the row doesn't have <M>
170816 adding alt to sampleAlt[key]
'''
import pandas as pd
import csv
import re
import getopt
import sys
import math

'''
opts, args = getopt.getopt( sys.argv[1:],"hi:o:v:",["infile=", "ofile=", "vcffile"] )
for opt, arg in opts:
    if opt == '-h':
        print (" parser.py -i <input ivcf> -o <output vcf> -v <vcf_candidate>")
    if opt == '-i':
        inputfile=arg
    if opt == '-o':
        outputfile=arg
    if opt == '-v':
        vcffile=arg
'''

def main(inputfile, outputfile, vcffile):
    pd.set_option('display.max_colwidth', -1)

    def replaceLastElem(fullList,newEntry):
        # replace last element with "newEntry"
        itms=fullList.split(":")
        itms[-1]=newEntry
        newList=":".join(itms)
        return newList
    file=open(inputfile,'r')
    def printDF(d):
        x=d.to_string(header=False,index=False).split('\n')
        vals=[",".join(ele.split()) for ele in x]
        print (",".join(vals)+"\n")
    #outputfile="ex.170717.vcf"
    outfile=open(outputfile,'w')
    row2Skip=0
    ## here we are going through the gvcf file and extracting the header with "#"
    ## We also count how many rows to skip
    for line in file:
        if re.match("#.*", line):
            outfile.write(line)
            row2Skip += 1
    ## subtracting 1 because we need to include header for pandas dataframe
    row2Skip -= 1
    #print "row is "+ str(row2Skip) #debug
    vcf=pd.read_csv(inputfile,sep="\t",skiprows=row2Skip)
    row2SkipPisces=row2Skip+2 #Scylla output has 2 additional lines
    phasedInputFile=re.sub("genome","phased.genome",inputfile)
    phasedVcf=pd.read_csv(phasedInputFile,sep="\t",skiprows=row2SkipPisces, dtype={'ALT':str} )
    ## 170809 needed to import everything as str if not, some empty entry (a pisces bug) will be float!
    # https://stackoverflow.com/questions/13293810/import-pandas-dataframe-column-as-string-not-int

    ## adding MNP code here 10/5 to red in from a file MNP.txt
    '''with open("mnp.txt", 'r') as f:
        for line in f:
            items = line.split()
            key, values = items[0], items[1:]
            mnp[key] = values
    '''
    for mnp, mnp2, alt,anchor in zip((71887766,91310151,117232191,183184686,122277741,81534622,241816967,51065766,108196135,108143539,158564126,136221514,55648503,117232194,108196134,117304854,241816967,122277742,81534624,51065765),(71887766,91310151,117232197,183184686,122277742,81534624,241816967,51065766,108196135,108143539,158564126,136221514,55648503,117232194,108196135,117304855,241816967,122277743,81534625,51065767), ("ACCCC","ATTAGATTC","GA","CACCAC","AGA","GCCT","CG","AG","TCTC","CTGAT","CTATACT","TCAT","CAACAGCACTA","G","ATCTC","CAA","CG","GA","CT","AG"),("A","AT","GA","CA","AGA","C","CG","AG","T","CTG","CTATA","T","CA","G","T","C","C","A","G","G")):

        ## MNP = Multi Nucleotide Polymorphism
        ## this section is a duct tape.  We are reading in phased genotype for these two position.
        #print "working on "+str(mnp) # debug

        # grab info from vcf with anchor var and position
        #print "mnp is "+str(mnp)  #debug
        gvcf_db_mnp=vcf[ (vcf['POS'].between(mnp,mnp2,inclusive=True)) & (vcf['ALT']==anchor) ]
        #printDF(gvcf_db_mnp) #debug
        if not gvcf_db_mnp.empty:
            new_info=gvcf_db_mnp.iloc[0][9]
        # filter the dataframe from the phased gvcf for just the MNP of interest
        if mnp==117232191:
            gvcf_db_mnp2=vcf[ vcf['POS']==mnp2 ]
            if not gvcf_db_mnp2.empty and not gvcf_db_mnp.empty:
                sampleName=gvcf_db_mnp2.columns.values[9]
                if re.match("0/1",gvcf_db_mnp.iloc[0][9] ):
                    if re.match("0/1",gvcf_db_mnp2.iloc[0][9] ) :
                        mnp_index= vcf.index[ vcf['POS']==mnp ].tolist()
                        for i in mnp_index:
                            vcf.set_value(i,'REF','GAAGAAATTCAATCCT')
                            vcf.set_value(i,'ALT','GAAAGAAA')
                            vcf.set_value(i,sampleName,new_info)
                        #print "In MNP"
                        #printDF(vcf[vcf['POS']==mnp])
        phasedVar=phasedVcf[ (phasedVcf['POS'].between(mnp,mnp2,inclusive=True))&(phasedVcf['ALT']==alt) ]
        #printDF(phasedVar) #debug
        sampleName=phasedVar.columns.values[9]
        for index, df in phasedVar.iterrows():
            info=df.iloc[9]
            #print info # this section replace incorrect 1/. call by Pisces to be
            if re.match("1/.",info):
                #new_info=re.sub("1/.","1/0",info)
                phasedVar.set_value(index,sampleName,new_info)
                #printDF(phasedVar)

            #print new_info
        # filter the gvcf for everything but the MNP
        # Do not filter or else we will not find the var
        # vcf=vcf[vcf['POS']!=mnp]
        # combine phased MNP + gvcf
        vcf=pd.concat([vcf,phasedVar])
        #printDF(phasedVar)   #debug

    ## because of jira ticket https://jira.illumina.com/browse/PICS-840 we need to add in 4 MNV call fourMNV if they do not exist
    #chr12 122277742 122277742 AC GA
    #chr14 81534624 81534624 AG CT
    #chr2 241816967 241816967 GC CG
    #chr22 51065766 51065766 GA AG
    #chr16 66565297 66565298 GC TT - added 190401
    for pos, ref, alt in zip((122277742,81534624,241816967,51065766,66565297),("AC","AG","GC","GA","GC"),("GA","CT","CG","AG","TT")):
        vcfMNV=vcf[(vcf['POS']==pos) &(vcf['REF']==ref) & (vcf['ALT']==".") ]
        if vcfMNV.empty: # if vcf file doen't contain the 4 mnv, we will copy the information from first base and alter ref/alt and inject it to our vcf file
            vcfMNV2=vcf[(vcf['POS']==pos)]
            for i,df in vcfMNV2.iterrows():
                vcfMNV2.set_value(i,'REF',ref)
                vcfMNV2.set_value(i,'ALT',alt)
            vcf=pd.concat([vcf,vcfMNV2])
    ## end of addition for JIRA PICS-840

    ## Need to initialize some dictionary
    sampleRecord={}
    sampleAlt={}
    qual={}
    strandBias={}

    ## Keep track of two indels AG1998 and AG3268 - DATE 190401
    AG1998_part1 = ''
    AG1998_part1_df = pd.DataFrame()
    AG1998_part2 = ''
    AG3268_part1 = ''
    AG3268_part1_df = pd.DataFrame()
    AG3268_part2 = ''

    # read in and start to loop in candidate vcf file and search for these candidates in our gvcf file
    with open (vcffile,'r') as csv_file:
        csv_reader=csv.reader(csv_file,delimiter="\t")
        for row in csv_reader:
            # ignore header matching "#"
            if re.match('^#.*',row[0]) or row[4]=="." :
                continue
            chr=row[0]
            pos=row[1]
            ref=row[3]
            #if pos == '71891547':
            #    quit()
            key=chr+"."+pos+"."+ref # create a key for dictionary
            altCand=row[4]
            sampleAlt[key]=altCand # here we add the alternative we are looking for to our final output
            sampleAltList=[]
            sampleAltList=altCand.split(",")
            #print "line 146 working on altCand "+altCand # debug
            #print "pos is" + pos # debug
            #sampleAlt[key]=""
            ## by default keep qual of pos and strandBias to be 0
            qual[key]=0
            strandBias[key]="0.0000"
            # here we find the chr and pos of gvcf.  Note, we may have more than one record per chr and pos
            # which we will loop through next
            eachRecord=vcf[(vcf['#CHROM']==chr )&( vcf['POS']==int(pos))&( vcf['REF']==ref ) ]
            if ((eachRecord['POS']) == 88713540).any():  # special case for AGID 1476
                eachRecord = eachRecord[eachRecord["ALT"].apply(lambda x: x) == altCand]

            #printDF(eachRecord)

            # Now we loop through the gvcf of the specific chr and pos
            for i,(index,df) in enumerate(eachRecord.iterrows()):
                qual[key]=df.iloc[5] #capture the quality regardless if it pass  otherwise, single record would have 0
                #printDF(df)
                # sample is the last column of the gvcf containing the sample information.
                sample=df.iloc[9]
                alt=df.iloc[4]
                #print "line 164 sampleAlt "+sampleAlt[key]
                #print "line 164 alt is "+alt+ " index is "+str(i) +" sample is "+sample# debug
                #print "sampleAltList is "+ ",".join(sampleAltList)
                #print df[0]
                #if ( re.match(',*<M>,*',"",alt) ):
                    #continue
                alt=re.sub(',*<M>,*',"",alt)  # replace all <M> which is vcf way of saying "something else" in alt
                info=df.iloc[6] # info is column 7
                #print "line 168 info is "+ info + " alt is "+ alt + " alt candidate "+ altCand
                #print "line 168 sample is "+sample
                ## this section replaces Quality and SB with right record from "." in alt
                if ( altCand == alt ) :#and ( ( re.match("|".join(["q20","LowVariantFreq","LowDP","SB","MultiAllelicSite","R5x9"]),info) ) or ( info == "ForcedReport" ) ):
                    #print "line 160 found filtered alt "+alt
                    #print "found alt "+ alt
                    if not key in sampleRecord.keys():
                        sampleRecord[key]=sample
                if re.match("PASS",info):
                    #print "line 165 "+ key+" match "+alt
                    qual[key]=df.iloc[5] # capture quality
                    samples=sample.split(":")
                    strandBias[key]=samples[-1] # capture strandbias
                    #print "populated strandbias "+strandBias[key]
                ## if it is het or hom/alt then keep the alt as the first record i.e. alt,"misc"
                ## I know there are better regex I can use, but I want it to be explicit
                if ( re.match("0/1",sample) ) or ( re.match("1/0",sample) ) or ( re.match("1/1",sample) ):
                ## here we are calling alt and to avoid adding 2 alt with identical entry, delete old entry
                    #print "line 185 sub "+ sampleAlt[key] +" alt is "+ alt  # debug
                    if (alt in sampleAltList) :
                        sampleAltList.remove(alt)
                    #if not altCand.startswith(alt):
                    #    sample=re.sub("/1","/2",sample)
                    sampleRecord[key]=sample
                    #print "adding info "+sample #debug
                    sampleAltList.insert(0,alt)
                    #print "line 196 added alt "+sampleAlt[key]
                ## if it is not het or hom alt then record alt as second alt i.e. "misc",alt

                elif re.match("2/2",sample):
                    if i+1==len(eachRecord) and not key in sampleRecord:
                    # we will capture 2/2 record if this is the last record and we have not yet captured any sampleRecord
                        sampleRecord[key]=sample
                    #print "line 200 in 2/2 loop "+",".join(sampleAltList)+ " sampleRecord[key] is "+sampleRecord[key]
                    if (not alt in sampleAltList ):## however, if we already has alt ignore it.
                        sampleAltList.append(alt)

                else: ## capture 0/0  Here the addAlt need to add alternative to as a secondary variant
                    if not altCand.startswith(alt):
                        sample=re.sub("/1","/2",sample)
                    #print "key is " +  key # debug
                    #print "line 197 sub sampleAlt is "+ sampleAlt[key] + " alt "+alt + " altCand "+altCand # debug
                    # if a sampleRecord doesn't exist, capture it.
                    if not key in sampleRecord:
                        sampleRecord[key]=sample
                    # if we see ForcedReport, we will use the sampleinfo
                    if re.match(".*ForcedReport",info) or re.match("\.\/\.",sampleRecord[key]):
                        sampleRecord[key]=sample

                    if (not re.match("\.",alt) )  and (not alt in sampleAltList ): ## here if alt is not "." we add alt
                        #print "line 156 adding "+ alt +" to "+ sampleAlt[key]
                        sampleAltList.extend(alt)
                    #print "line 204 sampleRecord[key] is "+sampleRecord[key]
                #print "line 167 sampleAlt is "+sampleAlt[key] # debug
                ## if we are at the last record, print out the chr/pos of interest below
                if i+1 == len(eachRecord):  # reached last record
                    #print "key is " +  key  # debug
                    if re.match("\./\.",sampleRecord[key]) or re.match("0/\.",sampleRecord[key]):
                        ## this fixes ./. to be NNNN for Variant Studio
                    #    sampleAlt[key]=addAlt(sampleAlt[key],"NNN",1)
                        sampleAltList.insert(0,"NNN")
                        sampleRecord[key]=re.sub("0/\.","0/1",sampleRecord[key])
                        sampleRecord[key]=re.sub("\./\.","1/1",sampleRecord[key])
                    if re.match("2/2",sampleRecord[key]):
                        #print sampleRecord[key]
                        #print key
                        sampleRecord[key]=re.sub("2/2","0/0",sampleRecord[key])
                        ### need to investigate why 117232266 and 21118573 and 5248233 have 2/2
                    if re.match("1/\.",sampleRecord[key]) :
                        ## this fixes 1/. to be NNNN for Variant Studio
                        #print "line 170 in 1/. loop " + sampleRecord[key]

                        sampleAltList.insert(0,"NNN")
                        sampleRecord[key]=re.sub("1/\.","2/1",sampleRecord[key])

                    #print sampleAlt[key] + " "+key
                    #print type(sampleAlt[key]) # debug
                    #if not sampleAlt[key] and re.match("0/0",sampleRecord[key]):   ## NEED to debug Pisces then get rid of this
                    #    sampleAlt[key]=altCand  # this is for weird case of 71887766 where we have "" as alt is detecting
                    #printDF(df) #debug
                    df.iloc[4]=",".join(sampleAltList)
                    df.iloc[8]=re.sub("GQ","GQX",df.iloc[8]) ## replace GQ with GQX
                    #sampleRecord[key]=replaceLastElem(sampleRecord[key],strandBias[key])  # we will not replace last elem
                    '''
                    if df.iloc[1] == 88713540:
                        if anchor==df.iloc[4].split(',')[0]:
                            df.iloc[9]=sampleRecord[key]
                    else:
                    '''
                    df.iloc[9] = sampleRecord[key]

                    if key in qual:
                        df.iloc[5]=qual[key]

                    ## Keep track of indel AG1998 - DATE 190401
                    if df.iloc[1] == 20763658: # We are in chr13_20763658_TCCAATGCTGG_T
                        AG1998_part1_alt = df.iloc[4] # Keep track for NNN (no calls).
                        AG1998_part1 = df.iloc[9] # Keep track of genotype.
                        AG1998_part1_df = df # Save df.
                        continue # Next loop will be chr13_20763669_TG_T
                    if df.iloc[1] == 20763669: # We are in chr13_20763669_TG_T
                        AG1998_part2_alt = df.iloc[4] # Get alt variants (for NNN if exists).
                        AG1998_part2 = df.iloc[9]
                        AG1998_part1_GT = AG1998_part1.split(":")[0] # Get genotype.
                        AG1998_part2_GT = AG1998_part2.split(":")[0] # Get genotype.
                        if AG1998_part1_GT == AG1998_part2_GT: # Both parts of the mutation have equal genotypes, we combine into one.
                            df.iloc[1] = "20763658" # Position.
                            df.iloc[3] = "TCCAATGCTGGTG" # Ref.
                            if ("NNN" in AG1998_part1_alt) or ("NNN" in AG1998_part2_alt): # Check if mutation is no call.
                                df.iloc[4] = "NNN,TT" # Alt (no call).
                            else:
                                df.iloc[4] = "TT" # Alt.
                            AG1998_part1_VF = AG1998_part1.split(":")[4] # Get variant frequency.
                            AG1998_part2_VF = AG1998_part2.split(":")[4] # Get variant frequency.
                            if AG1998_part1_VF > AG1998_part2_VF: # Take stats with higher variant frequency.
                                df.iloc[9] = AG1998_part1
                        else: # Mutation parts have different genotypes, keep them seperate for vcf.
                            x=AG1998_part1_df.to_string(header=False,index=False).split('\n')
                            vals=[",".join(ele.split()) for ele in x]
                            outfile.write("\t".join(vals)+"\n") # Write AG1998_part1 first.


                    ## Keep track of indel AG3268 - DATE 190401
                    if df.iloc[1] == 51890841: # We are in chr6_51890841_TG_T
                        AG3268_part1_alt = df.iloc[4] # Keep track for NNN (no calls).
                        AG3268_part1 = df.iloc[9] # Keep track of genotype.
                        AG3268_part1_df = df # Save df.
                        continue # Next loop will be chr6_51890847_G_C
                    if df.iloc[1] == 51890847: # We are in chr6_51890847_G_C
                        AG3268_part2_alt = df.iloc[4] # Get alt variants (for NNN if exists).
                        AG3268_part2 = df.iloc[9]
                        AG3268_part1_GT = AG3268_part1.split(":")[0] # Get genotype.
                        AG3268_part2_GT = AG3268_part2.split(":")[0] # Get genotype.
                        if AG3268_part1_GT == AG3268_part2_GT: # Both parts of the mutation have equal genotypes, we combine into one.
                            df.iloc[1] = "51890845" # Position.
                            df.iloc[3] = "GGG" # Ref.
                            if ("NNN" in AG3268_part1_alt) or ("NNN" in AG3268_part2_alt): # Check if mutation is no call.
                                df.iloc[4] = "NNN,GC" # Alt (no call).
                            else:
                                df.iloc[4] = "GC" # Alt.
                            AG3268_part1_VF = AG3268_part1.split(":")[4] # Get variant frequency.
                            AG3268_part2_VF = AG3268_part2.split(":")[4] # Get variant frequency.
                            if AG3268_part1_VF > AG3268_part2_VF: # Take stats with higher variant frequency.
                                df.iloc[9] = AG3268_part1
                        else: # Mutation parts have different genotypes, keep them seperate for vcf.
                            x=AG3268_part1_df.to_string(header=False,index=False).split('\n')
                            vals=[",".join(ele.split()) for ele in x]
                            outfile.write("\t".join(vals)+"\n") # Write AG3268_part1 first.


                    x=df.to_string(header=False,index=False).split('\n')
                    vals=[",".join(ele.split()) for ele in x]
                    outfile.write("\t".join(vals)+"\n")
                    #print "\t".join(vals)+"\n"

if __name__ == '__main__':
    inputfile = sys.argv[1]
    outputfile = sys.argv[2]
    vcffile = sys.argv[3]
    main(inputfile, outputfile, vcffile)
