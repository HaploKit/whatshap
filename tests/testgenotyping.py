from nose.tools import raises
from whatshap.core import ReadSet, PedigreeDPTable, Pedigree, NumericSampleIds, PhredGenotypeLikelihoods, GenotypeDPTable
from .phasingutils import string_to_readset, brute_force_phase
from .phasingutils import string_to_readset, string_to_readset_pedigree, brute_force_phase


def test_genotyping_empty_readset():
	rs = ReadSet()
	recombcost = [1,1]
	genotypes = [1,1]
	numeric_sample_ids = NumericSampleIds()
	pedigree = Pedigree(numeric_sample_ids)
	genotype_likelihoods = [None, None]
	pedigree.add_individual('individual0', genotypes, genotype_likelihoods)
	dp_forward_backward = GenotypeDPTable(numeric_sample_ids,rs, recombcost, pedigree)

def check_genotyping_single_individual(reads, weights = None, expected = None, genotypes = None, scaling=None):
	# 0) set up read set
	readset = string_to_readset(reads, weights, scale_quality=scaling)
	positions = readset.get_positions()

	# 1) Phase using PedMEC code for single individual
	recombcost = [1] * len(positions) # recombination costs 1, should not occur
	numeric_sample_ids = NumericSampleIds()
	pedigree = Pedigree(numeric_sample_ids)
	genotype_likelihoods = [PhredGenotypeLikelihoods(0,0,0)] * len(positions)
	pedigree.add_individual('individual0', [1] * len(positions), genotype_likelihoods) # all genotypes heterozygous
	dp_forward_backward = GenotypeDPTable(numeric_sample_ids, readset, recombcost,pedigree)
	## also get the phasing result
	dp_table = PedigreeDPTable(readset, recombcost, pedigree, distrust_genotypes=True)
	superreads, transmission_vector = dp_table.get_super_reads()
	
	assert(len(superreads)==1)
	haplotypes = tuple(sorted(''.join(str(v.allele) for v in sr) for sr in superreads[0]))
	haplo_geno = [0] * len(positions)

	for sr in superreads[0]:
		geno = 0
		i = 0
		for pos in sr:
			haplo_geno[i] += pos.allele			
			i += 1
	
	print('haplotypes: ', haplotypes, ' corresponding genotypes: ',haplo_geno)
	
	# get the genotype likelihoods as computed by forward-backward alg.
	if not expected==None:
		for i in range(len(positions)):
			likelihoods = dp_forward_backward.get_genotype_likelihoods('individual0',i)
			print(likelihoods,i)
			assert(likelihoods == expected[i])
	
	# check if likeliest genotypes are the same and are equal to the haplotypes
	for i in range(len(positions)):
		likelihoods = dp_forward_backward.get_genotype_likelihoods('individual0',i)
		# find likeliest genotype 
		max_val = -1
		max_index = -1
		for j in range(3):
			if likelihoods[j] > max_val:
				max_val = likelihoods[j]
				max_index = j
				
		print('genotype likelihoods: ', likelihoods, ' likeliest genotype: ',max_index)
			
		# compare likeliest genotype to haplotype
		if haplo_geno[i] < 3:
			assert(max_index==haplo_geno[i])
		elif haplo_geno[i] == 3:
			assert(max_index<2)
		elif haplo_geno[i] == 4:
			assert(max_index>0)

		if not genotypes==None:
			assert(max_index==genotypes[i])
			
	# 2) Phase using PedMEC code for trios with two "empty" individuals (i.e. having no reads)
	recombcost = [1] * len(positions) # recombination costs 1, should not occur
	numeric_sample_ids = NumericSampleIds()
	pedigree = Pedigree(numeric_sample_ids)
	genotype_likelihoods = [PhredGenotypeLikelihoods(0,0,0)] * len(positions)
	pedigree.add_individual('individual0', [1] * len(positions), genotype_likelihoods) # all genotypes heterozygous
	pedigree.add_individual('individual1', [1] * len(positions), genotype_likelihoods) # all genotypes heterozygous
	pedigree.add_individual('individual2', [1] * len(positions), genotype_likelihoods) # all genotypes heterozygous
	pedigree.add_relationship('individual0', 'individual1', 'individual2')
	dp_forward_backward = GenotypeDPTable(numeric_sample_ids,readset,recombcost,pedigree)
	
	## TODO check the results!!!
		
			
def test_geno_exact1() :
	reads = """
          11
           01
        """
	# as computed manually, with weight 10 for each position
	expected_likelihoods = [[0.05, 0.5, 0.45],[0.1323529411764706, 0.7352941176470589, 0.1323529411764706],[0.05, 0.5, 0.45]]
	check_genotyping_single_individual(reads,None,expected_likelihoods,None,10)

def test_geno_exact2():
	reads = """
		11
		11
		"""
	weights = """
		11
		22
		"""
	expected_likelihoods = [[0.0006656057777641766, 0.4062796462343544, 0.5930547479878814],[0.0006656057777641766, 0.4062796462343544, 0.5930547479878814]]
	check_genotyping_single_individual(reads,weights,expected_likelihoods,None,10)

def test_geno_exact3():
	reads = """
          01
          11
        """
	# as computed manually, with weight 10 for each position
	expected_likelihoods = [[0.1493963782696177, 0.7012072434607646, 0.1493963782696177],[0.008551307847082495, 0.2987927565392354, 0.6926559356136821]]
	check_genotyping_single_individual(reads,None,expected_likelihoods,None,10)
   
def test_geno1():
	reads= """
	1111111111
	0000011111
	"""

	genotypes = [1,1,1,1,1,2,2,2,2,2]
	check_genotyping_single_individual(reads,None,None,genotypes,10)   
   
def test_geno2():
	reads = """
	101
	101
	101
	101
	100
	100
	100
	100
	"""
	
	genotypes = [2,0,1]
	check_genotyping_single_individual(reads,None,None,genotypes,10)

def test_geno3():
	reads = """
	011011
	110110
	110 10
	110110
	111110
	000 00
	01000 
	000010
	100100
	"""
	
	genotypes = [1,1,0,1,1,0]
	check_genotyping_single_individual(reads,None,None,genotypes,10)

##

def test_geno4():
	reads = """
	  1  11010
	  00 00101
	  001 01110
	   1    111
	"""
	check_genotyping_single_individual(reads,None,None,None,10)


def test_geno5():
	reads = """
	  0             0
	  110111111111
	  00100
	       0001000000
	       000
	        10100
	              101
	"""
	check_genotyping_single_individual(reads,None,None,None,10)

def test_geno6():
	reads = """
		0100000000000
		0100010000000
		1110000000010
		0100000000000
		0101000001000
		0100010   000
		0 10000000100
		1111111011100
		0100111010011
		1111111000111
		1111110011111
		11110000  000
		1110011011111
		1111001011111
		0111111110  1
		"""
	genotypes = [1,2,1,1,1,1,1,0,1,1,1,1,1]
	check_genotyping_single_individual(reads,None,None,genotypes,60)

# TODO: currently the result is 0.25,0.5,0.25. Should this be 1/3,1/3,1/3 ??
def test_geno7():
	reads = """
		111
		101
		111
		101
		010
		000
		010
		000
		"""
	genotypes = [1,1,1]
	check_genotyping_single_individual(reads,None,None,genotypes,60)

def test_weighted_phasing1():
	reads = """
	  1  11010
	  00 00101
	  001 01110
	   1    111
	"""
	weights = """
	  2  13112
	  11 23359
	  223 56789
	   2    111
	"""
	check_genotyping_single_individual(reads, weights,None,None,10)

