"""0.5.9.3.20: recuperación energética y relaciones con evidencia física."""
import sqlite3
import unittest
from pathlib import Path
from survival import ensure_needs, update_needs
from physical_links import snapshot, entities_for_action
from archive import History

ROOT=Path(__file__).resolve().parent.parent


class EnergyRecovery(unittest.TestCase):
    def test_rest_recovers_from_above_seventy_five_to_hundred(self):
        p={"needs":{"energia":78,"hidratacion":80,"nutricion":80,
                    "abrigo":80,"seguridad":80}, "clock_minutes":0}
        before=p["needs"]["energia"]
        update_needs(p,{},60,at_shelter=True,resting=True)
        self.assertGreater(p["needs"]["energia"],before)
        self.assertGreater(p["needs"]["energia"],75)
        update_needs(p,{},120,at_shelter=True,resting=True)
        self.assertEqual(p["needs"]["energia"],100)

    def test_inactivity_recovers_without_cliff_at_seventy_five(self):
        p={"needs":{"energia":75.4,"hidratacion":80,"nutricion":80,
                    "abrigo":80,"seguridad":80}}
        update_needs(p,{},60)
        self.assertGreater(p["needs"]["energia"],75.4)
        self.assertLessEqual(p["needs"]["energia"],100)

    def test_activity_still_consumes_energy(self):
        p={"needs":{"energia":86,"hidratacion":80,"nutricion":80,
                    "abrigo":80,"seguridad":80}}
        update_needs(p,{},60,active=True)
        self.assertLess(p["needs"]["energia"],86)

    def test_recovery_does_not_change_cap_or_hydration_policy(self):
        p={"needs":{"energia":99,"hidratacion":81,"nutricion":81,
                    "abrigo":80,"seguridad":80}}
        update_needs(p,{},60,at_shelter=True,resting=True)
        self.assertEqual(p["needs"]["energia"],100)
        self.assertLess(p["needs"]["hidratacion"],81)


class PhysicalRelationships(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(":memory:")
        self.archive=History(self.db)
        self.journal={"id":"j-1","text":"Reuní materiales y fabriqué una herramienta.",
                      "when":"Día 2 · 12:00"}
        self.archive.add("journal",self.journal)

    def tearDown(self):
        self.db.close()

    def test_material_gain_is_a_delta_not_a_fake_item(self):
        self.archive.add("measurement",{
            "id":"med-wood","journal_id":"j-1","when":"Día 2 · 12:01",
            "op":"gather","success":True,
            "inventory_delta":{"madera":2,"piedra":-1}})
        rows=self.archive.relations_for("journal","j-1")
        mats=[r for r in rows if r["category"]=="material"]
        self.assertEqual(len(mats),2)
        self.assertTrue(any("+2" in m["title"] and "madera" in m["title"] for m in mats))
        self.assertTrue(any("-1" in m["title"] and "piedra" in m["title"] for m in mats))
        self.assertFalse(any(r["category"]=="tool" for r in rows))

    def test_unrelated_measurement_is_not_linked(self):
        self.archive.add("measurement",{
            "id":"med-other","journal_id":"j-other","op":"gather",
            "inventory_delta":{"madera":6}})
        self.assertFalse(any(r["category"]=="material" for r in self.archive.relations_for("journal","j-1")))

    def test_tool_creation_by_id_and_old_revision(self):
        w={"structures":[]}
        p={"items":[]}
        before=snapshot(w,p)
        p["items"]=[{"id":"t-1","name":"Punta mineral","revision":1}]
        effects=entities_for_action(before,w,p,{"op":"craft"},
                    {"condition":"intemperie","success":True})
        self.assertEqual(effects,[{"category":"tool","id":"t-1","relation":"creada"}])
        self.archive.add("tool",p["items"][0])
        self.archive.add("measurement",{
            "id":"med-craft","journal_id":"j-1","op":"craft",
            "when":"Día 2 · 12:02","entity_links":effects})
        rows=self.archive.relations_for("journal","j-1")
        self.assertTrue(any(r["category"]=="tool" and r["id"]=="t-1"
                            and r["phase"]=="new" for r in rows))

    def test_structure_modified_and_rest_used(self):
        w={"structures":[{"id":"b-1","name":"Refugio","pos":[15,10,0],
                          "revision":1,"category":"habitaculo"}]}
        p={"items":[]}
        before=snapshot(w,p)
        w["structures"][0]["revision"]=2
        effects=entities_for_action(before,w,p,{"op":"modify"},
                    {"condition":"intemperie","success":True})
        self.assertEqual(effects[0]["relation"],"modificada")
        rested=entities_for_action(snapshot(w,p),w,p,{"op":"rest"},{
            "condition":"refugio","start":{"position":[15,10,0]},"success":True})
        self.assertIn({"category":"construction","id":"b-1","relation":"descanso_en"},rested)

    def test_duplicate_names_cannot_fabricate_specific_item(self):
        p={"items":[{"id":"a","name":"Punta","revision":1},
                    {"id":"b","name":"Punta","revision":1}]}
        effects=entities_for_action(snapshot({"structures":[]},p),
                  {"structures":[]},p,{"op":"use","item":"Punta"},
                  {"condition":"intemperie","success":True})
        self.assertEqual(effects,[])


class UiContract(unittest.TestCase):
    def test_optional_project_is_accepted(self):
        from brain import normalize_decision
        choice=normalize_decision({"cuaderno":"Camino libremente.",
            "plan":[{"op":"explore"}],"accion_proyecto":"sin_proyecto"})
        self.assertEqual(choice["accion_proyecto"],"sin_proyecto")

    def test_all_four_features_present(self):
        html=(ROOT/"interfaz.html").read_text("utf-8")
        self.assertIn("function enforceAccordionGroup(node)",html)
        self.assertIn("function assignAccordionGroups()",html)
        self.assertIn("function recentTabEntry(t)",html)
        self.assertIn("function relocateExplainer()",html)
        self.assertIn("section-help-popover",html)
        self.assertIn("record-material",html)
        self.assertIn("data-skill-index",html)
        self.assertIn("filtrar",html.lower())
        self.assertEqual(html.count('id="catchup-shortcut"'),1)
        self.assertIn('class="catchup-dock"',html)
        self.assertIn(".panel.third>.catchup-dock{flex:none;position:sticky;bottom:0",html)
        self.assertIn('class="activity-meta"',html)
        self.assertNotIn('avance de esta actividad',html)
        self.assertNotIn('Las reservas varían con el tiempo.',html)
        self.assertIn('.needline.need-inactive{opacity:',html)
        self.assertNotIn('sin el antiguo límite de 75',html)



if __name__=="__main__":
    unittest.main()
