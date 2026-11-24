"""E09h.4: verify a conditional map, not the original EXE's pointers."""
import json
from pathlib import Path
import unittest

from experiments.neurolab.e09_historical_receptor import Receptor
from experiments.neurolab.e09_historical_locus import (
    route_brain_chem_loci, initialize_brain_chem_loci,
)
from experiments.neurolab.c1_svrule_runtime import C1SVTable, evaluate


def pool(**values):
    result = [0]*256
    for chemical, value in values.items():
        result[int(chemical[1:])] = value
    return tuple(result)


def fixtures():
    repo = Path(__file__).resolve().parents[3]
    filepath = repo/"docs"/"neurolab"/"resultados"/"e09h3_receptores_genoma_original.json"
    with filepath.open(encoding="utf-8") as f:
        known = json.load(f)
    genes = tuple(Receptor(int(idx), **fields)
                  for idx, fields in known["brain_receptors"].items())
    concentrations = tuple(known["example_pool"].items())
    chemical_pool = pool(**{"c"+key: value for key,value in concentrations})
    return known, genes, chemical_pool


class BrainChemicalLocusTests(unittest.TestCase):
    def test_original_six_genes_and_svtable(self):
        known, genes, chemical_pool = fixtures()
        self.assertEqual(known["receptor_count"], 43)
        self.assertEqual(len(genes), 6)
        self.assertEqual({g.gene_index for g in genes},
                         {88,89,126,127,128,129})
        decision = route_brain_chem_loci(genes, chemical_pool, 6, (0,0,0,0))
        concept = route_brain_chem_loci(genes, chemical_pool, 8, (0,0,0,0))
        self.assertEqual(decision, (11,11,5,16))
        self.assertEqual(concept, (0,0,0,0))
        self.assertEqual({str(g.gene_index): decision[g.locus-13] if g.lobe == 6
                          else concept[g.locus-13] for g in genes},
                         known["locus_values"])
        state = C1SVTable(chem0=decision[0],chem1=decision[1],
                          chem2=decision[2],chem3=decision[3],
                          susceptibility=4,stw=30)
        self.assertEqual(evaluate(bytes((5,0,0,0,0,0,0,0)),state),11)
        self.assertEqual(evaluate(bytes((6,0,0,0,0,0,0,0)),state),11)
        self.assertEqual(evaluate(bytes((7,0,0,0,0,0,0,0)),state),5)
        self.assertEqual(evaluate(bytes((8,0,0,0,0,0,0,0)),state),16)
        self.assertEqual(evaluate(bytes((18,22,5,22,19,0,0,0)),state),30)

    def test_original_receptor_loading_uses_nominals(self):
        _, genes, chemical_pool = fixtures()
        decision_before = initialize_brain_chem_loci(genes, 6)
        concept_before = initialize_brain_chem_loci(genes, 8)
        self.assertEqual(decision_before, (0,0,16,16))
        self.assertEqual(concept_before, (0,4,0,0))
        self.assertEqual(route_brain_chem_loci(
            genes, chemical_pool, 6, decision_before,
        ), (11,11,5,16))
        self.assertEqual(route_brain_chem_loci(
            genes, chemical_pool, 8, concept_before,
        ), (0,0,0,0))

    def test_nominal_loader_rejects_duplicate_in_lab(self):
        r1=Receptor(1,0,6,13,49,0,10,255,0)
        r2=Receptor(2,0,6,13,50,0,20,255,0)
        with self.assertRaisesRegex(ValueError, "duplicate nominal"):
            initialize_brain_chem_loci((r1,r2),6)
        with self.assertRaises(ValueError):
            initialize_brain_chem_loci((r1,),6,(256,0,0,0))

    def test_concept_and_decision_channels_independent(self):
        _, genes, _ = fixtures()
        mixed = pool(c49=0,c50=12,c51=12,c52=0,c53=12,c70=0)
        initial = (40,41,42,43)
        decision = route_brain_chem_loci(genes,mixed,6,initial)
        concept = route_brain_chem_loci(genes,mixed,8,initial)
        self.assertEqual(decision,(0,11,5,16))
        self.assertEqual(concept,(11,4,42,43))
        self.assertEqual(evaluate(bytes((5,0,0,0,0,0,0,0)),
                                  C1SVTable(chem0=concept[0])),11)
        self.assertEqual(initial,(40,41,42,43))

    def test_absent_receptors_preserve_provided_prior_state(self):
        _, genes, chemical_pool=fixtures()
        self.assertEqual(route_brain_chem_loci(genes,chemical_pool,7,(10,20,30,40)),
                         (10,20,30,40))

    def test_unrelated_loci_ignored_but_chem0_preserved_when_id_zero(self):
        entries=(Receptor(1,0,6,19,49,0,0,255,0),
                 Receptor(2,0,6,13,0,0,0,255,0),
                 Receptor(3,1,6,14,49,0,0,255,0))
        self.assertEqual(route_brain_chem_loci(entries,pool(c49=100),6,(10,20,30,40)),
                         (10,20,30,40))

    def test_duplicate_binding_rejected_not_assigned_last_wins(self):
        entries=(Receptor(1,0,6,13,49,0,0,255,0),
                 Receptor(2,0,6,13,50,0,0,255,0))
        with self.assertRaisesRegex(ValueError,"duplicate"):
            route_brain_chem_loci(entries,pool(c49=2,c50=3),6,(0,0,0,0))

    def test_wrong_inputs_rejected(self):
        g=Receptor(1,0,6,13,49,0,0,255,0)
        for target in (-1,256,True):
            with self.subTest(target=target), self.assertRaises(ValueError):
                route_brain_chem_loci((g,),pool(),target,(0,0,0,0))
        with self.assertRaises(ValueError):
            route_brain_chem_loci((g,),(0,),6,(0,0,0,0))
        with self.assertRaises(ValueError):
            route_brain_chem_loci((g,),pool(),6,(0,0,256,0))
        with self.assertRaises(TypeError):
            route_brain_chem_loci((object(),),pool(),6,(0,0,0,0))

    def test_no_mutation_and_determinism(self):
        _, genes, chemical_pool = fixtures()
        original = (30,31,32,33)
        a = route_brain_chem_loci(genes,chemical_pool,6,original)
        b = route_brain_chem_loci(genes,chemical_pool,6,original)
        self.assertEqual(a,b)
        self.assertEqual(original,(30,31,32,33))
        self.assertEqual(chemical_pool[49],12)


if __name__=="__main__":
    unittest.main()
